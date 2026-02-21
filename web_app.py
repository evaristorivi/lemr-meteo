"""
Aplicación web meteorológica para pilotos ULM de La Morgal (LEMR).
Interfaz web moderna con actualización automática cada hora de 06:00 a 23:00.
Integra mapas AEMET, METAR LEAS, Open-Meteo, Windy y análisis IA.
"""
from datetime import date, datetime, timedelta
from threading import Lock, Thread
import time as _time
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import config
from ai_service import (
    interpret_fused_forecast_with_ai,
)
from aemet_service import (
    get_significant_maps_for_three_days,
    get_analysis_map_url,
    get_analysis_map_b64,
    get_avisos_cap_asturias,
)
from metar_service import get_metar, classify_flight_category
from metar_generator import generate_metar_lemr, get_metar_disclaimer
from weather_service import get_weather_forecast, weather_code_to_description
from windy_service import get_windy_point_forecast
from telegram_monitor import send_alert as _tg_alert

app = Flask(__name__)

# Rate limiting: previene abuso y DoS
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per hour", "100 per minute"],
    storage_uri="memory://"
)


# ============================================================================
# FUNCIONES OGIMET (Vista Semanal Rápida)
# ============================================================================

def _build_ogimet_image_url(date_str: str, run: str, projection_hours: int) -> str:
    """Construye URL directa de imagen Ogimet."""
    proy_str = f"{projection_hours:03d}"
    return (
        f"https://www.ogimet.com/forecasts/{date_str}_{run}/SFC/"
        f"{date_str}{run}H{proy_str}_SP00_SFC.jpg"
    )


def _get_latest_ogimet_run_fast():
    """
    Calcula el run de Ogimet más reciente SIN hacer requests HTTP.
    Ogimet genera runs a las 00Z y 12Z, disponibles ~5-6 horas después.
    """
    utc_now = datetime.now(ZoneInfo("UTC"))
    
    if utc_now.hour >= 18:  # Después de las 18:00 UTC, usar run 12Z de hoy
        run = "12"
        run_date = utc_now
    elif utc_now.hour >= 6:  # Entre 06:00 y 18:00 UTC, usar run 00Z de hoy
        run = "00"
        run_date = utc_now
    else:  # Antes de las 06:00 UTC, usar run 12Z de ayer
        run = "12"
        run_date = utc_now - timedelta(days=1)
    
    return {
        'date_str': run_date.strftime("%Y%m%d"),
        'run': run,
        'run_date': run_date
    }


def get_ogimet_week_forecast():
    """
    Genera previsión semanal de Ogimet (7 días, 1 mapa por día).
    Versión rápida: no verifica existencia de imágenes.
    Prefiere proyecciones cercanas a las 12:00 UTC (mediodía).
    """
    latest_run = _get_latest_ogimet_run_fast()
    run_time = datetime.strptime(f"{latest_run['date_str']} {latest_run['run']}", "%Y%m%d %H")
    
    today = datetime.now(MADRID_TZ).date()
    weekday_short = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    
    # Recopilar todas las proyecciones y agruparlas por día
    daily_projections = {}
    
    for hours in range(12, 193, 6):
        valid_time = run_time + timedelta(hours=hours)
        day_key = valid_time.date()
        
        # Calcular distancia al mediodía (12:00 UTC)
        distance_to_noon = abs(valid_time.hour - 12)
        
        # Si no tenemos este día, o si esta proyección está más cerca del mediodía
        if day_key not in daily_projections or distance_to_noon < daily_projections[day_key]['distance']:
            daily_projections[day_key] = {
                'hours': hours,
                'valid_time': valid_time,
                'distance': distance_to_noon
            }
    
    # Ordenar por fecha y tomar los primeros 7 días
    sorted_days = sorted(daily_projections.keys())[:7]
    
    week_forecast = []
    for day_key in sorted_days:
        proj = daily_projections[day_key]
        valid_time = proj['valid_time']
        hours = proj['hours']
        
        # Etiqueta del día
        if day_key == today:
            day_label = "HOY"
        elif day_key == today + timedelta(days=1):
            day_label = "MAÑANA"
        elif day_key == today + timedelta(days=2):
            day_label = "PASADO"
        else:
            day_label = weekday_short[day_key.weekday()]
        
        image_url = _build_ogimet_image_url(latest_run['date_str'], latest_run['run'], hours)
        
        week_forecast.append({
            'date': day_key.strftime("%Y-%m-%d"),
            'day_label': day_label,
            'weekday': weekday_short[day_key.weekday()],
            'date_formatted': day_key.strftime("%d/%m"),
            'image_url': image_url,
            'valid_time': f"{weekday_short[valid_time.weekday()]} {valid_time.strftime('%d/%m %H:00')}",
            'description': f"Válido para {weekday_short[valid_time.weekday()]} {valid_time.strftime('%d/%m/%Y %H:00 UTC')}",
            'projection_hours': hours
        })
    
    return {
        'success': True,
        'run_info': {
            'date': latest_run['date_str'],
            'run': latest_run['run'],
            'label': f"Run {latest_run['run']}:00 UTC del {run_time.strftime('%d/%m/%Y')}",
            'full_label': f"Run {latest_run['run']}:00 UTC del {run_time.strftime('%d/%m/%Y')}"
        },
        'week': week_forecast,
        'total_days': len(week_forecast)
    }

