"""
Servicio de acceso a AEMET OpenData API.
Obtiene mapas significativos, mapas de análisis y observaciones convencionales.

Flujo AEMET en dos pasos:
  1) Llamada autenticada → JSON con campo "datos" (URL temporal)
  2) GET a esa URL temporal → contenido real (imagen PNG, JSON, etc.)
"""
import io
import base64
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from typing import Optional, Dict, List
from zoneinfo import ZoneInfo

import requests
import config

AEMET_BASE = "https://opendata.aemet.es/opendata"
MADRID_TZ = ZoneInfo("Europe/Madrid")

# Reintentos ante HTTP 429 (rate-limit AEMET)
_MAX_RETRIES = 2
_RETRY_WAIT = 12  # segundos entre reintentos

# Mapeo de periodo → código 'dia' en el endpoint mapas significativos
# a = D+0 00-12, b = D+0 12-24, c = D+1 00-12, d = D+1 12-24,
# e = D+2 00-12, f = D+2 12-24
DAY_PERIOD_CODES = {
    (0, "am"): "a",
    (0, "pm"): "b",
    (1, "am"): "c",
    (1, "pm"): "d",
    (2, "am"): "e",
    (2, "pm"): "f",
}


def _api_key() -> str:
    return getattr(config, "AEMET_API_KEY", "")


def _aemet_get(endpoint: str, timeout: int = 15) -> Optional[dict]:
    """
    Paso 1: llamada autenticada a un endpoint AEMET.
    Reintenta automáticamente ante HTTP 429 (rate-limit).
    """
    api_key = _api_key()
    if not api_key:
        print("AEMET_API_KEY no configurada")
        return None

    url = f"{AEMET_BASE}{endpoint}"
    for attempt in range(_MAX_RETRIES + 1):
        try:
            resp = requests.get(
                url,
                params={"api_key": api_key},
                headers={"cache-control": "no-cache"},
                timeout=timeout,
            )
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429 and attempt < _MAX_RETRIES:
                print(f"AEMET 429 rate-limit en {endpoint}, reintentando en {_RETRY_WAIT}s...")
                time.sleep(_RETRY_WAIT)
                continue
            print(f"AEMET {endpoint} -> HTTP {resp.status_code}")
            return None
        except Exception as exc:
            print(f"Error AEMET GET {endpoint}: {exc}")
            return None
    return None


def _fetch_datos_url(datos_url: str, timeout: int = 15, as_bytes: bool = False):
    """
    Paso 2: descarga el contenido real desde la URL temporal AEMET.
    Si as_bytes=True devuelve bytes (imágenes), si no devuelve texto/JSON.
    """
    if not datos_url:
        return None
    try:
        resp = requests.get(datos_url, timeout=timeout)
        if resp.status_code != 200:
            print(f"AEMET datos URL → HTTP {resp.status_code}")
            return None
        if as_bytes:
            return resp.content
        # Intentar JSON, sino texto
        try:
            return resp.json()
        except Exception:
            return resp.text
    except Exception as exc:
        print(f"Error descargando datos AEMET: {exc}")
        return None


# ─────── Mapas significativos (vía URL directa ama.aemet.es) ───────
# La API OpenData no siempre devuelve datos para mapas significativos;
# ama.aemet.es publica las imágenes con el patrón:
#   QGQE70LEMM{HH}00________{YYYYMMDD}.png
# donde HH = 00, 06, 12, 18 (horas UTC)
AMA_MAP_BASE = "https://ama.aemet.es/o/estaticos/bbdd/imagenes"
SIG_MAP_UTC_HOURS = ["00", "06", "12", "18"]


def _url_has_image(url: str, timeout: int = 5) -> bool:
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            content_type = (resp.headers.get("Content-Type") or "").lower()
            if "image" in content_type or "png" in content_type or not content_type:
                return True
    except Exception:
        pass

    try:
        resp = requests.get(url, timeout=timeout, stream=True)
        ok = resp.status_code == 200
        resp.close()
        return ok
    except Exception:
        return False


def _direct_sig_map_url(target_date: date, utc_hour: str) -> str:
    """Construye la URL directa ama.aemet.es para un mapa significativo."""
    return (
        f"{AMA_MAP_BASE}/QGQE70LEMM{utc_hour}00________"
        f"{target_date.strftime('%Y%m%d')}.png"
    )


