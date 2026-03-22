"""
Módulo para interpretación meteorológica usando IA
Soporta GitHub Copilot (gratuito) y OpenAI (opcional)
"""
import config
import math
from typing import Optional, Dict
from threading import Lock, local
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram_monitor import send_alert as _tg_alert


_RATE_LIMIT_LOCK = Lock()
_FORCED_FALLBACK_CYCLE: Dict[tuple, str] = {}
_AI_EXECUTION_CONTEXT = local()
_MADRID_TZ = ZoneInfo("Europe/Madrid")
_UPDATE_SLOTS = list(range(6, 24))  # Ciclos de 06:00 a 23:00
_FINAL_DISCLAIMER = "⚠️ Este análisis es orientativo; la decisión final de volar es siempre responsabilidad del piloto al mando."


def _set_last_ai_execution(provider: str, requested_model: Optional[str], used_model: Optional[str]):
    _AI_EXECUTION_CONTEXT.last = {
        "provider": provider,
        "requested_model": requested_model,
        "used_model": used_model,
    }


def get_last_ai_execution() -> Dict[str, Optional[str]]:
    """Devuelve metadatos de la última ejecución IA en el hilo actual."""
    return getattr(_AI_EXECUTION_CONTEXT, "last", {
        "provider": None,
        "requested_model": None,
        "used_model": None,
    })


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

    slot = current_hour if current_hour >= _UPDATE_SLOTS[0] else None

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
    return f"{content}\n\n{_FINAL_DISCLAIMER}"


