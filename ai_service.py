"""
Módulo para interpretación meteorológica usando IA
Soporta GitHub Copilot (gratuito) y OpenAI (opcional)
"""
import config
from typing import Optional, Dict
from threading import Lock
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


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

Ejemplo CORRECTO:
"Viento: 33.8 km/h = 18.3 kt (conversión: 33.8 ÷ 1.852)
Componente crosswind = 18.3 × sin(59°) = 15.7 kt"

Ejemplo INCORRECTO ❌:
"Viento: 33.8 km/h ≈ 18.3 kt
Componente crosswind = 33.8 × sin(59°) = 28.9 kt" ← ESTO ESTÁ MAL, usó km/h en vez de kt

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
- ⚠️ Diferencia rachas-viento medio: > 10 kt = ALTO RIESGO (turbulencia mecánica)
- ⚠️ Componente crosswind: Generalmente 10-12 kt máximo (consultar POH)
- ⚠️ Turbulencia moderada o superior: NO VOLAR
- ⚠️ Visibilidad < 5 km: MÍNIMO LEGAL (precaución extrema)
- ⚠️ Techo de nubes < 1000 ft AGL: IFR/LIFR → ❌ PROHIBIDO
- ⚠️ Techo de nubes 1000-3000 ft: MVFR → ❌ PROHIBIDO (condiciones marginales)
- ⚠️ Precipitación activa (lluvia/nieve): NO VOLAR (pérdida sustentación, visibilidad)
- ⚠️ Nubosidad BKN/OVC < 3000 ft: PRECAUCIÓN (restricción vertical)

CONSIDERACIONES GENERALES ULM:
- Bajo peso: muy afectados por ráfagas y turbulencias
- Velocidades bajas: el análisis de viento es crítico
- Mayor sensibilidad a condiciones meteorológicas que aviación general
- Operaciones VFR exclusivamente
- En días muy cálidos el avión rinde peor que en días fríos: trepa menos y en despegue conviene dejarlo volar más antes de rotar.

INFORMACIÓN AERÓDROMO LA MORGAL (LEMR):
- 🛫 Pista 10/28 (orientación 100°/280° magnético)
- 🛫 Longitud: 890m | Elevación: 545 ft (180m)
- 🛫 Coordenadas: 43°25.833'N 005°49.617'W

CONTEXTO OPERATIVO OBLIGATORIO - AERÓDROMO DE LA MORGAL (LEMR):
- Nombre: Aeródromo de La Morgal (Asturias)
- Coordenadas: 43 25.833 N / 05 49.617 O
- Frecuencia: 123.500
- Elevación: 545 ft / 180 m
- Pista: 10/28, 890 m, asfalto
- Horario operativo:
    - Invierno: Diario de 09:00 a 20:00
    - Verano: Diario de 09:00 a 21:45

REGLA DE PLANIFICACIÓN DE HORARIOS (CRÍTICA):
- Cuando propongas "mejor hora para volar", SIEMPRE debe cumplir simultáneamente:
    1) Horario DIURNO (entre amanecer y atardecer)
    2) Horario de APERTURA del aeródromo de La Morgal
- Si una buena ventana meteorológica cae fuera de horario operativo, debes descartarla.

