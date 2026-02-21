"""
Servicio de acceso a AEMET OpenData API.
Obtiene mapas significativos, mapas de análisis y observaciones convencionales.

Flujo AEMET en dos pasos:
  1) Llamada autenticada → JSON con campo "datos" (URL temporal)
  2) GET a esa URL temporal → contenido real (imagen PNG, JSON, etc.)
"""
import base64
import time
from datetime import date, datetime, timedelta
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
    
    # Limpiar caché si es necesario
    _clear_cache_if_needed()
    
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
# La API OpenData no siempre devuelve datos para mapas significativos;
# ama.aemet.es publica las imágenes con el patrón:
#   QGQE70LEMM{HH}00________{YYYYMMDD}.png
# donde HH = 00, 06, 12, 18 (horas UTC)
AMA_MAP_BASE = "https://ama.aemet.es/o/estaticos/bbdd/imagenes"
SIG_MAP_UTC_HOURS = ["00", "06", "12", "18"]

# Caché de URLs verificadas (evita verificar la misma URL múltiples veces)
_URL_AVAILABILITY_CACHE: Dict[str, bool] = {}
_CACHE_LAST_CLEAR_TIME = time.time()
_CACHE_CLEAR_INTERVAL = 1800  # Limpiar caché cada 30 minutos

# Contador de peticiones AEMET (para monitoring)
_AEMET_REQUEST_COUNT = 0


def _clear_cache_if_needed():
    """Limpia el caché de URLs si ha pasado el intervalo de tiempo."""
    global _URL_AVAILABILITY_CACHE, _CACHE_LAST_CLEAR_TIME
    if time.time() - _CACHE_LAST_CLEAR_TIME > _CACHE_CLEAR_INTERVAL:
        _URL_AVAILABILITY_CACHE.clear()
        _CACHE_LAST_CLEAR_TIME = time.time()
        print("🧹 Caché de URLs AEMET limpiado")


def get_aemet_request_count() -> int:
    """Devuelve el número de peticiones AEMET realizadas desde el inicio."""
    return _AEMET_REQUEST_COUNT


def _url_has_image(url: str, timeout: int = 5) -> bool:
    # Usar caché para evitar verificaciones repetidas
    if url in _URL_AVAILABILITY_CACHE:
        return _URL_AVAILABILITY_CACHE[url]
    
    result = False
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            content_type = (resp.headers.get("Content-Type") or "").lower()
            if "image" in content_type or "png" in content_type or not content_type:
                result = True
    except Exception:
        pass

    if not result:
        try:
            resp = requests.get(url, timeout=timeout, stream=True)
            result = resp.status_code == 200
            resp.close()
        except Exception:
            pass
    
    # Cachear resultado (evita verificar de nuevo en este ciclo)
    _URL_AVAILABILITY_CACHE[url] = result
    return result


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
    Obtiene la URL temporal del mapa de análisis en superficie (isobaras, frentes).
    
    ⚠️ NOTA: Esta URL es temporal y puede tener problemas de CORS en navegadores.
    Para usar en navegador, usar get_analysis_map_b64() que devuelve base64.
    Para IA (OpenAI/GitHub Models), esta URL funciona perfectamente.
    
    Returns:
        URL temporal de la API de AEMET (más ligera para IA, ~100 tokens)
    """
    meta = _aemet_get("/api/mapasygraficos/analisis")
    if meta and meta.get("datos"):
        return meta["datos"]  # URL temporal: https://opendata.aemet.es/opendata/sh/XXX
    return None


def get_analysis_map_b64() -> Optional[str]:
    """
    Descarga el mapa de análisis en superficie y lo convierte a base64.
    
    Se actualiza cada ~12h. Ideal para embedding en navegadores (evita CORS y URLs expiradas).
    
    Returns:
        String data URI base64 o None si hay error (~15k tokens, NO usar para IA)
    """
    temp_url = get_analysis_map_url()
    if not temp_url:
        return None
    
    # Descargar la imagen con reintentos (las URLs temporales a veces tardan)
    max_attempts = 2
    for attempt in range(max_attempts):
        try:
            # Paso 2: descargar desde URL temporal con timeout generoso
            raw_bytes = _fetch_datos_url(temp_url, timeout=20, as_bytes=True)
            
            if raw_bytes and len(raw_bytes) > 1000:  # Verificar que sea una imagen real
                # Convertir a base64 para embedding directo
                import base64
                b64_str = base64.b64encode(raw_bytes).decode("ascii")
                print(f"✅ Mapa análisis descargado: {len(raw_bytes)} bytes → {len(b64_str)} chars base64")
                return f"data:image/png;base64,{b64_str}"
            else:
                print(f"⚠️ Mapa análisis: respuesta muy pequeña (intento {attempt+1}/{max_attempts})")
                
        except Exception as e:
            print(f"⚠️ Error descargando mapa análisis (intento {attempt+1}/{max_attempts}): {e}")
            
        if attempt < max_attempts - 1:
            import time
            time.sleep(2)  # Esperar antes de reintentar
    
    print(f"❌ No se pudo descargar el mapa de análisis después de {max_attempts} intentos")
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

def get_avisos_cap_asturias() -> Optional[str]:
    """
    Obtiene avisos meteorológicos CAP activos para Asturias (área 33).
    Devuelve cadena compacta con los avisos activos, o None si no hay.
    """
    try:
        meta = _aemet_get("/api/avisos_cap/ultimoelaborado/area/33")
        if not meta or not meta.get("datos"):
            return None
        data = _fetch_datos_url(meta["datos"])
        if not data:
            return None

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

    print("\n3) Predicción Llanera:")
    pred = get_prediccion_llanera()
    if pred:
        print(f"   Municipio: {pred.get('nombre', 'N/A')}")
    else:
        print("   N/A")