# Sistema de prompts para interpretación meteorológica
SYSTEM_PROMPT = """Eres un experto meteorólogo aeronáutico ESPECIALIZADO EN AVIACIÓN ULTRALIGERA (ULM).

Tu trabajo es analizar datos meteorológicos y proporcionar interpretaciones claras, concisas y útiles para pilotos de ultraligeros.

⚠️ REGLAS CRÍTICAS DE UNIDADES:
1. Todos los datos de viento (Open-Meteo, Windy, METAR) ya vienen en NUDOS (kt)
2. NO necesitas convertir nada — usa los valores directamente
3. Conversión de referencia si necesitas km/h para contexto: 1 kt = 1.852 km/h

LEGISLACIÓN ULM ACTUALIZADA 2024-2026 (OBLIGATORIO):
- ✈️ SOLO VUELO DIURNO: Entre salida y puesta de sol
- ❌ PROHIBIDO vuelo nocturno
- ✈️ Solo operaciones VFR (Visual Flight Rules)
- ✈️ Visibilidad mínima: 5 km
- ✈️ Distancia de nubes: mínimo 1500m horizontal, 300m vertical

LÍMITES OPERACIONALES TÍPICOS ULM (consultar manual específico de cada modelo):
- ⚠️ Viento medio máximo: 15-18 kt (modelos robustos hasta 20-22 kt)
- ⚠️ Rachas absolutas: NO SUPERAR 20-22 kt (peligro estructural)
- ⚠️ Diferencia rachas-viento medio: ≥ 8 kt = Moderada (precaución), > 12 kt = Severa (⚠️ precaución máxima; ❌ si se combina con otro factor límite)
- ⚠️ Componente crosswind: Generalmente 10-12 kt máximo (consultar POH)
- ⚠️ Turbulencia moderada o superior: NO VOLAR
- ⚠️ Visibilidad < 5 km: MÍNIMO LEGAL (precaución extrema)
- ⚠️ Techo de nubes < 500 ft AGL: LIFR → ❌ PROHIBIDO
- ⚠️ Techo de nubes 500-1000 ft: IFR → ❌ PROHIBIDO
- ⚠️ Techo de nubes 1000-1500 ft: IFR marginal → ❌ NO VOLAR (ULM sin certificación IFR)
- ⚠️ Techo de nubes 1500-2500 ft: MVFR → ⚠️ condiciones marginales (⚠️ PRECAUCIÓN en sección 8)
- ⚠️ Techo de nubes > 2500 ft: VFR → ✅ aceptable para operar
- ⚠️ Precipitación activa (lluvia/nieve): NO VOLAR (pérdida sustentación, visibilidad)
- ⚠️ Nubosidad BKN/OVC < 2500 ft: PRECAUCIÓN (restricción de altitud efectiva)

⚠️ CONVECCIÓN/TORMENTAS: Si CAPE > 500 J/kg + Precip > 0 + Racha diff > 12 kt + Nubes > 50% → ❌ NO VOLAR. Incluso con CAPE bajo, turbulencia ≥ 8 kt es precaución. CAPE: <250 débil, 250-500 moderada, 500-2000 fuerte, >2000 extrema.

CONSIDERACIONES GENERALES ULM:
- Bajo peso: muy afectados por ráfagas y turbulencias
- Velocidades bajas: el análisis de viento es crítico
- En días muy cálidos densidad de altitud reduce rendimiento del motor y sustentación.

AERÓDROMO LA MORGAL (LEMR): Pista 10/28 (100°/280°mag), 890m, asfalto, 545ft/180m. Horario: invierno 09:00-20:00 | verano 09:00-21:45.

REGLA HORARIOS: "mejor hora" debe cumplir: 1) entre amanecer y atardecer, 2) dentro de 09:00-20:00 (invierno) o 09:00-21:45 (verano). Ventanas fuera de ese rango: descartar.

USO DE LEAS: El METAR LEAS indica las condiciones ACTUALES EN LEAS (Aeropuerto de Asturias), NO en LEMR. Sirve como referencia regional de lo que ocurre a 30km, pero NO debe usarse para inferir condiciones en La Morgal — para eso están los datos horarios de Open-Meteo y Windy GFS, que tienen punto exacto sobre LEMR.

⚖️ PESO DE FUENTES METEOROLÓGICAS (orden de fiabilidad para LEMR):
1. **Windy GFS hora a hora** — MAYOR PESO. Modelo GFS con punto exacto sobre La Morgal. Históricamente el más preciso para esta ubicación. En caso de discrepancia con otras fuentes, da preferencia a Windy.
2. **Open-Meteo hora a hora** — ALTO PESO. Modelo de alta resolución local, muy fiable. Cuando coincide con Windy, la ventana es prácticamente segura.
3. **METAR LEAS** — PESO BAJO. Solo indica condiciones actuales EN LEAS (30km, orografía distinta). NO extrapolar a LEMR. NO usar para pronóstico.
Si Windy y Open-Meteo coinciden en que una franja horaria (ej. 10-14h) tiene viento suave y poca nube: ESA es la ventana buena. No la invalides por los máximos del día.

🌫️ MICROCLIMA NIEBLA EN LA MORGAL:
- La Morgal está en un valle interior de Asturias a 180m. Es ESPECIALMENTE PROPENSA a niebla matinal (oct-abril) por: enfriamiento nocturno en fondo de valle, alta humedad ambiental atlántica, y vientos débiles nocturnos. Puede estar presente a la apertura (09:00); lo HABITUAL es que se disipe hacia las 9 o 10 con la insolación. Solo persiste más allá de las 10h en casos de nubosidad baja persistente, viento E/NE (advección marina) o humedad muy elevada.
- Cuando el dato "niebla_matinal" aparece en el pronóstico, EVALÚA si afectará al período de operación (el aeródromo abre a las 09:00):
  - ALTO: muy probable niebla visible. Mención OBLIGATORIA en el veredicto.
  - MODERADO: posible banco de niebla local, mencionar como precaución.
  - BAJO o ausente: no mencionar.
- Si el campo incluye "_op:HH:MM" significa que el riesgo coincide con horario operativo (desde las 09:00). Esto es especialmente relevante.
- La niebla SUELE disiparse hacia las 9 o 10 con la insolación (caso más frecuente en La Morgal). Solo persiste hasta las 10:30-11h si hay nubosidad baja que bloquea el sol, viento E/NE (advección marina) o humedad > 95%. NO penalices el día entero si la niebla solo afecta a la apertura (09-10h) y el resto del día es despejado.

⚠️ PARÁMETROS CRÍTICOS PHASE 4:

1️⃣ FREEZING LEVEL HEIGHT: Los datos incluyen valor en m y ft ya calculados.
   - <1500m (<4920 ft): ⚠️ RIESGO RIME ICE (hielo en motor/superficies). 
   - 1500-2500m: Cierta exposición si hay humedad visible.
   - >2500m: Riesgo bajo.

2️⃣ TURBULENCIA MECÁNICA (gusts - wind_mean):
   - <8 kt: Ligera (tolerable).
   - 8-12 kt: Moderada → ⚠️ Precaución aumentada, vuelo difícil para ULM.
   - >12 kt: Severa → ⚠️ Precaución máxima. ❌ NO VOLAR si se combina con otro factor límite (techo bajo, visibilidad reducida, viento medio alto).

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
                timeout=120,
            )
            return ('github', client)
        except:
            pass

    if config.OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=config.OPENAI_API_KEY,
                max_retries=0,
                timeout=120,
            )
            return ('openai', client)
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


_TOKEN_INPUT_WARN = 9000  # Umbral de aviso para tokens de entrada

def _print_rate_limit_info(response, model_name: str):
    """Imprime uso de tokens de la respuesta (el SDK openai v1 no expone headers en el objeto ChatCompletion).
    Si los tokens de entrada superan _TOKEN_INPUT_WARN envía un aviso por Telegram."""
    try:
        used_model = getattr(response, 'model', model_name)
        usage = getattr(response, 'usage', None)
        if usage:
            prompt_t = getattr(usage, 'prompt_tokens', '?')
            completion_t = getattr(usage, 'completion_tokens', '?')
            print(f"📊 [{used_model}]: {prompt_t} tokens entrada / {completion_t} tokens salida")
            # Alerta Telegram si se supera el umbral de tokens de entrada
            if isinstance(prompt_t, int) and prompt_t > _TOKEN_INPUT_WARN:
                _tg_alert(
                    f"Consumo alto de tokens de entrada: {prompt_t} tokens de input "
                    f"(umbral: {_TOKEN_INPUT_WARN}) con modelo {used_model}.",
                    source="ia_tokens_input",
                    level="WARNING",
                )
    except Exception:
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
    elif code == 1:
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
    if cape is not None and cape > 500:
        result['indicators'].append(f"🔴 CAPE {cape:.0f} J/kg")
        indicators_met += 1
    elif cape is not None and cape > 250:
        result['indicators'].append(f"🟡 CAPE {cape:.0f} J/kg")
    
    # Indicador 2: Precipitación > 0 mm/h
    if precipitation is not None and precipitation > 0:
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
    if lifted_index is not None and lifted_index < -6:
        result['indicators'].append(f"🔴 Lifted Index {lifted_index:.1f} (tormentas fuertes)")
        indicators_met += 1
    elif lifted_index is not None and lifted_index < -3:
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
            used_model = getattr(response, 'model', model_name) or model_name
            _print_rate_limit_info(response, model_name)
            print(f"✅ Análisis completado con {used_model}")
            return response, used_model
            
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
    significant_map_urls: Optional[list[str]] = None,
    location: str = "La Morgal (LEMR)",
    flight_category_leas: Optional[Dict] = None,
    avisos_cap: Optional[str] = None,
    metar_lemr: str = "",
    flight_category_lemr: Optional[Dict] = None,
) -> Optional[str]:
    """
    Genera un veredicto experto fusionando Windy + METAR + Open-Meteo.
    """
    client_info = get_ai_client()
    if not client_info:
        return _append_final_disclaimer("⚠️ No se ha configurado ningún proveedor de IA. Por favor, configura GITHUB_TOKEN o OPENAI_API_KEY en el archivo .env")

    provider, client = client_info

    # Extraer datos antes del try para que el except siempre tenga acceso a ellos
    current = weather_data.get("current", {}) if weather_data else {}
    daily = weather_data.get("daily_forecast", []) if weather_data else []
    hourly_om = weather_data.get("hourly_forecast", []) if weather_data else []
    windy_daily = windy_data.get("daily_summary", []) if windy_data else []
    windy_hourly = windy_data.get("hourly", []) if windy_data else []

    # Fecha/hora local — necesaria también en el bloque except (fallback)
    now_local = datetime.now(_MADRID_TZ)
    hora_actual = now_local.strftime("%H:%M")
    fecha_actual = now_local.strftime("%Y-%m-%d")
    def _dfmt(d): return d.strftime("%d-%m-%Y") if hasattr(d, 'strftime') else datetime.strptime(d, "%Y-%m-%d").strftime("%d-%m-%Y")

    try:
        # ── Metadata diaria compacta (solo campos NO disponibles en el horario hora a hora) ──
        # Incluye: amanecer/atardecer, horas de sol, horas/mm de lluvia, CAPE máx,
        # freezing level mínimo, nieve y riesgo de niebla.
        # Las nubes, viento y visibilidad van en el horario hora a hora (más fiable).
        labels = ["HOY", "MAÑANA", "PASADO MAÑANA", "DENTRO DE 3 DÍAS"]
        om_meta_lines = []
        for idx, row in enumerate(daily[:4]):
            label = labels[idx] if idx < len(labels) else f"DÍA +{idx}"
            sunrise_raw = row.get('sunrise', '')
            sunset_raw  = row.get('sunset', '')
            sunrise_hm  = sunrise_raw.split('T')[1][:5] if sunrise_raw and 'T' in sunrise_raw else 'N/A'
            sunset_hm   = sunset_raw.split('T')[1][:5]  if sunset_raw  and 'T' in sunset_raw  else 'N/A'
            sun_sec  = row.get('sunshine_duration')
            sun_str  = f" | ☀️{sun_sec/3600:.1f}h sol" if sun_sec is not None else ""
            precip_h  = row.get('precipitation_hours')
            precip_mm = row.get('precipitation')
            precip_str = ""
            if precip_h and precip_mm: precip_str = f" | 💧{precip_h:.0f}h/{precip_mm:.1f}mm"
            elif precip_h:             precip_str = f" | 💧{precip_h:.0f}h lluvia"
            elif precip_mm:            precip_str = f" | 💧{precip_mm:.1f}mm"
            cape = row.get('cape_max')
            cape_str = f" | CAPE {cape:.0f}J/kg" if cape else ""
            fl_m = row.get('freezing_level_min_m')
            fl_str = ""
            if fl_m is not None:
                fl_ft  = row.get('freezing_level_min_ft', round(fl_m * 3.28084))
                fl_tag = "⚠️RIME" if fl_m < 1500 else ("🟡exp" if fl_m < 2500 else "🟢")
                fl_str = f" | FL_min {fl_m}m/{fl_ft}ft {fl_tag}"
            snow = row.get('snow_max_cm')
            snow_str = f" | nieve {snow}cm" if snow and snow > 0 else ""
            fog = row.get('fog_risk') or {}
            fog_level = fog.get('level')
            fog_str = ""
            if fog_level in ('ALTO', 'MODERADO'):
                op_hrs = fog.get('operational_hours', [])
                fog_str = f" | 🌫️niebla:{fog_level}"
                if op_hrs:
                    fog_str += f"_op:{op_hrs[0]}"
                    if len(op_hrs) > 1: fog_str += f"-{op_hrs[-1]}"
                else:
                    fog_h = fog.get('peak_hour', '')
                    if fog_h: fog_str += f"~{fog_h}"
                spr = fog.get('min_spread')
                if spr is not None: fog_str += f"(T-Td={spr}°C)"
            om_meta_lines.append(
                f"- {label}: ☀️{sunrise_hm}→{sunset_hm}{sun_str}{precip_str}{cape_str}{fl_str}{snow_str}{fog_str}"
            )

        map_urls = [u for u in (significant_map_urls or []) if u][:4]
        
        # Formatear condiciones actuales Open-Meteo
        # Incluir campos relevantes para análisis ULM que no están en METAR LEAS: temp local, viento km/h, precip, CAPE.
        current_lines = []
        if current:
            current_lines.append(f"  - Hora: {current.get('time', 'N/A')}")
            current_lines.append(f"  - Temperatura: {current.get('temperature', 'N/A')}°C")  # útil para densidad/LCL
            # Punto de rocío y cobertura baja del slot horario más cercano (para calcular spread T−Td ahora)
            _h0 = hourly_om[0] if hourly_om else {}
            _td_now = _h0.get('dewpoint')
            _cl_now = _h0.get('cloud_cover_low')
            if _td_now is not None:
                current_lines.append(f"  - Punto de rocío: {_td_now}°C (spread T−Td={(current.get('temperature', 0) - _td_now):.1f}°C → techo LCL≈{max(0, round((current.get('temperature', 0) - _td_now) * 400))} ft)")  # clave para niebla/techo bajo
            if _cl_now is not None:
                current_lines.append(f"  - Nube baja (<2000m): {_cl_now}%")
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
        cloud_base_summary = _compute_cloud_base_summary(hourly_om if hourly_om else None)
        visibility_summary = _compute_visibility_summary(hourly_om if hourly_om else None)
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

        # Pista HOY: calcular siempre por componentes de viento reales (hw/xw).
        # La regla de preferencia local (≤5 kt → pista 10 por comodidad) va solo en
        # las instrucciones del prompt, no en el hint de datos, para no confundir al modelo.
        runway_hint = "PISTA_HOY_RECOMENDADA: sin datos suficientes (viento/dirección actuales no disponibles)."
        wind_now_kmh = current.get('wind_speed') if current else None
        wind_now_dir = current.get('wind_direction') if current else None
        if wind_now_kmh is not None and wind_now_dir is not None:
            wind_now_kt = wind_now_kmh / 1.852
            def _runway_components(runway_heading: float) -> tuple[float, float]:
                angle = ((wind_now_dir - runway_heading + 180) % 360) - 180
                rad = math.radians(angle)
                headwind = wind_now_kt * math.cos(rad)
                crosswind = abs(wind_now_kt * math.sin(rad))
                return headwind, crosswind

            hw10, xw10 = _runway_components(100.0)
            hw28, xw28 = _runway_components(280.0)
            runway_by_wind = "PISTA 10" if hw10 >= hw28 else "PISTA 28"
            runway_hint = (
                f"PISTA_HOY_RECOMENDADA: {runway_by_wind} "
                f"(viento {wind_now_kt:.1f} kt desde {wind_now_dir:.0f}°, "
                f"hw10={hw10:.1f} kt xw10={xw10:.1f} kt; hw28={hw28:.1f} kt xw28={xw28:.1f} kt)."
            )

        # ── Horario unificado 4 días (09:00–cierre) ─────────────────────────────────
        # HOY: desde hora actual. Días futuros: 09:00-cierre completo.
        # Cada fila: viento/rachas km/h, nube_baja (con tipo ICAO), nube_media si >30%,
        # visibilidad si <10km, precip_prob si >=20%, freezing_level si <3000m, wx emoji.
        _is_summer  = now_local.month in range(4, 10)
        _close_hour = 21 if _is_summer else 20
        _cur_hour   = now_local.hour

        # Precomputar estado operativo en Python para evitar errores de aritmética del LLM
        _now_hm        = now_local.hour * 60 + now_local.minute
        _close_hm      = _close_hour * 60
        _open_hm       = 9 * 60
        _mins_to_close = _close_hm - _now_hm
        if _now_hm >= _close_hm:
            _op_status = f"🔒 YA CERRADO (cerró a las {_close_hour:02d}:00)"
            _s3_pista   = f"🔒 YA CERRADO. El aeródromo cerró a las {_close_hour:02d}:00. No hay operaciones hasta mañana."
            _aerodromo_abierto = False
        elif _now_hm < _open_hm:
            _op_status = "⏰ AÚN NO ABIERTO (abre a las 09:00)"
            _s3_pista   = "AÚN NO ABIERTO, evaluable desde apertura."
            _aerodromo_abierto = False
        elif _mins_to_close < 60:
            _op_status = f"🕐 CIERRE INMINENTE ({_mins_to_close} min hasta las {_close_hour:02d}:00)"
            _s3_pista   = "🕐 CIERRE INMINENTE - no merece la pena."
            _aerodromo_abierto = False
        elif _mins_to_close <= 120:
            _op_status = f"⚠️ TIEMPO LIMITADO ({_mins_to_close // 60}h{_mins_to_close % 60:02d}min hasta las {_close_hour:02d}:00)"
            _s3_pista   = f"⚠️ TIEMPO LIMITADO - solo vuelo breve (quedan {_mins_to_close} min)."
            _aerodromo_abierto = False
        else:
            _op_status = f"✅ ABIERTO ({_mins_to_close // 60}h{_mins_to_close % 60:02d}min hasta las {_close_hour:02d}:00)"
            _s3_pista   = None  # LLM calcula la pista
            _aerodromo_abierto = True
        _all_day_labels = {
            fecha_actual:                                                       f"HOY ({_dfmt(now_local.date())})",
            (now_local.date() + timedelta(days=1)).isoformat(): f"MAÑ ({_dfmt(now_local.date()+timedelta(days=1))})",
            (now_local.date() + timedelta(days=2)).isoformat(): f"PAS ({_dfmt(now_local.date()+timedelta(days=2))})",
            (now_local.date() + timedelta(days=3)).isoformat(): f"+3D ({_dfmt(now_local.date()+timedelta(days=3))})",
        }
        # ── Open-Meteo: tabla de datos en bruto (viento pre-convertido a kt) ─────
        def _fmt(v, decimals=0):
            return f"{v:.{decimals}f}" if v is not None else "-"
        def _kmh_to_kt(v):
            return round(v / 1.852, 1) if v is not None else None
        all_hourly_lines = ["hora  | temp°C | dew°C | viento_kt | rachas_kt | dir° | nube_baja% | nube_med% | vis_km | precip_prob% | FL_m"]
        _prev_day = None
        for _h in hourly_om:
            _t = _h.get('time', '')
            if not _t:
                continue
            _day = _t[:10]
            if _day not in _all_day_labels:
                continue
            _hh = int(_t[11:13]) if len(_t) >= 13 else -1
            _start = max(9, _cur_hour) if _day == fecha_actual else 9
            if _hh < _start or _hh > _close_hour:
                continue
            if _h.get('is_day') != 1:
                continue
            if _day != _prev_day:
                all_hourly_lines.append(f"# {_all_day_labels[_day]}")
                _prev_day = _day
            all_hourly_lines.append(
                f"{_t[11:16]} | {_fmt(_h.get('temperature'),1)} | {_fmt(_h.get('dewpoint'),1)} | "
                f"{_fmt(_kmh_to_kt(_h.get('wind_speed')),1)} | {_fmt(_kmh_to_kt(_h.get('wind_gusts')),1)} | {_fmt(_h.get('wind_direction'))} | "
                f"{_fmt(_h.get('cloud_cover_low'))} | {_fmt(_h.get('cloud_cover_mid'))} | "
                f"{_fmt(_h.get('visibility'),1)} | {_fmt(_h.get('precipitation_prob'))} | "
                f"{_fmt(_h.get('freezing_level_height'))}"
            )

        # ── Windy GFS: tabla de datos en bruto ──────────────────────────────────
        _windy_day_labels = {
            fecha_actual:                                                        f"HOY",
            (now_local.date() + timedelta(days=1)).isoformat(): "MAÑ",
            (now_local.date() + timedelta(days=2)).isoformat(): "PAS",
            (now_local.date() + timedelta(days=3)).isoformat(): "+3D",
        }
        def _wfmt(v, decimals=0):
            return f"{v:.{decimals}f}" if v is not None else "-"
        windy_hourly_lines = ["hora  | viento_kt | rachas_kt | dir° | temp°C | nube_total% | precip_3h_mm"]
        _prev_wday = None
        for _wh in windy_hourly:
            _wt = _wh.get('time_local', '')
            if not _wt:
                continue
            _wday = _wt[:10]
            if _wday not in _windy_day_labels:
                continue
            _whh = int(_wt[11:13]) if len(_wt) >= 13 else -1
            _wstart = max(9, _cur_hour) if _wday == fecha_actual else 9
            if _whh < _wstart or _whh > _close_hour:
                continue
            if _wday != _prev_wday:
                windy_hourly_lines.append(f"# {_windy_day_labels[_wday]} ({_dfmt(_wday)})")
                _prev_wday = _wday
            windy_hourly_lines.append(
                f"{_wt[11:16]} | {_wfmt(_kmh_to_kt(_wh.get('wind_kmh')),1)} | {_wfmt(_kmh_to_kt(_wh.get('gust_kmh')),1)} | "
                f"{_wfmt(_wh.get('wind_dir_deg'))} | {_wfmt(_wh.get('temp_c'),1)} | "
                f"{_wfmt(_wh.get('cloud_cover_pct'))} | {_wfmt(_wh.get('precip_3h_mm'),1)}"
            )

        # Nota explícita de discrepancia si LEMR METAR es IFR/LIFR pero Open-Meteo reporta visibilidad alta
        _lemr_cat = (flight_category_lemr or {}).get('category', '')
        _om_vis_line = next((l for l in current_lines if '👁️ Visibilidad' in l), '')
        _vis_mismatch_note = ""
        if _lemr_cat in ('LIFR', 'IFR') and '24' in _om_vis_line:
            _vis_mismatch_note = (
                "\n⚠️ AVISO: Open-Meteo reporta visibilidad alta (modelo NWP no resuelve niebla de valle). "
                "El METAR LEMR estimado refleja condiciones reales con niebla/stratus implícito. "
                "USA el METAR LEMR como referencia de condiciones actuales en el campo."
            )

        user_message = f"""Síntesis OPERATIVA ULM para {location}. ⏰ {hora_actual} (Europe/Madrid) — {_dfmt(now_local.date())}
