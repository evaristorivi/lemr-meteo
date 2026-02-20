"""
Módulo para obtener datos meteorológicos de ubicaciones sin servicio METAR
"""
import requests
from typing import Optional, Dict
from datetime import datetime, timedelta
import config


def _compute_fog_risk(date_str: str, hourly_forecast: list) -> dict:
    """
    Evalúa el riesgo de niebla matinal para una fecha dada.
    Analiza desde las 22:00 de la noche previa hasta las 13:00 del día,
    cubriendo tanto la formación nocturna como la persistencia en horario operativo.

    Criterios (niebla de radiación / advectiva, típica en La Morgal):
      - Spread T−Td ≤ 3°C  (condición necesaria; ≤2°C = riesgo alto)
      - Viento ≤ 10 km/h      (>10 mezcla y disipa)
      - Sin precipitación activa (pp < 30%)
      - Visibilidad < 5 km     (refuerza, <1 km = confirmación)
      - WX code 45/48          (niebla detectada directamente por el modelo)
    """
    target_dt = datetime.fromisoformat(date_str)
    prev_date = (target_dt - timedelta(days=1)).strftime('%Y-%m-%d')

    fog_hours = [
        h for h in hourly_forecast
        if len(h.get('time', '')) >= 13
        and (
            (h['time'][:10] == prev_date and int(h['time'][11:13]) >= 22)
            or (h['time'][:10] == date_str and int(h['time'][11:13]) <= 13)
        )
    ]

    if not fog_hours:
        return {'level': None}

    risky = []
    for h in fog_hours:
        temp = h.get('temperature')
        dp   = h.get('dewpoint')
        wind = h.get('wind_speed') or 0
        pp   = h.get('precipitation_prob') or 0
        wx   = h.get('weather_code') or 0
        vis  = h.get('visibility')  # ya en km

        if pp > 30:
            continue  # lluvia activa inhibe niebla de radiación

        # Niebla confirmada por el modelo WMO
        if wx in (45, 48):
            risky.append({'time': h['time'][11:16], 'spread': 0.0,
                          'wind': round(wind, 1), 'score': 5, 'confirmed': True})
            continue

        if temp is None or dp is None:
            continue

        spread = temp - dp
        score  = 0

        if spread <= 2:
            score += 2
        elif spread <= 3:
            score += 1
        else:
            continue  # spread > 3°C → sin riesgo

        if wind <= 5:
            score += 2
        elif wind <= 10:
            score += 1

        if vis is not None:
            if vis < 1:
                score += 2
            elif vis < 5:
                score += 1

        if score >= 2:
            risky.append({'time': h['time'][11:16], 'spread': round(spread, 1),
                          'wind': round(wind, 1), 'score': score, 'confirmed': False})

    if not risky:
        return {'level': 'BAJO'}

    max_score = max(r['score'] for r in risky)
    confirmed = any(r.get('confirmed') for r in risky)
    best      = max(risky, key=lambda r: r['score'])
    spreads   = [r['spread'] for r in risky if not r.get('confirmed')]

    if confirmed or max_score >= 4:
        level = 'ALTO'
    elif max_score >= 3:
        level = 'MODERADO'
    else:
        level = 'BAJO'

    return {
        'level': level,
        'peak_hour': best['time'],
        'min_spread': min(spreads) if spreads else None,
        'n_hours': len(risky),
        # Horas con riesgo dentro del horario operativo (09:00-13:00)
        'operational_hours': sorted({
            r['time'] for r in risky
            if r['time'] >= '09:00' and r['time'] <= '13:00'
        }),
    }


