"""
Módulo para generar METAR sintético desde datos meteorológicos de Open-Meteo.
Basado en especificaciones ICAO Annex 3.
"""
import math
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Dict


def calculate_dewpoint(temperature_c: float, humidity_percent: float) -> float:
    """
    Calcula el punto de rocío usando la fórmula Magnus.
    
    Args:
        temperature_c: Temperatura en grados Celsius
        humidity_percent: Humedad relativa en porcentaje (0-100)
    
    Returns:
        Punto de rocío en grados Celsius
    """
    if humidity_percent <= 0 or humidity_percent > 100:
        return temperature_c - 5  # Estimación conservadora
    
    a = 17.27
    b = 237.7
    
    alpha = ((a * temperature_c) / (b + temperature_c)) + math.log(humidity_percent / 100.0)
    dewpoint = (b * alpha) / (a - alpha)
    
    return dewpoint


def kmh_to_knots(speed_kmh: float) -> int:
    """Convierte km/h a nudos (kt)."""
    return round(speed_kmh * 0.539957)


def get_weather_phenomena(weather_code: int) -> str:
    """
    Mapea weather_code de Open-Meteo a fenómenos meteorológicos METAR.
    
    Basado en WMO Code Table 4677:
    https://open-meteo.com/en/docs
    
    Args:
        weather_code: Código WMO de Open-Meteo
    
    Returns:
        Fenómeno meteorológico en formato METAR (ej: "RA", "+SN", "FG")
    """
    weather_map = {
        0: "",      # Clear sky
        1: "",      # Mainly clear
        2: "",      # Partly cloudy
        3: "",      # Overcast
        45: "FG",   # Fog
        48: "FG",   # Depositing rime fog
        51: "DZ",   # Drizzle: Light
        53: "DZ",   # Drizzle: Moderate
        55: "+DZ",  # Drizzle: Dense intensity
        56: "-FZDZ",  # Freezing Drizzle: Light
        57: "FZDZ",   # Freezing Drizzle: Dense
        61: "-RA",  # Rain: Slight
        63: "RA",   # Rain: Moderate
        65: "+RA",  # Rain: Heavy
        66: "-FZRA",  # Freezing Rain: Light
        67: "FZRA",   # Freezing Rain: Heavy
        71: "-SN",  # Snow fall: Slight
        73: "SN",   # Snow fall: Moderate
        75: "+SN",  # Snow fall: Heavy
        77: "SG",   # Snow grains
        80: "-SHRA",  # Rain showers: Slight
        81: "SHRA",   # Rain showers: Moderate
        82: "+SHRA",  # Rain showers: Violent
        85: "-SHSN",  # Snow showers: Slight
        86: "+SHSN",  # Snow showers: Heavy
        95: "TS",   # Thunderstorm: Slight or moderate
        96: "TSRA",  # Thunderstorm with slight hail
        99: "+TSRA", # Thunderstorm with heavy hail
    }
    
    return weather_map.get(weather_code, "")


# Visibilidad máxima (km) por weather_code WMO cuando hay precipitación/fenómeno.
# Se usa para limitar el valor de Open-Meteo cuando el modelo es demasiado optimista.
_VIS_CAP_KM: dict = {
    # Niebla
    45: 0.8,  48: 0.8,
    # Llovizna
    51: 8.0,  53: 6.0,  55: 3.0,
    # Llovizna engelante
    56: 2.0,  57: 1.5,
    # Lluvia
    61: 8.0,  63: 6.0,  65: 3.0,
    # Lluvia engelante
    66: 2.0,  67: 1.5,
    # Nieve
    71: 8.0,  73: 5.0,  75: 2.0,
    # Granos de nieve
    77: 5.0,
    # Chubascos de lluvia
    80: 8.0,  81: 6.0,  82: 2.0,
    # Chubascos de nieve
    85: 6.0,  86: 2.0,
    # Tormenta
    95: 3.0,  96: 1.5,  99: 1.5,
}


def get_visibility(weather_code: int, cloud_cover: int) -> str:
    """
    Estima visibilidad basándose en weather_code WMO (fallback cuando Open-Meteo
    no proporciona visibility_km directo).

    Args:
        weather_code: Código WMO de Open-Meteo
        cloud_cover: Porcentaje de cobertura nubosa (no usado actualmente, reservado)

    Returns:
        Visibilidad en formato METAR (ej: "9999", "5000", "0800")
    """
    cap = _VIS_CAP_KM.get(weather_code)
    if cap is None:
        return "9999"  # Cielo despejado / nuboso sin precipitación
    vis_m = int(cap * 1000)
    if vis_m >= 9999:
        return "9999"
    return f"{round(vis_m / 100) * 100:04d}"