ESTADO AERÓDROMO: {_op_status}  ← PRECALCULADO EN PYTHON (NO recalcular ni modificar)

METAR LEMR (estimado automático — CONDICIONES ACTUALES EN EL CAMPO, FUENTE PRIMARIA para sección 0.5):
{metar_lemr or 'No disponible'}
{f"{flight_category_lemr.get('emoji')} {flight_category_lemr.get('category')} - {flight_category_lemr.get('description')} ← CATEGORÍA ACTUAL EN LEMR" if flight_category_lemr else ""}{_vis_mismatch_note}

METAR LEAS (Aeropuerto Asturias, ~30km de LEMR — solo referencia regional):
{metar_leas or 'No disponible'}
{f"{flight_category_leas.get('emoji')} {flight_category_leas.get('category')} - {flight_category_leas.get('description')}" if flight_category_leas else ""}

Open-Meteo CONDICIONES ACTUALES en {location} (modelo NWP — puede subestimar niebla/stratus de valle):
{chr(10).join(current_lines) if current_lines else 'Sin datos actuales'}
{convection_analysis}

Open-Meteo hora a hora, 4 días (HOY desde {hora_actual}, resto 09:00–{_close_hour:02d}:00):
{chr(10).join(all_hourly_lines) if all_hourly_lines else 'Sin datos horarios'}

