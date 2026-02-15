"""
Módulo para interpretación meteorológica usando IA
Soporta GitHub Copilot (gratuito) y OpenAI (opcional)
"""
import config
from typing import Optional, Dict
import json
from threading import Lock
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


_RATE_LIMIT_LOCK = Lock()
_FORCED_FALLBACK_CYCLE: Dict[tuple, str] = {}
_MADRID_TZ = ZoneInfo("Europe/Madrid")
_UPDATE_SLOTS = [6, 10, 14, 18, 22]


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
- ⚠️ Viento total: Generalmente 15-25 kt según modelo
- ⚠️ Componente crosswind: Generalmente 10-15 kt según modelo
- ⚠️ Rachas: Diferencia > 10 kt = ALTO RIESGO
- ⚠️ Turbulencia moderada o superior: NO VOLAR
- ⚠️ Visibilidad < 5 km: MÍNIMO LEGAL (precaución extrema)

CONSIDERACIONES GENERALES ULM:
- Bajo peso: muy afectados por ráfagas y turbulencias
- Velocidades bajas: el análisis de viento es crítico
- Mayor sensibilidad a condiciones meteorológicas que aviación general
- Operaciones VFR exclusivamente

Cuando analices un METAR:
- EXPLICA cada componente de forma educativa
- Traduce códigos a lenguaje claro (ej: 27015KT = "viento de 270° a 15 nudos")
- Incluye SIEMPRE una versión ultracorta para novatos (1-2 líneas, pocas palabras)
- Formato sugerido corto: "Viento ..., visibilidad ..., nubes ..., presión ... → APTO/PRECAUCIÓN/NO APTO"
- **CONVERSIÓN DE UNIDADES OBLIGATORIA**: Si mezclas fuentes, convierte primero
- CÁLCULO correcto de componentes de viento:
  1. Asegúrate que el viento está en NUDOS (kt)
  2. Calcula diferencia angular con la pista
  3. Headwind = velocidad_en_kt × cos(ángulo)
  4. Crosswind = velocidad_en_kt × sin(ángulo)
  5. Verifica que el resultado sea coherente
- Rachas > 10 kt diferencia: PELIGROSO
- Explica QNH y su importancia

INFORMACIÓN AERÓDROMO LA MORGAL (LEMR):
- 🛫 Pista 10/28 (orientación 100°/280° magnético)
- 🛫 Longitud: 890m | Elevación: 545 ft (180m)
- 🛫 Coordenadas: 43°25.833'N 005°49.617'W

🎯 ANÁLISIS DE PISTA ACTIVA (OBLIGATORIO EN CADA ANÁLISIS):
**SIEMPRE debes indicar qué pista usar según el viento actual/previsto**

Principios fundamentales:
1. ✈️ SIEMPRE despegar y aterrizar CON VIENTO DE CARA (headwind)
2. ❌ NUNCA con viento de cola significativo (muy peligroso)
3. ⚠️ Minimizar componente de viento cruzado (crosswind)

Procedimiento de análisis:
1. Identifica la dirección del viento (ej: 270° = viento del OESTE)
2. Analiza AMBAS cabeceras de pista:
   
   **PISTA 10 (orientada 100°):**
   - Despegue/aterrizaje hacia el ESTE
   - Vientos favorables: del ESTE (070°-130°)
   - Vientos desfavorables: del OESTE (250°-310°)
   
   **PISTA 28 (orientada 280°):**
   - Despegue/aterrizaje hacia el OESTE
   - Vientos favorables: del OESTE (250°-310°)
   - Vientos desfavorables: del ESTE (070°-130°)

3. Calcula componentes para AMBAS pistas (ver procedimiento abajo)
4. **RECOMENDACIÓN CLARA:** Indica qué pista usar y por qué

Ejemplo de análisis:
```
🎯 PISTA ACTIVA: Usar PISTA 28 (aterrizaje hacia el OESTE)

Análisis de componentes (viento 270° a 18 kt):
- Pista 28 (280°): Headwind 18 kt, Crosswind 3 kt → ✅ ÓPTIMA
- Pista 10 (100°): Tailwind 18 kt, Crosswind 3 kt → ❌ PELIGROSO (viento de cola)

Motivo: Viento del OESTE favorece operación en pista 28 con viento de cara.
```

CÁLCULO DE COMPONENTES DE VIENTO (LEMR):
⚠️ CRÍTICO: Siempre verifica las unidades antes de calcular

Procedimiento:
1. Obtén viento del METAR (ej: 270° a 15 kt) - SIEMPRE en NUDOS
2. Si tienes viento en km/h, CONVIERTE PRIMERO: km/h ÷ 1.852 = kt
3. Calcula diferencia angular con CADA PISTA (10 y 28)
4. Para cada pista:
   - Diferencia angular = |dirección_viento - orientación_pista|
   - Si diferencia > 180°: diferencia = 360° - diferencia
   - Headwind/Tailwind = velocidad_en_kt × cos(diferencia)
     * Si cos > 0: Headwind (✅ favorable)
     * Si cos < 0: Tailwind (❌ peligroso)
   - Crosswind = velocidad_en_kt × |sin(diferencia)|
