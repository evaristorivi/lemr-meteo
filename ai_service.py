"""
Módulo para interpretación meteorológica usando IA
Soporta GitHub Copilot (gratuito) y OpenAI (opcional)
"""
import config
from typing import Optional, Dict
from threading import Lock
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram_monitor import send_alert as _tg_alert


_RATE_LIMIT_LOCK = Lock()
_FORCED_FALLBACK_CYCLE: Dict[tuple, str] = {}
_MADRID_TZ = ZoneInfo("Europe/Madrid")
_UPDATE_SLOTS = list(range(6, 24))  # Ciclos de 06:00 a 23:00
_FINAL_DISCLAIMER = "⚠️ Este análisis es orientativo; sigue siempre las indicaciones de tus instructores y, en caso de duda, mejor no volar."


def _count_tokens(messages: list, model: str = "gpt-4o") -> int:
    """
    Cuenta los tokens exactos del payload completo de mensajes usando tiktoken.
    Sigue la fórmula oficial de OpenAI para Chat Completions:
      total = 3 (reply primer) + por cada mensaje: 3 (overhead) + tokens(role) + tokens(content)
    Para modelos sin encoding propio (llama, phi, mistral) usa cl100k_base como aproximación.
    Para partes de imagen usa la estimación de detalle bajo (~85 tokens).
    """
    try:
        import tiktoken
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Modelo no reconocido por tiktoken (llama, phi, mistral, etc.)
            encoding = tiktoken.get_encoding("cl100k_base")

        total = 3  # tokens del reply primer
        for msg in messages:
            total += 3  # overhead por mensaje (rol + delimitadores)
            total += len(encoding.encode(msg.get("role", "")))
            content = msg.get("content", "")
            if isinstance(content, str):
                total += len(encoding.encode(content))
            elif isinstance(content, list):
                for part in content:
                    if part.get("type") == "text":
                        total += len(encoding.encode(part.get("text", "")))
                    elif part.get("type") == "image_url":
                        total += 85  # estimación detalle bajo (~85 tokens por imagen URL)
        return total
    except ImportError:
        # Fallback si tiktoken no está disponible: estimación por chars
        total_chars = sum(
            len(str(m.get("content", ""))) for m in messages
        )
        return total_chars // 4


def _current_cycle_id() -> str:
    now_local = datetime.now(_MADRID_TZ)
    current_hour = now_local.hour

    slot = None
    for candidate in _UPDATE_SLOTS:
        if current_hour >= candidate:
            slot = candidate

    cycle_date = now_local.date()
    if slot is None:
        slot = _UPDATE_SLOTS[-1]
        cycle_date = cycle_date - timedelta(days=1)

    return f"{cycle_date.isoformat()}-{slot:02d}"


def _is_primary_locked_for_cycle(provider: str, model: str) -> bool:
    key = (provider, model)
    current_cycle = _current_cycle_id()
    with _RATE_LIMIT_LOCK:
        locked_cycle = _FORCED_FALLBACK_CYCLE.get(key)
        return locked_cycle == current_cycle


def _lock_primary_for_cycle(provider: str, model: str):
    key = (provider, model)
    current_cycle = _current_cycle_id()
    with _RATE_LIMIT_LOCK:
        _FORCED_FALLBACK_CYCLE[key] = current_cycle


def _append_final_disclaimer(text: Optional[str]) -> str:
    content = (text or "").strip()
    if not content:
        return _FINAL_DISCLAIMER

    normalized = content.lower()
    if (
        "análisis es orientativo" in normalized
        and "instructores" in normalized
        and "caso de duda" in normalized
    ):
        return content

    return f"{content}\n\n{_FINAL_DISCLAIMER}"


# Sistema de prompts para interpretación meteorológica
SYSTEM_PROMPT = """Eres un experto meteorólogo aeronáutico ESPECIALIZADO EN AVIACIÓN ULTRALIGERA (ULM).

Tu trabajo es analizar datos meteorológicos y proporcionar interpretaciones claras, concisas y útiles para pilotos de ultraligeros.

⚠️ REGLAS CRÍTICAS DE CONVERSIÓN DE UNIDADES (NO VIOLAR NUNCA):
1. Los METAR siempre reportan viento en NUDOS (kt)
2. Los pronósticos meteorológicos suelen usar KM/H
3. ANTES de cualquier cálculo matemático, CONVIERTE TODO A LA MISMA UNIDAD
4. Conversión: 1 kt = 1.852 km/h | 1 km/h = 0.54 kt
5. NUNCA uses directamente km/h en fórmulas que esperan nudos
6. MUESTRA SIEMPRE la conversión explícitamente antes de calcular

Ejemplo: "Viento: 33.8 km/h = 18.3 kt (conversión: 33.8 ÷ 1.852), Crosswind = 18.3 × sin(59°) = 15.7 kt"

LEGISLACIÓN ULM ACTUALIZADA 2024-2026 (OBLIGATORIO):
- ✈️ SOLO VUELO DIURNO: Entre salida y puesta de sol
- ❌ PROHIBIDO vuelo nocturno
- ✈️ Solo operaciones VFR (Visual Flight Rules)
- ✈️ Visibilidad mínima: 5 km
- ✈️ Distancia de nubes: mínimo 1500m horizontal, 300m vertical
- ✈️ Peso máximo ULM biplaza: 600 kg

LÍMITES OPERACIONALES TÍPICOS ULM (consultar manual específico de cada modelo):
- ⚠️ Viento medio máximo: 15-18 kt (modelos robustos hasta 20-22 kt)
- ⚠️ Rachas absolutas: NO SUPERAR 20-22 kt (peligro estructural)
- ⚠️ Diferencia rachas-viento medio: ≥ 8 kt = Moderada (precaución), > 12 kt = Severa (NO VOLAR)
- ⚠️ Componente crosswind: Generalmente 10-12 kt máximo (consultar POH)
- ⚠️ Turbulencia moderada o superior: NO VOLAR
- ⚠️ Visibilidad < 5 km: MÍNIMO LEGAL (precaución extrema)
- ⚠️ Techo de nubes < 1000 ft AGL: IFR/LIFR → ❌ PROHIBIDO
- ⚠️ Techo de nubes 1000-3000 ft: MVFR → ❌ PROHIBIDO (condiciones marginales)
- ⚠️ Precipitación activa (lluvia/nieve): NO VOLAR (pérdida sustentación, visibilidad)
- ⚠️ Nubosidad BKN/OVC < 3000 ft: PRECAUCIÓN (restricción vertical)

⚠️ CONVECCIÓN/TORMENTAS: Si CAPE > 500 J/kg + Precip > 0 + Racha diff > 12 kt + Nubes > 50% → ❌ NO VOLAR. Incluso con CAPE bajo, turbulencia ≥ 8 kt es precaución. CAPE: <250 débil, 250-500 moderada, 500-2000 fuerte, >2000 extrema.

CONSIDERACIONES GENERALES ULM:
- Bajo peso: muy afectados por ráfagas y turbulencias
- Velocidades bajas: el análisis de viento es crítico
- Mayor sensibilidad a condiciones meteorológicas que aviación general
- Operaciones VFR exclusivamente
- En días muy cálidos el avión rinde peor que en días fríos: trepa menos y en despegue conviene dejarlo volar más antes de rotar.

AERÓDROMO LA MORGAL (LEMR): Pista 10/28 (100°/280°mag), 890m, asfalto, 545ft/180m. Coordenadas: 43°25.833'N 005°49.617'W. Horario: invierno 09:00-20:00 | verano 09:00-21:45.

REGLA DE PLANIFICACIÓN DE HORARIOS (CRÍTICA):
- Cuando propongas "mejor hora para volar", SIEMPRE debe cumplir simultáneamente:
    1) Horario DIURNO (entre amanecer y atardecer)
    2) Horario de APERTURA del aeródromo de La Morgal
- Si una buena ventana meteorológica cae fuera de horario operativo, debes descartarla.

USO DE LEAS: LEMR sin METAR continuo. Usa LEAS + pronóstico local para inferir condiciones LEMR. Nota: diferencias por distancia/orografía.

🌫️ MICROCLIMA NIEBLA EN LA MORGAL:
- La Morgal está en un valle interior de Asturias a 180m. Es ESPECIALMENTE PROPENSA a niebla matinal (oct-abril) por: enfriamiento nocturno en fondo de valle, alta humedad ambiental atlántica, y vientos débiles nocturnos. Puede estar presente a la apertura (09:00) y persistir hasta las 11h.
- Cuando el dato "niebla_matinal" aparece en el pronóstico, EVALÚA si afectará al período de operación (el aeródromo abre a las 09:00):
  - ALTO: muy probable niebla visible. Mención OBLIGATORIA en el veredicto.
  - MODERADO: posible banco de niebla local, mencionar como precaución.
  - BAJO o ausente: no mencionar.
- Si el campo incluye "_op:HH:MM" significa que el riesgo coincide con horario operativo (desde las 09:00). Esto es especialmente relevante.
- La niebla SUELE disiparse al salir el sol (09-11h), pero puede persistir con nubosidad baja o viento E (advección marina).

⚠️ PARÁMETROS CRÍTICOS PHASE 4:

1️⃣ FREEZING LEVEL HEIGHT: Los datos incluyen valor en m y ft ya calculados.
   - <1500m (<4920 ft): ⚠️ RIESGO RIME ICE (hielo en motor/superficies). 
   - 1500-2500m: Cierta exposición si hay humedad visible.
   - >2500m: Riesgo bajo.

2️⃣ TURBULENCIA MECÁNICA (gusts - wind_mean):
   - <8 kt: Ligera (tolerable).
   - 8-12 kt: Moderada → ⚠️ Precaución aumentada, vuelo difícil para ULM.
   - >12 kt: Severa → ❌ NO VOLAR (riesgo estructural/control).

3️⃣ PRECIPITATION HOURS (duración lluvia en 24h):
   - 0-2h: Lluvia ligera/dispersa, viable.
   - 2-6h: Lluvia moderada sostenida, precaución.
   - >10h: Lluvia persistente → NO VOLAR.

4️⃣ SUNSHINE DURATION: Valor ya en horas en los datos.
   - <4h: Débil potencial térmico.
   - 4-6h: Moderado, térmicas pequeñas.
   - >8h: Excelente para termaling.

5️⃣ SNOW DEPTH: Invierno solo (≥5cm afecta pista).
   - >20cm: Cierre probable de pista.

6️⃣ CLOUD LAYERS — los datos ya incluyen el tipo ICAO entre paréntesis p.ej. (St/Sc), (As), (Ci/Cs):
   BAJA (<3000 ft): St/Sc/Ns → factor MÁS CRÍTICO para ULM (limita altitud de vuelo).
   MEDIA (3000-20000 ft): As/Ac → limita techo visual, reduce térmicas.
   ALTA (>20000 ft): Ci/Cs/Cc → solo impacto en visibilidad solar/térmicas, sin veto operativo.
   NUNCA digas solo "nubosidad baja/media/alta" — usa siempre el tipo: "nubes bajas (St/Sc) X%", etc.
"""