# ============================================================================


def get_weather_icon_from_text(prediction_text: str) -> str:
    """
    Determina el icono meteorológico más apropiado basándose en el texto de predicción.
    Analiza palabras clave para elegir el emoji más representativo.
    Prioriza condiciones más severas (tormentas > lluvia > nubes).
    """
    if not prediction_text:
        return "🌦️"  # Por defecto
    
    text_lower = prediction_text.lower()
    
    # Prioridad de detección: condiciones más específicas/severas primero
    
    # Tormentas (máxima prioridad en precipitación)
    if any(word in text_lower for word in ["tormenta", "tormentoso", "eléctrica", "aparato eléctrico"]):
        return "⛈️"
    
    # Nieve
    if any(word in text_lower for word in ["nieve", "nevadas", "nevada", "copos"]):
        return "🌨️"
    
    # Niebla
    if any(word in text_lower for word in ["niebla", "neblina", "bruma", "banco de niebla"]):
        return "🌫️"
    
    # Lluvia fuerte / Chubascos (antes de verificar lluvia general)
    if any(word in text_lower for word in ["chubasco", "chubascos", "lluvia fuerte", "precipitaciones intensas", 
                                             "aguacero", "precipitaciones abundantes"]):
        return "🌧️"
    
    # Lluvia / Precipitación general (pero NO si dice "sin precipitación")
    if not any(phrase in text_lower for phrase in ["sin precipitacion", "sin lluvia", "no precipita"]):
        if any(word in text_lower for word in ["lluvia", "lluvias", "precipitación", "precipitaciones", 
                                                 "llovizna", "mojado"]):
            return "🌦️"
    
    # Viento fuerte
    if any(word in text_lower for word in ["viento fuerte", "vientos fuertes", "vendaval", "temporal", 
                                             "rachas muy fuertes", "rachas fuertes"]):
        return "💨"
    
    # Muy nuboso / Cubierto (antes de nuboso general)
    if any(word in text_lower for word in ["muy nuboso", "cubierto", "cielos cubiertos", "nubosidad abundante",
                                             "bastante nuboso", "cielo muy nuboso"]):
        return "☁️"
    
    # Poco nuboso (debe ir antes de "nuboso" general)
    if any(word in text_lower for word in ["poco nuboso", "algunas nubes", "escasa nubosidad", 
                                             "cielo poco nuboso", "cielo: poco nuboso"]):
        return "🌤️"
    
    # Intervalos nubosos / Parcialmente nuboso
    if any(word in text_lower for word in ["intervalos nubosos", "nubosidad variable", "parcialmente nuboso",
                                             "cielo con intervalos", "cielo: intervalos"]):
        return "⛅"
    
    # Nuboso general (después de las variantes específicas)
    if any(word in text_lower for word in ["nuboso", "nubosidad", "nubes", "cielos nubosos", 
                                             "cielo nuboso", "cielo: nuboso"]):
        return "⛅"
    
    # Despejado / Soleado
    if any(word in text_lower for word in ["despejado", "despejados", "cielos despejados", "soleado", 
                                             "buen tiempo", "sin nubes", "cielo despejado", "cielo: despejado",
                                             "cielo limpio", "poco o ningún"]):
        return "☀️"
    
    # Default: si no detectamos nada específico, usar símbolo genérico
    return "🌦️"


