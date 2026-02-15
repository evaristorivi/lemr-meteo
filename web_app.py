"""
Aplicación web meteorológica para pilotos ULM de La Morgal (LEMR).
Reemplaza el flujo de Telegram por una web moderna con actualización automática 5 veces al día.
Integra mapas AEMET, METAR LEAS, Open-Meteo y análisis IA.
"""
from datetime import date, datetime, time, timedelta
from threading import Lock, Thread
import time as _time
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, render_template, request

import config
from ai_service import (
    interpret_fused_forecast_with_ai,
)
from aemet_service import (
    get_significant_maps_for_three_days,
    get_analysis_map_url,
    get_prediccion_asturias_hoy,
    get_prediccion_asturias_manana,
    get_prediccion_asturias_pasado_manana,
    get_prediccion_llanera,
)
from metar_service import get_metar
from weather_service import get_weather_forecast, weather_code_to_description
from windy_service import get_windy_point_forecast, get_windy_map_forecast

app = Flask(__name__)

MADRID_TZ = ZoneInfo("Europe/Madrid")
UPDATE_SLOTS = [6, 10, 14, 18, 22]
_CACHE_LOCK = Lock()
_CACHE = {
    "cache_key": None,
    "generated_at": None,
    "payload": None,
}
_WARMER_STARTED = False

SUPPORTED_WINDY_MODELS = ["gfs", "iconEu", "arome"]


def _parse_iso_time(value: str) -> time | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).time()
    except ValueError:
        return None


def _is_summer_schedule(target_date: date) -> bool:
    return 4 <= target_date.month <= 9


def _operating_hours(target_date: date) -> dict:
    if _is_summer_schedule(target_date):
        return {
            "season": "verano",
            "open": "09:00",
            "close": "21:45",
        }

    return {
        "season": "invierno",
        "open": "09:00",
        "close": "20:00",
    }


def _best_operational_window_for_day(day_data: dict) -> str:
    target_date = datetime.fromisoformat(day_data["date"]).date()
    operating = _operating_hours(target_date)

    sunrise_t = _parse_iso_time(day_data.get("sunrise"))
    sunset_t = _parse_iso_time(day_data.get("sunset"))

    open_h = datetime.strptime(operating["open"], "%H:%M").time()
    close_h = datetime.strptime(operating["close"], "%H:%M").time()

    start = open_h
    end = close_h

    if sunrise_t:
        sunrise_plus = (datetime.combine(target_date, sunrise_t) + timedelta(hours=2)).time()
        start = max(start, sunrise_plus)

    if sunset_t:
        sunset_minus = (datetime.combine(target_date, sunset_t) - timedelta(hours=2)).time()
        end = min(end, sunset_minus)

    if end <= start:
        if sunrise_t:
            start = max(open_h, sunrise_t)
        if sunset_t:
            end = min(close_h, sunset_t)

    if end <= start:
        return f"Sin ventana clara (revisar condiciones y horario {operating['open']}-{operating['close']})"

    return f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')} ({operating['season']})"


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


def _build_map_url(target_date: date) -> str:
    return config.AEMET_MAP_TEMPLATE_URL.format(date=target_date.strftime("%Y%m%d"))