def get_ai_client():
    """
    Obtiene el cliente de IA apropiado según la configuración
    
    Returns:
        Cliente configurado o None si no hay configuración válida
    """
    # Intentar GitHub Models primero (gratuito con GitHub token)
    if config.GITHUB_TOKEN and config.AI_PROVIDER == 'github':
        try:
            from openai import OpenAI
            
            print("🚀 Usando GitHub Models (Gratuito)")
            client = OpenAI(
                api_key=config.GITHUB_TOKEN,
                base_url="https://models.inference.ai.azure.com",
                max_retries=0,
                timeout=120,  # 120s para modelos open source más lentos
            )
            return ('github', client)
        except Exception as e:
            print(f"Error configurando GitHub Models: {e}")
            return None
    
    # Intentar OpenAI si está configurado
    if config.OPENAI_API_KEY and config.AI_PROVIDER == 'openai':
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=config.OPENAI_API_KEY,
                max_retries=0,
                timeout=120,  # 120s timeout
            )
            return ('openai', client)
        except Exception as e:
            print(f"Error configurando OpenAI: {e}")
            return None
    
    # Fallback: intentar GitHub Models primero, luego OpenAI
    if config.GITHUB_TOKEN:
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=config.GITHUB_TOKEN,
                base_url="https://models.inference.ai.azure.com",
                max_retries=0,
                timeout=60,
            )
            return ('github', client)
        except:
            pass
    
    return None


def _is_rate_limit_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return (
        "ratelimit" in text
        or "rate limit" in text
        or "too many requests" in text
        or " 429" in text
        or "error code: 429" in text
    )


def _print_rate_limit_info(response, model_name: str):
    """Imprime información de rate limits de la respuesta de la API"""
    try:
        # Intentar obtener las cabeceras de rate limit
        if hasattr(response, '_response') and hasattr(response._response, 'headers'):
            headers = response._response.headers
            limit = headers.get('x-ratelimit-limit-requests', 'N/A')
            remaining = headers.get('x-ratelimit-remaining-requests', 'N/A')
            reset = headers.get('x-ratelimit-reset-requests', 'N/A')
            
            if limit != 'N/A' or remaining != 'N/A':
                print(f"📊 Rate Limit [{model_name}]: {remaining}/{limit} requests restantes (reset: {reset})")
    except Exception as e:
        # Si no podemos leer las cabeceras, no es crítico
        pass


def _is_timeout_error(exc: Exception) -> bool:
    """Detecta si el error es un timeout"""
    text = str(exc).lower()
    return (
        "timeout" in text
        or "timed out" in text
        or "read timeout" in text
        or "connection timeout" in text
    )


def _is_context_length_error(exc: Exception) -> bool:
    """Detecta si el error es por superar la ventana de contexto del modelo."""
    text = str(exc).lower()
    return (
        "context_length_exceeded" in text
        or "maximum context length" in text
        or "context window" in text
        or "reduce your message" in text
        or "too many tokens" in text
        or "tokens exceed" in text
        or "input is too long" in text
        or "prompt is too long" in text
    )


def _infer_cloud_type(layer: str, pct: Optional[int], wx_code: Optional[int]) -> str:
    """
    Infiere el tipo probable de nube (abreviatura ICAO) a partir de la capa,
    cobertura y weather_code WMO. Devuelve p.ej. "(Sc)", "(As)", "(Ci/Cs)".
    layer: 'low' | 'mid' | 'high'
    """
    if pct is None or pct == 0:
        return ""
    wx = wx_code or 0
    if layer == "low":
        if wx in (95, 96, 99):                   return "(Cb)"
        if wx in (80, 81, 82, 85, 86):           return "(Cu/Cb)"
        if wx in (61, 63, 65, 71, 73, 75, 77):  return "(Ns)"
        if wx in (51, 53, 55):                   return "(St)"
        if wx in (45, 48):                       return "(St)"
        if pct >= 75:                            return "(St/Sc)"
        if pct >= 25:                            return "(Sc)"
        return "(Cu)"
    if layer == "mid":
        return "(As)" if pct >= 50 else "(Ac)"
    if layer == "high":
        if pct >= 70: return "(Cs)"
        if pct >= 20: return "(Ci)"
        return "(Cc)"
    return ""


def _map_weather_code(code: Optional[int]) -> str:
    """
    Mapea código WMO a emoji + descripción compacta para IA.
    
    Args:
        code: Código WMO weather code
    
    Returns:
        String con emoji + descripción (ej: "🌧️ LLUVIA")
    """
    if code is None:
        return "⛅ VARIABLE"
    
    # Mapeo comprimido a categorías críticas para ULM
    if code in (95, 96, 99):
        return "⛈️ TORMENTA"
    elif code in (80, 81, 82, 85, 86):
        return "🌧️ CHUBASCOS"
    elif code in (61, 63, 65):
        return "🌧️ LLUVIA"
    elif code in (51, 53, 55):
        return "🌫️ LLOVIZNA"
    elif code in (71, 73, 75, 77):
        return "🌨️ NIEVE"
    elif code in (45, 48):
        return "🌫️ NIEBLA"
    elif code in (2, 3):
        return "☁️ NUBLADO"
    elif code in (1,):
        return "🌥️ PARCIAL"
    else:
        return "⛅ DESPEJADO"


