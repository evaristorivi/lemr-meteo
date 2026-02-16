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


def get_cloud_group(cloud_cover_percent: int, elevation_m: int = 180) -> str:
    """
    Mapea porcentaje de cobertura nubosa a grupo METAR.
    Estima altura de nubes basándose en elevación del aeródromo.
    
    Args:
        cloud_cover_percent: Cobertura de nubes en porcentaje (0-100)
        elevation_m: Elevación del aeródromo en metros (default: 180m LEMR)
    
    Returns:
        Grupo de nubes en formato METAR (ej: "SCT025", "BKN040", "FEW015")
    """
    if cloud_cover_percent <= 12:
        return "SKC"  # Sky clear / CAVOK
    
    # Estimar altura de base de nubes en función de elevación
    # LEMR está a 180m (590ft), asumimos nubes bajas típicas de Asturias
    base_height_ft = 2000 + (elevation_m * 2)  # Aproximación conservadora
    height_code = f"{int(base_height_ft / 100):03d}"
    
    if 13 <= cloud_cover_percent <= 25:
        return f"FEW{height_code}"  # Few (1-2 octas)
    elif 26 <= cloud_cover_percent <= 50:
        return f"SCT{height_code}"  # Scattered (3-4 octas)
    elif 51 <= cloud_cover_percent <= 87:
        return f"BKN{height_code}"  # Broken (5-7 octas)
    else:  # 88-100%
        return f"OVC{height_code}"  # Overcast (8 octas)


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


def get_visibility(weather_code: int, cloud_cover: int) -> str:
    """
    Estima visibilidad basándose en condiciones meteorológicas.
    
    Args:
        weather_code: Código WMO de condiciones meteorológicas
        cloud_cover: Porcentaje de cobertura nubosa
    
    Returns:
        Visibilidad en formato METAR (ej: "9999", "5000", "0800")
    """
    # Niebla o condiciones reducidas
    if weather_code in [45, 48]:
        return "0800"  # < 1km en niebla
    
    # Precipitación intensa
    if weather_code in [55, 65, 67, 75, 82, 86, 99]:
        return "3000"  # 3km en precipitación fuerte
    
    # Precipitación moderada
    if weather_code in [53, 63, 73, 81]:
        return "6000"  # 6km en precipitación moderada
    
    # Precipitación ligera
    if weather_code in [51, 61, 71, 80, 85]:
        return "8000"  # 8km en precipitación ligera
    
    # Condiciones buenas
    return "9999"  # 10km o más (CAVOK)


def generate_metar_lemr(current_weather: Dict, icao: str = "LEMR", elevation_m: int = 180) -> Optional[str]:
    """
    Genera un METAR sintético para LEMR basándose en datos de Open-Meteo.
    
    Args:
        current_weather: Diccionario con datos actuales de Open-Meteo
        icao: Código ICAO del aeródromo (default: LEMR)
        elevation_m: Elevación del aeródromo en metros (default: 180)
    
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
        if None in [temp, humidity, wind_speed, wind_dir, pressure]:
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
        
        if wind_kt < 1:
            wind_group = "00000KT"  # Viento en calma
        elif wind_gusts and wind_gusts > wind_speed + 5:
            gusts_kt = kmh_to_knots(wind_gusts)
            wind_group = f"{wind_dir_rounded:03d}{wind_kt:02d}G{gusts_kt:02d}KT"
        else:
            wind_group = f"{wind_dir_rounded:03d}{wind_kt:02d}KT"
        
        # Visibilidad
        visibility = get_visibility(weather_code, cloud_cover)
        
        # Fenómenos meteorológicos
        wx = get_weather_phenomena(weather_code)
        wx_str = f" {wx}" if wx else ""
        
        # Nubes
        clouds = get_cloud_group(cloud_cover, elevation_m)
        
        # Temperatura y punto de rocío
        temp_int = round(temp)
        dewpoint = calculate_dewpoint(temp, humidity)
        dewpoint_int = round(dewpoint)
        
        # Formato con signo para temperaturas negativas
        temp_sign = "M" if temp_int < 0 else ""
        dp_sign = "M" if dewpoint_int < 0 else ""
        temp_group = f"{temp_sign}{abs(temp_int):02d}/{dp_sign}{abs(dewpoint_int):02d}"
        
        # Presión (QNH)
        pressure_int = round(pressure)
        qnh = f"Q{pressure_int:04d}"
        
        # Ensamblar METAR
        metar = f"METAR {icao} {day_hour}Z AUTO {wind_group} {visibility}{wx_str} {clouds} {temp_group} {qnh} NOSIG"
        
        # Limpiar espacios dobles
        metar = " ".join(metar.split())
        
        return metar
        
    except Exception as e:
        print(f"Error generando METAR sintético: {e}")
        return None


def get_metar_disclaimer() -> str:
    """Devuelve el disclaimer para el METAR sintético."""
    return "⚠️ METAR estimado generado automáticamente desde Open-Meteo · NO OFICIAL · Solo informativo"
