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
AI_PROVIDER = os.getenv('AI_PROVIDER')  
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Sistema de cascada automática de modelos
# El sistema prueba cada modelo en orden hasta encontrar uno disponible
AI_MODEL_CASCADE = [
    "gemini-3.5-flash",       # frontier, gratuito con límites de AI Studio
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",  # más ligero, buen último escalón
]

# AEMET OpenData
AEMET_API_KEY = os.getenv('AEMET_API_KEY', '')

# Windy APIs
WINDY_POINT_FORECAST_API_KEY = os.getenv('WINDY_POINT_FORECAST_API_KEY', '')
WINDY_MODEL = os.getenv('WINDY_MODEL', 'gfs')

# Telegram monitorización
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

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
WINDY_POINT_FORECAST_API = 'https://api.windy.com/api/point-forecast/v2'
