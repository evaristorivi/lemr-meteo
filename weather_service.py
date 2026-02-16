"""
Módulo para obtener datos meteorológicos de ubicaciones sin servicio METAR
"""
import requests
from typing import Optional, Dict
from datetime import datetime
import config


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
                'wind_gusts_10m'
            ],
            'hourly': [
                'temperature_2m',
                'precipitation_probability',
                'weather_code',
                'cloud_cover',
                'visibility',
                'wind_speed_10m',
                'wind_direction_10m'
            ],
            'daily': [
                'temperature_2m_max',
                'temperature_2m_min',
                'sunrise',
                'sunset',
                'precipitation_sum',
                'wind_speed_10m_max',
                'wind_gusts_10m_max',
                'weather_code'
            ],
            'timezone': 'Europe/Madrid',
            'forecast_days': 3  # Hoy, mañana y pasado
        }
        
        response = requests.get(config.OPEN_METEO_API, params=params, timeout=10)
        response.raise_for_status()
        
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
        }
        
        # Añadir pronóstico por horas (próximas 24 horas)
        hourly = data.get('hourly', {})
        hourly_forecast = []
        
        if hourly.get('time'):
            for i in range(min(24, len(hourly['time']))):
                hourly_forecast.append({
                    'time': hourly['time'][i],
                    'temperature': hourly['temperature_2m'][i] if hourly.get('temperature_2m') else None,
                    'precipitation_prob': hourly['precipitation_probability'][i] if hourly.get('precipitation_probability') else None,
                    'weather_code': hourly['weather_code'][i] if hourly.get('weather_code') else None,
                    'cloud_cover': hourly['cloud_cover'][i] if hourly.get('cloud_cover') else None,
                    'visibility': hourly['visibility'][i] / 1000 if hourly.get('visibility') else None,  # Convertir metros a km
                    'wind_speed': hourly['wind_speed_10m'][i] if hourly.get('wind_speed_10m') else None,
                    'wind_direction': hourly['wind_direction_10m'][i] if hourly.get('wind_direction_10m') else None,
                })
        
        # Añadir pronóstico diario (3 días)
        daily = data.get('daily', {})
        daily_forecast = []
        
        if daily.get('time'):
            for i in range(len(daily['time'])):
                daily_forecast.append({
                    'date': daily['time'][i],
                    'temp_max': daily['temperature_2m_max'][i] if daily.get('temperature_2m_max') else None,
                    'temp_min': daily['temperature_2m_min'][i] if daily.get('temperature_2m_min') else None,
                    'sunrise': daily['sunrise'][i] if daily.get('sunrise') else None,
                    'sunset': daily['sunset'][i] if daily.get('sunset') else None,
                    'precipitation': daily['precipitation_sum'][i] if daily.get('precipitation_sum') else None,
                    'wind_max': daily['wind_speed_10m_max'][i] if daily.get('wind_speed_10m_max') else None,
                    'wind_gusts_max': daily['wind_gusts_10m_max'][i] if daily.get('wind_gusts_10m_max') else None,
                    'weather_code': daily['weather_code'][i] if daily.get('weather_code') else None,
                })
        
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
    
    # Añadir pronóstico de 3 días
    daily = weather_data.get('daily_forecast', [])
    if daily and len(daily) > 0:
        report += "\n━━━━━━━━━━━━━━━━━━━━\n"
        report += "**PRONÓSTICO 3 DÍAS (ULM - Solo vuelo diurno):**\n\n"
        
        day_names = ["📅 HOY", "📅 MAÑANA", "📅 PASADO MAÑANA"]
        
        for i, day in enumerate(daily[:3]):
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