def format_date_spanish(date_obj: date) -> str:
    """
    Formatea una fecha en español sin depender del locale del sistema.
    Formato: "Domingo, 15 de febrero de 2026"
    """
    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    
    # weekday() devuelve 0=lunes, 6=domingo
    dia_nombre = dias[date_obj.weekday()].capitalize()
    mes_nombre = meses[date_obj.month - 1]
    
    return f"{dia_nombre}, {date_obj.day} de {mes_nombre} de {date_obj.year}"


MADRID_TZ = ZoneInfo("Europe/Madrid")
UPDATE_SLOTS = list(range(6, 24))  # Cada hora de 06:00 a 23:00
_CACHE_LOCK = Lock()
_CACHE = {
    "cache_key": None,
    "generated_at": None,
    "payload": None,
}
_WARMER_STARTED = False

SUPPORTED_WINDY_MODELS = ["gfs", "iconEu", "arome"]


def _build_cycle_id(now_local: datetime) -> str:
    current_hour = now_local.hour

    slot = None
    for candidate in UPDATE_SLOTS:
        if current_hour >= candidate:
            slot = candidate

    cycle_date = now_local.date()
    if slot is None:
        slot = UPDATE_SLOTS[-1]
        cycle_date = cycle_date - timedelta(days=1)

    return f"{cycle_date.isoformat()}-{slot:02d}"


def _sanitize_windy_model(value: str | None) -> str:
    if not value:
        return config.WINDY_MODEL
    for model in SUPPORTED_WINDY_MODELS:
        if value.lower() == model.lower():
            return model
    return config.WINDY_MODEL


def _build_windy_section(selected_windy_model: str) -> dict:
    windy_data = get_windy_point_forecast(
        config.LA_MORGAL_COORDS["lat"],
        config.LA_MORGAL_COORDS["lon"],
        selected_windy_model,
    )

    return {
        "provider": windy_data.get("provider") if windy_data else "Windy Point Forecast",
        "model": windy_data.get("model") if windy_data else selected_windy_model,
        "lat": windy_data.get("lat") if windy_data else config.LA_MORGAL_COORDS["lat"],
        "lon": windy_data.get("lon") if windy_data else config.LA_MORGAL_COORDS["lon"],
        "available_models": SUPPORTED_WINDY_MODELS,
        "hourly": windy_data.get("hourly", [])[:24] if windy_data else [],
        "daily_summary": windy_data.get("daily_summary", []) if windy_data else [],
        "error": windy_data.get("error") if windy_data else None,
        "map_embed_url": windy_data.get("map_embed_url") if windy_data else (
            f"https://embed.windy.com/embed2.html?lat={config.LA_MORGAL_COORDS['lat']}&lon={config.LA_MORGAL_COORDS['lon']}"
            "&zoom=9&level=surface&overlay=wind&menu=&message=true&marker=true&calendar=24"
            "&pressure=true&type=map&location=coordinates"
            f"&detail=true&detailLat={config.LA_MORGAL_COORDS['lat']}&detailLon={config.LA_MORGAL_COORDS['lon']}"
            f"&metricWind=km%2Fh&metricTemp=%C2%B0C&model={selected_windy_model}"
        ),
        "map_link": windy_data.get("map_link") if windy_data else (
            f"https://www.windy.com/?{config.LA_MORGAL_COORDS['lat']},{config.LA_MORGAL_COORDS['lon']},10"
        ),
    }