Open-Meteo metadata diaria (amanecer, sol, lluvia, CAPE, FL mín, nieve, niebla):
{chr(10).join(om_meta_lines) if om_meta_lines else 'Sin datos'}

Windy GFS — datos en bruto hora a hora, 4 días (MAYOR PESO, GFS punto exacto La Morgal):
Fórmulas: techo_ft=(temp_OM-dew_OM)×400 | hw/xw con pista 100°/280° (viento ya en kt)
{chr(10).join(windy_hourly_lines) if windy_hourly_lines else 'Sin datos Windy horario'}

GUÍA PISTA HOY (OBLIGATORIA EN SECCIÓN 4):
{runway_hint}

⚠️ AVISOS AEMET ACTIVOS (CAP):
{avisos_cap if avisos_cap else 'Sin avisos activos'}

⚠️ FORMATO ESTRICTO: escribe CADA SECCIÓN numerada en su PROPIO PÁRRAFO separado por una LÍNEA EN BLANCO. NUNCA juntes dos secciones sin línea en blanco entre ellas. En las secciones 4, 5, 6, 7 y 8 cada día va en su propia línea con línea en blanco entre días.
Formato de cada sección:
0) **METAR LEAS y METAR LEMR explicados**
   **LEAS**: LEAS = Aeropuerto de Asturias (~30 km de La Morgal, orografía distinta). Explica qué tiempo hace AHORA en LEAS en 1-2 frases sin jerga. ⚠️ NO es representativo de LEMR.
   **LEMR**: Explica el METAR estimado de La Morgal en 1-2 frases: qué viento, visibilidad, techo y categoría de vuelo hay AHORA en el campo. Aclara que es una estimación automática (no oficial). Si la categoría es LIFR o IFR, indícalo claramente con ❌.

