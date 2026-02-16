"""
Servicio para consumir Windy Point Forecast API.
"""
from datetime import datetime
from math import atan2, degrees, sqrt
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

import requests

import config

MADRID_TZ = ZoneInfo("Europe/Madrid")


def _windy_key() -> str:
    return getattr(config, "WINDY_POINT_FORECAST_API_KEY", "")


def _windy_model_for_embed(model_name: str) -> str:
    model = (model_name or "gfs").lower()
    if model == "iconeu":
        return "iconEu"
    if model == "arome":
        return "arome"
    return "gfs"


def _build_windy_embed_url(lat: float, lon: float, model_name: str) -> str:
    model = _windy_model_for_embed(model_name)
    return (
        "https://embed.windy.com/embed2.html"
        f"?lat={lat}&lon={lon}&zoom=9&level=surface&overlay=wind"
        "&menu=&message=true&marker=true&calendar=24&pressure=true&type=map&location=coordinates"
        f"&detail=true&detailLat={lat}&detailLon={lon}&metricWind=km%2Fh&metricTemp=%C2%B0C&model={model}"
    )


def _extract_series(data: dict, key: str) -> list:
    value = data.get(key)
    if isinstance(value, list):
        return value
    return []


def _vector_to_wind_kmh_and_dir(u: float, v: float) -> tuple[float, float]:
    speed_ms = sqrt((u or 0.0) ** 2 + (v or 0.0) ** 2)
    speed_kmh = speed_ms * 3.6
    direction_from = (degrees(atan2(-(u or 0.0), -(v or 0.0))) + 360.0) % 360.0
    return speed_kmh, direction_from


def _build_day_summary(hourly: List[dict]) -> List[dict]:
    grouped: Dict[str, List[dict]] = {}
    for row in hourly:
        day = row["time_local"][:10]
        grouped.setdefault(day, []).append(row)

    result = []
    for day, rows in sorted(grouped.items())[:7]:  # Extendido a 7 días
        max_wind = max((r.get("wind_kmh") or 0) for r in rows)
        max_gust = max((r.get("gust_kmh") or 0) for r in rows)
        avg_temp = round(sum((r.get("temp_c") or 0) for r in rows) / max(len(rows), 1), 1)
        total_precip = round(sum((r.get("precip_3h_mm") or 0) for r in rows), 1)
        result.append(
            {
                "date": day,
                "max_wind_kmh": round(max_wind, 1),
                "max_gust_kmh": round(max_gust, 1),
                "avg_temp_c": avg_temp,
                "precip_total_mm": total_precip,
            }
        )
    return result


def _parameters_for_model(model_name: str) -> list[str]:
    base = [
        "wind",
        "windGust",
        "temp",
        "dewpoint",
        "rh",
        "precip",
        "lclouds",
        "mclouds",
        "hclouds",
    ]
    # AROME no acepta "pressure" en Point Forecast v2
    if model_name.lower() != "arome":
        base.append("pressure")
    return base