def _generate_report_payload(windy_model: str | None = None, include_ai: bool = True) -> dict:
    from aemet_service import get_aemet_request_count
    
    now_local = datetime.now(MADRID_TZ)
    aemet_count_start = get_aemet_request_count()
    
    metar_leas = get_metar(config.LEAS_ICAO)
    if not metar_leas:
        print("⚠️ METAR LEAS no disponible — sin observación en tiempo real del aeropuerto")
        _tg_alert(
            "METAR LEAS (Asturias) no disponible. Sin observacion en tiempo real del aeropuerto cercano.",
            source="metar",
            level="WARNING",
        )
    selected_windy_model = _sanitize_windy_model(windy_model)

    weather_data = get_weather_forecast(
        config.LA_MORGAL_COORDS["lat"],
        config.LA_MORGAL_COORDS["lon"],
        config.LA_MORGAL_COORDS["name"],
    )

    if not weather_data:
        print("⚠️ Open-Meteo no disponible — continuando con datos parciales (sin condiciones actuales ni pronóstico)")
        _tg_alert(
            "Open-Meteo no devolvio datos. El pronostico LEMR se generara sin condiciones actuales ni datos horarios.",
            source="openmeteo",
            level="ERROR",
        )
        weather_data = {"current": {}, "daily_forecast": [], "hourly_forecast": []}

    # Generar METAR sintético para LEMR desde datos Open-Meteo
    current = weather_data.get("current", {})
    hourly_om = weather_data.get("hourly_forecast", [])
    # Pasar visibilidad y punto de rocío de la primera hora hourly (más preciso que inferir del código)
    _h0 = hourly_om[0] if hourly_om else {}
    _visibility_km = _h0.get('visibility')  # ya en km (convertido en weather_service)
    _dewpoint_c = _h0.get('dewpoint')  # dewpoint directo del modelo (más preciso que Magnus)
    metar_lemr = generate_metar_lemr(
        current,
        icao="LEMR",
        elevation_m=config.LA_MORGAL_AERODROME["elevation_m"],
        visibility_km=_visibility_km,
        dewpoint_c=_dewpoint_c,
    )
    if metar_lemr:
        print(f"✅ METAR sintético LEMR generado: {metar_lemr}")
    else:
        print("⚠️ No se pudo generar METAR sintético para LEMR")
        metar_lemr = "LEMR METAR NOT AVAILABLE"

    daily = weather_data.get("daily_forecast", [])[:4]

    # ── Predicción Windy Point Forecast ──
    windy_section = _build_windy_section(selected_windy_model)
    if not windy_section.get("hourly"):
        _tg_alert(
            f"Windy Point Forecast sin datos horarios (modelo: {selected_windy_model}). El analisis IA carecera de pronostico Windy.",
            source="windy",
            level="WARNING",
        )

    # ── Mapas significativos AEMET (hoy/mañana/pasado, AM y PM) ──
    sig_maps = get_significant_maps_for_three_days(ambito="esp")

    # ── Mapa de análisis en superficie (isobaras, frentes) ──
    # URL temporal: para pasar a la IA (ligera, ~100 tokens)
    analysis_map_url = get_analysis_map_url()
    # Base64: para mostrar en navegador (evita CORS, pesada ~400KB)
    analysis_map_b64 = get_analysis_map_b64() if analysis_map_url else None
    
    if analysis_map_b64:
        print(f"✅ Mapa análisis obtenido (URL para IA + base64 para navegador)")
    else:
        print("⚠️ No se pudo obtener mapa de análisis de AEMET")
        _tg_alert(
            "Mapa de analisis en superficie AEMET no disponible (posible caida del servicio AEMET).",
            source="aemet_maps",
            level="WARNING",
        )

    # ── Avisos CAP (para la IA) ──
    avisos_cap = get_avisos_cap_asturias()
    if avisos_cap:
        print(f"⚠️ AEMET AVISOS CAP activos: {avisos_cap[:80]}")
    # ── Construir días con mapas AEMET integrados (slots UTC reales disponibles) ──
    sig_index = {}
    for m in sig_maps:
        sig_index.setdefault(m["date"], []).append(m)

    days = []
    labels = ["Hoy", "Mañana", "Pasado mañana", "Dentro de 3 días"]
    for index, day in enumerate(daily):
        target_date = datetime.fromisoformat(day["date"]).date()
        day_iso = target_date.isoformat()
        show_aemet_maps = index < 2

        map_slots = sorted(sig_index.get(day_iso, []), key=lambda item: item.get("utc_hour", "99")) if show_aemet_maps else []
        available_hours = [f"{slot.get('utc_hour')}" for slot in map_slots if slot.get("utc_hour")]

        days.append(
            {
                "label": labels[index] if index < len(labels) else day["date"],
                "date": day["date"],
                "show_aemet_maps": show_aemet_maps,
                "available_utc_hours": available_hours,
                "map_slots": map_slots,
            }
        )

    current = weather_data.get("current", {})

    metar_ai = "Análisis integrado en el veredicto final IA."
    weather_ai = "Análisis integrado en el veredicto final IA."
    windy_ai = "Análisis integrado en el veredicto final IA."
    map_ai = "Análisis integrado en el veredicto final IA."

    fused_ai = "⏳ Análisis IA en curso..."
    if include_ai:
        # Determinar si se va a usar gpt-4o o mini, y qué proveedor
        model_cascade = getattr(config, "AI_MODEL_CASCADE", [])
        primary_model = model_cascade[0] if model_cascade else "gpt-4o"
        ai_provider = getattr(config, "AI_PROVIDER", "github").lower()
        is_mini = "mini" in primary_model.lower()
        is_github = ai_provider == "github"
        
        # Excluir mapas para: mini models O GitHub (60k tokens/min - muy restrictivo)
        # Solo incluir mapas para OpenAI (límite de tokens más alto)
        map_urls_for_ai = []
        if not is_mini and not is_github:
            # Solo para OpenAI con gpt-4o: incluir URL del mapa análisis + mapas significativos
            if analysis_map_url:
                map_urls_for_ai.append(analysis_map_url)
            for m in sig_maps[:1]:  # Solo 1 mapa significativo
                u = m.get("map_url")
                if u and u not in map_urls_for_ai:
                    map_urls_for_ai.append(u)

        # Calcular clasificaciones de condiciones de vuelo antes de pasarlas a la IA
        flight_cat_leas = classify_flight_category(metar_leas) if metar_leas else None
        flight_cat_lemr = classify_flight_category(metar_lemr) if metar_lemr else None

        try:
            fused_ai = interpret_fused_forecast_with_ai(
                metar_leas=metar_leas or "",
                metar_lemr=metar_lemr or "",
                weather_data=weather_data,
                windy_data=windy_section or {},
                map_analysis_text="" if (is_mini or is_github) else (analysis_map_url or ""),
                significant_map_urls=map_urls_for_ai,
                location=config.LA_MORGAL_COORDS["name"],
                flight_category_leas=flight_cat_leas,
                flight_category_lemr=flight_cat_lemr,
                avisos_cap=avisos_cap,
            )
        except Exception as _ai_exc:
            print(f"\u274c Error en an\u00e1lisis IA: {_ai_exc}")
            _tg_alert(
                f"Analisis IA fallo (todos los modelos agotados). Error: {str(_ai_exc)[:300]}",
                source="ia",
                level="ERROR",
                exc=_ai_exc,
            )
            fused_ai = "\u26a0\ufe0f An\u00e1lisis IA no disponible temporalmente (error en todos los modelos)."
    else:
        # Si no se incluye IA, igualmente calcular las clasificaciones
        flight_cat_leas = classify_flight_category(metar_leas) if metar_leas else None
        flight_cat_lemr = classify_flight_category(metar_lemr) if metar_lemr else None

    # Log de peticiones AEMET realizadas en este ciclo
    aemet_count_end = get_aemet_request_count()
    aemet_requests_this_cycle = aemet_count_end - aemet_count_start
    print(f"📊 Ciclo completado: {aemet_requests_this_cycle} peticiones AEMET (total: {aemet_count_end})")

    return {
        "generated_at": now_local.isoformat(),
        "cycle_id": _build_cycle_id(now_local),
        "location": {
            "name": config.LA_MORGAL_AERODROME["name"],
            "icao": config.LA_MORGAL_AERODROME["icao"],
            "municipality": config.LA_MORGAL_AERODROME["municipality"],
            "coordinates": "43 25.833 N 05 49.617 O",
            "radio": config.LA_MORGAL_AERODROME["radio_frequency"],
            "elevation": f"{config.LA_MORGAL_AERODROME['elevation_ft']} ft / {config.LA_MORGAL_AERODROME['elevation_m']} m",
            "runway": "10/28 - 890m asfalto",
            "hours_invierno": config.LA_MORGAL_AERODROME["opening_hours"]["invierno"],
            "hours_verano": config.LA_MORGAL_AERODROME["opening_hours"]["verano"],
        },
        "current": {
            "time": current.get("time"),
            "temperature": current.get("temperature"),
            "feels_like": current.get("feels_like"),
            "humidity": current.get("humidity"),
            "wind_speed_kmh": current.get("wind_speed"),
            "wind_direction": current.get("wind_direction"),
            "wind_gusts_kmh": current.get("wind_gusts"),
            "pressure": current.get("pressure"),
            "cloud_cover": current.get("cloud_cover"),
            "precipitation": current.get("precipitation"),
            "cape": current.get("cape"),
            "condition": weather_code_to_description(current.get("weather_code")),
        },
        "metar": {
            "leas": {
                "station": config.LEAS_ICAO,
                "raw": metar_leas,
                "analysis": metar_ai,
                "flight_category": flight_cat_leas,
            },
            "lemr": {
                "station": "LEMR",
                "raw": metar_lemr,
                "disclaimer": get_metar_disclaimer(),
                "flight_category": flight_cat_lemr,
            },
        },
        "forecast_days": days,
        "analysis_map_url": analysis_map_b64,  # Base64 para navegador (evita CORS)

        "windy": windy_section,
        "ai": {
            "weather_analysis": weather_ai,
            "map_analysis": map_ai,
            "windy_analysis": windy_ai,
            "expert_final_verdict": fused_ai or "No disponible",
            "model_used": primary_model,
            "provider": ai_provider,
            "pending": not include_ai,
        },
        "refresh_policy": {
            "description": "Actualización automática cada hora de 06:00 a 23:00",
            "slots_local_time": [f"{h:02d}:00" for h in UPDATE_SLOTS],
            "timezone": "Europe/Madrid",
        },
    }