def _build_windy_section(selected_windy_model: str) -> dict:
    windy_data = get_windy_point_forecast(
        config.LA_MORGAL_COORDS["lat"],
        config.LA_MORGAL_COORDS["lon"],
        selected_windy_model,
    )

    windy_maps = get_windy_map_forecast(
        config.LA_MORGAL_COORDS["lat"],
        config.LA_MORGAL_COORDS["lon"],
        selected_windy_model,
    )
    if windy_data and isinstance(windy_data, dict) and windy_maps:
        windy_data["maps"] = windy_maps

    return {
        "provider": windy_data.get("provider") if windy_data else "Windy Point Forecast",
        "model": windy_data.get("model") if windy_data else selected_windy_model,
        "lat": windy_data.get("lat") if windy_data else config.LA_MORGAL_COORDS["lat"],
        "lon": windy_data.get("lon") if windy_data else config.LA_MORGAL_COORDS["lon"],
        "available_models": SUPPORTED_WINDY_MODELS,
        "hourly": windy_data.get("hourly", [])[:12] if windy_data else [],
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
    now_local = datetime.now(MADRID_TZ)
    metar_leas = get_metar(config.LEAS_ICAO)
    selected_windy_model = _sanitize_windy_model(windy_model)

    weather_data = get_weather_forecast(
        config.LA_MORGAL_COORDS["lat"],
        config.LA_MORGAL_COORDS["lon"],
        config.LA_MORGAL_COORDS["name"],
    )

    if not weather_data:
        raise RuntimeError("No se pudieron obtener datos meteorológicos de Open-Meteo.")

    daily = weather_data.get("daily_forecast", [])[:3]

    # ── Predicción Windy Point Forecast ──
    windy_section = _build_windy_section(selected_windy_model)

    # ── Mapas significativos AEMET (hoy/mañana/pasado, AM y PM) ──
    sig_maps = get_significant_maps_for_three_days(ambito="esp")

    # ── Mapa de análisis en superficie (isobaras, frentes) ──
    analysis_map_url = get_analysis_map_url()

    # ── Predicción AEMET textual Asturias ──
    # Obtener fechas esperadas para cada sección
    today_date = now_local.date()
    tomorrow_date = today_date + timedelta(days=1)
    day_after_tomorrow_date = today_date + timedelta(days=2)
    
    # Obtener predicciones
    pred_asturias_hoy = get_prediccion_asturias_hoy() or ""
    pred_asturias_manana = get_prediccion_asturias_manana() or ""
    pred_asturias_pasado_manana = get_prediccion_asturias_pasado_manana() or ""
    
    # Enriquecer con información de fecha esperada
    pred_asturias_hoy_label = f"📅 {today_date.strftime('%A, %d de %B de %Y')}\n{pred_asturias_hoy}" if pred_asturias_hoy else f"Sin datos para {today_date.strftime('%d/%m/%Y')}"
    pred_asturias_manana_label = f"📅 {tomorrow_date.strftime('%A, %d de %B de %Y')}\n{pred_asturias_manana}" if pred_asturias_manana else f"Sin datos para {tomorrow_date.strftime('%d/%m/%Y')}"
    pred_asturias_pasado_manana_label = f"📅 {day_after_tomorrow_date.strftime('%A, %d de %B de %Y')}\n{pred_asturias_pasado_manana}" if pred_asturias_pasado_manana else f"Sin datos para {day_after_tomorrow_date.strftime('%d/%m/%Y')}"

    # ── Predicción AEMET municipal Llanera ──
    pred_llanera = get_prediccion_llanera()
    pred_llanera_text = ""
    if pred_llanera:
        try:
            nombre = pred_llanera.get("nombre", "Llanera")
            dias = pred_llanera.get("prediccion", {}).get("dia", [])
            lines = [f"Predicción AEMET para {nombre}:"]
            for d in dias[:3]:
                fecha = d.get("fecha", "")[:10]

                temp = d.get("temperatura", {}) or {}
                t_min = temp.get("minima", "N/A")
                t_max = temp.get("maxima", "N/A")

                prob_precip = d.get("probPrecipitacion", []) or []
                pp_24 = next((p for p in prob_precip if p.get("periodo") == "00-24"), None)
                pp_value = pp_24.get("value") if isinstance(pp_24, dict) else None
                if pp_value is None and prob_precip:
                    vals = [p.get("value") for p in prob_precip if isinstance(p, dict) and p.get("value") is not None]
                    pp_value = max(vals) if vals else None

                viento = d.get("viento", []) or []
                viento_items = [v for v in viento if isinstance(v, dict)]
                viento_max_item = max(viento_items, key=lambda v: v.get("velocidad") or 0) if viento_items else None
                viento_dir = (viento_max_item or {}).get("direccion") or "VRB"
                viento_kmh = (viento_max_item or {}).get("velocidad")

                rachas = d.get("rachaMax", []) or []
                rachas_vals = []
                for r in rachas:
                    if isinstance(r, dict):
                        value = r.get("value")
                        if isinstance(value, (int, float)):
                            rachas_vals.append(value)
                        elif isinstance(value, str) and value.strip().isdigit():
                            rachas_vals.append(int(value.strip()))
                racha_max = max(rachas_vals) if rachas_vals else None

                lines.append(
                    f"  {fecha}: 🌡️ {t_min}/{t_max}°C · "
                    f"🌧️ precip {pp_value if pp_value is not None else 'N/A'}% · "
                    f"💨 viento máx {viento_kmh if viento_kmh is not None else 'N/A'} km/h ({viento_dir}) · "
                    f"🌬️ racha máx {racha_max if racha_max is not None else 'N/A'} km/h"
                )
            pred_llanera_text = "\n".join(lines)
        except Exception:
            pred_llanera_text = str(pred_llanera)[:500]

    # ── Construir días con mapas AEMET integrados (slots UTC reales disponibles) ──
    sig_index = {}
    for m in sig_maps:
        sig_index.setdefault(m["date"], []).append(m)

    days = []
    labels = ["Hoy", "Mañana", "Pasado mañana"]
    for index, day in enumerate(daily):
        target_date = datetime.fromisoformat(day["date"]).date()
        operating = _operating_hours(target_date)
        day_iso = target_date.isoformat()
        show_aemet_maps = index < 2

        map_slots = sorted(sig_index.get(day_iso, []), key=lambda item: item.get("utc_hour", "99")) if show_aemet_maps else []
        available_hours = [f"{slot.get('utc_hour')}" for slot in map_slots if slot.get("utc_hour")]

        days.append(
            {
                "label": labels[index] if index < len(labels) else day["date"],
                "date": day["date"],
                "description": weather_code_to_description(day.get("weather_code")),
                "temp_min": day.get("temp_min"),
                "temp_max": day.get("temp_max"),
                "wind_max_kmh": day.get("wind_max"),
                "wind_gusts_max_kmh": day.get("wind_gusts_max"),
                "sunrise": day.get("sunrise"),
                "sunset": day.get("sunset"),
                "operating_hours": f"{operating['open']} - {operating['close']} ({operating['season']})",
                "suggested_window": _best_operational_window_for_day(day),
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
        map_urls_for_ai = []
        if analysis_map_url:
            map_urls_for_ai.append(analysis_map_url)
        for m in sig_maps:
            u = m.get("map_url")
            if u and u not in map_urls_for_ai:
                map_urls_for_ai.append(u)
            if len(map_urls_for_ai) >= 4:
                break

        fused_ai = interpret_fused_forecast_with_ai(
            metar_leas=metar_leas or "",
            weather_data=weather_data,
            windy_data=windy_section or {},
            aemet_prediccion={
                "asturias_hoy": pred_asturias_hoy,
                "asturias_manana": pred_asturias_manana,
                "asturias_pasado_manana": pred_asturias_pasado_manana,
                "llanera": pred_llanera_text,
            },
            map_analysis_text=(analysis_map_url or (sig_maps[0].get("map_url") if sig_maps else "")),
            significant_map_urls=map_urls_for_ai,
            location=config.LA_MORGAL_COORDS["name"],
        )

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
            "condition": weather_code_to_description(current.get("weather_code")),
        },
        "metar": {
            "station": config.LEAS_ICAO,
            "raw": metar_leas,
            "analysis": metar_ai,
        },
        "forecast_days": days,
        "analysis_map_url": analysis_map_url,
        "aemet_prediccion": {
            "asturias_hoy": pred_asturias_hoy_label,
            "asturias_manana": pred_asturias_manana_label,
            "asturias_pasado_manana": pred_asturias_pasado_manana_label,
            "llanera": pred_llanera_text,
        },
        "windy": windy_section,
        "ai": {
            "weather_analysis": weather_ai,
            "map_analysis": map_ai,
            "windy_analysis": windy_ai,
            "expert_final_verdict": fused_ai or "No disponible",
            "pending": not include_ai,
        },
        "refresh_policy": {
            "description": "Actualización automática 5 veces al día",
            "slots_local_time": ["06:00", "10:00", "14:00", "18:00", "22:00"],
            "timezone": "Europe/Madrid",
        },
    }


def get_report_payload(force: bool = False, windy_model: str | None = None, include_ai: bool = True) -> dict:
    now_local = datetime.now(MADRID_TZ)
    cycle_id = _build_cycle_id(now_local)
    selected_model = _sanitize_windy_model(windy_model)
    cache_key = f"{cycle_id}|{selected_model}"

    with _CACHE_LOCK:
        if not force and _CACHE["payload"] and _CACHE["cache_key"] == cache_key:
            return _CACHE["payload"]

        payload = _generate_report_payload(windy_model=selected_model, include_ai=True)
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
def index():
    _start_cycle_warmer_once()
    with _CACHE_LOCK:
        payload = _CACHE.get("payload")
    if not payload:
        payload = get_report_payload(force=False, windy_model=config.WINDY_MODEL, include_ai=True)
    return render_template(
        "index.html",
        data=payload,
        windy_map_api_key=config.WINDY_MAP_FORECAST_API_KEY,
    )


@app.get("/api/report")
def api_report():
    _start_cycle_warmer_once()
    force = request.args.get("force", "0") == "1"
    windy_model = request.args.get("windy_model", config.WINDY_MODEL)
    payload = get_report_payload(force=force, windy_model=windy_model, include_ai=True)
    return jsonify(payload)


@app.get("/api/windy")
def api_windy():
    windy_model = request.args.get("windy_model", config.WINDY_MODEL)
    selected_model = _sanitize_windy_model(windy_model)
    windy_section = _build_windy_section(selected_model)
    return jsonify({"windy": windy_section})


if __name__ == "__main__":
    import sys
    # Forzar UTF-8 en stdout/stderr para evitar errores con emojis
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    print("Iniciando LEMR Meteo Web para La Morgal...")
    print(f"URL: http://{config.WEB_HOST}:{config.WEB_PORT}")
    print("Actualizacion automatica: 06:00, 10:00, 14:00, 18:00 y 22:00 (Europe/Madrid)")
    app.run(host=config.WEB_HOST, port=config.WEB_PORT, debug=False)