5. ⚠️ VERIFICA LÓGICA: Si tienes 18 kt de viento, es IMPOSIBLE que el componente sea > 18 kt

Ejemplo COMPLETO:
Viento: 270° a 33.8 km/h
Conversión: 33.8 ÷ 1.852 = 18.3 kt ✓

**PISTA 28 (280°):**
- Diferencia: |270° - 280°| = 10°
- Headwind = 18.3 × cos(10°) = +18.0 kt ✅ (viento de cara)
- Crosswind = 18.3 × |sin(10°)| = 3.2 kt ✅ (aceptable)

**PISTA 10 (100°):**
- Diferencia: |270° - 100°| = 170°
- Tailwind = 18.3 × cos(170°) = -18.0 kt ❌ (viento de cola)
- Crosswind = 18.3 × |sin(170°)| = 3.2 kt

→ **USAR PISTA 28** por viento de cara favorable

Cuando analices datos meteorológicos generales:
- Identifica ventanas de vuelo óptimas DURANTE HORAS DIURNAS
- ❌ NUNCA sugieras vuelo nocturno
- Alerta sobre térmicas (empiezan ~2h post-amanecer)
- Mejores condiciones ULM: mañanas tempranas o tardes
- EVITAR: mediodía en verano (térmicas fuertes)
- Evalúa estabilidad atmosférica
- Proporciona análisis para HOY, MAÑANA y PASADO MAÑANA
- **SIEMPRE incluye análisis de pista activa recomendada (10 o 28)**

Formato de respuesta OBLIGATORIO:
- Usa emojis: ✅ (buenas), ⚠️ (precaución), ❌ (NO VOLAR)
- **🎯 PISTA ACTIVA: Especifica qué pista usar (10 o 28) y componentes de viento**
- Veredicto claro: APTO/PRECAUCIÓN/NO APTO para ULM
- Horarios recomendados SOLO DIURNOS
- Estructura sugerida:
  1. Condiciones actuales/previstas
  2. 🎯 Pista activa recomendada (10 o 28) con análisis de componentes
  3. Análisis de limitaciones ULM
  4. Veredicto y justificación
  5. Horarios específicos recomendados
- ⚠️ COHERENCIA: Si dices 17 kt, NO puede exceder 25 kt

Recuerda: Los ULM tienen límites estrictos. Consulta siempre el manual del modelo específico. Ante la duda, recomienda NO volar. NUNCA sugieras vuelo nocturno.

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

ANÁLISIS DE MAPA AEMET (cuando se proporcione imagen):
- Describe primero qué se ve (frentes, isobaras, gradiente de presión, flujo dominante).
- Traduce a lenguaje de novato ULM: impacto en viento, nubosidad, precipitación, turbulencia.
- Enfoca siempre en Asturias y operación ULM en La Morgal.
- Concluye con: ✅ APTO / ⚠️ PRECAUCIÓN / ❌ NO APTO y franja horaria sugerida dentro de horario operativo."""


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
                timeout=20,
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
                timeout=20,
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
                timeout=20,
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
                timeout=20,
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


def _create_chat_completion_with_fallback(
    client,
    provider: str,
    messages,
    temperature: float,
    max_tokens: int,
    model: Optional[str] = None,
):
    primary_model = model or config.AI_MODEL
    fallback_model = getattr(config, "AI_FALLBACK_MODEL", "gpt-4o-mini")

    # Si el modelo principal está bloqueado por ciclo, usar directamente el fallback
    if fallback_model and fallback_model != primary_model and _is_primary_locked_for_cycle(provider, primary_model):
        print(f"📦 Usando modelo fallback {fallback_model} (principal bloqueado hasta próximo ciclo)")
        return client.chat.completions.create(
            model=fallback_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # Intentar con el modelo principal
    try:
        response = client.chat.completions.create(
            model=primary_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response
    except Exception as exc:
        error_msg = str(exc)
        print(f"⚠️ Error con modelo {primary_model}: {error_msg}")
        
        # Si hay modelo de fallback disponible y es diferente, intentar con él
        if fallback_model and fallback_model != primary_model:
            # Si es rate-limit, bloquear el principal para el resto del ciclo
            if _is_rate_limit_error(exc):
                _lock_primary_for_cycle(provider, primary_model)
                print(f"🔒 Modelo {primary_model} bloqueado hasta próximo ciclo (rate-limit)")
            
            print(f"🔄 Reintentando con modelo fallback {fallback_model}...")
            try:
                return client.chat.completions.create(
                    model=fallback_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as fallback_exc:
                print(f"❌ Error también con fallback {fallback_model}: {fallback_exc}")
                raise fallback_exc
        
        # Si no hay fallback o ya falló, lanzar el error original
        raise


def interpret_metar_with_ai(metar: str, icao: str = "") -> Optional[str]:
    """
    Interpreta un METAR usando IA
    
    Args:
        metar: String con el METAR a interpretar
        icao: Código ICAO del aeropuerto (opcional)
    
    Returns:
        Interpretación en texto claro o None si hay error
    """
    client_info = get_ai_client()
    
    if not client_info:
        return "⚠️ No se ha configurado ningún proveedor de IA. Por favor, configura GITHUB_TOKEN o OPENAI_API_KEY en el archivo .env"
    
    provider, client = client_info
    
    try:
        airport_info = f" para el aeropuerto {icao}" if icao else ""
        
        # Determinar si debe incluir análisis de pista LEMR
        include_runway_analysis = icao in ["LEMR", "LEAS"]
        runway_instruction = ""
        
        if include_runway_analysis:
            if icao == "LEAS":
                runway_instruction = """