def get_weather_forecast(lat: float, lon: float, location_name: str = "") -> Optional[Dict]:
    """
    Obtiene el pronóstico meteorológico para una ubicación dada
    Usa Open-Meteo API (gratuita, sin necesidad de API key)
    
    Args:
        lat: Latitud de la ubicación
        lon: Longitud de la ubicación
        location_name: Nombre opcional de la ubicación
    
    Returns:
        Diccionario con datos meteorológicos o None si hay error
    """
    try:
        # Parámetros para la API de Open-Meteo
        params = {
            'latitude': lat,
            'longitude': lon,
            'current': [
                'temperature_2m',
                'relative_humidity_2m',
                'apparent_temperature',
                'precipitation',
                'weather_code',
                'cloud_cover',
                'pressure_msl',
                'wind_speed_10m',
                'wind_direction_10m',
                'wind_gusts_10m',
                'cape'
            ],
            'hourly': [
                'temperature_2m',
                'dewpoint_2m',
                'precipitation_probability',
                'weather_code',
                'cloud_cover',
                'cloud_cover_low',
                'cloud_cover_mid',
                'cloud_cover_high',
                'visibility',
                'wind_speed_10m',
                'wind_direction_10m',
                'wind_gusts_10m',
                'freezing_level_height',
                'snow_depth',
                'is_day'
            ],
            'daily': [
                'temperature_2m_max',
                'temperature_2m_min',
                'dewpoint_2m_max',
                'dewpoint_2m_min',
                'sunrise',
                'sunset',
                'precipitation_sum',
                'precipitation_hours',
                'wind_speed_10m_max',
                'wind_gusts_10m_max',
                'wind_direction_10m_dominant',
                'weather_code',
                'cape_max',
                'precipitation_probability_max',
                'sunshine_duration'
            ],
            'timezone': 'Europe/Madrid',
            'forecast_days': 4  # Hoy + 3 días siguientes
        }
        
        # Intentar hasta 2 veces con timeout generoso (red lenta / servidor ocupado)
        last_exc = None
        response = None
        for _attempt in range(2):
            try:
                response = requests.get(config.OPEN_METEO_API, params=params, timeout=20)
                response.raise_for_status()
                break
            except requests.exceptions.Timeout as _e:
                last_exc = _e
                print(f"⏱️ Open-Meteo timeout (intento {_attempt + 1}/2), reintentando...")
            except requests.exceptions.RequestException as _e:
                last_exc = _e
                break
        if response is None or not response.ok:
            raise last_exc or RuntimeError("Open-Meteo no respondió")
        
        data = response.json()
        
        # Formatear datos actuales
        current = data.get('current', {})
        current_weather = {
            'location': location_name or f"Lat: {lat}, Lon: {lon}",
            'time': current.get('time', ''),
            'temperature': current.get('temperature_2m'),
            'feels_like': current.get('apparent_temperature'),
            'humidity': current.get('relative_humidity_2m'),
            'precipitation': current.get('precipitation'),
            'weather_code': current.get('weather_code'),
            'cloud_cover': current.get('cloud_cover'),
            'pressure': current.get('pressure_msl'),
            'wind_speed': current.get('wind_speed_10m'),
            'wind_direction': current.get('wind_direction_10m'),
            'wind_gusts': current.get('wind_gusts_10m'),
            'cape': current.get('cape'),  # Convective Available Potential Energy (J/kg)
        }
        
        # Añadir pronóstico por horas (próximas 24 horas)
        hourly = data.get('hourly', {})
        hourly_forecast = []
        
        if hourly.get('time'):
            for i in range(len(hourly['time'])):
                hourly_forecast.append({
                    'time': hourly['time'][i],
                    'temperature': hourly['temperature_2m'][i] if hourly.get('temperature_2m') else None,
                    'dewpoint': hourly['dewpoint_2m'][i] if hourly.get('dewpoint_2m') else None,
                    'precipitation_prob': hourly['precipitation_probability'][i] if hourly.get('precipitation_probability') else None,
                    'weather_code': hourly['weather_code'][i] if hourly.get('weather_code') else None,
                    'cloud_cover': hourly['cloud_cover'][i] if hourly.get('cloud_cover') else None,
                    'cloud_cover_low': hourly['cloud_cover_low'][i] if hourly.get('cloud_cover_low') else None,
                    'cloud_cover_mid': hourly['cloud_cover_mid'][i] if hourly.get('cloud_cover_mid') else None,
                    'cloud_cover_high': hourly['cloud_cover_high'][i] if hourly.get('cloud_cover_high') else None,
                    'visibility': hourly['visibility'][i] / 1000 if hourly.get('visibility') else None,  # Convertir metros a km
                    'wind_speed': hourly['wind_speed_10m'][i] if hourly.get('wind_speed_10m') else None,
                    'wind_direction': hourly['wind_direction_10m'][i] if hourly.get('wind_direction_10m') else None,
                    'wind_gusts': hourly['wind_gusts_10m'][i] if hourly.get('wind_gusts_10m') else None,
                    'freezing_level_height': hourly['freezing_level_height'][i] if hourly.get('freezing_level_height') else None,
                    'snow_depth': hourly['snow_depth'][i] if hourly.get('snow_depth') else None,
                    'is_day': hourly['is_day'][i] if hourly.get('is_day') else None,  # 1 = dia, 0 = noche
                })
        
        # Índice de horas diurnas por fecha para cálculos Phase 4
        # Filtra solo horas con is_day==1 para análisis relevante para pilotos
        hourly_day_by_date: dict = {}
        for h in hourly_forecast:
            if h.get('is_day') != 1:
                continue
            date_key = h['time'][:10]  # 'YYYY-MM-DD'
            hourly_day_by_date.setdefault(date_key, []).append(h)

        def _phase4_summary(day_rows: list) -> dict:
            """Calcula resumen de parámetros Phase 4 para una lista de horas diurnas."""
            result = {}

            # 1️⃣ Freezing level mínimo del día (metros y pies)
            fl_vals = [(h['freezing_level_height'], h['time']) for h in day_rows if h.get('freezing_level_height') is not None]
            if fl_vals:
                min_fl_m, min_fl_t = min(fl_vals, key=lambda x: x[0])
                result['freezing_level_min_m'] = round(min_fl_m)
                result['freezing_level_min_ft'] = round(min_fl_m * 3.28084)
                result['freezing_level_min_time'] = min_fl_t[11:16]  # 'HH:MM'

            # 2️⃣ Turbulencia mecánica: máx diferencia racha-viento (kt) del día
            turb_diffs = []
            for h in day_rows:
                wind_kmh = h.get('wind_speed')
                gust_kmh = h.get('wind_gusts')
                if wind_kmh is not None and gust_kmh is not None:
                    diff_kt = (gust_kmh - wind_kmh) / 1.852
                    turb_diffs.append(diff_kt)
            if turb_diffs:
                result['turb_diff_max_kt'] = round(max(turb_diffs), 1)

            # 5️⃣ Nieve máxima del día (m → cm)
            snow_vals = [h['snow_depth'] for h in day_rows if h.get('snow_depth') is not None]
            if snow_vals:
                max_snow_m = max(snow_vals)
                result['snow_max_cm'] = round(max_snow_m * 100, 1)

            # 6️⃣ Nubes por capa: cobertura máxima del día
            for key, field in [('cloud_low_max', 'cloud_cover_low'),
                                ('cloud_mid_max', 'cloud_cover_mid'),
                                ('cloud_high_max', 'cloud_cover_high')]:
                vals = [h[field] for h in day_rows if h.get(field) is not None]
                if vals:
                    result[key] = round(max(vals))

            # 7️⃣ Patrón temporal mañana (09-13h) vs tarde (14-21h)
            # Permite detectar si el día empeora/mejora a lo largo de la jornada
            for period_key, h_min, h_max in [('man', 9, 13), ('tard', 14, 21)]:
                rows_p = [h for h in day_rows
                          if h.get('time') and h_min <= int(h['time'][11:13]) <= h_max]
                if not rows_p:
                    continue
                gusts = [h['wind_gusts'] for h in rows_p if h.get('wind_gusts') is not None]
                winds = [h['wind_speed']  for h in rows_p if h.get('wind_speed')  is not None]
                cl_lo = [h['cloud_cover_low']  for h in rows_p if h.get('cloud_cover_low')  is not None]
                cl_mi = [h['cloud_cover_mid']  for h in rows_p if h.get('cloud_cover_mid')  is not None]
                cl_hi = [h['cloud_cover_high'] for h in rows_p if h.get('cloud_cover_high') is not None]
                pp    = [h['precipitation_prob'] for h in rows_p if h.get('precipitation_prob') is not None]
                # turbulencia mecánica por período (diff racha-viento en kt)
                turb_p = []
                for h in rows_p:
                    w = h.get('wind_speed')
                    g = h.get('wind_gusts')
                    if w is not None and g is not None:
                        turb_p.append((g - w) / 1.852)
                if gusts:  result[f'gust_{period_key}_max']       = round(max(gusts))
                if winds:  result[f'wind_{period_key}_max']       = round(max(winds))
                if cl_lo:  result[f'cloud_low_{period_key}_max']  = round(max(cl_lo))
                if cl_mi:  result[f'cloud_mid_{period_key}_max']  = round(max(cl_mi))
                if cl_hi:  result[f'cloud_high_{period_key}_max'] = round(max(cl_hi))
                if pp:     result[f'precip_prob_{period_key}_max'] = round(max(pp))
                if turb_p: result[f'turb_diff_{period_key}_max']  = round(max(turb_p), 1)

            # Hora del pico de rachas (útil para planificar franja horaria)
            gust_by_hour = [(h.get('wind_gusts', 0), h['time'][11:16])
                            for h in day_rows if h.get('wind_gusts') is not None]
            if gust_by_hour:
                result['peak_gust_hour'] = max(gust_by_hour, key=lambda x: x[0])[1]

            return result

        # Añadir pronóstico diario (4 días)
        daily = data.get('daily', {})
        daily_forecast = []
        
        if daily.get('time'):
            for i in range(len(daily['time'])):
                date_str = daily['time'][i]
                entry = {
                    'date': date_str,
                    'temp_max': daily['temperature_2m_max'][i] if daily.get('temperature_2m_max') else None,
                    'temp_min': daily['temperature_2m_min'][i] if daily.get('temperature_2m_min') else None,
                    'dewpoint_max': daily['dewpoint_2m_max'][i] if daily.get('dewpoint_2m_max') else None,
                    'dewpoint_min': daily['dewpoint_2m_min'][i] if daily.get('dewpoint_2m_min') else None,
                    'sunrise': daily['sunrise'][i] if daily.get('sunrise') else None,
                    'sunset': daily['sunset'][i] if daily.get('sunset') else None,
                    'precipitation': daily['precipitation_sum'][i] if daily.get('precipitation_sum') else None,
                    'precipitation_hours': daily['precipitation_hours'][i] if daily.get('precipitation_hours') else None,
                    'wind_max': daily['wind_speed_10m_max'][i] if daily.get('wind_speed_10m_max') else None,
                    'wind_gusts_max': daily['wind_gusts_10m_max'][i] if daily.get('wind_gusts_10m_max') else None,
                    'wind_direction_dominant': daily['wind_direction_10m_dominant'][i] if daily.get('wind_direction_10m_dominant') else None,
                    'weather_code': daily['weather_code'][i] if daily.get('weather_code') else None,
                    'cape_max': daily['cape_max'][i] if daily.get('cape_max') else None,
                    'precipitation_prob_max': daily['precipitation_probability_max'][i] if daily.get('precipitation_probability_max') else None,
                    'sunshine_duration': daily['sunshine_duration'][i] if daily.get('sunshine_duration') else None,
                }
                # Enriquecer con resúmenes Phase 4 calculados en Python
                day_rows = hourly_day_by_date.get(date_str, [])
                entry.update(_phase4_summary(day_rows))
                entry['fog_risk'] = _compute_fog_risk(date_str, hourly_forecast)
                daily_forecast.append(entry)
        
        return {
            'current': current_weather,
            'hourly_forecast': hourly_forecast,
            'daily_forecast': daily_forecast
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Error obteniendo datos meteorológicos: {e}")
        return None
    except Exception as e:
        print(f"Error procesando datos meteorológicos: {e}")
        return None


def weather_code_to_description(code: int) -> str:
    """
    Convierte el código WMO weather code a descripción en español
    
    Args:
        code: Código WMO
    
    Returns:
        Descripción del tiempo en español
    """
    weather_codes = {
        0: "Cielo despejado",
        1: "Principalmente despejado",
        2: "Parcialmente nublado",
        3: "Nublado",
        45: "Niebla",
        48: "Niebla con escarcha",
        51: "Llovizna ligera",
        53: "Llovizna moderada",
        55: "Llovizna intensa",
        61: "Lluvia ligera",
        63: "Lluvia moderada",
        65: "Lluvia intensa",
        71: "Nevada ligera",
        73: "Nevada moderada",
        75: "Nevada intensa",
        77: "Granos de nieve",
        80: "Chubascos ligeros",
        81: "Chubascos moderados",
        82: "Chubascos violentos",
        85: "Chubascos de nieve ligeros",
        86: "Chubascos de nieve intensos",
        95: "Tormenta",
        96: "Tormenta con granizo ligero",
        99: "Tormenta con granizo intenso"
    }
    
    return weather_codes.get(code, f"Código desconocido: {code}")


def format_weather_report(weather_data: Dict) -> str:
    """
    Formatea los datos meteorológicos en un reporte legible
    
    Args:
        weather_data: Diccionario con datos meteorológicos
    
    Returns:
        String con el reporte formateado
    """
    if not weather_data:
        return "No se pudieron obtener datos meteorológicos"
    
    current = weather_data.get('current', {})
    
    report = f"📍 **{current.get('location', 'Ubicación')}**\n\n"
    report += f"🕐 Actualizado: {current.get('time', 'N/A')}\n\n"
    report += "**CONDICIONES ACTUALES:**\n"
    
    temp = current.get('temperature')
    if temp is not None:
        report += f"🌡️ Temperatura: {temp}°C"
        feels_like = current.get('feels_like')
        if feels_like is not None:
            report += f" (sensación: {feels_like}°C)"
        report += "\n"
    
    weather_code = current.get('weather_code')
    if weather_code is not None:
        report += f"☁️ Condiciones: {weather_code_to_description(weather_code)}\n"
    
    humidity = current.get('humidity')
    if humidity is not None:
        report += f"💧 Humedad: {humidity}%\n"
    
    wind_speed = current.get('wind_speed')
    wind_dir = current.get('wind_direction')
    if wind_speed is not None:
        report += f"💨 Viento: {wind_speed} km/h"
        if wind_dir is not None:
            report += f" desde {wind_dir}°"
        wind_gusts = current.get('wind_gusts')
        if wind_gusts is not None:
            report += f" (rachas: {wind_gusts} km/h)"
        report += "\n"
    
    cloud_cover = current.get('cloud_cover')
    if cloud_cover is not None:
        report += f"☁️ Nubosidad: {cloud_cover}%\n"
    
    pressure = current.get('pressure')
    if pressure is not None:
        report += f"🔽 Presión: {pressure} hPa\n"
    
    precip = current.get('precipitation')
    if precip is not None and precip > 0:
        report += f"🌧️ Precipitación: {precip} mm\n"
    
    # Añadir pronóstico de 4 días
    daily = weather_data.get('daily_forecast', [])
    if daily and len(daily) > 0:
        report += "\n━━━━━━━━━━━━━━━━━━━━\n"
        report += "**PRONÓSTICO 4 DÍAS (ULM - Solo vuelo diurno):**\n\n"
        
        day_names = ["📅 HOY", "📅 MAÑANA", "📅 PASADO MAÑANA", "📅 DENTRO DE 3 DÍAS"]
        
        for i, day in enumerate(daily[:4]):
            day_label = day_names[i] if i < len(day_names) else f"Día {i+1}"
            report += f"{day_label}\n"
            
            # Horarios de sol
            sunrise = day.get('sunrise', 'N/A')
            sunset = day.get('sunset', 'N/A')
            if 'T' in sunrise:
                sunrise = sunrise.split('T')[1][:5]
            if 'T' in sunset:
                sunset = sunset.split('T')[1][:5]
            
            report += f"🌅 Amanecer: {sunrise} | 🌇 Atardecer: {sunset}\n"
            
            # Temperaturas
            temp_min = day.get('temp_min')
            temp_max = day.get('temp_max')
            if temp_min is not None and temp_max is not None:
                report += f"🌡️ Temp: {temp_min}°C - {temp_max}°C\n"
            
            # Viento
            wind_max = day.get('wind_max')
            wind_gusts_max = day.get('wind_gusts_max')
            if wind_max is not None:
                report += f"💨 Viento máx: {wind_max} km/h"
                if wind_gusts_max is not None:
                    report += f" (rachas: {wind_gusts_max} km/h)"
                report += "\n"
            
            # Precipitación
            precip_sum = day.get('precipitation')
            if precip_sum is not None and precip_sum > 0:
                report += f"🌧️ Lluvia: {precip_sum} mm\n"
            
            # Condiciones
            day_weather_code = day.get('weather_code')
            if day_weather_code is not None:
                report += f"☁️ {weather_code_to_description(day_weather_code)}\n"
            
            if i < len(daily) - 1:
                report += "\n"
    
    return report


if __name__ == '__main__':
    # Test
    print("Probando obtención de datos meteorológicos para La Morgal...")
    weather = get_weather_forecast(
        config.LA_MORGAL_COORDS['lat'],
        config.LA_MORGAL_COORDS['lon'],
        config.LA_MORGAL_COORDS['name']
    )
    
    if weather:
        print(format_weather_report(weather))
    else:
        print("No se pudieron obtener datos meteorológicos")