def get_significant_map_url(
    target_date: date,
    period: str = "am",
    ambito: str = "esp",
) -> Optional[str]:
    """
    Obtiene la URL de un mapa significativo.
    Intenta primero la URL directa de ama.aemet.es (más fiable);
    si no existe, intenta la API OpenData como fallback.
    """
    # Elegir hora UTC según periodo
    if period == "am":
        utc_hour = "06"
    else:
        utc_hour = "18"

    direct_url = _direct_sig_map_url(target_date, utc_hour)
    try:
        r = requests.head(direct_url, timeout=8)
        if r.status_code == 200:
            return direct_url
    except Exception:
        pass

    # Fallback 1: intentar la otra hora del mismo tramo
    alt_hour = "12" if period == "am" else "00"
    alt_url = _direct_sig_map_url(target_date, alt_hour)
    try:
        r = requests.head(alt_url, timeout=8)
        if r.status_code == 200:
            return alt_url
    except Exception:
        pass

    # Fallback 2: API OpenData
    today = datetime.now(MADRID_TZ).date()
    delta = (target_date - today).days
    if 0 <= delta <= 2:
        dia_code = DAY_PERIOD_CODES.get((delta, period))
        if dia_code:
            fecha_str = target_date.strftime("%Y-%m-%d")
            endpoint = f"/api/mapasygraficos/mapassignificativos/fecha/{fecha_str}/{ambito}/{dia_code}"
            meta = _aemet_get(endpoint)
            if meta and meta.get("datos"):
                return meta["datos"]

    return None


def get_significant_map_image_b64(
    target_date: date,
    period: str = "am",
    ambito: str = "esp",
) -> Optional[str]:
    """
    Descarga un mapa significativo y devuelve su contenido como base64
    (útil para incrustar directamente en <img src="data:image/png;base64,...">
    cuando la URL temporal AEMET haya caducado).
    """
    url = get_significant_map_url(target_date, period, ambito)
    if not url:
        return None
    raw = _fetch_datos_url(url, as_bytes=True)
    if raw:
        return base64.b64encode(raw).decode("ascii")
    return None


def get_significant_maps_for_three_days(ambito: str = "esp") -> List[Dict]:
    """
    Obtiene los mapas significativos para hoy y mañana
    por slots UTC reales (00, 06, 12, 18). Descarga SIEMPRE como base64 porque las URLs
    de ama.aemet.es redirigen a login cuando se acceden desde un navegador
    (anti-hotlinking), así que solo funcionan embebidas como data-URI.

    Returns:
        Lista de dicts con keys: date, label, utc_hour, slot_label, map_url, map_b64
    """
    today = datetime.now(MADRID_TZ).date()
    labels = ["Hoy", "Mañana"]
    results = []

    # Mapeo de desfase conocido para AEMET (verificado con AerBrava):
    # AEMET publica mapas con anticipación. La fuente de verdad es este mapeo:
    # - 00 UTC: QGQE70LEMM1200________{fecha_anterior}
    # - 06 UTC: QGQE70LEMM1800________{fecha_anterior}
    # - 12 UTC: QGQE70LEMM0000________{fecha_actual}
    # - 18 UTC: QGQE70LEMM0600________{fecha_actual}
    desfase_map = {
        "00": {"delta_date": -1, "source_hour": "12"},
        "06": {"delta_date": -1, "source_hour": "18"},
        "12": {"delta_date": 0, "source_hour": "00"},
        "18": {"delta_date": 0, "source_hour": "06"},
    }

    for delta in range(2):
        target = today + timedelta(days=delta)
        day_results: List[Dict] = []

        # Intentar cada hora UTC con su mapeo de desfase
        for target_hour in SIG_MAP_UTC_HOURS:
            mapping = desfase_map.get(target_hour, {})
            source_d = today + timedelta(days=delta + mapping.get("delta_date", 0))
            source_h = mapping.get("source_hour", target_hour)
            
            url = _direct_sig_map_url(source_d, source_h)
            
            if not _url_has_image(url, timeout=5):
                continue
            
            day_results.append({
                "date": target.isoformat(),
                "label": labels[delta],
                "utc_hour": target_hour,
                "slot_label": f"{target_hour} UTC",
                "map_url": url,
                "map_b64": None,
                "source_date": source_d.isoformat(),
                "source_utc_hour": source_h,
            })

        results.extend(day_results)

    return results


# ─────────────────────────── Mapa de análisis ──────────────────────────────


def get_analysis_map_url() -> Optional[str]:
    """
    Obtiene la URL temporal del último mapa de análisis en superficie
    (isobaras, frentes). Se actualiza cada ~12h.
    """
    meta = _aemet_get("/api/mapasygraficos/analisis")
    if meta and meta.get("datos"):
        return meta["datos"]
    return None


def get_analysis_map_b64() -> Optional[str]:
    url = get_analysis_map_url()
    if not url:
        return None
    raw = _fetch_datos_url(url, as_bytes=True)
    if raw:
        return base64.b64encode(raw).decode("ascii")
    return None


# ──────────────────── Observaciones convencionales ─────────────────────────


def get_conventional_observations() -> Optional[list]:
    """
    Descarga las observaciones convencionales actuales de todas las estaciones.
    Puede contener datos cercanos a La Morgal.
    """
    meta = _aemet_get("/api/observacion/convencional/todas")
    if meta and meta.get("datos"):
        return _fetch_datos_url(meta["datos"])
    return None