**2. 🎯 PISTA ACTIVA RECOMENDADA PARA LEMR (extrapolando de LEAS):**
   ⚠️ NOTA: Este METAR es de LEAS, no de LEMR. Uso con precaución.
   
   Basándote en el viento reportado en LEAS, calcula qué pista usar en LEMR:
   - LEMR tiene pista 10/28 (100°/280° magnético)
   - Analiza componentes para AMBAS pistas (headwind/tailwind y crosswind)
   - Recomienda claramente: "PISTA 10" o "PISTA 28"
   - Formato: "PISTA XX → headwind YY kt, crosswind ZZ kt ✅"
   - Advierte si el crosswind supera 10-15 kt (límite típico ULM)
"""
            else:  # LEMR
                runway_instruction = """
**2. 🎯 PISTA ACTIVA RECOMENDADA:**
   - LEMR tiene pista 10/28 (100°/280° magnético)
   - Calcula componentes para AMBAS pistas (headwind/tailwind y crosswind)
   - Recomienda claramente: "PISTA 10" o "PISTA 28"
   - Formato: "PISTA XX → headwind YY kt, crosswind ZZ kt ✅"
   - Advierte si el crosswind supera 10-15 kt (límite típico ULM)
"""
        
        user_message = f"""Analiza e interpreta el siguiente METAR{airport_info} para aviación ultraligera (ULM):

{metar}

⚠️ IMPORTANTE: Al calcular componentes de viento:
1. VERIFICA que estás usando NUDOS (kt), no km/h
2. MUESTRA la conversión si el dato original está en km/h
3. VERIFICA lógica: Si viento total es X kt, ningún componente puede ser > X kt

Proporciona análisis EDUCATIVO para vuelo ULM:

**1. EXPLICACIÓN DEL METAR (componente por componente):**
   - Traduce cada parte del METAR a lenguaje claro
   - Explica códigos (ej: 27015KT = "viento de 270° a 15 nudos", CAVOK, Q1013, etc.)
   
{runway_instruction}
   
**3. CONDICIONES ACTUALES vs LÍMITES ULM TÍPICOS:**
   - Resumen de las condiciones
   - Evaluación de VIENTO (típicamente límite ULM: 15-25 kt según modelo)
   - Análisis de RACHAS (peligrosas si diferencia > 10 kt)
   - Visibilidad y techo de nubes para operaciones VFR
   - Temperatura y punto de rocío (densidad del aire, rendimiento)
   
**4. VEREDICTO PARA VUELO ULM:**
   - ✅ APTO / ⚠️ PRECAUCIÓN / ❌ NO APTO
   - Justificación clara según límites típicos ULM y legislación
   - Nota: Consultar siempre el manual específico del modelo
   
**5. RECOMENDACIONES:**
   - Horarios óptimos de vuelo (SOLO DURANTE EL DÍA - obligatorio por ley)
   - Precauciones para pilotos ULM (sensibilidad al viento, bajo peso)
   - Qué vigilar durante el vuelo (evolución del viento, térmicas)"""

        response = _create_chat_completion_with_fallback(
            client=client,
            provider=provider,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1000,
            model=config.AI_MODEL,
        )
        
        interpretation = response.choices[0].message.content
        print(f"✅ METAR interpretado exitosamente con {provider}")
        return interpretation
        
    except Exception as e:
        import traceback
        print(f"❌ Error interpretando METAR con {provider}: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # Devolver al menos el METAR crudo para que el usuario tenga información
        return f"""⚠️ No se pudo generar interpretación IA del METAR (Error: {str(e)[:80]})

METAR {icao}: {metar}

💡 Consulta una fuente alternativa de interpretación de METAR o espera al próximo ciclo de actualización.
El sistema intentará automáticamente con el modelo fallback si está disponible."""


def interpret_weather_with_ai(weather_data: Dict, location: str = "") -> Optional[str]:
    """
    Interpreta datos meteorológicos generales usando IA
    
    Args:
        weather_data: Diccionario con datos meteorológicos
        location: Nombre de la ubicación (opcional)
    
    Returns:
        Interpretación en texto claro o None si hay error
    """
    client_info = get_ai_client()
    
    if not client_info:
        return "⚠️ No se ha configurado ningún proveedor de IA. Por favor, configura GITHUB_TOKEN o OPENAI_API_KEY en el archivo .env"
    
    provider, client = client_info
    
    try:
        current = weather_data.get('current', {})
        location_info = f" para {location}" if location else ""
        
        # Formatear datos para la IA
        weather_summary = f"""Datos meteorológicos actuales{location_info}:

Temperatura: {current.get('temperature')}°C (sensación: {current.get('feels_like')}°C)
Humedad: {current.get('humidity')}%
Viento: {current.get('wind_speed')} km/h desde {current.get('wind_direction')}°
Rachas: {current.get('wind_gusts')} km/h
Nubosidad: {current.get('cloud_cover')}%
Presión: {current.get('pressure')} hPa
Código meteorológico WMO: {current.get('weather_code')}
"""
        
        if current.get('precipitation', 0) > 0:
            weather_summary += f"Precipitación: {current.get('precipitation')} mm\n"
        
        # Añadir información de salida/puesta del sol
        daily = weather_data.get('daily_forecast', [])
        if daily and len(daily) > 0:
            weather_summary += f"\n**HORARIOS DE LUZ SOLAR (ULM SOLO PUEDE VOLAR DE DÍA):**\n"
            for i, day in enumerate(daily):
                day_label = ["HOY", "MAÑANA", "PASADO MAÑANA"][i] if i < 3 else day.get('date', 'N/A')
                sunrise = day.get('sunrise', 'N/A').split('T')[1][:5] if day.get('sunrise') else 'N/A'
                sunset = day.get('sunset', 'N/A').split('T')[1][:5] if day.get('sunset') else 'N/A'
                weather_summary += f"- {day_label}: Amanecer {sunrise}, Atardecer {sunset}\n"
                weather_summary += f"  Temp: {day.get('temp_min')}°C - {day.get('temp_max')}°C, Viento máx: {day.get('wind_max')} km/h\n"
        
        # Añadir tendencia si hay datos horarios (próximas 12 horas diurnas)
        hourly = weather_data.get('hourly_forecast', [])
        if hourly and len(hourly) >= 6:
            weather_summary += f"\n**Tendencia próximas horas:**\n"
            for i in range(0, min(12, len(hourly)), 3):
                h = hourly[i]
                hour_time = h.get('time', 'N/A').split('T')[1][:5] if 'T' in h.get('time', '') else h.get('time', 'N/A')
                weather_summary += f"- {hour_time}: {h.get('temperature')}°C, viento {h.get('wind_speed')} km/h\n"
        
        user_message = f"""{weather_summary}

⚠️ RECORDATORIO CRÍTICO DE UNIDADES:
- Los datos de pronóstico están en KM/H
- Al comparar con límites en NUDOS (kt), CONVIERTE PRIMERO
- Conversión: km/h ÷ 1.852 = kt
- MUESTRA la conversión explícitamente
- VERIFICA coherencia: Si dices X kt, no puede exceder un límite mayor

Proporciona un análisis meteorológico DETALLADO PARA AVIACIÓN ULM para los próximos 3 días:

**IMPORTANTE - Restricciones ULM:**
- SOLO VUELO DIURNO (amanecer a atardecer) - OBLIGATORIO por legislación
- Límites de viento típicos: 15-25 kt según modelo (consultar manual específico)
- Componente cruzado típico: 10-15 kt según modelo
- NO volar con turbulencia moderada o superior
- Usa los horarios de amanecer/atardecer proporcionados

**Análisis requerido para cada día:**

**1. HOY:**
   - Condiciones actuales para ULM
   - Evaluación de viento (convierte km/h a kt antes de analizar)
   - Mejor ventana horaria (horas de luz, viento suave)
   - Veredicto: ✅ APTO ULM / ⚠️ PRECAUCIÓN / ❌ NO APTO

**2. MAÑANA:**
   - Pronóstico para ULM
   - Análisis de evolución del viento (en kt, convertido)
   - Mejores horas para volar (solo horario diurno)
   - Veredicto: ✅ APTO ULM / ⚠️ PRECAUCIÓN / ❌ NO APTO

**3. PASADO MAÑANA:**
   - Pronóstico para ULM
   - Evaluación de condiciones
   - Veredicto: ✅ APTO ULM / ⚠️ PRECAUCIÓN / ❌ NO APTO

**4. RECOMENDACIONES ULM:**
   - Mejor día de los 3 para volar (menor viento)
   - Precauciones para ULM (bajo peso, sensible a ráfagas)
   - Qué vigilar (evolución viento, térmicas, rachas)
   - Nota: Consultar siempre manual específico del modelo