def generate_metar_lemr(
    current_weather: Dict,
    icao: str = "LEMR",
    elevation_m: int = 180,
    visibility_km: Optional[float] = None,
    dewpoint_c: Optional[float] = None,
    cloud_cover_low: Optional[int] = None,
) -> Optional[str]:
    """
    Genera un METAR sintético para LEMR basándose en datos de Open-Meteo.

    Args:
        current_weather: Diccionario con datos actuales de Open-Meteo (current)
        icao: Código ICAO del aeródromo
        elevation_m: Elevación del aeródromo en metros
        visibility_km: Visibilidad real en km de Open-Meteo hourly (más precisa
                       que inferirla solo del weather_code)
        dewpoint_c: Punto de rocío directo del modelo (°C), procedente de
                    hourly_forecast[0]['dewpoint']. Más preciso que la fórmula
                    Magnus derivada de la humedad relativa de 'current'.
        cloud_cover_low: Cobertura de nubes bajas (<2000m) en % de hourly_forecast[0].
                         Se usa para emitir FEW/SCT/BKN/OVC con altura estimada
                         por la fórmula LCL (T-Td)×400ft.

    Returns:
        String con METAR sintético en formato ICAO o None si faltan datos
    """
    try:
        # Extraer datos necesarios
        temp = current_weather.get("temperature")
        humidity = current_weather.get("humidity")
        wind_speed = current_weather.get("wind_speed")
        wind_dir = current_weather.get("wind_direction")
        wind_gusts = current_weather.get("wind_gusts")
        pressure = current_weather.get("pressure")
        cloud_cover = current_weather.get("cloud_cover", 0)
        weather_code = current_weather.get("weather_code", 0)
        time_str = current_weather.get("time", "")
        
        # Validar datos críticos
        if any(v is None for v in [temp, humidity, wind_speed, wind_dir, pressure]):
            return None
        
        # Fecha y hora en formato METAR (DDHHMM)
        if time_str:
            try:
                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                dt_utc = dt.astimezone(ZoneInfo("UTC"))
                day_hour = dt_utc.strftime("%d%H%M")
            except:
                dt_utc = datetime.now(ZoneInfo("UTC"))
                day_hour = dt_utc.strftime("%d%H%M")
        else:
            dt_utc = datetime.now(ZoneInfo("UTC"))
            day_hour = dt_utc.strftime("%d%H%M")
        
        # Viento
        wind_kt = kmh_to_knots(wind_speed)
        wind_dir_rounded = round(wind_dir / 10) * 10  # Redondear a 10°
        # Bug fix: norte magnético es 360 en METAR, no 000 (que significa calma)
        if wind_dir_rounded == 0 and wind_kt > 0:
            wind_dir_rounded = 360

        if wind_kt == 0:
            wind_group = "00000KT"  # Viento en calma
        elif wind_kt < 3:
            # ICAO Annex 3: VRB cuando velocidad < 3 kt (dirección inestable/no representativa)
            wind_group = f"VRB{wind_kt:02d}KT"
        elif wind_gusts and (wind_gusts - wind_speed) >= 18.5:  # ≥10 kt según ICAO Annex 3
            gusts_kt = kmh_to_knots(wind_gusts)
            wind_group = f"{wind_dir_rounded:03d}{wind_kt:02d}G{gusts_kt:02d}KT"
        else:
            wind_group = f"{wind_dir_rounded:03d}{wind_kt:02d}KT"

        # Visibilidad:
        # 1) Si hay weather_code con cap conocido, se aplica como techo máximo.
        #    Esto evita que Open-Meteo dé 10km con +RA o TS (modelos NWP son optimistas).
        # 2) Si Open-Meteo proporciona visibility_km, se usa min(valor_real, cap_código).
        # 3) Si no hay visibility_km, se usa el cap del código directamente.
        # ESPECIAL: niebla (45/48) siempre fuerza 0800 independientemente del modelo.
        vis_cap_km = _VIS_CAP_KM.get(weather_code)  # None = sin restricción por código
        if weather_code in [45, 48]:
            visibility = "0800"  # Niebla: forzado, el modelo no resuelve niebla de valle
        elif visibility_km is not None:
            # Limitar el valor real al máximo plausible para este weather_code
            effective_km = min(visibility_km, vis_cap_km) if vis_cap_km is not None else visibility_km
            vis_m = int(effective_km * 1000)
            if vis_m >= 9999:
                visibility = "9999"
            else:
                visibility = f"{max(100, round(vis_m / 100) * 100):04d}"
        else:
            visibility = get_visibility(weather_code, cloud_cover)
        
        # Fenómenos meteorológicos
        wx = get_weather_phenomena(weather_code)
        wx_str = f" {wx}" if wx else ""
        
        # Nubes: usar cloud_cover_low (capa <2000m) de hourly para emitir grupo real.
        # Altura de techo estimada por LCL: (T - Td) × 400 ft.
        # Si no hay nubes bajas, NCD (sin ceilómetro real, ICAO Annex 3).
        dp_for_lcl = dewpoint_c if dewpoint_c is not None else calculate_dewpoint(temp, humidity)
        lcl_ft = max(100, round((temp - dp_for_lcl) * 400 / 100) * 100)  # redondeado a 100ft
        lcl_hundreds = max(1, lcl_ft // 100)
        # Niebla implícita: T−Td ≤ 1°C con alta cobertura baja indica niebla/stratus
        # casi a nivel del suelo aunque Open-Meteo no emita código 45/48.
        # Esto ocurre porque los modelos NWP no resuelven niebla de valle/radiación.
        td_spread = temp - dp_for_lcl
        implicit_fog = (td_spread <= 1.0) and (cloud_cover_low is not None) and (cloud_cover_low > 87)

        if weather_code in [45, 48] or implicit_fog:
            # Niebla (explícita o implícita): forzar techo bajo y visibilidad degradada.
            # LCL muy bajo → OVC001-004 típico. Mínimo OVC001 para no salir de LIFR/IFR.
            fog_ceiling = min(lcl_hundreds, 4)  # máx 400 ft (OVC004), mínimo 100 ft
            clouds = f"OVC{max(1, fog_ceiling):03d}"
            # Si la visibilidad no estaba ya limitada por weather_code, forzarla.
            if weather_code not in [45, 48] and visibility == "9999":
                # T−Td ≤ 0.5 → niebla densa (≤300m), ≤1.0 → bruma/niebla (≤1000m)
                if td_spread <= 0.5:
                    visibility = "0300"
                    if not wx:
                        wx = "FG"
                        wx_str = " FG"
                else:
                    visibility = "1000"
                    if not wx:
                        wx = "BR"
                        wx_str = " BR"
        elif not cloud_cover_low:  # None o 0%
            clouds = "NCD"
        elif cloud_cover_low <= 25:
            clouds = f"FEW{lcl_hundreds:03d}"
        elif cloud_cover_low <= 50:
            clouds = f"SCT{lcl_hundreds:03d}"
        elif cloud_cover_low <= 87:
            clouds = f"BKN{lcl_hundreds:03d}"
        else:
            clouds = f"OVC{lcl_hundreds:03d}"
        
        # Temperatura y punto de rocío
        temp_int = round(temp)
        dewpoint = dewpoint_c if dewpoint_c is not None else calculate_dewpoint(temp, humidity)
        dewpoint_int = round(dewpoint)

        # Formato con signo para temperaturas negativas
        temp_sign = "M" if temp_int < 0 else ""
        dp_sign = "M" if dewpoint_int < 0 else ""
        temp_group = f"{temp_sign}{abs(temp_int):02d}/{dp_sign}{abs(dewpoint_int):02d}"

        # Presión (QNH)
        pressure_int = round(pressure)
        qnh = f"Q{pressure_int:04d}"

        # CAVOK: visibilidad ≥ 10km + sin fenómeno + sin nubes por debajo de 5000ft
        # Reemplaza los tres grupos (visibility + wx + clouds) según ICAO Annex 3.
        # Condición simplificada: 9999 + sin wx + NCD  (o nubes solo altas/medias)
        use_cavok = (
            visibility == "9999"
            and wx == ""
            and clouds == "NCD"
        )

        # Ensamblar METAR
        # Sin tendencia: este METAR es AUTO generado desde datos numéricos, sin observador.
        if use_cavok:
            metar = f"METAR {icao} {day_hour}Z AUTO {wind_group} CAVOK {temp_group} {qnh}"
        else:
            metar = f"METAR {icao} {day_hour}Z AUTO {wind_group} {visibility}{wx_str} {clouds} {temp_group} {qnh}"
        
        # Limpiar espacios dobles
        metar = " ".join(metar.split())
        
        return metar
        
    except Exception as e:
        print(f"Error generando METAR sintético: {e}")
        return None


def get_metar_disclaimer() -> str:
    """Devuelve el disclaimer para el METAR sintético."""
    return "⚠️ METAR estimado generado automáticamente desde Open-Meteo · NO OFICIAL · Solo informativo · Techo estimado por LCL (T−Td)×400ft usando solo nubes bajas (<2000m) · Nubes medias y altas no generan techo en este METAR"