def get_windy_point_forecast(lat: float, lon: float, model: Optional[str] = None) -> Optional[dict]:
    """
    Obtiene pronóstico de punto de Windy para coordenadas dadas.

    Returns:
        dict con series horarias y resumen diario, o None si hay error.
    """
    api_key = _windy_key()
    selected_model = model or config.WINDY_MODEL
    fallback_payload = {
        "provider": "Windy Point Forecast",
        "model": selected_model,
        "lat": lat,
        "lon": lon,
        "units": {},
        "hourly": [],
        "daily_summary": [],
        "map_embed_url": _build_windy_embed_url(lat, lon, selected_model),
        "map_link": f"https://www.windy.com/?{lat},{lon},10",
    }

    if not api_key:
        print("WINDY_POINT_FORECAST_API_KEY no configurada")
        fallback_payload["error"] = "WINDY_POINT_FORECAST_API_KEY no configurada"
        return fallback_payload

    parameters = _parameters_for_model(selected_model)

    payload = {
        "lat": lat,
        "lon": lon,
        "model": selected_model,
        "parameters": parameters,
        "levels": ["surface"],
        "key": api_key,
    }

    try:
        response = requests.post(config.WINDY_POINT_FORECAST_API, json=payload, timeout=20)
        if response.status_code == 204 and selected_model != "gfs":
            payload["model"] = "gfs"
            response = requests.post(config.WINDY_POINT_FORECAST_API, json=payload, timeout=20)

        if response.status_code != 200:
            print(f"Windy Point Forecast -> HTTP {response.status_code}: {response.text[:250]}")
            fallback_payload["error"] = f"Windy Point Forecast HTTP {response.status_code}"
            return fallback_payload

        data = response.json()

        ts = _extract_series(data, "ts")
        wind_u = _extract_series(data, "wind_u-surface")
        wind_v = _extract_series(data, "wind_v-surface")
        gust = _extract_series(data, "gust-surface")
        temp = _extract_series(data, "temp-surface")
        dewpoint = _extract_series(data, "dewpoint-surface")
        rh = _extract_series(data, "rh-surface")
        pressure = _extract_series(data, "pressure-surface")
        precip_3h = _extract_series(data, "past3hprecip-surface")
        lclouds = _extract_series(data, "lclouds-surface")
        mclouds = _extract_series(data, "mclouds-surface")
        hclouds = _extract_series(data, "hclouds-surface")

        points = min(
            len(ts), len(wind_u), len(wind_v),
            len(gust) if gust else len(ts),
            len(temp) if temp else len(ts),
        )

        hourly = []
        for i in range(points):
            dt_local = datetime.fromtimestamp(ts[i] / 1000, tz=ZoneInfo("UTC")).astimezone(MADRID_TZ)
            wind_kmh, wind_dir = _vector_to_wind_kmh_and_dir(wind_u[i], wind_v[i])
            gust_kmh = (gust[i] * 3.6) if i < len(gust) and gust[i] is not None else None

            cloud_low = lclouds[i] if i < len(lclouds) else None
            cloud_mid = mclouds[i] if i < len(mclouds) else None
            cloud_high = hclouds[i] if i < len(hclouds) else None
            cloud_total = None
            if cloud_low is not None and cloud_mid is not None and cloud_high is not None:
                cloud_total = min(100, max(cloud_low, cloud_mid, cloud_high))

            temp_k = temp[i] if i < len(temp) else None
            dewp_k = dewpoint[i] if i < len(dewpoint) else None

            hourly.append(
                {
                    "time_local": dt_local.isoformat(),
                    "wind_kmh": round(wind_kmh, 1),
                    "wind_dir_deg": round(wind_dir, 0),
                    "gust_kmh": round(gust_kmh, 1) if gust_kmh is not None else None,
                    "temp_c": round(temp_k - 273.15, 1) if temp_k is not None else None,
                    "dewpoint_c": round(dewp_k - 273.15, 1) if dewp_k is not None else None,
                    "rh_pct": rh[i] if i < len(rh) else None,
                    "pressure_pa": pressure[i] if i < len(pressure) else None,
                    "precip_3h_mm": precip_3h[i] if i < len(precip_3h) else None,
                    "cloud_cover_pct": cloud_total,
                }
            )

        return {
            "provider": "Windy Point Forecast",
            "model": payload["model"],
            "lat": lat,
            "lon": lon,
            "units": data.get("units", {}),
            "hourly": hourly[:168],  # Extendido a 168 horas (7 días)
            "daily_summary": _build_day_summary(hourly),
            "map_embed_url": _build_windy_embed_url(lat, lon, payload["model"]),
            "map_link": f"https://www.windy.com/?{lat},{lon},10",
        }
    except Exception as exc:
        print(f"Error consultando Windy Point Forecast: {exc}")
        fallback_payload["error"] = f"Error consultando Windy: {exc}"
        return fallback_payload