def _background_regenerate_cache(cache_key: str, windy_model: str, include_ai: bool):
    """Regenera el reporte en background y actualiza la caché."""
    try:
        now_local = datetime.now(MADRID_TZ)
        payload = _generate_report_payload(windy_model=windy_model, include_ai=include_ai)
        with _CACHE_LOCK:
            _CACHE["cache_key"] = cache_key
            _CACHE["generated_at"] = now_local.isoformat()
            _CACHE["payload"] = payload
        print(f"✅ Caché regenerada en background para ciclo {cache_key}")
    except Exception as exc:
        print(f"❌ Error regenerando caché en background: {exc}")
        _tg_alert(
            f"Error critico en ciclo de actualizacion automatica (background). Error: {str(exc)[:300]}",
            source="general",
            level="ERROR",
            exc=exc,
        )


def get_report_payload(force: bool = False, windy_model: str | None = None, include_ai: bool = True) -> dict:
    now_local = datetime.now(MADRID_TZ)
    cycle_id = _build_cycle_id(now_local)
    selected_model = _sanitize_windy_model(windy_model)
    cache_key = f"{cycle_id}|{selected_model}"

    with _CACHE_LOCK:
        # Caché válida: mismo ciclo
        if not force and _CACHE["payload"] and _CACHE["cache_key"] == cache_key:
            return _CACHE["payload"]
        
        # Caché desactualizada: nuevo ciclo pero tenemos datos viejos
        if not force and _CACHE["payload"] and _CACHE["cache_key"] != cache_key:
            print(f"🔄 Nuevo ciclo detectado ({cache_key}), mostrando datos previos mientras se actualiza...")
            old_payload = _CACHE["payload"]
            # Lanzar regeneración en background
            Thread(target=_background_regenerate_cache, args=(cache_key, selected_model, include_ai), daemon=True).start()
            return old_payload
        
        # Sin caché o forzado: generación síncrona
        payload = _generate_report_payload(windy_model=selected_model, include_ai=include_ai)
        _CACHE["cache_key"] = cache_key
        _CACHE["generated_at"] = now_local.isoformat()
        _CACHE["payload"] = payload
        return payload