def _compute_cloud_base_summary(hourly_data: Optional[list]) -> Dict:
    """
    Estima base de nubes a partir de (Temp - Dewpoint) × 400 ft.
    Solo para datos HORARIOS (HOY).
    
    Args:
        hourly_data: Lista de dicts con 'temperature', 'dewpoint'
    
    Returns:
        Dict con min_ft, hour_min, avg_ft, risk_level
    """
    if not hourly_data:
        return {'min_ft': None, 'avg_ft': None, 'risk': 'DESCONOCIDO', 'summary': 'Sin datos'}
    
    cloud_bases = []
    for row in hourly_data[:24]:
        temp = row.get('temperature')
        dewpoint = row.get('dewpoint')
        if temp is not None and dewpoint is not None and temp >= dewpoint:
            cloud_base_ft = (temp - dewpoint) * 400
            cloud_bases.append({'ft': cloud_base_ft, 'time': row.get('time', '')})
    
    if not cloud_bases:
        return {'min_ft': None, 'avg_ft': None, 'risk': 'DESCONOCIDO', 'summary': 'Sin datos'}
    
    min_row = min(cloud_bases, key=lambda x: x['ft'])
    min_ft = int(min_row['ft'])
    hour_str = min_row['time'].split('T')[1][:5] if 'T' in min_row['time'] else '??:??'
    avg_ft = int(sum(c['ft'] for c in cloud_bases) / len(cloud_bases))
    
    # Clasificar riesgo
    if min_ft < 1000:
        risk = 'ALTO'
    elif min_ft < 2000:
        risk = 'MODERADO'
    else:
        risk = 'BAJO'
    
    return {
        'min_ft': min_ft,
        'hour_min': hour_str,
        'avg_ft': avg_ft,
        'risk': risk,
        'summary': f"mín {min_ft} ft ({hour_str}) | media {avg_ft} ft | {risk}"
    }


def _compute_visibility_summary(hourly_data: Optional[list]) -> Dict:
    """
    Calcula visibilidad mínima y media del día (HOY).
    Solo para datos HORARIOS.
    
    Args:
        hourly_data: Lista de dicts con 'visibility' (en km)
    
    Returns:
        Dict con min_km, hour_min, avg_km, risk_level
    """
    if not hourly_data:
        return {'min_km': None, 'avg_km': None, 'risk': 'DESCONOCIDO', 'summary': 'Sin datos'}
    
    visibilities = []
    for row in hourly_data[:24]:
        vis = row.get('visibility')
        if vis is not None and vis > 0:
            visibilities.append({'km': vis, 'time': row.get('time', '')})
    
    if not visibilities:
        return {'min_km': None, 'avg_km': None, 'risk': 'DESCONOCIDO', 'summary': 'Sin datos'}
    
    min_row = min(visibilities, key=lambda x: x['km'])
    min_km = min_row['km']
    hour_str = min_row['time'].split('T')[1][:5] if 'T' in min_row['time'] else '??:??'
    avg_km = sum(v['km'] for v in visibilities) / len(visibilities)
    
    # Clasificar riesgo (límite legal ULM 5km)
    if min_km < 3:
        risk = 'ALTO'
    elif min_km < 5:
        risk = 'MODERADO'
    else:
        risk = 'BAJO'
    
    return {
        'min_km': round(min_km, 1),
        'hour_min': hour_str,
        'avg_km': round(avg_km, 1),
        'risk': risk,
        'summary': f"mín {min_km:.1f} km ({hour_str}) | media {avg_km:.1f} km | {risk}"
    }


def _detect_convective_risk(
    cape: Optional[float],
    precipitation: Optional[float],
    wind_speed_kmh: Optional[float],
    wind_gusts_kmh: Optional[float],
    cloud_cover_low: Optional[float],
    weather_code: Optional[int] = None,
    lifted_index: Optional[float] = None,
) -> Dict:
    """
    Detecta riesgo de convección probable (tormentas) basado en múltiples indicadores.
    
    Criterios de convección probable:
    1. CAPE > 500 J/kg (energía disponible para convección)
    2. Precipitación > 0 mm/h (desarrollo convectivo)
    3. Racha ≥ viento medio + 8–10 kt (patrón de downdrafts)
    4. Nubosidad BAJA > 50% (estratos/stratus fractus = peligro ULM)
    5. Weather code 95-99 = TORMENTA (veto automático)
    6. Lifted Index < -6 = Tormentas fuertes (indicador complementario)
    
    Args:
        cape: CAPE value (J/kg)
        precipitation: Precipitation rate (mm/h)
        wind_speed_kmh: Mean wind speed (km/h)
        wind_gusts_kmh: Wind gust speed (km/h)
        cloud_cover_low: Low cloud cover percentage (estratos)
        weather_code: WMO weather code (95-99 = tormenta)
        lifted_index: Atmospheric stability index
    
    Returns:
        Dict with convection risk assessment
    """
    result = {
        'has_convective_risk': False,
        'risk_level': 'NULO',  # NULO, BAJO, MODERADO, ALTO, CRÍTICO
        'indicators': [],
        'summary': ''
    }
    
    if all(v is None for v in [cape, precipitation, wind_speed_kmh, wind_gusts_kmh, cloud_cover_low, weather_code, lifted_index]):
        result['summary'] = 'Datos insuficientes para evaluar riesgo convectivo'
        return result
    
    # FILTRO CRÍTICO: Weather code 95-99 = TORMENTA AUTOMÁTICA
    if weather_code and weather_code in (95, 96, 99):
        result['risk_level'] = 'CRÍTICO'
        result['has_convective_risk'] = True
        result['indicators'].append("🔴 CÓDIGO 95-99: TORMENTA ACTIVA")
        result['summary'] = '⚠️⚠️ RIESGO CONVECTIVO CRÍTICO - Código WMO 95-99 detectado. Tormenta activa en zona. ❌ NO VOLAR'
        return result
    
    indicators_met = 0
    
    # Indicador 1: CAPE > 500 J/kg
    if cape and cape > 500:
        result['indicators'].append(f"🔴 CAPE {cape:.0f} J/kg")
        indicators_met += 1
    elif cape and cape > 250:
        result['indicators'].append(f"🟡 CAPE {cape:.0f} J/kg")
    
    # Indicador 2: Precipitación > 0 mm/h
    if precipitation and precipitation > 0:
        result['indicators'].append(f"🔴 Precip {precipitation:.1f} mm/h")
        indicators_met += 1
    
    # Indicador 3: Diferencia rachas-viento medio ≥ 8-10 kt
    if wind_speed_kmh and wind_gusts_kmh and wind_speed_kmh > 0:
        wind_speed_kt = wind_speed_kmh / 1.852
        wind_gusts_kt = wind_gusts_kmh / 1.852
        gust_diff_kt = wind_gusts_kt - wind_speed_kt
        
        if gust_diff_kt >= 8:
            result['indicators'].append(f"🔴 Racha Δ {gust_diff_kt:.1f} kt")
            indicators_met += 1
        elif gust_diff_kt >= 5:
            result['indicators'].append(f"🟡 Racha Δ {gust_diff_kt:.1f} kt")
    
    # Indicador 4: Nubosidad BAJA creciente (>50%) - MÁS CRÍTICO PARA ULM
    if cloud_cover_low and cloud_cover_low > 50:
        result['indicators'].append(f"🟡 Nubes baja {cloud_cover_low:.0f}%")
        if cloud_cover_low > 75:
            indicators_met += 0.5  # Nubosidad baja estratos = riesgo para ULM
    
    # Indicador 5: Lifted Index < -6 = Tormentas fuertes (complementa CAPE)
    if lifted_index and lifted_index < -6:
        result['indicators'].append(f"🔴 Lifted Index {lifted_index:.1f} (tormentas fuertes)")
        indicators_met += 1
    elif lifted_index and lifted_index < -3:
        result['indicators'].append(f"🟡 Lifted Index {lifted_index:.1f} (probable)")
    
    # Determinar nivel de riesgo basado en indicadores cumplidos
    if indicators_met >= 3:
        result['risk_level'] = 'CRÍTICO'
        result['has_convective_risk'] = True
        result['summary'] = '⚠️⚠️ RIESGO CONVECTIVO CRÍTICO - Más de 3 indicadores presentes. Posibilidad muy alta de tormentas/cumulonimbos. ❌ NO VOLAR'
    elif indicators_met >= 2.5:
        result['risk_level'] = 'ALTO'
        result['has_convective_risk'] = True
        result['summary'] = '⚠️ RIESGO CONVECTIVO ALTO - Múltiples indicadores presentes. Posibilidad significativa de desarrollo convectivo. Reconsiderar vuelo.'
    elif indicators_met >= 1.5:
        result['risk_level'] = 'MODERADO'
        result['has_convective_risk'] = True
        result['summary'] = '⚠️ RIESGO CONVECTIVO MODERADO - Algunos indicadores presentes. Monitora evolución meteorológica.'
    elif result['indicators']:
        result['risk_level'] = 'BAJO'
        result['summary'] = '🟡 RIESGO CONVECTIVO BAJO - Indicadores débiles o aislados.'
    else:
        result['risk_level'] = 'NULO'
        result['summary'] = '✅ Sin indicadores de convección probable.'
    
    return result