**Criterios GENERALES ULM:**
- Evitar térmicas fuertes (mediodía en verano)
- Mejores haras: mañana temprano (2h post-amanecer) o tarde (2h pre-atardecer)
- Rachas con diferencia > 10 kt: Alto riesgo"""

        response = _create_chat_completion_with_fallback(
            client=client,
            provider=provider,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1000,
            model=config.AI_MODEL,
        )
        
        interpretation = response.choices[0].message.content
        
        return interpretation
        
    except Exception as e:
        print(f"Error interpretando datos meteorológicos con {provider}: {e}")
        return f"⚠️ Error al interpretar datos meteorológicos: {str(e)}"


def interpret_aemet_map_with_ai(
    map_url: str,
    weather_data: Dict,
    metar_leas: str = "",
    target_location: str = "La Morgal (LEMR)"
) -> Optional[str]:
    """
    Interpreta un mapa meteorológico (AEMET) para pilotos novatos ULM en La Morgal.

    Args:
        map_url: URL de la imagen del mapa
        weather_data: Datos meteorológicos de Open-Meteo para contexto local
        metar_leas: METAR de LEAS para usar como referencia cercana
        target_location: Ubicación objetivo del análisis

    Returns:
        Interpretación en texto claro o None si hay error
    """
    client_info = get_ai_client()

    if not client_info:
        return "⚠️ No se ha configurado ningún proveedor de IA. Configura GITHUB_TOKEN u OPENAI_API_KEY en .env"

    provider, client = client_info

    try:
        current = weather_data.get('current', {}) if weather_data else {}
        daily = weather_data.get('daily_forecast', []) if weather_data else []

        daily_lines = []
        for index, day in enumerate(daily[:3]):
            label = ["HOY", "MAÑANA", "PASADO MAÑANA"][index]
            daily_lines.append(
                f"- {label}: temp {day.get('temp_min')}°C/{day.get('temp_max')}°C, "
                f"viento max {day.get('wind_max')} km/h, rachas {day.get('wind_gusts_max')} km/h"
            )

        context_text = "\n".join(daily_lines) if daily_lines else "Sin datos diarios disponibles"
        metar_context = metar_leas if metar_leas else "METAR LEAS no disponible"

        user_text = f"""Analiza este mapa meteorológico para pilotos NOVATOS de ULM en {target_location}.

Contexto local actual:
- Temperatura: {current.get('temperature')}°C
- Viento: {current.get('wind_speed')} km/h desde {current.get('wind_direction')}°
- Rachas: {current.get('wind_gusts')} km/h
- Presión: {current.get('pressure')} hPa

Tendencia 3 días:
{context_text}

Referencia cercana (LEAS):
{metar_context}

Requisitos de respuesta:
1) Explica de forma sencilla qué se ve en el mapa (frentes, isobaras, etc.)
2) Interpreta impacto para Asturias y específicamente La Morgal (LEMR)
3) Incluye predicción operativa para HOY, MAÑANA y PASADO MAÑANA
4) Da veredicto ULM por día: ✅ APTO / ⚠️ PRECAUCIÓN / ❌ NO APTO
5) Propón mejor franja horaria de vuelo SOLO dentro del horario operativo de La Morgal
   (Invierno 09:00-20:00, Verano 09:00-21:45) y en horario diurno
6) Si hay incertidumbre por no tener METAR en LEMR, explícalo claramente"""

        response = _create_chat_completion_with_fallback(
            client=client,
            provider=provider,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": map_url}}
                    ]
                }
            ],
            temperature=0.5,
            max_tokens=1200,
            model=config.AI_MODEL,
        )

        interpretation = response.choices[0].message.content
        return interpretation

    except Exception as e:
        print(f"Error interpretando mapa AEMET con {provider}: {e}")
        return (
            "⚠️ No se pudo analizar automáticamente el mapa AEMET con IA. "
            "Puedes revisar el mapa visualmente y usar el análisis meteorológico textual como respaldo."
        )


def interpret_windy_forecast_with_ai(
    windy_data: Dict,
    location: str = "La Morgal (LEMR)"
) -> Optional[str]:
    """
    Interpreta la predicción de Windy Point Forecast para operación ULM.
    """
    client_info = get_ai_client()

    if not client_info:
        return "⚠️ No se ha configurado ningún proveedor de IA. Por favor, configura GITHUB_TOKEN o OPENAI_API_KEY en el archivo .env"

    provider, client = client_info

    try:
        model_name = windy_data.get("model", "N/A") if windy_data else "N/A"
        daily_summary = windy_data.get("daily_summary", []) if windy_data else []
        hourly = windy_data.get("hourly", []) if windy_data else []

        summary_lines = []
        for row in daily_summary[:3]:
            summary_lines.append(
                f"- {row.get('date')}: viento máx {row.get('max_wind_kmh')} km/h, "
                f"rachas máx {row.get('max_gust_kmh')} km/h, temp media {row.get('avg_temp_c')}°C, "
                f"precipitación total {row.get('precip_total_mm')} mm"
            )

        hourly_lines = []
        for h in hourly[:12]:
            t = h.get("time_local", "")
            hh = t.split("T")[1][:5] if "T" in t else t
            hourly_lines.append(
                f"- {hh}: {h.get('wind_kmh')} km/h ({h.get('wind_dir_deg')}°), "
                f"rachas {h.get('gust_kmh')} km/h, temp {h.get('temp_c')}°C, "
                f"nubes {h.get('cloud_cover_pct')}%"
            )

        user_message = f"""Analiza esta predicción de Windy Point Forecast para operación ULM en {location}.

