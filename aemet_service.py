"""
Servicio de acceso a AEMET OpenData API.
Obtiene mapas significativos, mapas de análisis y observaciones convencionales.

Flujo AEMET en dos pasos:
  1) Llamada autenticada → JSON con campo "datos" (URL temporal)
  2) GET a esa URL temporal → contenido real (imagen PNG, JSON, etc.)
"""
import base64
import re
import threading
import time
from datetime import date, datetime, timedelta, timezone
from typing import Optional, Dict, List
from zoneinfo import ZoneInfo

import requests
import config

AEMET_BASE = "https://opendata.aemet.es/opendata"
MADRID_TZ = ZoneInfo("Europe/Madrid")

# Protección anti-rate-limit: delay entre peticiones consecutivas a AEMET
_LAST_AEMET_REQUEST_TIME = 0.0
_MIN_REQUEST_INTERVAL = 0.8  # segundos entre peticiones (evita rate-limit)

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
    Añade delay automático entre peticiones para evitar bloqueos.
    """
    global _LAST_AEMET_REQUEST_TIME, _AEMET_REQUEST_COUNT

    # Protección rate-limit: esperar si la última petición fue muy reciente
    time_since_last = time.time() - _LAST_AEMET_REQUEST_TIME
    if time_since_last < _MIN_REQUEST_INTERVAL:
        sleep_time = _MIN_REQUEST_INTERVAL - time_since_last
        print(f"⏳ Rate-limit protection: esperando {sleep_time:.1f}s antes de AEMET {endpoint[:40]}")
        time.sleep(sleep_time)
    
    api_key = _api_key()
    if not api_key:
        print("AEMET_API_KEY no configurada")
        return None

    url = f"{AEMET_BASE}{endpoint}"
    for attempt in range(_MAX_RETRIES + 1):
        try:
            _LAST_AEMET_REQUEST_TIME = time.time()  # Marcar timestamp
            _AEMET_REQUEST_COUNT += 1  # Incrementar contador
            resp = requests.get(
                url,
                params={"api_key": api_key},
                headers={"cache-control": "no-cache"},
                timeout=timeout,
            )
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429 and attempt < _MAX_RETRIES:
                print(f"⚠️ AEMET 429 rate-limit en {endpoint}, reintentando en {_RETRY_WAIT}s...")
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
# ⚠️ NO se usa la API OpenData autenticada para los mapas significativos.
# El endpoint /api/mapasygraficos/mapassignificativos/... existe pero AEMET
# no publica datos por él de forma fiable (devuelve 404 "No hay datos que
# satisfagan esos criterios" la mayoría del tiempo, verificado 2026-03-23).
# En cambio, ama.aemet.es publica las imágenes con el patrón:
#   QGQE70LEMM{HH}00________{YYYYMMDD}.png
# donde HH = 00, 06, 12, 18 (hora UTC de emisión; validez = emisión + 12h)
#
# ⚠️ CERO peticiones desde el backend (desde 2026-11-04): ama.aemet.es está
# detrás de un WAF anti-bot (F5) que bloquea por IP ante patrones de sondeo.
# Las URLs se CALCULAN de forma determinista y el navegador del usuario carga
# cada imagen una sola vez; si falla, el <img onerror> del frontend lo indica.
AMA_MAP_BASE = "https://ama.aemet.es/o/estaticos/bbdd/imagenes"
SIG_MAP_UTC_HOURS = ["00", "06", "12", "18"]

# Horas que tarda AEMET en publicar un mapa tras su hora nominal de emisión.
# Demasiado bajo → durante un rato sale "Imagen no disponible" en el último
# slot; demasiado alto → el mapa aparece más tarde. Ajustable por env.
SIG_MAP_PUBLISH_LAG_H = float(getattr(config, "SIG_MAP_PUBLISH_LAG_H", 3))

# Contador de peticiones AEMET OpenData (para monitoring)
_AEMET_REQUEST_COUNT = 0


def get_aemet_request_count() -> int:
    """Devuelve el número de peticiones AEMET realizadas desde el inicio."""
    return _AEMET_REQUEST_COUNT


def _direct_sig_map_url(target_date: date, utc_hour: str) -> str:
    """Construye la URL directa ama.aemet.es para un mapa significativo."""
    return (
        f"{AMA_MAP_BASE}/QGQE70LEMM{utc_hour}00________"
        f"{target_date.strftime('%Y%m%d')}.png"
    )


def get_significant_maps_for_three_days(ambito: str = "esp") -> List[Dict]:
    """
    Calcula, SIN hacer ninguna petición HTTP, los mapas significativos para
    hoy y mañana por slots UTC de validez (00, 06, 12, 18).

    Cada slot de validez V se cubre con el fichero emitido 12h antes
    (V - 12h), equivalente al mapeo verificado con AerBrava:
      00 UTC → QGQE70LEMM1200 del día anterior · 06 UTC → 1800 día anterior
      12 UTC → QGQE70LEMM0000 del mismo día    · 18 UTC → 0600 mismo día
    Solo se incluyen los slots cuyo fichero ya debería estar publicado:
    emisión + SIG_MAP_PUBLISH_LAG_H <= ahora (UTC).

    Returns:
        Lista de dicts con keys: date, label, utc_hour, slot_label, map_url,
        map_b64, source_date, source_utc_hour, verified (siempre False: el
        backend ya no verifica; lo comprueba el navegador al cargar).
    """
    now_utc = datetime.now(timezone.utc)
    today = datetime.now(MADRID_TZ).date()
    labels = ["Hoy", "Mañana"]
    results: List[Dict] = []

    for delta in range(2):
        target = today + timedelta(days=delta)
        for target_hour in SIG_MAP_UTC_HOURS:
            valid_dt = datetime(target.year, target.month, target.day,
                                int(target_hour), tzinfo=timezone.utc)
            issue_dt = valid_dt - timedelta(hours=12)
            if issue_dt + timedelta(hours=SIG_MAP_PUBLISH_LAG_H) > now_utc:
                continue  # todavía no debería estar publicado: no se pide

            source_d = issue_dt.date()
            source_h = f"{issue_dt.hour:02d}"
            results.append({
                "date": target.isoformat(),
                "label": labels[delta],
                "utc_hour": target_hour,
                "slot_label": f"{target_hour} UTC",
                "map_url": _direct_sig_map_url(source_d, source_h),
                "map_b64": None,
                "source_date": source_d.isoformat(),
                "source_utc_hour": source_h,
                "verified": False,
            })

    return results


# ─────────────────────────── Mapa de análisis ──────────────────────────────


def get_analysis_map_url() -> Optional[str]:
    """
    URL del mapa de análisis en superficie (isobaras, frentes).

    Fuente principal: página pública www.aemet.es (SIN api key, URL estable,
    válida para el navegador y para la IA). Respaldo: OpenData (requiere key;
    URL temporal).
    """
    web = _web_analysis()
    if web:
        return web["url"]
    return _opendata_analysis_url()


def get_analysis_map_b64() -> Optional[str]:
    """
    Mapa de análisis en superficie como data URI base64 para el navegador
    (~15k tokens, NO usar para IA). Se descarga una sola vez por publicación.
    """
    web = _web_analysis()
    if web and web.get("b64"):
        return web["b64"]
    return _opendata_analysis_b64()


# ── Fuente principal: www.aemet.es (sin api key) ──
# La página publica el análisis como .../mapa_frentes/{YYYYMMDDHH}+000_<sufijo>.gif.
# El sufijo no es predecible, así que se lee la página (1 petición) y se extrae.
# robots.txt de www.aemet.es permite esta ruta; con caché hacemos ≤1 lectura/h.
AEMET_WEB_BASE = "https://www.aemet.es"
_FRENTES_PAGE = f"{AEMET_WEB_BASE}/es/eltiempo/prediccion/mapa_frentes"
_FRENTES_RE = re.compile(
    r"/?(imagenes_d/eltiempo/prediccion/mapa_frentes/\d{10}\+000_[A-Za-z0-9_]+\.gif)"
)
_WEB_HEADERS = {"User-Agent": "analisis-meteo-LEMR/1.0"}
_WEB_ANALYSIS_TTL = 3600  # segundos entre lecturas de la página
_web_analysis_lock = threading.Lock()
_web_analysis_cache: Dict = {"checked_at": 0.0, "url": None, "b64": None}


def _web_analysis() -> Optional[Dict]:
    """Devuelve {'url', 'b64'} del último análisis publicado en www.aemet.es."""
    with _web_analysis_lock:
        cache = _web_analysis_cache
        if cache["url"] and time.time() - cache["checked_at"] < _WEB_ANALYSIS_TTL:
            return dict(cache)
        try:
            resp = requests.get(_FRENTES_PAGE, headers=_WEB_HEADERS, timeout=15)
            match = _FRENTES_RE.search(resp.text) if resp.status_code == 200 else None
            if not match:
                print(f"⚠️ Mapa análisis web: patrón no encontrado (HTTP {resp.status_code})")
                return dict(cache) if cache["url"] else None
            url = f"{AEMET_WEB_BASE}/{match.group(1)}"
            if url != cache["url"] or not cache["b64"]:
                img = requests.get(url, headers=_WEB_HEADERS, timeout=20)
                ctype = (img.headers.get("Content-Type") or "").lower()
                if img.status_code != 200 or "image" not in ctype or len(img.content) < 1000:
                    print(f"⚠️ Mapa análisis web: imagen no válida (HTTP {img.status_code}, {ctype})")
                    return dict(cache) if cache["url"] else None
                cache["b64"] = (
                    f"data:{ctype.split(';')[0]};base64,"
                    + base64.b64encode(img.content).decode("ascii")
                )
                cache["url"] = url
                print(f"✅ Mapa análisis (www.aemet.es): {url} ({len(img.content)} bytes)")
            cache["checked_at"] = time.time()
            return dict(cache)
        except Exception as exc:
            print(f"⚠️ Mapa análisis web error: {exc}")
            return dict(cache) if cache["url"] else None


# ── Respaldo: OpenData (requiere api key) ──

def _opendata_analysis_url() -> Optional[str]:
    meta = _aemet_get("/api/mapasygraficos/analisis")
    if meta and meta.get("datos"):
        return meta["datos"]  # URL temporal: https://opendata.aemet.es/opendata/sh/XXX
    return None


def _opendata_analysis_b64() -> Optional[str]:
    temp_url = _opendata_analysis_url()
    if not temp_url:
        return None
    for attempt in range(2):
        try:
            raw_bytes = _fetch_datos_url(temp_url, timeout=20, as_bytes=True)
            if raw_bytes and len(raw_bytes) > 1000:
                return "data:image/png;base64," + base64.b64encode(raw_bytes).decode("ascii")
            print(f"⚠️ Mapa análisis OpenData: respuesta muy pequeña (intento {attempt + 1}/2)")
        except Exception as e:
            print(f"⚠️ Error descargando mapa análisis OpenData (intento {attempt + 1}/2): {e}")
        if attempt == 0:
            time.sleep(2)
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


# ──────────────── Avisos CAP Asturias ──────────────────────────────────────

AVISOS_NO_DISPONIBLES = (
    "⚠️ AVISOS AEMET NO DISPONIBLES: no se pudieron consultar (no implica que "
    "no haya avisos). Indica al piloto que los verifique en "
    "https://www.aemet.es/es/eltiempo/prediccion/avisos antes de volar."
)


def get_avisos_cap_asturias() -> Optional[str]:
    """
    Obtiene avisos meteorológicos CAP activos para Asturias (área 33).
    Devuelve cadena compacta con los avisos activos, None si AEMET confirma
    que no hay, o AVISOS_NO_DISPONIBLES si no se pudo consultar (key caducada,
    error de red...). Nunca hay que confundir "no consultado" con "sin avisos".
    """
    try:
        meta = _aemet_get("/api/avisos_cap/ultimoelaborado/area/33")
        if not meta or not meta.get("datos"):
            return AVISOS_NO_DISPONIBLES
        data = _fetch_datos_url(meta["datos"])
        if not data:
            return AVISOS_NO_DISPONIBLES

        # data puede ser lista de avisos o dict con una lista
        avisos = data if isinstance(data, list) else data.get("avisos", []) if isinstance(data, dict) else []
        if not avisos:
            return None

        now = datetime.now(MADRID_TZ)
        lines = []
        niveles_peso = {"rojo": 3, "naranja": 2, "amarillo": 1}

        for aviso in avisos:
            if not isinstance(aviso, dict):
                continue
            # Filtrar solo avisos vigentes
            nivel = (aviso.get("nivel") or aviso.get("nivel_aviso") or "").lower()
            if not nivel or nivel == "verde":
                continue

            parametro = (
                aviso.get("parametro")
                or aviso.get("fenomeno")
                or aviso.get("phenomenon")
                or "METEOROLÓGICO"
            ).upper()

            effective_raw = aviso.get("effective") or aviso.get("onset") or ""
            expires_raw = aviso.get("expires") or aviso.get("expiry") or ""

            # Intentar parsear fechas para filtrar avisos caducados
            try:
                if expires_raw:
                    expires_dt = datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
                    if expires_dt < now:
                        continue
            except Exception:
                pass

            # Formatear intervalo horario
            try:
                eff_str = datetime.fromisoformat(effective_raw.replace("Z", "+00:00")).strftime("%d/%m %H:%Mh") if effective_raw else "?"
                exp_str = datetime.fromisoformat(expires_raw.replace("Z", "+00:00")).strftime("%d/%m %H:%Mh") if expires_raw else "?"
                intervalo = f"{eff_str}→{exp_str}"
            except Exception:
                intervalo = ""

            descripcion = (aviso.get("descripcion") or aviso.get("description") or "").strip()
            umbral = (aviso.get("umbral") or "").strip()

            nivel_ico = {"rojo": "🔴", "naranja": "🟠", "amarillo": "🟡"}.get(nivel, "⚠️")
            linea = f"{nivel_ico} AVISO {nivel.upper()} {parametro}"
            if umbral:
                linea += f": {umbral}"
            elif descripcion:
                linea += f": {descripcion[:80]}"
            if intervalo:
                linea += f" — {intervalo}"
            lines.append((niveles_peso.get(nivel, 0), linea))

        if not lines:
            return None

        # Ordenar por peso descendente (rojo primero)
        lines.sort(key=lambda x: x[0], reverse=True)
        return "\n".join(l for _, l in lines)

    except Exception as exc:
        print(f"⚠️ get_avisos_cap_asturias error: {exc}")
        return AVISOS_NO_DISPONIBLES





# ──────────────── Utilidad: resumen rápido test ────────────────────────────

if __name__ == "__main__":
    print("=== Test AEMET Service ===")

    print("\n1) Mapa de análisis:")
    url = get_analysis_map_url()
    print(f"   URL: {url}")

    print("\n2) Mapas significativos (ama.aemet.es, URLs calculadas, sin peticiones):")
    for m in get_significant_maps_for_three_days():
        print(f"   {m['label']} {m['utc_hour']} UTC: {m['map_url']}")

    print("\n3) Predicción Llanera:")
    pred = get_prediccion_llanera()
    if pred:
        print(f"   Municipio: {pred.get('nombre', 'N/A')}")
    else:
        print("   N/A")