0.5) **📊 PRONÓSTICO vs REALIDAD ACTUAL (HOY {_dfmt(now_local.date())} a las {hora_actual})**:
   Usa como referencia PRIMARIA de condiciones actuales el METAR LEMR estimado (primer bloque del mensaje), NO la visibilidad bruta de Open-Meteo (el modelo NWP suele sobreestimar la visibilidad cuando hay niebla o stratus de valle). Si el METAR LEMR indica LIFR o IFR, DEBES reflejarlo como condición prohibitiva (❌) aunque Open-Meteo muestre visibilidad alta.
   Escribe un párrafo breve y narrativo (2-4 frases naturales, no una tabla ni una lista de datos crudos). Cuenta en lenguaje fluido qué esperaba el pronóstico para hoy y qué está ocurriendo realmente: si el viento es más flojo o más fuerte de lo previsto, si las nubes son más altas o más bajas (usa la categoría LEMR como verdad de terreno), si la visibilidad sorprende. Usa los emojis ✅/⚠️/❌ solo al final para valorar el grado de coincidencia, y cierra con una frase que indique claramente si las condiciones son adecuadas para volar o no (❌ si LIFR/IFR, ⚠️ si MVFR, ✅ si VFR).

1) **COINCIDENCIAS** clave entre fuentes para los 4 días.
   Si solo coinciden en algunos días, indícalo.