# ──────────────── Predicción CCAA para Asturias ────────────────────────────

ASTURIAS_CCAA_CODE = "ast"  # código AEMET para Asturias


def get_prediccion_asturias_hoy() -> Optional[str]:
    """Predicción textual de AEMET para Asturias - hoy."""
    meta = _aemet_get(f"/api/prediccion/ccaa/hoy/{ASTURIAS_CCAA_CODE}")
    if meta and meta.get("datos"):
        data = _fetch_datos_url(meta["datos"])
        if isinstance(data, list) and data:
            text = data[0].get("prediccion", {}).get("texto", str(data[0]))
        else:
            text = str(data) if data else None
        # Limpiar metadatos AEMET innecesarios: mantener solo la predicción textual
        if text and "PREDICCIÓN" in text:
            try:
                # Extraer solo la sección "B.- PREDICCIÓN" hasta el final
                parts = text.split("B.- PREDICCIÓN")
                if len(parts) > 1:
                    return parts[1].strip()
            except:
                pass
        return text
    return None


def get_prediccion_asturias_manana() -> Optional[str]:
    """Predicción textual de AEMET para Asturias - mañana."""
    meta = _aemet_get(f"/api/prediccion/ccaa/manana/{ASTURIAS_CCAA_CODE}")
    if meta and meta.get("datos"):
        data = _fetch_datos_url(meta["datos"])
        if isinstance(data, list) and data:
            text = data[0].get("prediccion", {}).get("texto", str(data[0]))
        else:
            text = str(data) if data else None
        # Limpiar metadatos AEMET innecesarios
        if text and "PREDICCIÓN" in text:
            try:
                parts = text.split("B.- PREDICCIÓN")
                if len(parts) > 1:
                    return parts[1].strip()
            except:
                pass
        return text
    return None


def get_prediccion_asturias_pasado_manana() -> Optional[str]:
    """Predicción textual de AEMET para Asturias - pasado mañana."""
    meta = _aemet_get(f"/api/prediccion/ccaa/pasadomanana/{ASTURIAS_CCAA_CODE}")
    if meta and meta.get("datos"):
        data = _fetch_datos_url(meta["datos"])
        if isinstance(data, list) and data:
            text = data[0].get("prediccion", {}).get("texto", str(data[0]))
        else:
            text = str(data) if data else None
        # Limpiar metadatos AEMET innecesarios
        if text and "PREDICCIÓN" in text:
            try:
                parts = text.split("B.- PREDICCIÓN")
                if len(parts) > 1:
                    return parts[1].strip()
            except:
                pass
        return text
    return None


# ──────────────── Predicción municipal Llanera ─────────────────────────────

LLANERA_MUNICIPIO_CODE = "33035"  # Llanera (Asturias) – donde está La Morgal


def get_prediccion_llanera() -> Optional[dict]:
    """
    Predicción por municipio para Llanera (donde está La Morgal).
    Devuelve dict con la predicción diaria completa.
    """
    meta = _aemet_get(f"/api/prediccion/especifica/municipio/diaria/{LLANERA_MUNICIPIO_CODE}")
    if meta and meta.get("datos"):
        data = _fetch_datos_url(meta["datos"])
        if isinstance(data, list) and data:
            return data[0]
        return data
    return None


def get_prediccion_llanera_horaria() -> Optional[dict]:
    """
    Predicción horaria para Llanera (donde está La Morgal).
    Devuelve dict con la predicción horaria completa (hasta 48h).
    """
    meta = _aemet_get(f"/api/prediccion/especifica/municipio/horaria/{LLANERA_MUNICIPIO_CODE}")
    if meta and meta.get("datos"):
        data = _fetch_datos_url(meta["datos"])
        if isinstance(data, list) and data:
            return data[0]
        return data
    return None


# ──────────────── Utilidad: resumen rápido test ────────────────────────────

if __name__ == "__main__":
    print("=== Test AEMET Service ===")

    print("\n1) Mapa de análisis:")
    url = get_analysis_map_url()
    print(f"   URL: {url}")

    print("\n2) Mapas significativos (ama.aemet.es):")
    today = datetime.now(MADRID_TZ).date()
    for h in SIG_MAP_UTC_HOURS:
        u = _direct_sig_map_url(today, h)
        try:
            r = requests.head(u, timeout=8)
            print(f"   {h} UTC: {'✅' if r.status_code == 200 else '❌'} {u}")
        except Exception:
            print(f"   {h} UTC: ❌ error")

    print("\n3) Predicción Asturias hoy:")
    pred = get_prediccion_asturias_hoy()
    print(f"   {(pred or 'N/A')[:200]}")

    print("\n4) Predicción Llanera:")
    pred = get_prediccion_llanera()
    if pred:
        print(f"   Municipio: {pred.get('nombre', 'N/A')}")
    else:
        print("   N/A")