def _create_chat_completion_with_fallback(
    client,
    provider: str,
    messages,
    temperature: float,
    max_tokens: int,
    model: Optional[str] = None,
):
    """
    Intenta crear un chat completion con sistema de cascada de modelos.
    Prueba modelos en orden de preferencia hasta encontrar uno disponible.
    """
    # Obtener lista de modelos a probar
    model_cascade = getattr(config, "AI_MODEL_CASCADE", [
        'gpt-4o',
        'gpt-4o-mini',
        'meta-llama-3.1-405b-instruct',
        'mistral-large',
    ])
    
    # Si se especifica un modelo, intentar primero con ese
    if model and model not in model_cascade:
        model_cascade = [model] + list(model_cascade)
    
    last_exception = None
    attempted_models = []
    
    for model_name in model_cascade:
        # Saltar modelos bloqueados en este ciclo
        if _is_primary_locked_for_cycle(provider, model_name):
            print(f"⏭️  Saltando {model_name} (bloqueado hasta próximo ciclo)")
            attempted_models.append(f"{model_name} (bloqueado)")
            continue
        
        try:
            print(f"🔄 Intentando con modelo: {model_name}")
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # ¡Éxito!
            _print_rate_limit_info(response, model_name)
            print(f"✅ Análisis completado con {model_name}")
            return response
            
        except Exception as exc:
            error_msg = str(exc)
            attempted_models.append(model_name)
            
            # Clasificar el tipo de error
            if _is_rate_limit_error(exc):
                # Rate limit: bloquear este modelo para el resto del ciclo
                _lock_primary_for_cycle(provider, model_name)
                print(f"🔒 {model_name} alcanzó límite de rate-limit (bloqueado hasta próximo ciclo)")
                _tg_alert(
                    f"Modelo IA {model_name} ha alcanzado su rate-limit (429). Saltando al siguiente modelo de la cascada.",
                    source=f"ia_{model_name}",
                    level="WARNING",
                )
            elif _is_context_length_error(exc):
                # Prompt demasiado largo: avisar para que se ajuste el truncado
                print(f"📏 {model_name} rechazó el prompt por exceso de tokens: {error_msg[:120]}")
                _tg_alert(
                    f"Modelo IA {model_name} rechazo el prompt por exceso de tokens (context window). "
                    f"Error: {error_msg[:250]}",
                    source=f"ia_{model_name}",
                    level="ERROR",
                )
            elif _is_timeout_error(exc):
                # Timeout: NO bloquear (puede ser temporal/saturación)
                print(f"⏱️ {model_name} dio timeout ({error_msg[:80]}) - continuando con siguiente modelo")
            else:
                # Otro error (modelo no existe, error de API, etc.)
                print(f"⚠️ Error con {model_name}: {error_msg[:100]}")
            
            last_exception = exc
            # Continuar con el siguiente modelo en la cascada
    
    # Si llegamos aquí, todos los modelos fallaron
    print(f"❌ Todos los modelos fallaron. Intentados: {', '.join(attempted_models)}")
    if last_exception:
        raise last_exception
    else:
        raise Exception("No hay modelos disponibles para procesar la solicitud")