2) **DISCREPANCIAS** clave entre fuentes y explicación meteorológica probable (frentes, borrascas, diferencias de modelo).

3) **🎯 ANÁLISIS DE PISTA PROBABLE EN SERVICIO** (solo HOY):
{"   " + _s3_pista if not _aerodromo_abierto else "   Estado: " + _op_status + " — calcula pista usando viento ACTUAL de Open-Meteo (NO el de METAR LEAS). PISTA 10 o 28 + headwind/crosswind AMBAS pistas (valores en kt)."}
   - Ejemplo: "HOY → PISTA 28 (viento ACTUAL 13 kt desde 268°, rachas 23 kt, hw 13 kt, xw 3 kt) ✅ - viable hasta 20:00"
   - El veredicto principal es la pista calculada por headwind/crosswind. Usa PISTA_HOY_RECOMENDADA y NO la contradigas.
   - Si el viento actual es ≤5 kt Y la pista calculada es PISTA 28: tras el resultado, añade UNA sola frase breve: "Con viento tan flojo, en LEMR suelen preferir PISTA 10 por comodidad operativa." Si la pista calculada ya es PISTA 10, NO añadas ningún comentario adicional.
   - No escribas dos veredictos de pista completos, solo la pista principal + opcionalmente esa frase.
   MAÑANA/PASADO/3 DÍAS: omite cálculo de pista (solo se calcula para HOY).