USO DE LEAS COMO REFERENCIA PARA LEMR:
- LEMR no dispone de METAR operativo continuo.
- Usa METAR/TAF de LEAS + pronóstico local + mapas sinópticos para inferir condiciones probables en LEMR.
- Explica explícitamente la incertidumbre de esa extrapolación (distancia, orografía, microclima local).
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
        windy_daily = windy_data.get("daily_summary", []) if windy_data else []
        windy_hourly = windy_data.get("hourly", []) if windy_data else []

        om_lines = []
        labels = ["HOY", "MAÑANA", "PASADO MAÑANA", "DENTRO DE 3 DÍAS"]
        for idx, row in enumerate(daily[:4]):
            label = labels[idx] if idx < len(labels) else f"DÍA +{idx}"
            om_lines.append(
                f"- {label}: temp {row.get('temp_min')}-{row.get('temp_max')}°C, "
                f"viento máx {row.get('wind_max')} km/h, rachas máx {row.get('wind_gusts_max')} km/h, "
                f"amanecer {row.get('sunrise')}, atardecer {row.get('sunset')}"
            )

        windy_lines = []
        for row in windy_daily[:4]:
            windy_lines.append(
                f"- {row.get('date')}: viento máx {row.get('max_wind_kmh')} km/h, "
                f"rachas máx {row.get('max_gust_kmh')} km/h, precip {row.get('precip_total_mm')} mm"
            )

        hourly_lines = []
        for row in windy_hourly[:24]:  # Ampliado a 24 horas para mejor planificación
            t = row.get("time_local", "")
            hh = t.split("T")[1][:5] if "T" in t else t
            hourly_lines.append(
                f"- {hh}: {row.get('wind_kmh')} km/h ({row.get('wind_dir_deg')}°), "
                f"rachas {row.get('gust_kmh')} km/h"
            )

        aemet_hoy = (aemet_prediccion or {}).get("asturias_hoy", "")
        aemet_man = (aemet_prediccion or {}).get("asturias_manana", "")
        aemet_pas = (aemet_prediccion or {}).get("asturias_pasado_manana", "")
        # Llanera: el dict tiene llanera_dia0..3, combinar los disponibles
        _llan_parts = [
            (aemet_prediccion or {}).get("llanera_dia0", ""),
            (aemet_prediccion or {}).get("llanera_dia1", ""),
            (aemet_prediccion or {}).get("llanera_dia2", ""),
            (aemet_prediccion or {}).get("llanera_dia3", ""),
        ]
        aemet_llan = "\n".join(p for p in _llan_parts if p)
        
        # Optimización: reducir AEMET para GitHub Models (límite 60k tokens/min)
        is_github = provider.lower() == "github"
        aemet_limit = 600 if is_github else 1200  # Mitad de tamaño para GitHub Models

        map_urls = [u for u in (significant_map_urls or []) if u][:4]
        
        # Obtener hora actual para contexto
        now_local = datetime.now(_MADRID_TZ)
        hora_actual = now_local.strftime("%H:%M")
        fecha_actual = now_local.strftime("%Y-%m-%d")

        # Formatear condiciones actuales Open-Meteo
        current_lines = []
        if current:
            current_lines.append(f"  - Hora: {current.get('time', 'N/A')}")
            current_lines.append(f"  - Temperatura: {current.get('temperature', 'N/A')}°C (sensación {current.get('feels_like', 'N/A')}°C)")
            current_lines.append(f"  - Humedad: {current.get('humidity', 'N/A')}%")
            current_lines.append(f"  - Viento: {current.get('wind_speed', 'N/A')} km/h desde {current.get('wind_direction', 'N/A')}°")
            current_lines.append(f"  - Rachas: {current.get('wind_gusts', 'N/A')} km/h")
            current_lines.append(f"  - Nubosidad: {current.get('cloud_cover', 'N/A')}%")
            current_lines.append(f"  - Presión: {current.get('pressure', 'N/A')} hPa")
            current_lines.append(f"  - Precipitación: {current.get('precipitation', 'N/A')} mm")

        user_message = f"""Actúa como experto en meteorología aeronáutica ULM para {location} y crea una síntesis OPERATIVA final de alta precisión.

⏰ HORA ACTUAL: {hora_actual} (Europe/Madrid) - Fecha: {fecha_actual}

DATOS FIJOS AERÓDROMO LEMR:
    - Pista: 10/28 (rumbos 100° y 280°)
    - Horario operativo: Invierno (oct-mar) 09:00-20:00 / Verano (abr-sep) 09:00-21:45
    - Solo VFR diurno

METAR LEAS (referencia):
{metar_leas or 'No disponible'}
{f"{flight_category_leas.get('emoji')} Clasificación: {flight_category_leas.get('category')} - {flight_category_leas.get('description')}" if flight_category_leas else ""}

METAR LEMR (estimado local):
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

Open-Meteo (resumen 4 días):
{chr(10).join(om_lines) if om_lines else 'Sin datos'}

Windy Point Forecast (resumen 4 días):
{chr(10).join(windy_lines) if windy_lines else 'Sin datos'}

Windy próximas 24 horas:
{chr(10).join(hourly_lines) if hourly_lines else 'Sin datos'}

AEMET Asturias HOY:
{aemet_hoy[:aemet_limit] if aemet_hoy else 'No disponible'}

AEMET Asturias MAÑANA:
{aemet_man[:aemet_limit] if aemet_man else 'No disponible'}

AEMET Asturias PASADO MAÑANA:
{aemet_pas[:aemet_limit] if aemet_pas else 'No disponible'}

AEMET Llanera:
{aemet_llan[:aemet_limit] if aemet_llan else 'No disponible'}

Lectura sinóptica/mapa AEMET previa:
(Sin mapas en análisis de fusión para reducir payload)

Objetivo: comparación razonada entre Windy vs AEMET (solo texto) vs METAR/Open-Meteo para DECISIÓN DE VUELO ULM en LEMR.

⚙️ **RENDIMIENTO**: Temp >25°C o presión <1010 hPa → menciona mayor carrera de despegue y peor ascenso. Temp <15°C + presión >1020 hPa → aire denso, rendimiento óptimo.

⚠️ VALIDACIÓN HORARIA PARA HOY (CRÍTICA):
- Determina si {fecha_actual} es temporada invierno (oct-mar) o verano (abr-sep)
- Si invierno: horario operativo es 09:00-20:00 | Si verano: 09:00-21:45
- Compara {hora_actual} (hora actual) contra el horario operativo
- Si {hora_actual} está ANTES de la apertura: NO marques HOY como no disponible; indica "aún no abierto" y evalúa HOY desde la hora de apertura
- Si {hora_actual} está DENTRO del horario operativo: 
  * Calcula el tiempo restante hasta el cierre
  * Si quedan **< 1 hora**: marca "🕐 CIERRE INMINENTE - Ya no merece la pena (cierra pronto, tiempo insuficiente)"
  * Si quedan **1-2 horas**: marca "⚠️ TIEMPO LIMITADO - Solo para vuelo muy breve (cierra en X minutos, va justo)"
  * Si quedan **> 2 horas**: HOY es viable, analiza viento y condiciones meteorológicas
- Si {hora_actual} está DESPUÉS del cierre: marca HOY como "🕐 YA NO DISPONIBLE - fuera de horario operativo"

Formato obligatorio:
0) **METAR LEAS explicado** (versión corta para novatos - máximo 2 líneas, sin jerga)
0.1) **METAR LEMR explicado** (versión corta para novatos - máximo 2 líneas, sin jerga, indicando que es estimado/local)

0.5) **📊 PRONÓSTICO vs REALIDAD ACTUAL (HOY {fecha_actual} a las {hora_actual})**:
   OBLIGATORIO: Compara explícitamente qué decía el pronóstico para HOY vs qué está pasando AHORA MISMO:
   - Ejemplo: "Pronóstico HOY: viento máx 26 km/h, rachas máx 35 km/h → REALIDAD AHORA: viento 24.1 km/h, rachas 42.8 km/h ⚠️ (rachas más fuertes de lo esperado)"
   - Ejemplo: "Pronóstico HOY: nubosidad variable → REALIDAD AHORA: 100% nublado (peor de lo esperado)"
   - Ejemplo: "Pronóstico HOY: temp máx 15°C → REALIDAD AHORA: 14.6°C (dentro de lo esperado)"
   - Si las condiciones actuales son MEJORES o PEORES que el pronóstico, menciónalo claramente
   - Este análisis es CRÍTICO para decidir si HOY es viable AHORA vs lo que se esperaba

1) **COINCIDENCIAS** clave entre fuentes para los 4 días (¿qué dicen TODAS las fuentes para los próximos 4 días?)
   - Analiza las coincidencias entre Open-Meteo, Windy y AEMET para los 4 días completos
   - Ejemplo: "Todas las fuentes coinciden en vientos moderados HOY y MAÑANA, y vientos fuertes PASADO MAÑANA"
   - Ejemplo: "Todas las fuentes coinciden en cielos despejados los 4 días"
   - Si solo coinciden en algunos días, indícalo: "Coinciden en buen tiempo HOY y MAÑANA, pero difieren en PASADO MAÑANA"

2) **DISCREPANCIAS** clave entre fuentes para los 4 días y explicación meteorológica probable
   - Analiza las discrepancias entre Open-Meteo, Windy y AEMET para los 4 días completos
   - Ejemplo: "Windy prevé rachas de 87 km/h DENTRO DE 3 DÍAS, mientras que Open-Meteo solo prevé 45 km/h - posible diferencia en el modelo de borrasca"
   - Ejemplo: "Open-Meteo prevé lluvia MAÑANA por la tarde, pero Windy solo indica nubosidad - posible discrepancia en la progresión del frente"
   - Si hay discrepancias significativas, explica la causa meteorológica probable (frentes, borrascas, modelos diferentes)

3) **📊 EVOLUCIÓN METEOROLÓGICA POR DÍA** (análisis temporal conciso para los 4 días):
   Para cada día (HOY, MAÑANA, PASADO MAÑANA, DENTRO DE 3 DÍAS):
   - **Carácter del día**: ESTABLE / CAMBIANTE / INESTABLE / DETERIORO PROGRESIVO / MEJORA PROGRESIVA
   - **Mañana vs Tarde**: ¿Mejora o empeora? (ej: "Mañana tranquila, tarde ventosa" o "Estable todo el día")
   - **Tendencia del viento**: ¿Rota? ¿Cambia de pista probable? (ej: "Viento rola de W a NW → cambio pista 28→10 tarde")
   - **Formato compacto**: Max 1 línea por día (ej: "HOY: ESTABLE, viento constante W todo el día, pista 28 | MAÑANA: DETERIORO tarde, viento aumenta — dirección no disponible | PASADO MAÑANA: ...")
   - Nota: la pista probable solo se puede indicar para HOY (usando viento actual). Para días futuros, omite la indicación de pista.

4) **🎯 ANÁLISIS DE PISTA PROBABLE EN SERVICIO** (solo HOY — dirección de viento no disponible para días futuros):
   
   **HOY ({fecha_actual}):**
    - Valida si {hora_actual} está antes de apertura, dentro de horario o después de cierre (detecta invierno/verano automáticamente)
    - Calcula el tiempo restante hasta el cierre
    - Si está ANTES de apertura: indica "aún no abierto" y evalúa HOY desde la hora de apertura
    - Si está DENTRO: Analiza viento ACTUAL (usa "CONDICIONES ACTUALES", no pronóstico) Y tiempo restante
    - Si está DESPUÉS de cierre: "YA NO DISPONIBLE - fuera de horario operativo"
   - Indica: "PISTA 10" o "PISTA 28" (basado en dirección viento ACTUAL)
   - Componentes: headwind/tailwind y crosswind para AMBAS pistas (con datos ACTUALES)
    - Ejemplo si antes de abrir: "HOY → AÚN NO ABIERTO (son las {hora_actual}, abre a las 09:00), pero evaluable desde apertura"
    - Ejemplo si tras cierre: "HOY → YA NO DISPONIBLE (son las {hora_actual}, aeródromo cierra a las 20:00)"
    - Ejemplo si < 1h restante: "HOY → 🕐 CIERRE INMINENTE (quedan 45 min, cierra a las 20:00) - Ya no merece la pena"
    - Ejemplo si 1-2h restante: "HOY → ⚠️ TIEMPO LIMITADO (quedan 1h 30min, cierra a las 20:00) - Solo vuelo muy breve"
    - Ejemplo si > 2h restante viable: "HOY → PISTA 28 (viento ACTUAL 13 kt desde 268°, rachas ACTUALES 23 kt, headwind 13 kt, crosswind 3 kt) ✅ - viable hasta cierre a las 20:00"
   
   **MAÑANA / PASADO MAÑANA / DENTRO DE 3 DÍAS:**
   - ⚠️ No hay datos estructurados de dirección de viento para días futuros.
   - NO calcules headwind/crosswind ni indiques pista en servicio para estos días.
   - Si el texto de AEMET menciona explícitamente la dirección del viento para algún día, puedes citarlo como referencia orientativa (indicando la fuente), pero sin cálculos de componentes.
   - Omite esta subsección para los días futuros.

5) **VEREDICTO POR DÍA** (los 4 días completos):
   - **HOY**: ✅ APTO / ⚠️ PRECAUCIÓN / ⚠️ TIEMPO LIMITADO / 🕐 CIERRE INMINENTE / ❌ NO APTO / 🕐 YA NO DISPONIBLE
     ⚠️ CRÍTICO: Para HOY usa las "CONDICIONES ACTUALES" (datos reales a las {hora_actual}), NO el pronóstico diario.
    - Evalúa PRIMERO el tiempo restante hasta el cierre:
      * Si < 1h: marca "🕐 CIERRE INMINENTE - Ya no merece la pena" (aunque las condiciones meteorológicas sean buenas)
      * Si 1-2h: marca "⚠️ TIEMPO LIMITADO - Solo para vuelo muy breve" (si las condiciones son aceptables)
      * Si > 2h: evalúa normalmente según condiciones meteorológicas (✅ APTO / ⚠️ PRECAUCIÓN / ❌ NO APTO)
    - Si es ANTES de apertura, NO marques "YA NO DISPONIBLE": evalúa HOY igualmente y aclara que el aeródromo aún no está abierto.
     - Si las condiciones actuales son MEJORES que el pronóstico: indícalo (ej: "mejor de lo esperado")
     - Si las condiciones actuales son PEORES que el pronóstico: indícalo (ej: "rachas más fuertes de lo previsto")
   - **MAÑANA**: ✅ APTO / ⚠️ PRECAUCIÓN / ❌ NO APTO (basado en pronóstico)
   - **PASADO MAÑANA**: ✅ APTO / ⚠️ PRECAUCIÓN / ❌ NO APTO (basado en pronóstico)
   - **DENTRO DE 3 DÍAS**: ✅ APTO / ⚠️ PRECAUCIÓN / ❌ NO APTO (basado en pronóstico)
   - **JUSTIFICACIÓN MULTIFACTOR (OBLIGATORIA)**:
     * Para HOY: cita los valores ACTUALES EN TIEMPO REAL (viento, rachas, nubosidad AHORA a las {hora_actual})
     * Para HOY: MENCIONA SIEMPRE el tiempo restante hasta el cierre y su hora (ej: "quedan 3h hasta cierre a las 20:00")
     * Para MAÑANA/PASADO: cita el pronóstico esperado
     * Cita explícitamente: viento medio (kt), rachas (kt), diferencia rachas-medio (kt)
     * Cita: nubosidad (techo ft, cobertura FEW/SCT/BKN/OVC)
     * Cita: precipitación (tipo, intensidad)
     * Cita: visibilidad (km)
     * Cita: componentes headwind/crosswind para pista recomendada
   - **CRITERIO ESTRICTO**:
     * ✅ APTO: Todos los parámetros dentro de límites cómodos
     * ⚠️ PRECAUCIÓN: 1 parámetro en límite (ej: rachas 18-20 kt)
     * ❌ NO APTO: 2+ parámetros en límite O 1 factor crítico (rachas > 22 kt, lluvia, techo < 800 ft)

6) **RIESGOS CRÍTICOS** — OBLIGATORIO PARA LOS 4 DÍAS (HOY / MAÑANA / PASADO MAÑANA / DENTRO DE 3 DÍAS):
   ⚠️ NO omitas ningún día. Aunque el riesgo sea bajo, indícalo explícitamente.
   Para cada día cita: rachas, nubosidad, precipitación, visibilidad y turbulenicia.
   ⚠️ Para HOY: usa los valores de "CONDICIONES ACTUALES" (rachas, nubosidad, viento AHORA MISMO)
   Factores a evaluar por día:
   - **Rachas**: diferencia con viento medio, valor absoluto (cita valores actuales para HOY)
   - **Precipitación**: tipo (lluvia/nieve/granizo), intensidad (-/mod/+)
   - **Nubosidad**: techo bajo (ft AGL), cobertura extensa (BKN/OVC)
   - **Visibilidad**: si < 8 km (precaución), si < 5 km (límite legal)
   - **Crosswind excesivo**: si > 12 kt para pista recomendada
   - **Turbulencia mecánica por viento**: >15 kt precaución, >20 kt significativa, >25 kt fuerte/peligrosa
   - **Densidad del aire**: Temp >25°C + presión <1010 hPa = baja densidad → ⚠️ rendimiento reducido. Temp <10°C + presión >1020 hPa = alta densidad → ✅ mejor rendimiento
   - **Estabilidad atmosférica**: térmicas fuertes, convección, turbulencia orográfica
   Formato obligatorio:
   **HOY**: [lista de riesgos con valores]
   **MAÑANA**: [lista de riesgos con valores]
   **PASADO MAÑANA**: [lista de riesgos con valores]
   **DENTRO DE 3 DÍAS**: [lista de riesgos con valores]

7) **FRANJAS HORARIAS RECOMENDADAS** — OBLIGATORIO PARA LOS 4 DÍAS (HOY / MAÑANA / PASADO MAÑANA / DENTRO DE 3 DÍAS):
   - NO omitas ningún día. Si no hay ventana segura para ese día, escribe "NO RECOMENDADA".
   - Considera amanecer, atardecer, horario operativo (invierno 09:00-20:00, verano 09:00-21:45) y condiciones meteorológicas.
   - Para HOY: ten en cuenta la hora actual ({hora_actual}) y el tiempo restante hasta cierre.
   Formato obligatorio:
   **HOY**: MAÑANA 09:00-XX:00 ✅/⚠️ | TARDE XX:00-XX:00 ✅/⚠️ (o "NO RECOMENDADA")
   **MAÑANA**: MAÑANA 09:00-XX:00 ✅/⚠️ | TARDE XX:00-XX:00 ✅/⚠️ (o "NO RECOMENDADA")
   **PASADO MAÑANA**: MAÑANA 09:00-XX:00 ✅/⚠️ | TARDE XX:00-XX:00 ✅/⚠️ (o "NO RECOMENDADA")
   **DENTRO DE 3 DÍAS**: MAÑANA 09:00-XX:00 ✅/⚠️ | TARDE XX:00-XX:00 ✅/⚠️ (o "NO RECOMENDADA")

8) **🏆 MEJOR DÍA PARA VOLAR** (de los 4 días analizados):
   - Indica claramente: "HOY", "MAÑANA", "PASADO MAÑANA" o "DENTRO DE 3 DÍAS"
   - Justifica por qué es el mejor (menor viento, mejor visibilidad, menos rachas, etc.)
   - **CARÁCTER DEL MEJOR DÍA**: Especifica si será placentero/estable/agitado
   - **TIPO DE VUELO POSIBLE**: Travesías/circuitos/solo tráficos escuela
   - Si ningún día es bueno: "NINGUNO - condiciones adversas los 4 días"

9) **¿MERECE LA PENA VOLAR?** — OBLIGATORIO LOS 4 DÍAS, en este orden exacto:
   - 🎉 **SÍ, IDEAL**: Condiciones placenteras, excelente para disfrutar (solo si ✅ APTO pleno)
   - ✅ **SÍ, ACEPTABLE**: Condiciones estables, buen día para volar (solo si ✅ APTO)
   - ⚠️ **SOLO SI NECESITAS PRÁCTICA**: Agitado pero técnicamente dentro de límites (⚠️ PRECAUCIÓN)
   - 🏠 **NO MERECE LA PENA**: Límite o ❌ NO APTO con algo de esperanza
   - ☕ **QUEDARSE EN EL BAR**: ❌ NO APTO claro, MVFR/IFR/LIFR, lluvia, viento peligroso 🍲
   Formato OBLIGATORIO (los 4 días, sin omitir ninguno):
   HOY: [emoji + etiqueta] (motivo breve)
   MAÑANA: [emoji + etiqueta] (motivo breve)
   PASADO MAÑANA: [emoji + etiqueta] (motivo breve)
   DENTRO DE 3 DÍAS: [emoji + etiqueta] (motivo breve)

10) **VEREDICTO FINAL GLOBAL** (una línea contundente con carácter del vuelo y recomendación honesta)

Reglas CRÍTICAS:
- **ANÁLISIS DE PISTA: SOLO PARA HOY** (con viento actual real). Para días futuros no hay dirección disponible, omitir cálculo de componentes.
- **VALIDACIÓN HORARIA EN HOY ES CRÍTICA**: Detecta invierno/verano, valida {hora_actual} contra límites operativos
- **ANÁLISIS COMPLETO MULTIFACTOR (OBLIGATORIO para cada día)**:
  1. Viento medio (convertido a kt)
  2. Rachas y diferencia con viento medio
  3. Nubosidad: techo, cobertura, altura base
  4. Precipitación: intensidad, tipo
  5. Visibilidad
  6. Componentes headwind/crosswind para AMBAS pistas
- **CRITERIO DE RACHAS (SIN EXCEPCIONES)**:
  * Diferencia rachas-viento medio > 10 kt = ⚠️ PRECAUCIÓN o ❌ NO APTO
  * Rachas absolutas > 22 kt = ❌ NO APTO (límite estructural)
  * Ejemplo: 15G25KT = diferencia 10 kt + rachas 25 kt = ❌ NO APTO
- **CRITERIO DE NUBOSIDAD**:
  * Techo < 1000 ft = IFR/LIFR → ❌ PROHIBIDO
  * Techo 1000-3000 ft = MVFR → ❌ PROHIBIDO
  * BKN/OVC < 2000 ft = ⚠️ PRECAUCIÓN
  * Precipitación activa = ❌ NO APTO (salvo llovizna muy ligera)
- **SÉ CONSERVADOR**: Si hay 2+ factores límite simultáneos, marca ❌ NO APTO
- Convierte km/h a kt cuando compares con límites ULM Y cuando calcules componentes de viento
- No uses afirmaciones vagas: para cada día cita al menos 4 datos concretos (viento/racha/precip/nube/vis)
- Si usas los mapas significativos, menciona qué patrón sinóptico observas (frentes/isobaras/gradiente de presión, flujo dominante) y su impacto en LEMR
- Recuerda: PISTA 10 orientada 100° (despegue al ESTE), PISTA 28 orientada 280° (despegue al OESTE)
- Viento del OESTE (250°-310°) → probable PISTA 28 en servicio | Viento del ESTE (070°-130°) → probable PISTA 10 en servicio
- No propongas vuelos fuera de horario diurno ni fuera de horario operativo
- **SIEMPRE indica cuál es el MEJOR DÍA para volar** (o NINGUNO si todos son malos)
- Si hay incertidumbre, dilo explícitamente"""

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
        _llan_fb = [
            (aemet_prediccion or {}).get('llanera_dia0', ''),
            (aemet_prediccion or {}).get('llanera_dia1', ''),
            (aemet_prediccion or {}).get('llanera_dia2', ''),
            (aemet_prediccion or {}).get('llanera_dia3', ''),
        ]
        aemet_llan = '\n'.join(p for p in _llan_fb if p)
        
        if aemet_hoy or aemet_man or aemet_pas:
            fallback_sections.append("\n**PREDICCIONES AEMET ASTURIAS:**")
            if aemet_hoy:
                fallback_sections.append(f"\nHOY:\n{aemet_hoy[:300]}{'...' if len(aemet_hoy) > 300 else ''}")
            if aemet_man:
                fallback_sections.append(f"\nMAÑANA:\n{aemet_man[:300]}{'...' if len(aemet_man) > 300 else ''}")
            if aemet_pas:
                fallback_sections.append(f"\nPASADO MAÑANA:\n{aemet_pas[:300]}{'...' if len(aemet_pas) > 300 else ''}")
        
        if aemet_llan:
            fallback_sections.append(f"\n**PREDICCIÓN AEMET LLANERA:**\n{aemet_llan[:300]}{'...' if len(aemet_llan) > 300 else ''}")
        
        # Notas finales
        fallback_sections.append("\n⚠️ **IMPORTANTE:**")
        fallback_sections.append("- Los datos anteriores NO incluyen análisis experto IA")
        fallback_sections.append("- Consulta briefing oficial AEMET y METAR actualizado antes de volar")
        fallback_sections.append("- El análisis IA completo estará disponible en el siguiente ciclo de actualización")
        fallback_sections.append("- Para ULM: límites típicos viento medio 15-18 kt, rachas 20-22 kt (consulta POH de tu modelo)")
        
        return _append_final_disclaimer("\n".join(fallback_sections))