def _cycle_warmer_loop():
    while True:
        try:
            get_report_payload(force=False, windy_model=config.WINDY_MODEL, include_ai=True)
        except Exception as exc:
            print(f"Cycle warmer error: {exc}")
        _time.sleep(60)


def _start_cycle_warmer_once():
    global _WARMER_STARTED
    if _WARMER_STARTED:
        return
    with _CACHE_LOCK:
        if _WARMER_STARTED:
            return
        Thread(target=_cycle_warmer_loop, daemon=True).start()
        _WARMER_STARTED = True


@app.get("/")
@limiter.limit("100 per minute")
def index():
    _start_cycle_warmer_once()
    with _CACHE_LOCK:
        payload = _CACHE.get("payload")
    if not payload:
        payload = get_report_payload(force=False, windy_model=config.WINDY_MODEL, include_ai=True)
    return render_template(
        "index.html",
        data=payload,
    )


@app.get("/api/report")
def api_report():
    _start_cycle_warmer_once()
    # Parámetro force eliminado: la caché se actualiza automáticamente cada ciclo horario
    windy_model = request.args.get("windy_model", config.WINDY_MODEL)
    payload = get_report_payload(force=False, windy_model=windy_model, include_ai=True)
    return jsonify(payload)


@app.get("/api/windy")
@limiter.limit("10 per minute")
def api_windy():
    windy_model = request.args.get("windy_model", config.WINDY_MODEL)
    selected_model = _sanitize_windy_model(windy_model)
    windy_section = _build_windy_section(selected_model)
    return jsonify({"windy": windy_section})


