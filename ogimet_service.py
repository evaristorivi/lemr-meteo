"""
Servicio para obtener mapas de análisis meteorológico de Ogimet.
URLs públicas de modelos numéricos de superficie para España.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

MADRID_TZ = ZoneInfo("Europe/Madrid")


def _get_latest_run_time(now: datetime) -> tuple[str, str]:
    """
    Determina el run más reciente disponible (00Z, 06Z, 12Z, 18Z).
    Retorna (date_str YYYYMMDD, run_str HH).
    
    Estrategia conservadora: usa el run 18Z del día anterior,
    que garantiza estar siempre disponible.
    """
    utc_now = now.astimezone(ZoneInfo("UTC"))
    
    # Usar run 18Z del día anterior (siempre disponible)
    yesterday = utc_now - timedelta(days=1)
    date_str = yesterday.strftime("%Y%m%d")
    run = "18"
    
    return date_str, run


def _build_ogimet_url(date_str: str, run: str, projection_hours: int) -> str:
    """
    Construye URL de mapa Ogimet para superficie (SFC) España.
    
    Args:
        date_str: Fecha en formato YYYYMMDD
        run: Run del modelo (00, 06, 12, 18)
        projection_hours: Horas de proyección (12, 36, 60, etc.)
    
    Returns:
        URL completa del mapa
    """
    proy_str = f"{projection_hours:03d}"  # 012, 036, 060
    return (
        f"https://www.ogimet.com/show_foremaps.php?"
        f"niv=SFC&date={date_str}&run={run}&proy={proy_str}&zone=SP00&drun={date_str}_{run}"
    )


def get_surface_maps_three_days() -> dict:
    """
    Obtiene URLs de mapas de superficie de Ogimet para HOY, MAÑANA y PASADO MAÑANA.
    
    Returns:
        {
            "today": {"url": str, "label": str, "projection": str},
            "tomorrow": {"url": str, "label": str, "projection": str},
            "day_after": {"url": str, "label": str, "projection": str},
            "run_info": {"date": str, "run": str, "description": str}
        }
    """
    now = datetime.now(MADRID_TZ)
    date_str, run = _get_latest_run_time(now)
    
    # Proyecciones para cada día (ajustadas al run)
    # Si es run 00Z: +12h (mediodía HOY), +36h (mediodía MAÑANA), +60h (mediodía PASADO)
    projections = {
        "today": 12,
        "tomorrow": 36,
        "day_after": 60,
    }
    
    today_date = now.date()
    tomorrow_date = today_date + timedelta(days=1)
    day_after_date = today_date + timedelta(days=2)
    
    return {
        "today": {
            "url": _build_ogimet_url(date_str, run, projections["today"]),
            "label": f"HOY {today_date.strftime('%d/%m')}",
            "projection": f"+{projections['today']}h",
        },
        "tomorrow": {
            "url": _build_ogimet_url(date_str, run, projections["tomorrow"]),
            "label": f"MAÑANA {tomorrow_date.strftime('%d/%m')}",
            "projection": f"+{projections['tomorrow']}h",
        },
        "day_after": {
            "url": _build_ogimet_url(date_str, run, projections["day_after"]),
            "label": f"PASADO {day_after_date.strftime('%d/%m')}",
            "projection": f"+{projections['day_after']}h",
        },
        "run_info": {
            "date": date_str,
            "run": run,
            "description": f"Run {run}Z del {date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}",
        },
    }