def interpret_fused_forecast_with_ai(
    metar_leas: str,
    weather_data: Dict,
    windy_data: Dict,
    aemet_prediccion: Dict,
    map_analysis_text: str,
    metar_lemr: str = "",
    significant_map_urls: Optional[list[str]] = None,
    location: str = "La Morgal (LEMR)",
    flight_category_leas: Optional[Dict] = None,
    flight_category_lemr: Optional[Dict] = None,
    avisos_cap: Optional[str] = None,
    llanera_horaria_compact: Optional[str] = None,
) -> Optional[str]:
    """
    Genera un veredicto experto fusionando Windy + AEMET + METAR + Open-Meteo.
    """
    client_info = get_ai_client()
    if not client_info:
        return _append_final_disclaimer("⚠️ No se ha configurado ningún proveedor de IA. Por favor, configura GITHUB_TOKEN o OPENAI_API_KEY en el archivo .env")

    provider, client = client_info

    try:
        current = weather_data.get("current", {}) if weather_data else {}
        daily = weather_data.get("daily_forecast", []) if weather_data else []
        hourly_om = weather_data.get("hourly_forecast", []) if weather_data else []
        windy_daily = windy_data.get("daily_summary", []) if windy_data else []
        windy_hourly = windy_data.get("hourly", []) if windy_data else []

        om_lines = []
        labels = ["HOY", "MAÑANA", "PASADO MAÑANA", "DENTRO DE 3 DÍAS"]
        for idx, row in enumerate(daily[:4]):
            label = labels[idx] if idx < len(labels) else f"DÍA +{idx}"
            weather_emoji = _map_weather_code(row.get('weather_code'))

            # --- campos base ---
            cape_max = row.get('cape_max')
            cape_str = f", CAPE máx {cape_max:.0f} J/kg" if cape_max is not None else ""
            precip_h = row.get('precipitation_hours')
            precip_sum_mm = row.get('precipitation')
            if precip_h is not None and precip_sum_mm is not None:
                precip_h_str = f", precip {precip_h:.0f}h/{precip_sum_mm:.1f}mm"
            elif precip_h is not None:
                precip_h_str = f", precip {precip_h:.0f}h"
            elif precip_sum_mm is not None:
                precip_h_str = f", precip {precip_sum_mm:.1f}mm"
            else:
                precip_h_str = ""
            sun_sec = row.get('sunshine_duration')
            sun_h_str = f", sol {sun_sec / 3600:.1f}h" if sun_sec is not None else ""

            # --- Phase 4 pre-calculados en Python (solo horas diurnas) ---
            fl_m = row.get('freezing_level_min_m')
            fl_str = ""
            if fl_m is not None:
                fl_ft = row.get('freezing_level_min_ft', round(fl_m * 3.28084))
                fl_tag = ("⚠️ RIME" if fl_m < 1500
                          else "🟡 exp" if fl_m < 2500
                          else "🟢 ok")
                fl_str = f", FL_min {fl_m}m/{fl_ft}ft {fl_tag}"
            turb = row.get('turb_diff_max_kt')
            turb_str = ""
            if turb is not None:
                turb_tag = ("🔴 SEVERA" if turb > 12
                            else "🟡 MOD" if turb > 8
                            else "🟢 lig")
                turb_str = f", turb_diff_max {turb}kt {turb_tag}"
            snow = row.get('snow_max_cm')
            snow_str = f", nieve {snow}cm" if snow and snow > 0 else ""
            cl_low  = row.get('cloud_low_max')
            cl_mid  = row.get('cloud_mid_max')
            cl_high = row.get('cloud_high_max')
            wx_code_row = row.get('weather_code')
            clouds_str = ""
            if cl_low is not None:
                lo_type = _infer_cloud_type('low',  cl_low,  wx_code_row)
                mi_type = _infer_cloud_type('mid',  cl_mid,  wx_code_row)
                hi_type = _infer_cloud_type('high', cl_high, wx_code_row)
                low_tag = " 🔴BKN/OVC" if cl_low > 50 else ""
                clouds_str = (
                    f", nubes_bajas{lo_type}(<3000ft) {cl_low}%{low_tag}"
                    f" / medias{mi_type} {cl_mid}%"
                    f" / altas{hi_type} {cl_high}%"
                )

            # --- hora amanecer/atardecer: solo la hora HH:MM ---
            sunrise_raw = row.get('sunrise', 'N/A')
            sunset_raw  = row.get('sunset',  'N/A')
            sunrise_hm  = sunrise_raw.split('T')[1][:5] if sunrise_raw and 'T' in sunrise_raw else sunrise_raw
            sunset_hm   = sunset_raw.split('T')[1][:5]  if sunset_raw  and 'T' in sunset_raw  else sunset_raw

            # --- patrón mañana→tarde (solo si hay variación significativa) ---
            man_gust  = row.get('gust_man_max')
            tard_gust = row.get('gust_tard_max')
            man_cl    = row.get('cloud_low_man_max')
            tard_cl   = row.get('cloud_low_tard_max')
            man_pp    = row.get('precip_prob_man_max')
            tard_pp   = row.get('precip_prob_tard_max')
            man_turb  = row.get('turb_diff_man_max')
            tard_turb = row.get('turb_diff_tard_max')
            peak_h    = row.get('peak_gust_hour')
            trend_parts = []
            if man_gust is not None and tard_gust is not None:
                diff = tard_gust - man_gust
                if abs(diff) >= 10:  # solo si la diferencia es operacionalmente relevante
                    arrow = "📈" if diff > 0 else "📉"
                    trend_parts.append(f"rachas mañ {man_gust:.0f}→tard {tard_gust:.0f}km/h {arrow}")
            if man_cl is not None and tard_cl is not None and abs(tard_cl - man_cl) >= 20:
                arrow = "📈" if tard_cl > man_cl else "📉"
                lo_type_trend = _infer_cloud_type('low', max(man_cl, tard_cl), wx_code_row)
                trend_parts.append(f"nube_baja{lo_type_trend}(<3000ft) mañ {man_cl:.0f}%→tard {tard_cl:.0f}% {arrow}")
            if man_pp is not None and tard_pp is not None and abs(tard_pp - man_pp) >= 20:
                arrow = "📈" if tard_pp > man_pp else "📉"
                trend_parts.append(f"precip_prob mañ {man_pp:.0f}%→tard {tard_pp:.0f}% {arrow}")
            elif man_pp or tard_pp:
                if man_pp and man_pp >= 20: trend_parts.append(f"precip mañ {man_pp:.0f}%")
                if tard_pp and tard_pp >= 20: trend_parts.append(f"precip tard {tard_pp:.0f}%")
            if man_turb is not None and tard_turb is not None and abs(tard_turb - man_turb) >= 3:
                arrow = "📈" if tard_turb > man_turb else "📉"
                trend_parts.append(f"turb mañ {man_turb}kt→tard {tard_turb}kt {arrow}")
            if peak_h and (man_gust or tard_gust):
                trend_parts.append(f"pico {peak_h}h")
            trend_str = ("\n  ↕️ tendencia: " + ", ".join(trend_parts)) if trend_parts else ""

            fog = row.get('fog_risk') or {}
            fog_level = fog.get('level')
            fog_str = ""
            if fog_level in ('ALTO', 'MODERADO'):
                fog_h   = fog.get('peak_hour', '')
                spr     = fog.get('min_spread')
                op_hrs  = fog.get('operational_hours', [])
                fog_str = f", 🌫️niebla_matinal:{fog_level}"
                if op_hrs:
                    fog_str += f"_op:{op_hrs[0]}"
                    if len(op_hrs) > 1:
                        fog_str += f"-{op_hrs[-1]}"
                elif fog_h:
                    fog_str += f"~{fog_h}"
                if spr is not None:
                    fog_str += f"(T-Td={spr}°C)"

            om_lines.append(
                f"- {label}: {weather_emoji} temp {row.get('temp_min')}-{row.get('temp_max')}°C"
                f", viento_max {row.get('wind_max')} km/h rachas_max {row.get('wind_gusts_max')} km/h"
                f"{cape_str}{precip_h_str}{sun_h_str}"
                f"{fl_str}{turb_str}{snow_str}{clouds_str}{fog_str}"
                f", ☀️ {sunrise_hm} 🌇 {sunset_hm}"
                f"{trend_str}"
            )

        windy_lines = []
        for row in windy_daily[:4]:
            w_man  = row.get('gust_man_max')
            w_tard = row.get('gust_tard_max')
            w_trend = ""
            if w_man is not None and w_tard is not None and abs(w_tard - w_man) >= 10:
                arrow = "📈" if w_tard > w_man else "📉"
                w_trend = f", rachas mañ {w_man:.0f}→tard {w_tard:.0f}km/h {arrow}"
            windy_lines.append(
                f"- {row.get('date')}: viento máx {row.get('max_wind_kmh')} km/h, "
                f"rachas máx {row.get('max_gust_kmh')} km/h, precip {row.get('precip_total_mm')} mm"
                f"{w_trend}"
            )

        hourly_lines = []  # se construye más abajo, tras definir now_local y _close_hour

        aemet_hoy = (aemet_prediccion or {}).get("asturias_hoy", "")
        aemet_man = (aemet_prediccion or {}).get("asturias_manana", "")
        aemet_pas = (aemet_prediccion or {}).get("asturias_pasado_manana", "")
        # Nota: La predicción de La Morgal 4 días es Open-Meteo y ya está en om_lines (no duplicar)
        
        # Optimización: reducir AEMET para GitHub Models (límite por request)
        is_github = provider.lower() == "github"
        aemet_limit = 300 if is_github else 1200  # 300 chars por sección AEMET en GitHub
        hor_limit = 400 if is_github else 700    # cap para Llanera horaria

        map_urls = [u for u in (significant_map_urls or []) if u][:4]
        
        # Obtener hora actual para contexto
        now_local = datetime.now(_MADRID_TZ)
        hora_actual = now_local.strftime("%H:%M")
        fecha_actual = now_local.strftime("%Y-%m-%d")

        # Formatear condiciones actuales Open-Meteo
        # Omitir campos ya presentes en el METAR sintético (temp/dewpoint, viento kt, QNH, nubosidad)
        # para no duplicar tokens; conservar los que el METAR no expresa.
        current_lines = []
        if current:
            current_lines.append(f"  - Hora: {current.get('time', 'N/A')}")
            current_lines.append(f"  - Temperatura: {current.get('temperature', 'N/A')}°C")  # útil para densidad/LCL
            current_lines.append(f"  - Viento: {current.get('wind_speed', 'N/A')} km/h desde {current.get('wind_direction', 'N/A')}° (rachas {current.get('wind_gusts', 'N/A')} km/h)")  # km/h para cálculos ULM
            current_lines.append(f"  - Precipitación: {current.get('precipitation', 'N/A')} mm")
            current_lines.append(f"  - CAPE (energía convectiva): {current.get('cape', 'N/A')} J/kg")
        
        # Detectar riesgo convectivo (tormentas) con los datos actuales
        convection_risk = _detect_convective_risk(
            cape=current.get('cape') if current else None,
            precipitation=current.get('precipitation') if current else None,
            wind_speed_kmh=current.get('wind_speed') if current else None,
            wind_gusts_kmh=current.get('wind_gusts') if current else None,
            cloud_cover_low=hourly_om[0].get('cloud_cover_low') if hourly_om else None,
            weather_code=current.get('weather_code') if current else None,
            lifted_index=None  # Open-Meteo no proporciona lifted_index directamente
        )
        
        # Calcular resúmenes de techo y visibilidad (HOY solamente)
        cloud_base_summary = _compute_cloud_base_summary(hourly_om[:24] if hourly_om else None)
        visibility_summary = _compute_visibility_summary(hourly_om[:24] if hourly_om else None)
        weathercode_emoji = _map_weather_code(current.get('weather_code') if current else None)
        
        # Formato compacto del análisis convectivo
        convection_analysis = f"⚠️ RIESGO CONVECTIVO: {convection_risk['risk_level']}"
        if convection_risk['indicators']:
            convection_analysis += f"\n  • {' | '.join(convection_risk['indicators'][:3])}"  # Máximo 3 indicadores para ahorrar tokens
        convection_analysis += f"\n  → {convection_risk['summary']}"
        
        # Agregar resúmenes de techo, visibilidad y condición actual
        if cloud_base_summary['min_ft']:
            current_lines.append(f"  - ⬇️ Techo est: mín {cloud_base_summary['min_ft']} ft ({cloud_base_summary['hour_min']}) | media {cloud_base_summary['avg_ft']} ft | {cloud_base_summary['risk']}")
        if visibility_summary['min_km']:
            current_lines.append(f"  - 👁️ Visibilidad: mín {visibility_summary['min_km']} km ({visibility_summary['hour_min']}) | media {visibility_summary['avg_km']} km | {visibility_summary['risk']}")
        current_lines.append(f"  - ☁️ Condición: {weathercode_emoji}")

        # Phase 4 ya está pre-calculado en weather_service y viaja dentro de daily (om_lines)
        # No se necesita procesamiento adicional aquí

        # Open-Meteo horario HOY — solo franjas operativas relevantes desde ahora en adelante
        # Invierno (oct-mar): 09:00-20:00 | Verano (abr-sep): 09:00-21:45
        _is_summer = now_local.month in range(4, 10)
        _close_hour = 21 if _is_summer else 20
        _cur_hour = now_local.hour
        om_hoy_hourly_lines = []
        for _h in hourly_om:
            _t = _h.get('time', '')
            if not _t or _t[:10] != fecha_actual:
                continue
            _hh = int(_t[11:13]) if len(_t) >= 13 else -1
            # Solo horas desde la actual hasta el cierre del aeródromo
            if _hh < max(9, _cur_hour) or _hh > _close_hour:
                continue
            if _h.get('is_day') != 1:
                continue
            _wind  = _h.get('wind_speed')
            _gusts = _h.get('wind_gusts')
            _wdir  = _h.get('wind_direction')
            _cl_lo = _h.get('cloud_cover_low')
            _vis   = _h.get('visibility')
            _pp    = _h.get('precipitation_prob')
            _wcode = _h.get('weather_code')
            _wx    = _map_weather_code(_wcode)
            _parts = [f"{_t[11:16]}:"]
            if _wind is not None and _gusts is not None:
                _dir_str = f"({_wdir:.0f}°)" if _wdir is not None else ""
                _parts.append(f"{_wind:.0f}/{_gusts:.0f}km/h{_dir_str}")
            if _cl_lo is not None:
                _lo_type = _infer_cloud_type('low', int(_cl_lo), _wcode)
                _lo_tag  = "🔴" if _cl_lo > 50 else ""
                _parts.append(f"nube_baja{_lo_type} {_cl_lo:.0f}%{_lo_tag}")
            if _vis is not None and _vis < 10:
                _parts.append(f"vis {_vis:.1f}km")
            if _pp is not None and _pp >= 20:
                _parts.append(f"pp {_pp:.0f}%")
            _parts.append(_wx)
            om_hoy_hourly_lines.append("  " + " ".join(_parts))

        # Open-Meteo horario MAÑANA / PASADO MAÑANA / DENTRO DE 3 DÍAS — franjas operativas 09-close
        # Reutiliza now_local y _close_hour ya definidos arriba
        _future_labels = {
            (now_local.date() + timedelta(days=1)).isoformat(): "MAÑ",
            (now_local.date() + timedelta(days=2)).isoformat(): "PAS",
            (now_local.date() + timedelta(days=3)).isoformat(): "+3D",
        }
        _prev_day = None
        for _h in hourly_om:
            _t = _h.get('time', '')
            if not _t:
                continue
            _day = _t[:10]
            if _day not in _future_labels:
                continue
            _hh = int(_t[11:13]) if len(_t) >= 13 else -1
            if _hh < 9 or _hh > _close_hour:
                continue
            if _h.get('is_day') != 1:
                continue
            _wind  = _h.get('wind_speed')
            _gusts = _h.get('wind_gusts')
            _wdir  = _h.get('wind_direction')
            _cl_lo = _h.get('cloud_cover_low')
            _vis   = _h.get('visibility')
            _pp    = _h.get('precipitation_prob')
            _wcode = _h.get('weather_code')
            _wx    = _map_weather_code(_wcode)
            if _day != _prev_day:
                hourly_lines.append(f"{_future_labels[_day]} ({_day}):")
                _prev_day = _day
            _parts = [f"  {_t[11:16]}:"]
            if _wind is not None and _gusts is not None:
                _dir_str = f"({_wdir:.0f}°)" if _wdir is not None else ""
                _parts.append(f"{_wind:.0f}/{_gusts:.0f}km/h{_dir_str}")
            if _cl_lo is not None:
                _lo_type = _infer_cloud_type('low', int(_cl_lo), _wcode)
                _lo_tag  = "🔴" if _cl_lo > 50 else ""
                _parts.append(f"nube_baja{_lo_type} {_cl_lo:.0f}%{_lo_tag}")
            if _vis is not None and _vis < 10:
                _parts.append(f"vis {_vis:.1f}km")
            if _pp is not None and _pp >= 20:
                _parts.append(f"pp {_pp:.0f}%")
            _parts.append(_wx)
            hourly_lines.append(" ".join(_parts))

        user_message = f"""Actúa como experto en meteorología aeronáutica ULM para {location} y crea una síntesis OPERATIVA final de alta precisión.

⏰ HORA ACTUAL: {hora_actual} (Europe/Madrid) - Fecha: {fecha_actual}

DATOS FIJOS AERÓDROMO LEMR:
    - Pista: 10/28 (rumbos 100° y 280°)
    - Horario operativo: Invierno (oct-mar) 09:00-20:00 / Verano (abr-sep) 09:00-21:45
    - Solo VFR diurno

METAR LEAS — Aeropuerto de Asturias (referencia más cercana, a ~30 km de LEMR):
{metar_leas or 'No disponible'}
{f"{flight_category_leas.get('emoji')} Clasificación: {flight_category_leas.get('category')} - {flight_category_leas.get('description')}" if flight_category_leas else ""}

METAR LEMR — La Morgal (estimado local, NO es METAR oficial):
{metar_lemr or 'No disponible'}
{f"{flight_category_lemr.get('emoji')} Clasificación: {flight_category_lemr.get('category')} - {flight_category_lemr.get('description')}" if flight_category_lemr else ""}

⚠️ IMPORTANTE: Los METAR son OBSERVACIONES PUNTUALES del momento indicado en el timestamp del METAR, NO son pronósticos para todo el día. Las condiciones meteorológicas pueden mejorar o empeorar durante el día - usa los pronósticos Windy/AEMET/Open-Meteo para evaluar tendencias y evolución.
las condiciones meteorológicas pueden clasificarse en:
- VFR: techo > 3000 ft Y visibilidad > 5 km
- MVFR: techo 1000–3000 ft O visibilidad 3–5 km
- IFR: techo 500–1000 ft O visibilidad 1–3 km
- LIFR: techo < 500 ft O visibilidad < 1 km
ULM: Solo vuela en VFR. En IFR y LIFR está prohibido. En MVFR al ser condiciones marginales queda prohibido también. 

Open-Meteo CONDICIONES ACTUALES en {location}:
{chr(10).join(current_lines) if current_lines else 'Sin datos actuales'}
{convection_analysis}

Open-Meteo HOY horas pendientes (hasta cierre {_close_hour:02d}:00) — viento/rachas km/h, nube_baja, vis si <10km:
{chr(10).join(om_hoy_hourly_lines) if om_hoy_hourly_lines else 'Sin datos horarios o aeródromo ya cerrado'}

Open-Meteo (resumen 4 días) — incl. Phase 4: freezing_level, turbulencia, snow, nubes por capa, sol, precip_hours:
{chr(10).join(om_lines) if om_lines else 'Sin datos'}

Windy Point Forecast (resumen 4 días):
{chr(10).join(windy_lines) if windy_lines else 'Sin datos'}

Open-Meteo horario MAÑANA/PASADO/+3D (franjas operativas 09-{_close_hour:02d}h) — viento/rachas km/h, nube_baja, vis si <10km:
{chr(10).join(hourly_lines) if hourly_lines else 'Sin datos'}

⚠️ AVISOS AEMET ACTIVOS (CAP):
{avisos_cap if avisos_cap else 'Sin avisos activos'}

AEMET Asturias HOY:
{aemet_hoy[:aemet_limit] if aemet_hoy else 'No disponible'}

AEMET Asturias MAÑANA:
{aemet_man[:aemet_limit] if aemet_man else 'No disponible'}

AEMET Asturias PASADO MAÑANA:
{aemet_pas[:aemet_limit] if aemet_pas else 'No disponible'}

AEMET Llanera horaria (hoy+mañana franjas operativas):
{llanera_horaria_compact[:hor_limit] if llanera_horaria_compact else 'No disponible'}

⚙️ **RENDIMIENTO**: Temp >25°C o presión <1010 hPa → menciona mayor carrera de despegue y peor ascenso. Temp <15°C + presión >1020 hPa → aire denso, rendimiento óptimo.

⚠️ FORMATO ESTRICTO: escribe CADA SECCIÓN numerada en su PROPIO PÁRRAFO separado por una LÍNEA EN BLANCO. NUNCA juntes dos secciones sin línea en blanco entre ellas. En las secciones 7 y 8 cada día va en su propia línea con línea en blanco entre días.
Formato de cada sección:
0) **METAR LEAS explicado** — LEAS = Aeropuerto de Asturias (referencia, ~30 km de La Morgal) (versión corta para novatos - máximo 2 líneas, sin jerga)

0.1) **METAR LEMR explicado** — LEMR = La Morgal (estimado/local, NO confundir con LEAS) (versión corta para novatos - máximo 2 líneas, sin jerga)

0.5) **📊 PRONÓSTICO vs REALIDAD ACTUAL (HOY {fecha_actual} a las {hora_actual})**:
   Escribe un párrafo breve y narrativo (2-4 frases naturales, no una tabla ni una lista de datos crudos). Cuenta en lenguaje fluido qué esperaba el pronóstico para hoy y qué está ocurriendo realmente: si el viento es más flojo o más fuerte de lo previsto, si las nubes son más altas o más bajas, si la visibilidad sorprende. Usa los emojis ✅/⚠️/〰️ solo al final para valorar el grado de coincidencia, y cierra con una frase que indique si las condiciones son adecuadas para volar o no.

1) **COINCIDENCIAS** clave entre fuentes para los 4 días.
   Si solo coinciden en algunos días, indícalo.

2) **DISCREPANCIAS** clave entre fuentes y explicación meteorológica probable (frentes, borrascas, diferencias de modelo).

3) **📊 EVOLUCIÓN METEOROLÓGICA POR DÍA** — 1 línea por día: carácter (ESTABLE/CAMBIANTE/INESTABLE/DETERIORO/MEJORA), mañana vs tarde, tendencia viento. Pista solo para HOY.
   Ej: "HOY: ESTABLE, viento W constante, pista 28 | MAÑANA: DETERIORO tarde | PASADO MAÑANA: ... | DENTRO DE 3 DÍAS: ..."

4) **🎯 ANÁLISIS DE PISTA PROBABLE EN SERVICIO** (solo HOY):
   Valida {hora_actual} contra horario (invierno 09:00-20:00 / verano 09:00-21:45). Usa viento ACTUAL (no pronóstico).
   - Antes apertura: "AÚN NO ABIERTO, evaluable desde apertura"
   - <1h hasta cierre: "🕐 CIERRE INMINENTE - no merece la pena"
   - 1-2h: "⚠️ TIEMPO LIMITADO - solo vuelo breve"
   - >2h: PISTA 10 o 28 + headwind/crosswind AMBAS pistas (con valores ACTUALES en kt)
   - Ejemplo: "HOY → PISTA 28 (viento ACTUAL 13 kt desde 268°, rachas 23 kt, hw 13 kt, xw 3 kt) ✅ - viable hasta 20:00"
   MAÑANA/PASADO/3 DÍAS: sin datos de dirección → omite cálculo de pista.

5) **🕐 EVOLUCIÓN MAÑANA/TARDE** (los 4 días):
   Para cada día, redacta 2 frases narrativas cortas — una para la mañana (09-14h) y otra para la tarde (14-cierre) — describiendo en lenguaje natural cómo evolucionan el viento, nubosidad y condiciones. NO hagas listas de horas. Usa los datos horarios Open-Meteo disponibles.
   Ejemplo: "HOY — Mañana: viento flojo del norte, cielos despejados, condiciones óptimas. Tarde: rachas aumentan ligeramente pero siguen dentro de límites."

6) **VEREDICTO POR DÍA** (los 4 días):
   HOY: usa CONDICIONES ACTUALES (no pronóstico). Evalúa PRIMERO tiempo restante hasta cierre, DESPUÉS riesgo convectivo (CRÍTICO/ALTO → ❌ inmediato), DESPUÉS condiciones.
   - <1h cierre: 🕐 CIERRE INMINENTE | 1-2h: ⚠️ TIEMPO LIMITADO | Antes apertura: evalúa igualmente (no es YA NO DISPONIBLE)
   MAÑANA/PASADO/3 DÍAS: basado en pronóstico.
   Justificación obligatoria cada día: viento kt, rachas kt, Δrachas-medio kt, techo ft, cobertura, precip, visibilidad, headwind/crosswind.
   Criterio: ✅ todos OK + convección NULA/BAJA | ⚠️ 1 parámetro límite o convección MODERADA | ❌ 2+ límite o factor crítico (rachas >22 kt / lluvia / techo <800 ft / convección ALTA/CRÍTICA)
   ⚠️ CRÍTICO: cuando el veredicto sea ⚠️, SIEMPRE nombra explícitamente qué parámetro(s) están en el límite. NO escribas solo "1 parámetro límite" — di cuál: ej. "⚠️ techo bajo (1800 ft BKN)", "⚠️ rachas límite (20 kt)", "⚠️ visibilidad reducida (6 km)", etc.

7) **RIESGOS CRÍTICOS** (HOY, MAÑANA, PASADO MAÑANA, DENTRO DE 3 DÍAS):
   Para cada día escribe UNA sola frase narrativa que mencione SOLO los factores que realmente suponen un riesgo o llamada de atención. Si el día no tiene ningún riesgo relevante, escribe "Sin riesgos destacables."
   NO hagas listas de parámetros. NO repitas lo que ya está en el veredicto. Solo lo que merece una advertencia concreta.
   Umbrales que justifican mención: rachas >18 kt, diff racha-viento >8 kt, techo <3000 ft, vis <8 km, precip >0, CAPE >200 J/kg, crosswind >10 kt.
   **HOY**: [frase narrativa o "Sin riesgos destacables."]

   **MAÑANA**: [frase narrativa o "Sin riesgos destacables."]

   **PASADO MAÑANA**: [frase narrativa o "Sin riesgos destacables."]

   **DENTRO DE 3 DÍAS**: [frase narrativa o "Sin riesgos destacables."]

8) **¿Cuándo merece la pena volar?** (los 4 días, en este orden exacto):
   - 🎉 **SÍ, IDEAL**: Condiciones placenteras, excelente para disfrutar
   - ✅ **SÍ, ACEPTABLE**: Condiciones estables, buen día para volar
   - ⚠️ **SOLO SI NECESITAS PRÁCTICA**: Agitado pero dentro de límites
   - 🏠 **NO MERECE LA PENA**: Límite o ❌ NO APTO con algo de esperanza
   - ☕ **QUEDARSE EN EL BAR**: ❌ NO APTO claro, MVFR/IFR/LIFR, lluvia, viento peligroso 🍲
   Formato (los 4 días, sin omitir ninguno). Para cada día indica la etiqueta general Y a continuación las franjas horarias viables (09:00-14:00 mañana, 17:00-20:00 tarde, ajusta según horario operativo y condiciones):
   HOY: [emoji + etiqueta] → Mañana HH-HH [✅/⚠️/❌] | Tarde HH-HH [✅/⚠️/❌] (motivo breve)

   MAÑANA: [emoji + etiqueta] → Mañana HH-HH [✅/⚠️/❌] | Tarde HH-HH [✅/⚠️/❌] (motivo breve)

   PASADO MAÑANA: [emoji + etiqueta] → Mañana HH-HH [✅/⚠️/❌] | Tarde HH-HH [✅/⚠️/❌] (motivo breve)

   DENTRO DE 3 DÍAS: [emoji + etiqueta] → Mañana HH-HH [✅/⚠️/❌] | Tarde HH-HH [✅/⚠️/❌] (motivo breve)

9) **🏆 MEJOR DÍA PARA VOLAR** (de los 4 días analizados):
   ⚠️ OBLIGATORIO: antes de responder, repasa mentalmente el veredicto de cada día de la sección 6:
   - Descarta inmediatamente cualquier día con ❌ NO APTO (rachas >22 kt, lluvia, techo <800 ft, convección ALTA/CRÍTICA)
   - Entre los restantes, ordénalos por: 1º menor racha absoluta, 2º menor diff racha-viento, 3º techo más alto, 4º mejor visibilidad
   - El mejor es el que queda primero tras ese ranking. Si empatan, desempata por "más horas de ventana operativa"
   - Si TODOS tienen ❌: "NINGUNO - condiciones adversas los 4 días"
   Indica el día elegido, el ranking resumido que llevó a esa elección, carácter (placentero/estable/agitado) y tipo de vuelo posible (travesías/circuitos/solo tráficos escuela).

10) **🌡️ SENSACIÓN TÉRMICA EN VUELO Y EQUIPO**:
   Calcula wind chill en cabina abierta ULM (temp actual + viento). Indica la sensación real y recomienda equipo concreto (capas, abrigo o gorro). Añade nota de densidad de altitud si temp >25°C o presión <1010 hPa.

11) **🌀 TÉRMICAS Y CONVECCIÓN** (HOY y mañana):
   Con CAPE, nubosidad y temp: ¿térmicas aprovechables o peligrosas para ULM? Diferencia mañana vs tarde.
   Umbral ULM: térmicas >2 m/s incómodas; CAPE >500 J/kg = evitar. Para MAÑANA: tendencia convectiva.

12) **�️ PATRÓN SINÓPTICO**:
   2-3 frases: sistema dominante sobre NW Península (borrasca/anticiclón/frente/vaguada), flujo en capas bajas y su impacto en LEMR próximas 24-48h. Apoya en los mapas adjuntos si disponibles.

13) **VEREDICTO FINAL GLOBAL** (una línea contundente con carácter del vuelo y recomendación honesta)

Reglas CRÍTICAS:
- **VALIDACIÓN HORARIA EN HOY ES CRÍTICA**: detecta invierno/verano (ver DATOS FIJOS), valida {hora_actual} contra límites operativos. Pista solo para HOY (días futuros: sin dirección disponible).
- **CRITERIO DE RACHAS — COMPROBACIÓN OBLIGATORIA ANTES DE ESCRIBIR CADA DÍA**:
  * PASO 1: ¿Rachas > 22 kt? → ❌ NO APTO. STOP. No puede ser ⚠️. No hay excepción. (25 kt > 22 kt → ❌)
  * PASO 2: ¿Diff racha-viento > 10 kt? → ⚠️ PRECAUCIÓN como mínimo.
  * Ejemplos: 5G18KT = diff 13kt → ⚠️ | 5G24KT → ❌ | 15G25KT → ❌ | 12G25KT → ❌
  * RECORDATORIO: si en tus datos aparece un día con racha ≥23 kt, el veredicto ES ❌, jamás ⚠️.
- **SÉ CONSERVADOR**: Si hay 2+ factores límite simultáneos, marca ❌ NO APTO
- **UNIDADES**: Open-Meteo/Windy en km/h → kt: divide entre 1.852. NUNCA etiquetes kt sin convertir. METAR ya viene en kt.
- **DATOS CONCRETOS**: cada día cita ≥4 valores (viento/racha/precip/nube/vis). Si hay incertidumbre, dilo.
- **MEJOR DÍA**: indica siempre cuál es (o NINGUNO si todos son malos).
- **NUMERACIÓN Y SALTOS (CRÍTICO)**: Incluye SIEMPRE el número de sección (0, 0.1, 0.5, 1…13). Separa cada sección con línea en blanco. No escribas instrucciones internas del prompt en tu respuesta."""

        user_content: list[dict] = [{"type": "text", "text": user_message}]

        # Detectar si vamos a usar un modelo con límites bajos
        # GitHub Models: 60k tokens/min (muy restrictivo con mapas)
        # mini/small: bajo límite de tokens
        model_cascade = getattr(config, "AI_MODEL_CASCADE", [])
        primary_model = model_cascade[0] if model_cascade else "gpt-4o"
        is_mini_model = "mini" in primary_model.lower() or "small" in primary_model.lower()
        is_github_provider = provider.lower() == "github"

        # Excluir imágenes si: es mini, está bloqueado, O es GitHub Models
        # Solo incluir imágenes para OpenAI (límites más altos)
        if not is_mini_model and not is_github_provider and not (_is_primary_locked_for_cycle(provider, primary_model)):
            # Solo agregar imágenes si es OpenAI con modelo potente
            # Usar URLs (mucho menos tokens que base64: ~100 vs ~15k por imagen)
            for url in map_urls:
                user_content.append({"type": "image_url", "image_url": {"url": url}})
            print(f"📸 Incluyendo {len(map_urls)} mapas AEMET como URLs - OpenAI {primary_model}")
        else:
            reason = "está bloqueado por rate-limit"
            if is_mini_model:
                reason = f"es modelo limitado ({primary_model})"
            if is_github_provider:
                reason = f"es GitHub Models (60k tokens/min) - textos AEMET reducidos a {aemet_limit} chars"
            print(f"⚠️ NO incluyendo imágenes ({reason})")

        # Conteo EXACTO de tokens del payload completo (sistema + usuario)
        full_messages_preview = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
        exact_tokens = _count_tokens(full_messages_preview, model=primary_model)
        print(f"📊 Tokens de entrada EXACTOS: {exact_tokens} (payload completo sistema+usuario)")
        if exact_tokens > 7500:
            print(f"⚠️  ADVERTENCIA: payload cerca del límite de 8000 tokens ({exact_tokens}/8000)")
        elif exact_tokens > 6000:
            print(f"⚠️  Payload elevado: {exact_tokens} tokens — considera reducir datos")
        else:
            print(f"✅ Payload OK: {exact_tokens} tokens")


        response = _create_chat_completion_with_fallback(
            client=client,
            provider=provider,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.4,
            max_tokens=4000,
        )

        result = response.choices[0].message.content
        print(f"✅ Síntesis experta generada exitosamente con {provider}")
        return _append_final_disclaimer(result)

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ Error generando síntesis experta con {provider}: {e}")
        print(f"Detalles: {error_detail}")
        
        # Proporcionar un resumen COMPLETO de todos los datos disponibles como fallback
        daily = weather_data.get('daily_forecast', [])
        windy_daily = windy_data.get('daily_summary', []) if windy_data else []
        
        fallback_sections = []
        
        # Encabezado
        fallback_sections.append(f"⚠️ No se pudo generar análisis IA completo en este ciclo (Error: {str(e)[:100]})")
        fallback_sections.append("\n📊 RESUMEN COMPLETO DE DATOS DISPONIBLES:\n")
        
        # METAR
        fallback_sections.append(f"**METAR LEAS:**\n{metar_leas or 'No disponible'}\n")
        
        # Condiciones actuales
        fallback_sections.append("**CONDICIONES ACTUALES (Open-Meteo):**")
        fallback_sections.append(f"- Temperatura: {current.get('temperature', 'N/A')}°C (sensación: {current.get('feels_like', 'N/A')}°C)")
        fallback_sections.append(f"- Viento: {current.get('wind_speed', 'N/A')} km/h desde {current.get('wind_direction', 'N/A')}°")
        fallback_sections.append(f"- Rachas: {current.get('wind_gusts', 'N/A')} km/h")
        fallback_sections.append(f"- Presión: {current.get('pressure', 'N/A')} hPa")
        fallback_sections.append(f"- Nubosidad: {current.get('cloud_cover', 'N/A')}%\n")
        
        # Pronóstico 4 días
        if daily:
            fallback_sections.append("**PRONÓSTICO 4 DÍAS (Open-Meteo):**")
            labels = ["HOY", "MAÑANA", "PASADO MAÑANA", "DENTRO DE 3 DÍAS"]
            for i, day in enumerate(daily[:4]):
                label = labels[i] if i < len(labels) else f"DÍA +{i}"
                sunrise = day.get('sunrise', 'N/A')
                sunset = day.get('sunset', 'N/A')
                fallback_sections.append(f"\n{label} ({day.get('date', 'N/A')}):")
                fallback_sections.append(f"  🌡️ Temp: {day.get('temp_min', 'N/A')}°C - {day.get('temp_max', 'N/A')}°C")
                fallback_sections.append(f"  💨 Viento max: {day.get('wind_max', 'N/A')} km/h")
                fallback_sections.append(f"  🌬️ Rachas max: {day.get('wind_gusts_max', 'N/A')} km/h")
                fallback_sections.append(f"  ☀️ Amanecer: {sunrise.split('T')[1][:5] if 'T' in sunrise else sunrise}")
                fallback_sections.append(f"  🌅 Atardecer: {sunset.split('T')[1][:5] if 'T' in sunset else sunset}")
        
        # Windy
        if windy_daily:
            fallback_sections.append("\n**PRONÓSTICO WINDY (4 días):**")
            for day in windy_daily[:4]:
                fallback_sections.append(f"\n{day.get('date', 'N/A')}:")
                fallback_sections.append(f"  💨 Viento máx: {day.get('max_wind_kmh', 'N/A')} km/h")
                fallback_sections.append(f"  🌬️ Rachas máx: {day.get('max_gust_kmh', 'N/A')} km/h")
                fallback_sections.append(f"  🌡️ Temp media: {day.get('avg_temp_c', 'N/A')}°C")
                fallback_sections.append(f"  🌧️ Precip: {day.get('precip_total_mm', 'N/A')} mm")
        
        # AEMET predicciones
        aemet_hoy = aemet_prediccion.get('asturias_hoy', '') if aemet_prediccion else ''
        aemet_man = aemet_prediccion.get('asturias_manana', '') if aemet_prediccion else ''
        aemet_pas = aemet_prediccion.get('asturias_pasado_manana', '') if aemet_prediccion else ''
        
        if aemet_hoy or aemet_man or aemet_pas:
            fallback_sections.append("\n**PREDICCIONES AEMET ASTURIAS:**")
            if aemet_hoy:
                fallback_sections.append(f"\nHOY:\n{aemet_hoy[:300]}{'...' if len(aemet_hoy) > 300 else ''}")
            if aemet_man:
                fallback_sections.append(f"\nMAÑANA:\n{aemet_man[:300]}{'...' if len(aemet_man) > 300 else ''}")
            if aemet_pas:
                fallback_sections.append(f"\nPASADO MAÑANA:\n{aemet_pas[:300]}{'...' if len(aemet_pas) > 300 else ''}")
        
        # Notas finales
        fallback_sections.append("\n⚠️ **IMPORTANTE:**")
        fallback_sections.append("- Los datos anteriores NO incluyen análisis experto IA")
        fallback_sections.append("- Consulta briefing oficial AEMET y METAR actualizado antes de volar")
        fallback_sections.append("- El análisis IA completo estará disponible en el siguiente ciclo de actualización")
        fallback_sections.append("- Para ULM: límites típicos viento medio 15-18 kt, rachas 20-22 kt (consulta POH de tu modelo)")
        
        return _append_final_disclaimer("\n".join(fallback_sections))
