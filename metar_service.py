"""
Módulo para obtener datos METAR de aeropuertos
"""
import requests
from typing import Optional, Dict
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