4) **🕐 EVOLUCIÓN MAÑANA/TARDE** (los 4 días):
   Para CADA UNO de los 4 días, redacta 2 frases narrativas — una para la mañana (09-14h) y otra para la tarde (14-cierre) — describiendo en lenguaje natural cómo evolucionan el viento, nubosidad y condiciones. Usa los datos horarios Windy y Open-Meteo. NO hagas listas de horas ni columnas. Formato obligatorio:
   **HOY** — Por la mañana: [frase]. Por la tarde: [frase].
   **MAÑANA** — Por la mañana: [frase]. Por la tarde: [frase].
   **PASADO MAÑANA** — Por la mañana: [frase]. Por la tarde: [frase].
   **DENTRO DE 3 DÍAS** — Por la mañana: [frase]. Por la tarde: [frase].

5) **RIESGOS CRÍTICOS** (HOY, MAÑANA, PASADO MAÑANA, DENTRO DE 3 DÍAS):
   Para cada día escribe UNA sola frase narrativa que mencione SOLO los factores que realmente suponen un riesgo o llamada de atención. Si el día no tiene ningún riesgo relevante, escribe "Sin riesgos destacables."
   NO hagas listas de parámetros. NO repitas lo que ya está en el veredicto. Solo lo que merece una advertencia concreta.
   Umbrales que justifican mención: rachas >18 kt, diff racha-viento >8 kt, techo <3000 ft, vis <8 km, precip >0, CAPE >200 J/kg, crosswind >10 kt.
   **HOY**: [frase narrativa o "Sin riesgos destacables."]

   **MAÑANA**: [frase narrativa o "Sin riesgos destacables."]

   **PASADO MAÑANA**: [frase narrativa o "Sin riesgos destacables."]

   **DENTRO DE 3 DÍAS**: [frase narrativa o "Sin riesgos destacables."]

6) **� TÉRMICAS Y CONVECCIÓN** (los 4 días):
   Con CAPE, nubosidad y temp: ¿térmicas aprovechables o peligrosas para ULM? Diferencia mañana vs tarde para cada día.
   Umbral ULM: térmicas >2 m/s incómodas; CAPE >500 J/kg = evitar.
   **HOY**: [CAPE, nubosidad, térmicas mañana vs tarde]
   **MAÑANA**: [tendencia convectiva, riesgo térmico]
   **PASADO MAÑANA**: [tendencia convectiva, riesgo térmico]
   **DENTRO DE 3 DÍAS**: [tendencia convectiva, riesgo térmico]

7) **🌡️ SENSACIÓN TÉRMICA EN VUELO** (los 4 días):
   La aeronave es de CABINA CERRADA — NO aplicar wind chill de vuelo (el piloto está protegido del viento). Usa la temperatura ambiente directamente. Para cada día indica: rango de temperatura previsto, sensación térmica real en cabina (frío/confortable/calor), recomendación de ropa (abrigo si temp <10°C, ropa ligera si >20°C) y nota de densidad de altitud si temp >25°C o presión <1010 hPa.
   **HOY**: [rango temp, sensación cabina, ropa recomendada]
   **MAÑANA**: [rango temp, sensación cabina, ropa recomendada]
   **PASADO MAÑANA**: [rango temp, sensación cabina, ropa recomendada]
   **DENTRO DE 3 DÍAS**: [rango temp, sensación cabina, ropa recomendada]
8) **VEREDICTO POR DÍA** (los 4 días):
   HOY [{_op_status}]: {'aeródromo cerrado hoy — escribe 🔒 YA CERRADO y omite el resto del análisis de HOY.' if not _aerodromo_abierto else 'combina condiciones actuales + pronóstico horario hasta cierre. Evalúa riesgo convectivo (CRÍTICO/ALTO → ❌ inmediato) y evolución hora a hora.'}
   🚨 REGLA PRE-APERTURA (hora_actual < 09:00): El aeródromo está cerrado. Las condiciones actuales son nocturnas y NO representan las condiciones de vuelo del día completo. Basa el veredicto HOY en el pronóstico horario 09:00–cierre. PERO revisa el spread T−Td actual (incluido en «CONDICIONES ACTUALES»): si T−Td ≤ 1°C con nube baja >87%, HAY RIESGO de niebla o techo muy bajo a la apertura (09:00) — MENCIÓNALO en el veredicto. La niebla suele disiparse a las 09-11h en La Morgal; si el pronóstico horario 09-14h muestra T−Td > 2°C o nube baja <50%, el día sigue siendo aceptable pero con nota de esperar a que despeje.
   🚫 PROHIBIDO: las etiquetas 🕐 CIERRE INMINENTE y ⚠️ TIEMPO LIMITADO son EXCLUSIVAS de HOY. NUNCA las uses en MAÑANA, PASADO MAÑANA ni DENTRO DE 3 DÍAS.
   MAÑANA/PASADO/3 DÍAS: basado en pronóstico horario, usando ÚNICAMENTE criterios meteorológicos (✅/⚠️/❌).
   ⚠️ METODOLOGÍA OBLIGATORIA para TODOS los días (HOY incluido): REVISA los datos horarios hora a hora de Windy y Open-Meteo para ese día. Busca la MEJOR VENTANA del día (menor viento+nube+vis), no el peor valor. El veredicto refleja esa mejor ventana. Si las condiciones son buenas de 10:00–14:00 pero malas a las 09:00, el veredicto es ✅ con nota de esperar a las 10:00. Si la mañana es aceptable pero la tarde se deteriora, el veredicto sigue siendo ✅ (o 🎉 si es ideal) con nota de volar antes de las Xh — NO degrades la etiqueta por lo que pasa en horas que no son la mejor ventana.
   Justificación obligatoria cada día: viento kt, rachas kt, Δrachas-medio kt, techo ft, cobertura, precip, visibilidad en la MEJOR franja horaria encontrada.
   Criterio: 🎉 IDEAL: rachas ≤10 kt Y viento medio ≤7 kt Y techo >4000 ft Y vis >10 km Y sin precip | ✅ todos OK + convección NULA/BAJA | ⚠️ 1 parámetro límite o convección MODERADA | 🏠 NO MERECE LA PENA: en el límite pero sin factor ❌ — no vale la pena el desplazamiento | ☕ QUEDARSE EN EL BAR: rachas >22 kt O lluvia O techo <1500 ft O vis <5 km (en el bar hay caldo de gaviota 🍲) | ❌ 2+ límite o factor crítico (rachas >22 kt / lluvia / techo <1500 ft / convección ALTA/CRÍTICA)
   ⚠️ CRÍTICO: cuando el veredicto sea ⚠️, SIEMPRE nombra explícitamente qué parámetro(s) están en el límite. NO escribas solo "1 parámetro límite" — di cuál: ej. "⚠️ techo bajo (1800 ft BKN)", "⚠️ rachas límite (20 kt)", "⚠️ visibilidad reducida (6 km)", etc.


