"""
Módulo para obtener datos METAR de aeropuertos
"""
import requests
import re
from typing import Optional, Dict, Tuple
import config


def get_metar(icao_code: str) -> Optional[str]:
    """
    Obtiene el METAR actual de un aeropuerto dado su código ICAO
    
    Args:
        icao_code: Código ICAO del aeropuerto (ej: LEAS)
    
    Returns:
        String con el METAR o None si hay error
    """
    try:
        # Usar la API de aviationweather.gov (gratuita y oficial)
        params = {
            'ids': icao_code,
            'format': 'raw',
            'taf': 'false'
        }
        
        response = requests.get(config.METAR_API_URL, params=params, timeout=10)
        response.raise_for_status()
        
        metar = response.text.strip()
        
        if metar and not metar.startswith('No'):
            return metar
        else:
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error obteniendo METAR para {icao_code}: {e}")
        return None


def get_taf(icao_code: str) -> Optional[str]:
    """
    Obtiene el TAF (Terminal Aerodrome Forecast) de un aeropuerto
    
    Args:
        icao_code: Código ICAO del aeropuerto
    
    Returns:
        String con el TAF o None si hay error
    """
    try:
        url = 'https://aviationweather.gov/api/data/taf'
        params = {
            'ids': icao_code,
            'format': 'raw'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        taf = response.text.strip()
        
        if taf and not taf.startswith('No'):
            return taf
        else:
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error obteniendo TAF para {icao_code}: {e}")
        return None


def parse_metar_components(metar: str) -> Dict[str, str]:
    """
    Extrae componentes básicos del METAR para facilitar su interpretación
    
    Args:
        metar: String con el METAR completo
    
    Returns:
        Diccionario con componentes extraídos
    """
    components = {
        'raw': metar,
        'icao': '',
        'time': '',
        'wind': '',
        'visibility': '',
        'weather': '',
        'clouds': '',
        'temperature': '',
        'pressure': ''
    }
    
    if not metar:
        return components
    
    parts = metar.split()
    
    if len(parts) > 0:
        components['icao'] = parts[0]
    
    if len(parts) > 1:
        components['time'] = parts[1]
    
    # Buscar componentes específicos
    for part in parts:
        # Viento (ej: 27015KT)
        if 'KT' in part and len(part) >= 5:
            components['wind'] = part
        
        # Presión (ej: Q1013)
        if part.startswith('Q') and len(part) == 5:
            components['pressure'] = part
        
        # Temperatura (ej: 15/08)
        if '/' in part and len(part) <= 6:
            components['temperature'] = part
    
    return components


def classify_flight_category(metar: str) -> Dict[str, str]:
    """
    Clasifica las condiciones de vuelo según el METAR en categorías LIFR/IFR/MVFR/VFR.
    
    Args:
        metar: String con el METAR completo
    
    Returns:
        Diccionario con 'category', 'color', 'emoji' y 'description'
    """
    # Resultado por defecto
    result = {
        'category': 'DESCONOCIDO',
        'color': '#888888',
        'emoji': '⚪',
        'description': 'No se pudo clasificar'
    }
    
    if not metar or len(metar) < 10:
        return result
    
    # Extraer visibilidad en metros
    visibility_m = None
    
    # Buscar patrón de visibilidad (4 dígitos después de KT)
    # Ejemplos: "28011KT 3000", "00000KT 9999", "27015KT 0800"
    vis_match = re.search(r'\d{5}KT\s+(\d{4})', metar)
    if vis_match:
        visibility_m = int(vis_match.group(1))
    else:
        # Intentar formato alternativo
        vis_match = re.search(r'KT\s+(\d{4})(?:\s|$)', metar)
        if vis_match:
            visibility_m = int(vis_match.group(1))
    
    # Si es 9999, significa >= 10km
    if visibility_m == 9999:
        visibility_m = 10000
    
    # Extraer techo de nubes (capa BKN o OVC más baja) en pies
    ceiling_ft = None
    
    # Buscar grupos de nubes BKN o OVC
    # Ejemplos: "BKN003", "OVC023", "BKN040"
    cloud_pattern = re.findall(r'(BKN|OVC)(\d{3})', metar)
    
    if cloud_pattern:
        # Convertir a pies (cada dígito representa cientos de pies)
        ceilings = [int(height) * 100 for _, height in cloud_pattern]
        ceiling_ft = min(ceilings)  # Tomar el más bajo
    
    # Clasificar según las reglas (tomar la más restrictiva)
    # LIFR: techo <500 ft O visibilidad <1000m
    # IFR: techo <1000 ft O visibilidad <3000m
    # MVFR: techo 1000-3000 ft O visibilidad 3000-5000m
    # VFR: techo >3000 ft Y visibilidad >5000m
    
    category = 'VFR'  # Por defecto
    
    # Evaluar restricciones
    if (ceiling_ft is not None and ceiling_ft < 500) or (visibility_m is not None and visibility_m < 1000):
        category = 'LIFR'
    elif (ceiling_ft is not None and ceiling_ft < 1000) or (visibility_m is not None and visibility_m < 3000):
        category = 'IFR'
    elif (ceiling_ft is not None and ceiling_ft <= 3000) or (visibility_m is not None and visibility_m <= 5000):
        category = 'MVFR'
    else:
        category = 'VFR'
    
    # Asignar colores y emojis según categoría
    categories = {
        'VFR': {
            'category': 'VFR',
            'color': '#22c55e',  # verde
            'emoji': '🟢',
            'description': 'Condiciones visuales (>3000 ft, >5000 m)'
        },
        'MVFR': {
            'category': 'MVFR',
            'color': '#3b82f6',  # azul
            'emoji': '🔵',
            'description': 'Condiciones visuales marginales (1000-3000 ft, 3000-5000 m)'
        },
        'IFR': {
            'category': 'IFR',
            'color': '#ef4444',  # rojo
            'emoji': '🔴',
            'description': 'Condiciones por instrumentos (<1000 ft, <3000 m)'
        },
        'LIFR': {
            'category': 'LIFR',
            'color': '#a855f7',  # magenta
            'emoji': '🟣',
            'description': 'Condiciones por instrumentos bajas (<500 ft, <1000 m)'
        }
    }
    
    return categories.get(category, result)


if __name__ == '__main__':
    # Test
    print("Probando obtención de METAR para LEAS...")
    metar = get_metar('LEAS')
    if metar:
        print(f"METAR obtenido: {metar}")
        print("\nComponentes:")
        components = parse_metar_components(metar)
        for key, value in components.items():
            if value:
                print(f"  {key}: {value}")
    else:
        print("No se pudo obtener el METAR")
