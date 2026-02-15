"""
Configuración para meteorología aeronáutica LEMR
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde el directorio del propio script
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_PATH, override=True)

# Configuración Web
WEB_HOST = os.getenv('WEB_HOST', '127.0.0.1')
WEB_PORT = int(os.getenv('WEB_PORT', '8000'))

# Configuración de IA
AI_PROVIDER = os.getenv('AI_PROVIDER', 'github')  # 'github' o 'openai'
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Sistema de cascada automática de modelos
# El sistema prueba cada modelo en orden hasta encontrar uno disponible
AI_MODEL_CASCADE = [
    'gpt-4o',                          # ⭐ Mejor calidad, límite bajo (50/día)
    'gpt-4o-mini',                     # 🥈 Buena calidad, límite medio (150/día)
    'meta-llama-3.1-405b-instruct',   # 🔥 Gran modelo open source (límite alto)
    'phi-4',                           # 🚀 Modelo pequeño pero eficiente de Microsoft
]

# AEMET OpenData
AEMET_API_KEY = os.getenv('AEMET_API_KEY', '')

# Windy APIs
WINDY_POINT_FORECAST_API_KEY = os.getenv('WINDY_POINT_FORECAST_API_KEY', '')
WINDY_MAP_FORECAST_API_KEY = os.getenv('WINDY_MAP_FORECAST_API_KEY', '')
WINDY_MODEL = os.getenv('WINDY_MODEL', 'gfs')

# Aeropuertos
LEAS_ICAO = 'LEAS'  # Aeropuerto de Asturias
LEMR_ICAO = 'LEMR'  # Aeródromo La Morgal

# Información completa del Aeródromo La Morgal (LEMR)
LA_MORGAL_COORDS = {
    'lat': 43.43055,  # 43° 25.833' N
    'lon': -5.82695,  # 05° 49.617' W
    'name': 'La Morgal, Lugo de Llanera, Asturias'
}

LA_MORGAL_AERODROME = {
    'icao': 'LEMR',
    'name': 'Aeródromo de La Morgal',
    'coordinates': LA_MORGAL_COORDS,
    'municipality': 'Lugo de Llanera, Asturias',
    'radio_frequency': '123.500',  # MHz
    'elevation_ft': 545,
    'elevation_m': 180,
    'opening_hours': {
        'invierno': 'Diario de 09:00 a 20:00',
        'verano': 'Diario de 09:00 a 21:45'
    },
    'runway': {
        'designation': '10/28',
        'heading_10': 100,  # Rumbo magnético 100° (pista 10)
        'heading_28': 280,  # Rumbo magnético 280° (pista 28)
        'length_m': 890,
        'surface': 'asfalto'
    }
}

# URLs de APIs
METAR_API_URL = 'https://aviationweather.gov/api/data/metar'
OPEN_METEO_API = 'https://api.open-meteo.com/v1/forecast'
AEMET_MAP_TEMPLATE_URL = 'https://ama.aemet.es/o/estaticos/bbdd/imagenes/QGQE70LEMM1800________{date}.png'
WINDY_POINT_FORECAST_API = 'https://api.windy.com/api/point-forecast/v2'
WINDY_MAP_FORECAST_API = 'https://api.windy.com/api/map-forecast/v2'
WINDY_EMBED_URL_TEMPLATE = (
    'https://embed.windy.com/embed2.html?lat={lat}&lon={lon}&zoom=9&level=surface&overlay=wind'
    '&menu=&message=true&marker=true&calendar=24&pressure=true&type=map&location=coordinates'
    '&detail=true&detailLat={lat}&detailLon={lon}&metricWind=km%2Fh&metricTemp=%C2%B0C'
)