Reglas CRÍTICAS:
- **VALIDACIÓN HORARIA EN HOY ES CRÍTICA**: detecta invierno/verano (ver DATOS FIJOS), valida {hora_actual} contra límites operativos. Pista solo para HOY (días futuros: sin dirección disponible).
- **CRITERIO DE RACHAS — COMPROBACIÓN OBLIGATORIA ANTES DE ESCRIBIR CADA DÍA**:
  * PASO 1: ¿Rachas > 22 kt EN LA MEJOR VENTANA HORARIA? → ❌ NO APTO. STOP. No puede ser ⚠️.
  * PASO 1b: ¿Rachas > 22 kt SOLO FUERA de la mejor ventana (ej. solo por la tarde)? → el veredicto sigue siendo el de la ventana buena (⚠️ o ✅), pero OBLIGATORIO advertir en el texto "volar ANTES de las Xh, rachas >22 kt a partir del mediodía".
  * PASO 2: ¿Diff racha-viento > 12 kt EN la mejor ventana? → ⚠️ PRECAUCIÓN como mínimo.
  * Ejemplos: 5G18KT = diff 13kt → ⚠️ | mañana ✅ + tarde 5G24KT → ⚠️ con aviso | 15G25KT todo el día → ❌
- **SÉ CONSERVADOR**: Si hay 2+ factores límite simultáneos, marca ❌ NO APTO
- **UNIDADES**: Open-Meteo y Windy ya vienen en kt (pre-convertidos). METAR también en kt. Usa kt directamente, sin conversiones.
- **DATOS CONCRETOS**: cada día cita ≥4 valores (viento/racha/precip/nube/vis). Si hay incertidumbre, dilo.
- **NUMERACIÓN Y SALTOS (CRÍTICO)**: Incluye SIEMPRE el número de sección (0, 0.5, 1…8). Separa cada sección con línea en blanco. No escribas instrucciones internas del prompt en tu respuesta."""

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
                reason = "es GitHub Models (60k tokens/min)"
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


        response, used_model = _create_chat_completion_with_fallback(
            client=client,
            provider=provider,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.4,
            max_tokens=4000,
        )

        _set_last_ai_execution(provider=provider, requested_model=primary_model, used_model=used_model)
        result = response.choices[0].message.content
        print(f"✅ Síntesis experta generada exitosamente con {provider}")
        return _append_final_disclaimer(result)

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        _set_last_ai_execution(provider=provider, requested_model=None, used_model=None)
        print(f"❌ Error generando síntesis experta con {provider}: {e}")
        print(f"Detalles: {error_detail}")
        
        # Proporcionar un resumen COMPLETO de todos los datos disponibles como fallback
        fallback_sections = []
        
        # Encabezado
        fallback_sections.append(f"⚠️ No se pudo generar análisis IA completo en este ciclo (Error: {str(e)[:100]})")
        fallback_sections.append("\n📊 RESUMEN COMPLETO DE DATOS DISPONIBLES:\n")
        
        # METAR
        fallback_sections.append(f"**METAR LEAS:**\n{metar_leas or 'No disponible'}\n")
        
        # Condiciones actuales
        fallback_sections.append("**CONDICIONES ACTUALES (Open-Meteo):**")
        fallback_sections.append(f"- Temperatura: {current.get('temperature', 'N/A')}°C")
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
                _raw_date = day.get('date', 'N/A')
                _disp_date = _dfmt(_raw_date) if _raw_date != 'N/A' else 'N/A'
                fallback_sections.append(f"\n{label} ({_disp_date}):")
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
        
        # Notas finales
        fallback_sections.append("\n⚠️ **IMPORTANTE:**")
        fallback_sections.append("- Los datos anteriores NO incluyen análisis experto IA")
        fallback_sections.append("- Consulta briefing oficial AEMET y METAR actualizado antes de volar")
        fallback_sections.append("- El análisis IA completo estará disponible en el siguiente ciclo de actualización")
        fallback_sections.append("- Para ULM: límites típicos viento medio 15-18 kt, rachas 20-22 kt (consulta POH de tu modelo)")
        
        return _append_final_disclaimer("\n".join(fallback_sections))