Modelo Windy: {model_name}

Resumen 3 días:
{chr(10).join(summary_lines) if summary_lines else 'Sin resumen disponible'}

Próximas horas:
{chr(10).join(hourly_lines) if hourly_lines else 'Sin datos horarios disponibles'}

Requisitos de respuesta:
1) Evalúa condiciones HOY, MAÑANA y PASADO MAÑANA para ULM
2) Convierte km/h a kt cuando compares con límites ULM
3) Veredicto por día: ✅ APTO / ⚠️ PRECAUCIÓN / ❌ NO APTO
4) Propón franjas horarias recomendadas SOLO diurnas y dentro del horario de La Morgal
5) Señala riesgos principales (viento cruzado probable, rachas, precipitación, nubosidad baja)
"""

        response = _create_chat_completion_with_fallback(
            client=client,
            provider=provider,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.5,
            max_tokens=1000,
            model=config.AI_MODEL,
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"Error interpretando Windy con {provider}: {e}")
        return "⚠️ No se pudo generar el análisis IA de la predicción Windy en este ciclo."


def interpret_fused_forecast_with_ai(
    metar_leas: str,
    weather_data: Dict,
    windy_data: Dict,
    aemet_prediccion: Dict,
    map_analysis_text: str,
    significant_map_urls: Optional[list[str]] = None,
    location: str = "La Morgal (LEMR)",
) -> Optional[str]:
    """
    Genera un veredicto experto fusionando Windy + AEMET + METAR + Open-Meteo.
    """
    client_info = get_ai_client()
    if not client_info:
        return "⚠️ No se ha configurado ningún proveedor de IA. Por favor, configura GITHUB_TOKEN o OPENAI_API_KEY en el archivo .env"

    provider, client = client_info

    try:
        current = weather_data.get("current", {}) if weather_data else {}
        daily = weather_data.get("daily_forecast", []) if weather_data else []
        windy_daily = windy_data.get("daily_summary", []) if windy_data else []
        windy_hourly = windy_data.get("hourly", []) if windy_data else []

        om_lines = []
        for idx, row in enumerate(daily[:3]):
            label = ["HOY", "MAÑANA", "PASADO MAÑANA"][idx]
            om_lines.append(
                f"- {label}: temp {row.get('temp_min')}-{row.get('temp_max')}°C, "
                f"viento máx {row.get('wind_max')} km/h, rachas máx {row.get('wind_gusts_max')} km/h, "
                f"amanecer {row.get('sunrise')}, atardecer {row.get('sunset')}"
            )

        windy_lines = []
        for row in windy_daily[:3]:
            windy_lines.append(
                f"- {row.get('date')}: viento máx {row.get('max_wind_kmh')} km/h, "
                f"rachas máx {row.get('max_gust_kmh')} km/h, precip {row.get('precip_total_mm')} mm"
            )

        hourly_lines = []
        for row in windy_hourly[:10]:
            t = row.get("time_local", "")
            hh = t.split("T")[1][:5] if "T" in t else t
            hourly_lines.append(
                f"- {hh}: {row.get('wind_kmh')} km/h ({row.get('wind_dir_deg')}°), "
                f"rachas {row.get('gust_kmh')} km/h, nubes {row.get('cloud_cover_pct')}%, precip3h {row.get('precip_3h_mm')}"
            )

        aemet_hoy = (aemet_prediccion or {}).get("asturias_hoy", "")
        aemet_man = (aemet_prediccion or {}).get("asturias_manana", "")
        aemet_llan = (aemet_prediccion or {}).get("llanera", "")

        map_urls = [u for u in (significant_map_urls or []) if u][:4]
        
        # Obtener hora actual para contexto
        from datetime import datetime
        from zoneinfo import ZoneInfo
        now_local = datetime.now(ZoneInfo("Europe/Madrid"))
        hora_actual = now_local.strftime("%H:%M")
        fecha_actual = now_local.strftime("%Y-%m-%d")

        user_message = f"""Actúa como experto en meteorología aeronáutica ULM para {location} y crea una síntesis OPERATIVA final de alta precisión.

⏰ HORA ACTUAL: {hora_actual} (Europe/Madrid) - Fecha: {fecha_actual}

DATOS FIJOS AERÓDROMO LEMR:
    - Pista: 10/28 (rumbos 100° y 280°)
    - Horario operativo: Invierno (oct-mar) 09:00-20:00 / Verano (abr-sep) 09:00-21:45
    - Solo VFR diurno

METAR LEAS (referencia):
{metar_leas or 'No disponible'}

Open-Meteo (resumen 3 días):
{chr(10).join(om_lines) if om_lines else 'Sin datos'}

Windy Point Forecast (resumen 3 días):
{chr(10).join(windy_lines) if windy_lines else 'Sin datos'}

Windy próximas horas:
{chr(10).join(hourly_lines) if hourly_lines else 'Sin datos'}

AEMET Asturias HOY:
{aemet_hoy[:1200] if aemet_hoy else 'No disponible'}

AEMET Asturias MAÑANA:
{aemet_man[:1200] if aemet_man else 'No disponible'}