@app.get("/api/ogimet/week")
@limiter.limit("15 per minute")
def api_ogimet_week():
    """API endpoint para la vista semanal de Ogimet (7 días, 1 mapa/día)"""
    try:
        forecast_data = get_ogimet_week_forecast()
        return jsonify(forecast_data)
    except Exception as e:
        _tg_alert(
            f"Ogimet /api/ogimet/week lanzo excepcion: {str(e)[:300]}",
            source="general",
            level="ERROR",
            exc=e,
        )
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.get("/api/ogimet/debug")
def api_ogimet_debug():
    """Endpoint de debug para verificar URLs de Ogimet"""
    import requests
    try:
        forecast_data = get_ogimet_week_forecast()
        
        # Verificar disponibilidad de cada imagen
        results = []
        for day in forecast_data['week']:
            url = day['image_url']
            try:
                response = requests.head(url, timeout=5, allow_redirects=True)
                status = response.status_code
                available = status == 200
            except Exception as e:
                status = 'ERROR'
                available = False
            
            results.append({
                'day': day['day_label'],
                'date': day['date'],
                'projection_hours': day['projection_hours'],
                'url': url,
                'status': status,
                'available': available
            })
        
        return jsonify({
            'success': True,
            'run_info': forecast_data['run_info'],
            'images': results,
            'current_time_utc': datetime.now(ZoneInfo("UTC")).isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.get("/robots.txt")
def robots_txt():
    """Sirve el archivo robots.txt para SEO."""
    from flask import send_from_directory
    return send_from_directory('static', 'robots.txt', mimetype='text/plain')


@app.get("/sitemap.xml")
def sitemap_xml():
    """Sirve el archivo sitemap.xml para SEO."""
    from flask import send_from_directory
    return send_from_directory('static', 'sitemap.xml', mimetype='application/xml')


@app.get("/opensearch.xml")
def opensearch_xml():
    """Sirve el archivo opensearch.xml para búsqueda personalizada en navegadores."""
    from flask import send_from_directory
    return send_from_directory('static', 'opensearch.xml', mimetype='application/opensearchdescription+xml')


@app.get("/humans.txt")
def humans_txt():
    """Sirve el archivo humans.txt con créditos y información del sitio."""
    from flask import send_from_directory
    return send_from_directory('static', 'humans.txt', mimetype='text/plain')


@app.get("/manifest.json")
def manifest_json():
    """Sirve el archivo manifest.json para PWA."""
    from flask import send_from_directory
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')


@app.after_request
def set_security_headers(response):
    """Añade cabeceras de seguridad y SEO a todas las respuestas."""
    # Seguridad
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # SEO & Performance
    response.headers['Cache-Control'] = 'public, max-age=3600'
    response.headers['Pragma'] = 'cache'
    
    # HSTS solo en producción (cuando uses HTTPS)
    # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


if __name__ == "__main__":
    import sys
    # Forzar UTF-8 en stdout/stderr para evitar errores con emojis
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    print("Iniciando LEMR Meteo Web para La Morgal...")
    print(f"URL: http://{config.WEB_HOST}:{config.WEB_PORT}")
    print("Actualizacion automatica: cada hora de 06:00 a 23:00 (Europe/Madrid)")
    app.run(host=config.WEB_HOST, port=config.WEB_PORT, debug=False)