AEMET Llanera:
{aemet_llan[:1200] if aemet_llan else 'No disponible'}

Lectura sinóptica/mapa AEMET previa:
{(map_analysis_text or 'No disponible')[:1200]}

Mapas significativos AEMET (analiza visualmente estas imágenes si están disponibles):
{chr(10).join(f'- {u}' for u in map_urls) if map_urls else '- No disponibles'}

Objetivo: comparación razonada entre Windy vs AEMET (texto + mapas) vs METAR/Open-Meteo para DECISIÓN DE VUELO ULM en LEMR.

⚠️ VALIDACIÓN HORARIA PARA HOY (CRÍTICA):
- Determina si {fecha_actual} es temporada invierno (oct-mar) o verano (abr-sep)
- Si invierno: horario operativo es 09:00-20:00 | Si verano: 09:00-21:45
- Compara {hora_actual} (hora actual) contra el horario operativo
- Si {hora_actual} está DENTRO del horario operativo: HOY es viable, analiza viento para resto del día
- Si {hora_actual} está FUERA del horario operativo: marca HOY como "YA NO DISPONIBLE - fuera de horario operativo (abre a las HH:MM)"
- ⚠️ IMPORTANTE: No marques HOY como no disponible si aún hay tiempo útil de vuelo (mín 2h)

Formato obligatorio:
0) **METAR LEAS explicado** (versión corta para novatos - máximo 2 líneas, sin jerga)

1) **COINCIDENCIAS** clave entre fuentes (¿qué dicen todas las fuentes?)

2) **DISCREPANCIAS** clave y explicación meteorológica probable

3) **🎯 ANÁLISIS DE PISTA ACTIVA POR DÍA** (OBLIGATORIO para los 3 días):
   
   **HOY ({fecha_actual}):**
   - Valida si {hora_actual} está dentro del horario operativo (detecta invierno/verano automáticamente)
   - Si está FUERA: "YA NO DISPONIBLE - fuera de horario operativo"
   - Si está DENTRO: Analiza viento esperado para resto del día
   - Indica: "PISTA 10" o "PISTA 28" (basado en dirección viento actual/esperada)
   - Componentes: headwind/tailwind y crosswind para AMBAS pistas
   - Ejemplo si fuera de horario: "HOY → YA NO DISPONIBLE (son las {hora_actual}, aeródromo cierra a las 20:00)"
   - Ejemplo si viable: "HOY → PISTA 28 (headwind 15 kt, crosswind 4 kt) ✅ - viable {hora_actual}-16:00"
   
   **MAÑANA:**
   - Analyza viento previsto para todo el día de mañana
   - Indica: "PISTA 10" o "PISTA 28"
   - Componentes calculados para ambas pistas
   - Franjas horarias recomendadas (mañana y tarde, dentro de horario operativo)
   
   **PASADO MAÑANA:**
   - Analiza viento previsto para pasado mañana
   - Indica: "PISTA 10" o "PISTA 28"
   - Componentes calculados para ambas pistas
   - Franjas horarias recomendadas (mañana y tarde, dentro de horario operativo)

4) **VEREDICTO POR DÍA** (los 3 días completos):
   - **HOY**: ✅ APTO / ⚠️ PRECAUCIÓN / ❌ NO APTO / 🕐 YA NO DISPONIBLE
   - **MAÑANA**: ✅ APTO / ⚠️ PRECAUCIÓN / ❌ NO APTO
   - **PASADO MAÑANA**: ✅ APTO / ⚠️ PRECAUCIÓN / ❌ NO APTO
   - Justifica cada veredicto con datos concretos (viento, rachas, visibilidad)

5) **RIESGOS CRÍTICOS** por día (rachas, precipitación, nubosidad/visibilidad, crosswind excesivo)

6) **FRANJAS HORARIAS RECOMENDADAS** (para días viables):
   - Formato: "MAÑANA: 09:00-12:00 ✅ | TARDE: 15:00-19:00 ⚠️"
   - Si no hay ventana segura: "NO RECOMENDADA"
   - Considera amanecer, atardecer, horario operativo y condiciones meteorológicas

7) **🏆 MEJOR DÍA PARA VOLAR**:
   - Indica claramente: "MAÑANA" o "PASADO MAÑANA" (o "HOY" si aún es viable)
   - Justifica por qué es el mejor (menor viento, mejor visibilidad, menos rachas, etc.)
   - Si ningún día es bueno: "NINGUNO - condiciones adversas los 3 días"

8) **VEREDICTO FINAL GLOBAL** (una línea contundente y justificada con el mejor día destacado)

Reglas:
- **ANÁLISIS DE PISTA ES OBLIGATORIO PARA LOS 3 DÍAS**: No omitas ninguno
- **VALIDACIÓN HORARIA EN HOY ES CRÍTICA**: Detecta invierno/verano, valida {hora_actual} contra límites operativos
- Convierte km/h a kt cuando compares con límites ULM Y cuando calcules componentes de viento
- No uses afirmaciones vagas: para cada día cita al menos 2 datos concretos (viento/racha/precip/nube)
- Si usas los mapas significativos, menciona qué patrón sinóptico observas (frentes/isobaras/flujo dominante) y su impacto en LEMR
- Recuerda: PISTA 10 orientada 100° (despegue al ESTE), PISTA 28 orientada 280° (despegue al OESTE)
- Viento del OESTE (250°-310°) → usar PISTA 28 | Viento del ESTE (070°-130°) → usar PISTA 10
- No propongas vuelos fuera de horario diurno ni fuera de horario operativo
- **SIEMPRE indica cuál es el MEJOR DÍA para volar**
- Si hay incertidumbre, dilo explícitamente
"""

        user_content: list[dict] = [{"type": "text", "text": user_message}]
        
        # Detectar si vamos a usar un modelo con límites bajos (mini, small)
        # Si es mini, NO incluir imágenes para evitar exceder límite de tokens (413 error)
        primary_model = config.AI_MODEL
        fallback_model = getattr(config, "AI_FALLBACK_MODEL", "gpt-4o-mini")
        is_mini_model = "mini" in primary_model.lower() or "small" in primary_model.lower()
        
        # Si el modelo principal es mini O está bloqueado (va a usar fallback que es mini), no enviar imágenes
        if not is_mini_model and not (_is_primary_locked_for_cycle(provider, primary_model)):
            # Solo agregar imágenes si es modelo potente (gpt-4o)
            for url in map_urls:
                user_content.append({"type": "image_url", "image_url": {"url": url}})
            print(f"📸 Incluyendo {len(map_urls)} mapas AEMET (modelo {primary_model} soporta imágenes)")
        else:
            print(f"⚠️ NO incluyendo imágenes ({primary_model} {'es modelo limitado' if is_mini_model else 'está bloqueado por rate-limit'})")

        response = _create_chat_completion_with_fallback(
            client=client,
            provider=provider,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.4,
            max_tokens=1400,
            model=config.AI_MODEL,
        )

        result = response.choices[0].message.content
        print(f"✅ Síntesis experta generada exitosamente con {provider}")
        return result

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ Error generando síntesis experta con {provider}: {e}")
        print(f"Detalles: {error_detail}")
        
        # Intentar proporcionar un análisis básico sin IA como último recurso
        return f"""⚠️ No se pudo generar análisis IA completo en este ciclo (Error: {str(e)[:100]})

📊 RESUMEN BÁSICO DE DATOS DISPONIBLES:

METAR LEAS: {metar_leas or 'No disponible'}

Condiciones actuales Open-Meteo:
- Temperatura: {current.get('temperature', 'N/A')}°C
- Viento: {current.get('wind_speed', 'N/A')} km/h desde {current.get('wind_direction', 'N/A')}°
- Presión: {current.get('pressure', 'N/A')} hPa

⚠️ NOTA: Consulta briefing oficial AEMET y METAR actualizado antes de volar.
El próximo análisis IA completo estará disponible en el siguiente ciclo de actualización."""


def create_combined_report(metar: str, weather_data: Dict, metar_location: str, weather_location: str) -> str:
    """
    Crea un reporte combinado con METAR y datos meteorológicos generales
    
    Args:
        metar: String con METAR
        weather_data: Datos meteorológicos
        metar_location: Ubicación del METAR
        weather_location: Ubicación de datos generales
    
    Returns:
        Reporte combinado formateado
    """
    report = "🌤️ **REPORTE METEOROLÓGICO COMPLETO** 🌤️\n\n"
    
    # Sección METAR
    report += f"✈️ **AEROPUERTO {metar_location}** ✈️\n\n"
    report += f"```\n{metar}\n```\n\n"
    
    metar_interpretation = interpret_metar_with_ai(metar, metar_location)
    if metar_interpretation:
        report += metar_interpretation + "\n\n"
    
    report += "─" * 50 + "\n\n"
    
    # Sección meteorología general
    report += f"🏔️ **{weather_location}** 🏔️\n\n"
    
    # Importar función de formateo
    from weather_service import format_weather_report
    weather_report = format_weather_report(weather_data)
    report += weather_report + "\n"
    
    weather_interpretation = interpret_weather_with_ai(weather_data, weather_location)
    if weather_interpretation:
        report += "\n**ANÁLISIS:**\n" + weather_interpretation
    
    return report


if __name__ == '__main__':
    # Test
    print("Probando servicio de IA...")
    
    client_info = get_ai_client()
    if client_info:
        provider, _ = client_info
        print(f"✅ Cliente de IA configurado: {provider}")
        
        # Test con METAR de ejemplo
        test_metar = "LEAS 131630Z 27015KT 9999 FEW040 15/08 Q1013"
        print("\nProbando interpretación de METAR...")
        interpretation = interpret_metar_with_ai(test_metar, "LEAS")
        if interpretation:
            print(interpretation)
    else:
        print("❌ No se pudo configurar el cliente de IA")
        print("Por favor, configura GITHUB_TOKEN o OPENAI_API_KEY en el archivo .env")
