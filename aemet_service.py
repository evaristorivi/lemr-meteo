"""
Servicio de acceso a AEMET OpenData API.
Obtiene mapas significativos, mapas de análisis y observaciones convencionales.

Flujo AEMET en dos pasos:
  1) Llamada autenticada → JSON con campo "datos" (URL temporal)
  2) GET a esa URL temporal → contenido real (imagen PNG, JSON, etc.)
"""
import base64
import os
import re
import tempfile
import threading
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
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


# ──────── Mapas significativos SIGWX (caché en servidor) ────────
# El SERVIDOR descarga cada mapa UNA sola vez de ama.aemet.es, lo guarda en
# disco y lo sirve desde nuestro propio dominio (/sigwx/AAAAMMDD/HH.png). El
# navegador del usuario nunca toca ama.aemet.es, así que no le afecta el WAF
# anti-bot ni sus cookies.
#
# Patrón de AEMET:  QGQE70LEMM{HH}00________{YYYYMMDD}.png  (HH = emisión UTC)
# Validez = emisión + 12 h (verificado 2026-11-05 con el pie del propio mapa).
# Los botones son horas de VALIDEZ: 12 UTC del día D = fichero 0000 del día D, 00 UTC del día D =
# fichero 1200 del día D-1, etc.
#
# ⚠️ NO se usa la API OpenData para estos mapas: su endpoint
# /api/mapasygraficos/mapassignificativos/ devuelve 404 casi siempre
# (verificado 2026-03-23).
#
# Peticiones honestas: User-Agent identificativo y sin seguir redirecciones.
# Si AEMET bloquea al servidor (403 / redirección al reto del WAF) NO se
# intenta esquivar suplantando un navegador: se registra y se avisa por
# Telegram. ~4 descargas al día en total.
AMA_MAP_BASE = "https://ama.aemet.es/o/estaticos/bbdd/imagenes"
SIG_MAP_UTC_HOURS = ("00", "06", "12", "18")
SIGWX_DAYS = ((-1, "Ayer"), (0, "Hoy"), (1, "Mañana"))

# Horas que tarda AEMET en publicar un mapa tras su hora nominal de emisión.
SIG_MAP_PUBLISH_LAG_H = float(getattr(config, "SIG_MAP_PUBLISH_LAG_H", 3))
SIGWX_CACHE_DIR = Path(getattr(config, "SIGWX_CACHE_DIR", "")
                       or Path(__file__).resolve().parent / "cache" / "sigwx")

_SIGWX_USER_AGENT = "LEMR-Meteo/1.0 (+https://lemr-meteo.evaristorivieccio.com/)"
# La sincronización va alineada con el ciclo horario del informe (ver
# start_ama_sync_thread): una vez por hora, solo en las horas del ciclo, este
# margen después de la hora en punto.
_AMA_SLOT_DELAY_S = 60
_DEFAULT_SYNC_SLOTS = tuple(range(6, 24))  # = web_app.UPDATE_SLOTS (06:00-23:00 Madrid)
_SIGWX_RETRY_S = 15 * 60          # espera mínima entre reintentos de un mismo mapa
_SIGWX_ALERT_AFTER_H = 3          # falta un mapa X h después de su publicación → aviso
_SIGWX_ALERT_EVERY_S = 6 * 3600   # como mucho un aviso cada 6 h
_SIGWX_MAX_BYTES = 5 * 1024 * 1024
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_SIGWX_FILE_RE = re.compile(r"^(\d{8})_(\d{2})\.png$")

_SIGWX_LOCK = threading.Lock()
_SIGWX_LAST_ATTEMPT: Dict[str, float] = {}
_SIGWX_LAST_ERROR: Dict[str, str] = {}
_SIGWX_LAST_ALERT = 0.0

# Contador de peticiones AEMET OpenData (para monitoring)
_AEMET_REQUEST_COUNT = 0


def get_aemet_request_count() -> int:
    """Devuelve el número de peticiones AEMET realizadas desde el inicio."""
    return _AEMET_REQUEST_COUNT


def _direct_sig_map_url(issue_date: date, issue_hour: str) -> str:
    """URL de ama.aemet.es de un mapa significativo, por fecha/hora de EMISIÓN."""
    return (
        f"{AMA_MAP_BASE}/QGQE70LEMM{issue_hour}00________"
        f"{issue_date.strftime('%Y%m%d')}.png"
    )


def _sigwx_slots(now_utc: Optional[datetime] = None) -> List[Dict]:
    """Slots de ayer/hoy/mañana por hora UTC de validez (sin peticiones HTTP)."""
    now_utc = now_utc or datetime.now(timezone.utc)
    today = datetime.now(MADRID_TZ).date()
    slots = []
    for offset, label in SIGWX_DAYS:
        d = today + timedelta(days=offset)
        for hh in SIG_MAP_UTC_HOURS:
            valid = datetime(d.year, d.month, d.day, int(hh), tzinfo=timezone.utc)
            issue = valid - timedelta(hours=12)
            due_at = issue + timedelta(hours=SIG_MAP_PUBLISH_LAG_H)
            slots.append({
                "key": f"{d:%Y%m%d}_{hh}",
                "date": d,
                "label": label,
                "offset": offset,
                "utc_hour": hh,
                "valid": valid,
                "due_at": due_at,
                "due": due_at <= now_utc,
                "source_url": _direct_sig_map_url(issue.date(), f"{issue.hour:02d}"),
            })
    return slots


def _sigwx_path(key: str) -> Path:
    return SIGWX_CACHE_DIR / f"{key}.png"


def _ama_download(url: str, dest: Path, signature: bytes = _PNG_SIGNATURE) -> Optional[str]:
    """Descarga una imagen de AEMET a dest (escritura atómica), comprobando que
    empieza por `signature` (PNG por defecto). None si OK o el motivo del fallo."""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": _SIGWX_USER_AGENT, "Accept": "image/*"},
            timeout=20,
            stream=True,
            allow_redirects=False,  # una redirección = reto del WAF, no un mapa
        )
    except Exception as exc:
        return f"error de red: {exc}"
    try:
        if resp.status_code != 200:
            return f"HTTP {resp.status_code}"
        data = bytearray()
        for chunk in resp.iter_content(64 * 1024):
            data.extend(chunk)
            if len(data) > _SIGWX_MAX_BYTES:
                return "respuesta demasiado grande"
    finally:
        resp.close()
    if not bytes(data).startswith(signature):
        return "la respuesta no es la imagen esperada (¿página del WAF?)"

    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".tmp")
        tmp.write_bytes(bytes(data))
        os.replace(tmp, dest)  # atómico: nunca se sirve un fichero a medias
    except OSError as exc:
        return f"no se pudo escribir en {dest.parent}: {exc}"
    return None


# ── Estado de conexión con ama.aemet.es ──
# Si las descargas dejan de obtener respuesta y más tarde vuelven a obtenerla,
# se avisa una vez por Telegram. El estado se guarda en disco para que un
# reinicio del servicio no lo pierda.
_AMA_STATUS_FILE = Path(tempfile.gettempdir()) / "lemr_ama_status"
_AMA_STATUS_LOCK = threading.Lock()
_AMA_LAST_ERROR: Optional[str] = None


def _ama_responded(err: Optional[str]) -> Optional[bool]:
    """¿Contestó ama.aemet.es? True/False, o None si el resultado no lo aclara."""
    if err is None or err == "HTTP 404" or err.startswith(
            ("no se pudo escribir", "respuesta demasiado grande")):
        return True   # hubo respuesta del servidor (aunque no hubiera fichero)
    if err.startswith(("error de red", "la respuesta no es")) or \
            re.fullmatch(r"HTTP (3\d\d|403)", err):
        return False
    return None       # p. ej. 5xx: no indica nada sobre la conexión


def _ama_fetch(url: str, dest: Path) -> Optional[str]:
    """_ama_download para ama.aemet.es, registrando el estado de la conexión."""
    global _AMA_LAST_ERROR
    err = _ama_download(url, dest)
    if err is not None and err != "HTTP 404":
        _AMA_LAST_ERROR = err
    ok = _ama_responded(err)
    if ok is None:
        return err
    new = "ok" if ok else "ko"
    with _AMA_STATUS_LOCK:
        try:
            prev = _AMA_STATUS_FILE.read_text().strip()
        except OSError:
            prev = ""
        if new == prev:
            return err
        try:
            _AMA_STATUS_FILE.write_text(new)
        except OSError:
            pass
    print(f"ℹ️ ama.aemet.es: {'responde' if ok else 'sin respuesta'} ({err or 'OK'})")
    if ok and prev == "ko":
        from telegram_monitor import send_alert as _tg_alert_ama
        _tg_alert_ama(
            "✅ ama.aemet.es vuelve a responder a las descargas del servidor.",
            source="aemet_ama",
            level="WARNING",
        )
    return err


def _sigwx_purge(keep_keys: set) -> None:
    """Borra de la caché lo que ya no pertenece a ayer/hoy/mañana."""
    if not SIGWX_CACHE_DIR.is_dir():
        return
    for f in SIGWX_CACHE_DIR.iterdir():
        if f.name.endswith(".tmp") or (
            _SIGWX_FILE_RE.match(f.name) and f.stem not in keep_keys
        ):
            try:
                f.unlink()
            except OSError as exc:
                print(f"⚠️ SIGWX: no se pudo borrar {f.name}: {exc}")


def sync_sigwx_cache() -> Dict[str, int]:
    """Descarga los mapas ya publicados que falten en la caché y purga los viejos."""
    global _SIGWX_LAST_ALERT
    if not _SIGWX_LOCK.acquire(blocking=False):
        return {"skipped": 1}
    try:
        now = time.time()
        slots = _sigwx_slots()
        stats = {"downloaded": 0, "failed": 0, "cached": 0}
        for slot in slots:
            if _sigwx_path(slot["key"]).exists():
                stats["cached"] += 1
                continue
            if not slot["due"]:
                continue
            if now - _SIGWX_LAST_ATTEMPT.get(slot["key"], 0) < _SIGWX_RETRY_S:
                continue
            _SIGWX_LAST_ATTEMPT[slot["key"]] = now
            err = _ama_fetch(slot["source_url"], _sigwx_path(slot["key"]))
            if err is None:
                stats["downloaded"] += 1
                _SIGWX_LAST_ERROR.pop(slot["key"], None)
                print(f"✅ SIGWX descargado {slot['key']} ← {slot['source_url']}")
                continue
            stats["failed"] += 1
            _SIGWX_LAST_ERROR[slot["key"]] = err
            print(f"⚠️ SIGWX {slot['key']}: {err} ({slot['source_url']})")

        _sigwx_purge({s["key"] for s in slots})

        # Aviso si faltan mapas de hoy/mañana que ya deberían estar disponibles
        late_limit = datetime.now(timezone.utc) - timedelta(hours=_SIGWX_ALERT_AFTER_H)
        missing = [s["key"] for s in slots
                   if s["offset"] >= 0 and s["due_at"] < late_limit
                   and not _sigwx_path(s["key"]).exists()]
        if missing and now - _SIGWX_LAST_ALERT > _SIGWX_ALERT_EVERY_S:
            _SIGWX_LAST_ALERT = now
            from telegram_monitor import send_alert as _tg_alert_maps
            _tg_alert_maps(
                "Mapas significativos AEMET no disponibles "
                f"{_SIGWX_ALERT_AFTER_H} h después de su publicación: "
                + ", ".join(missing)
                + (f". Último error de descarga: {_AMA_LAST_ERROR}" if _AMA_LAST_ERROR else ""),
                source="aemet_sig_maps",
                level="ERROR",
            )
        stats["missing"] = len(missing)
        return stats
    except Exception as exc:
        print(f"❌ SIGWX sync error: {exc}")
        return {"error": 1}
    finally:
        _SIGWX_LOCK.release()


def get_sigwx_listing() -> List[Dict]:
    """
    Estado actual de los mapas SIGWX (lee el disco, sin peticiones HTTP).

    Returns:
        [{date, label, slots: [{utc_hour, valid_utc, status, url, source_url}]}]
        status: 'available' (en caché, url = /sigwx/AAAAMMDD/HH.png),
                'pending' (AEMET aún no lo ha publicado) o
                'missing' (debería estar publicado pero no se pudo descargar).
    """
    days: Dict[str, Dict] = {}
    for slot in _sigwx_slots():
        day = days.setdefault(slot["date"].isoformat(), {
            "date": slot["date"].isoformat(),
            "label": slot["label"],
            "slots": [],
        })
        cached = _sigwx_path(slot["key"]).exists()
        status = "available" if cached else ("missing" if slot["due"] else "pending")
        day["slots"].append({
            "utc_hour": slot["utc_hour"],
            "valid_utc": slot["valid"].isoformat(),
            "status": status,
            "url": f"/sigwx/{slot['date']:%Y%m%d}/{slot['utc_hour']}.png" if cached else None,
            "source_url": slot["source_url"],
        })
    return list(days.values())


def sigwx_file_path(yyyymmdd: str, utc_hour: str) -> Optional[Path]:
    """Ruta en disco de un mapa en caché, validando la entrada (sin path traversal)."""
    if not re.fullmatch(r"\d{8}", yyyymmdd or "") or utc_hour not in SIG_MAP_UTC_HOURS:
        return None
    path = _sigwx_path(f"{yyyymmdd}_{utc_hour}")
    return path if path.is_file() else None


# ───── Viento y temperatura en niveles de vuelo (VTPLOT, modelo HMAR) ─────
# Misma estrategia que los SIGWX: el servidor descarga cada imagen UNA vez y
# la sirve desde /vtplot/<pasada>/<nivel>/<paso>.png. Antes el navegador de
# cada visitante sondeaba cientos de URLs de ama.aemet.es (8 pasadas x 12
# pasos x nivel), justo lo que dispara el WAF anti-bot.
#
# Patrón: atap/{YYYYMMDD}/HMAR/{HH}/P3/{PPP}/VTPLOT_FL{NNN}__.1.png
#   HH  = pasada del modelo (00, 06, 12, 18 UTC)
#   PPP = alcance en horas (003..036 de 3 en 3) → validez = pasada + PPP
# AEMET publica cada pasada por partes (verificado 2026-11-05 18:20 UTC: la
# de 12Z tenía +003 pero aún no +036; la de 18Z, nada). Por eso, para cada
# hora de validez se usa la pasada MÁS RECIENTE que ya tenga esa imagen y, si
# aún no está, la anterior.
VTPLOT_LEVELS = ("020", "050", "100")
VTPLOT_STEPS = tuple(f"{h:03d}" for h in range(3, 37, 3))
VTPLOT_RUN_HOURS = (0, 6, 12, 18)
VTPLOT_DAYS = ((0, "Hoy"), (1, "Mañana"))
VTPLOT_CACHE_DIR = Path(getattr(config, "VTPLOT_CACHE_DIR", "")
                        or SIGWX_CACHE_DIR.parent / "vtplot")
_VTPLOT_RUN_LAG_H = 3            # antes de esto ni se pregunta por una pasada
_VTPLOT_STALE_H = 9              # imagen más reciente con más de X h → aviso (pasada nueva cada 6 h)
_VTPLOT_FILE_RE = re.compile(r"^(\d{10})$")

_VTPLOT_LOCK = threading.Lock()
_VTPLOT_RUN_PUBLISHED: set = set()          # pasadas confirmadas (YYYYMMDDHH)
_VTPLOT_LAST_ATTEMPT: Dict[str, float] = {}  # pasada o fichero → último intento
_VTPLOT_LAST_ALERT = 0.0


def _vtplot_source_url(run: datetime, level: str, step: str) -> str:
    return (
        "https://ama.aemet.es/o/estaticos/productos/atap/"
        f"{run:%Y%m%d}/HMAR/{run:%H}/P3/{step}/VTPLOT_FL{level}__.1.png"
    )


def _vtplot_path(run_key: str, level: str, step: str) -> Path:
    return VTPLOT_CACHE_DIR / run_key / f"{level}_{step}.png"


def _vtplot_valid_times() -> List[datetime]:
    today = datetime.now(MADRID_TZ).date()
    out = []
    for offset, _ in VTPLOT_DAYS:
        d = today + timedelta(days=offset)
        for h in range(0, 24, 3):
            out.append(datetime(d.year, d.month, d.day, h, tzinfo=timezone.utc))
    return out


def _vtplot_candidate_runs(now_utc: datetime) -> List[datetime]:
    """Pasadas que pueden cubrir hoy/mañana y que ya podrían estar publicadas."""
    first_valid = _vtplot_valid_times()[0]
    start = first_valid - timedelta(hours=36)
    start = start.replace(hour=(start.hour // 6) * 6, minute=0, second=0, microsecond=0)
    runs, r = [], start
    while r + timedelta(hours=_VTPLOT_RUN_LAG_H) <= now_utc:
        runs.append(r)
        r += timedelta(hours=6)
    return list(reversed(runs))  # la más reciente primero


def _vtplot_run_published(run: datetime, now: float) -> bool:
    """¿Ha empezado AEMET a publicar la pasada? 1 petición, con reintento cada 15 min."""
    key = f"{run:%Y%m%d%H}"
    if key in _VTPLOT_RUN_PUBLISHED:
        return True
    probe = _vtplot_path(key, VTPLOT_LEVELS[0], VTPLOT_STEPS[0])
    run_dir = VTPLOT_CACHE_DIR / key
    if probe.exists() or (run_dir.is_dir() and any(run_dir.glob("*.png"))):
        _VTPLOT_RUN_PUBLISHED.add(key)  # ya hay imágenes suyas en caché: no hace falta preguntar
        return True
    if now - _VTPLOT_LAST_ATTEMPT.get(key, 0) < _SIGWX_RETRY_S:
        return False
    _VTPLOT_LAST_ATTEMPT[key] = now
    err = _ama_fetch(_vtplot_source_url(run, VTPLOT_LEVELS[0], VTPLOT_STEPS[0]), probe)
    if err is None:
        _VTPLOT_RUN_PUBLISHED.add(key)
        print(f"✅ VTPLOT pasada {key} publicada")
        return True
    return False


def _vtplot_select(now_utc: datetime, download: bool) -> Dict:
    """
    Para cada (validez, nivel) elige la pasada más reciente con imagen. Si
    download=True descarga lo que falte (solo de pasadas ya publicadas).
    Devuelve {(valid, level): (run_key, step)}.
    """
    now = time.time()
    runs = _vtplot_candidate_runs(now_utc)
    if download:
        published = [r for r in runs if _vtplot_run_published(r, now)]
        # olvida pasadas que ya no pueden cubrir hoy/mañana
        _VTPLOT_RUN_PUBLISHED.intersection_update(f"{r:%Y%m%d%H}" for r in runs)
    else:
        published = runs  # solo lectura: basta con lo que haya en disco
    selection = {}
    for valid in _vtplot_valid_times():
        for level in VTPLOT_LEVELS:
            for run in published:
                hours = int((valid - run).total_seconds() // 3600)
                step = f"{hours:03d}"
                if step not in VTPLOT_STEPS:
                    continue
                run_key = f"{run:%Y%m%d%H}"
                path = _vtplot_path(run_key, level, step)
                if path.exists():
                    selection[(valid, level)] = (run_key, step)
                    break
                if not download:
                    continue
                fkey = f"{run_key}/{level}_{step}"
                if now - _VTPLOT_LAST_ATTEMPT.get(fkey, 0) < _SIGWX_RETRY_S:
                    continue  # falló hace poco (p. ej. aún no publicado): usar la anterior
                _VTPLOT_LAST_ATTEMPT[fkey] = now
                if _ama_fetch(_vtplot_source_url(run, level, step), path) is None:
                    selection[(valid, level)] = (run_key, step)
                    break
    return selection


def sync_vtplot_cache() -> Dict[str, int]:
    """Descarga las imágenes VTPLOT que falten para hoy/mañana y purga las demás."""
    global _VTPLOT_LAST_ALERT
    if not _VTPLOT_LOCK.acquire(blocking=False):
        return {"skipped": 1}
    try:
        now_utc = datetime.now(timezone.utc)
        selection = _vtplot_select(now_utc, download=True)

        # Purga: solo se conservan los ficheros que se están usando
        keep = {(rk, f"{lv}_{st}.png") for (_, lv), (rk, st) in selection.items()}
        if VTPLOT_CACHE_DIR.is_dir():
            for run_dir in VTPLOT_CACHE_DIR.iterdir():
                if not (run_dir.is_dir() and _VTPLOT_FILE_RE.match(run_dir.name)):
                    continue
                for f in run_dir.iterdir():
                    if (run_dir.name, f.name) not in keep:
                        try:
                            f.unlink()
                        except OSError as exc:
                            print(f"⚠️ VTPLOT: no se pudo borrar {f}: {exc}")
                try:
                    run_dir.rmdir()  # solo si ha quedado vacía
                except OSError:
                    pass

        # Aviso si la imagen más reciente de la caché está desactualizada
        mtimes = [f.stat().st_mtime for f in VTPLOT_CACHE_DIR.glob("*/*.png")] \
            if VTPLOT_CACHE_DIR.is_dir() else []
        age_h = (time.time() - max(mtimes)) / 3600 if mtimes else None
        if (age_h is None or age_h > _VTPLOT_STALE_H) and \
                time.time() - _VTPLOT_LAST_ALERT > _SIGWX_ALERT_EVERY_S:
            _VTPLOT_LAST_ALERT = time.time()
            from telegram_monitor import send_alert as _tg_alert_fl
            _tg_alert_fl(
                "Mapas de viento/temperatura FL AEMET sin actualizar"
                + (f" desde hace {age_h:.0f} h" if age_h is not None else " (no hay ninguno)")
                + (f". Último error de descarga: {_AMA_LAST_ERROR}" if _AMA_LAST_ERROR else ""),
                source="aemet_vtplot",
                level="ERROR",
            )
        return {"maps": len(selection), "runs": len(_VTPLOT_RUN_PUBLISHED),
                "age_h": None if age_h is None else round(age_h, 1)}
    except Exception as exc:
        print(f"❌ VTPLOT sync error: {exc}")
        return {"error": 1}
    finally:
        _VTPLOT_LOCK.release()


def get_vtplot_listing() -> Dict:
    """
    Estado de los mapas VTPLOT en caché (sin peticiones HTTP).

    Returns:
        {levels: [...], days: [{date, label, slots: [{utc_hour, valid_utc,
         maps: {nivel: {url, run} | None}}]}]}
    """
    selection = _vtplot_select(datetime.now(timezone.utc), download=False)
    labels = dict(VTPLOT_DAYS)
    today = datetime.now(MADRID_TZ).date()
    days: Dict[str, Dict] = {}
    for valid in _vtplot_valid_times():
        offset = (valid.date() - today).days
        day = days.setdefault(valid.date().isoformat(), {
            "date": valid.date().isoformat(), "label": labels.get(offset, ""), "slots": [],
        })
        maps = {}
        for level in VTPLOT_LEVELS:
            sel = selection.get((valid, level))
            maps[level] = None if sel is None else {
                "url": f"/vtplot/{sel[0]}/{level}/{sel[1]}.png",
                "run": f"{sel[0][-2:]}Z",
            }
        day["slots"].append({
            "utc_hour": f"{valid:%H}", "valid_utc": valid.isoformat(), "maps": maps,
        })
    return {"levels": list(VTPLOT_LEVELS), "days": list(days.values())}


def vtplot_file_path(run_key: str, level: str, step: str) -> Optional[Path]:
    """Ruta en disco de una imagen VTPLOT en caché, validando la entrada."""
    if (not _VTPLOT_FILE_RE.match(run_key or "") or level not in VTPLOT_LEVELS
            or step not in VTPLOT_STEPS):
        return None
    path = _vtplot_path(run_key, level, step)
    return path if path.is_file() else None


def _ama_sync_once() -> None:
    """Una pasada de sincronización de los tres mapas (nunca lanza excepción)."""
    for sync in (sync_sigwx_cache, sync_vtplot_cache, sync_analysis_cache):
        try:
            sync()
        except Exception as exc:  # el hilo debe sobrevivir a cualquier fallo
            print(f"❌ {sync.__name__} error: {exc}")


def _seconds_until_next_slot(slots) -> float:
    """Segundos hasta la próxima hora de `slots` (Europe/Madrid) + _AMA_SLOT_DELAY_S."""
    now = datetime.now(MADRID_TZ)
    for add_days in range(3):
        d = now.date() + timedelta(days=add_days)
        for h in sorted(slots):
            t = (datetime(d.year, d.month, d.day, h, tzinfo=MADRID_TZ)
                 + timedelta(seconds=_AMA_SLOT_DELAY_S))
            if t > now:
                return t.timestamp() - time.time()  # vía timestamp: correcto en cambios de hora
    return 3600.0


def _ama_sync_loop(slots) -> None:
    # Al arrancar (despliegue/reinicio) dentro del horario: rellena la caché ya,
    # sin esperar a la próxima hora en punto. Fuera del horario no hace nada.
    if datetime.now(MADRID_TZ).hour in slots:
        _ama_sync_once()
    while True:
        wait = max(1.0, _seconds_until_next_slot(slots))
        time.sleep(wait)
        _ama_sync_once()


def start_ama_sync_thread(slots=None) -> None:
    """
    Arranca (una vez por proceso) el hilo que mantiene las cachés de mapas.
    Sincroniza una vez por hora, alineado con el ciclo del informe: en cada
    hora de `slots` (por defecto 06-23, Europe/Madrid) + 1 min. Fuera de esas
    horas no hace ninguna petición a AEMET.
    """
    global _AMA_THREAD_STARTED
    if _AMA_THREAD_STARTED:
        return
    _AMA_THREAD_STARTED = True
    slots = tuple(slots) if slots else _DEFAULT_SYNC_SLOTS
    threading.Thread(target=_ama_sync_loop, args=(slots,), name="ama-sync",
                     daemon=True).start()


_AMA_THREAD_STARTED = False


# ─────────────────────────── Mapa de análisis ──────────────────────────────
# Fuente principal: página pública www.aemet.es/es/eltiempo/prediccion/mapa_frentes
# (sin api key). Publica el análisis como
#   /imagenes_d/eltiempo/prediccion/mapa_frentes/{YYYYMMDDHH}+000_<sufijo>.gif
# El sufijo no es predecible, así que se lee la página una vez por ciclo horario
# del informe (robots.txt permite la ruta) y, si hay un análisis nuevo, se
# descarga UNA vez a disco y se sirve desde /analisis/{YYYYMMDDHH}.gif.
# Respaldo: OpenData con AEMET_API_KEY, solo si la web falla y no hay caché.
AEMET_WEB_BASE = "https://www.aemet.es"
_FRENTES_PAGE = f"{AEMET_WEB_BASE}/es/eltiempo/prediccion/mapa_frentes"
_FRENTES_RE = re.compile(
    r"/?(imagenes_d/eltiempo/prediccion/mapa_frentes/(\d{10})\+000_[A-Za-z0-9_]+\.gif)"
)
_GIF_SIGNATURE = b"GIF8"
ANALISIS_CACHE_DIR = Path(getattr(config, "ANALISIS_CACHE_DIR", "")
                          or SIGWX_CACHE_DIR.parent / "analisis")
# < 1 h: como mucho una lectura por ciclo horario aunque la pidan el informe
# y el hilo de mapas en el mismo ciclo.
_ANALISIS_PAGE_TTL_S = 50 * 60
_ANALISIS_ALERT_AFTER_H = 24
_ANALISIS_KEY_RE = re.compile(r"^\d{10}$")

_ANALISIS_LOCK = threading.Lock()
_ANALISIS_STATE: Dict = {"checked_at": 0.0, "key": None, "source_url": None}
_ANALISIS_LAST_ALERT = 0.0


def _analisis_cached_key() -> Optional[str]:
    """Clave (YYYYMMDDHH) del análisis más reciente en disco, o None."""
    if not ANALISIS_CACHE_DIR.is_dir():
        return None
    keys = sorted(f.stem for f in ANALISIS_CACHE_DIR.glob("*.gif")
                  if _ANALISIS_KEY_RE.match(f.stem))
    return keys[-1] if keys else None


def sync_analysis_cache() -> Dict[str, object]:
    """Lee la página de frentes (máx. una vez por ciclo) y descarga el análisis si es nuevo."""
    global _ANALISIS_LAST_ALERT
    if not _ANALISIS_LOCK.acquire(blocking=False):
        return {"skipped": 1}
    try:
        now = time.time()
        if now - _ANALISIS_STATE["checked_at"] < _ANALISIS_PAGE_TTL_S:
            return {"cached": _analisis_cached_key()}
        _ANALISIS_STATE["checked_at"] = now

        error = None
        try:
            resp = requests.get(_FRENTES_PAGE, headers={"User-Agent": _SIGWX_USER_AGENT},
                                timeout=15, allow_redirects=False)
            match = _FRENTES_RE.search(resp.text) if resp.status_code == 200 else None
        except Exception as exc:
            match, error = None, f"error de red: {exc}"
        if match:
            key = match.group(2)
            source_url = f"{AEMET_WEB_BASE}/{match.group(1)}"
            dest = ANALISIS_CACHE_DIR / f"{key}.gif"
            if not dest.exists():
                error = _ama_download(source_url, dest, signature=_GIF_SIGNATURE)
                if error is None:
                    print(f"✅ Mapa análisis descargado {key} ← {source_url}")
            if dest.exists():
                _ANALISIS_STATE.update(key=key, source_url=source_url)
                for f in ANALISIS_CACHE_DIR.glob("*.gif*"):  # solo se guarda el último
                    if f != dest:
                        try:
                            f.unlink()
                        except OSError as exc:
                            print(f"⚠️ Análisis: no se pudo borrar {f.name}: {exc}")
        elif error is None:
            error = f"patrón no encontrado en la página (HTTP {resp.status_code})"
        if error:
            print(f"⚠️ Mapa análisis (www.aemet.es): {error}")

        cached = _analisis_cached_key()
        age_h = (None if cached is None else
                 (datetime.now(timezone.utc) - datetime.strptime(cached, "%Y%m%d%H")
                  .replace(tzinfo=timezone.utc)).total_seconds() / 3600)
        if (age_h is None or age_h > _ANALISIS_ALERT_AFTER_H) and \
                now - _ANALISIS_LAST_ALERT > _SIGWX_ALERT_EVERY_S:
            _ANALISIS_LAST_ALERT = now
            from telegram_monitor import send_alert as _tg_alert_an
            _tg_alert_an(
                "Mapa de análisis AEMET (www.aemet.es) sin actualizar"
                + (f" desde hace {age_h:.0f} h" if age_h is not None else "")
                + f": {error or 'sin análisis nuevo'}. Se usa OpenData como respaldo.",
                source="aemet_maps",
                level="WARNING",
            )
        return {"cached": cached, "error": error}
    finally:
        _ANALISIS_LOCK.release()


def get_analysis_map_url() -> Optional[str]:
    """
    URL pública del mapa de análisis, para la IA (OpenAI la descarga ella misma).
    Principal: GIF de www.aemet.es. Respaldo: URL temporal de OpenData (api key).
    """
    if _ANALISIS_STATE["source_url"] and _analisis_cached_key() == _ANALISIS_STATE["key"]:
        return _ANALISIS_STATE["source_url"]
    return _opendata_analysis_url()


def get_analysis_map_display() -> Optional[str]:
    """
    Lo que el navegador pone en el <img> del mapa de análisis: nuestra ruta
    /analisis/{YYYYMMDDHH}.gif si está en caché; si no, data URI de OpenData.

    Se llama al generar el informe de cada ciclo horario: antes comprueba si
    hay un análisis nuevo (máx. una lectura de la página por ciclo gracias al
    TTL), para que el informe no salga con el de la hora anterior.
    """
    sync_analysis_cache()
    key = _analisis_cached_key()
    if key:
        return f"/analisis/{key}.gif"
    print("⚠️ Mapa análisis: sin caché de www.aemet.es, usando OpenData (api key)")
    return _opendata_analysis_b64()


def analysis_file_path(key: str) -> Optional[Path]:
    """Ruta en disco del análisis en caché, validando la entrada."""
    if not _ANALISIS_KEY_RE.match(key or ""):
        return None
    path = ANALISIS_CACHE_DIR / f"{key}.gif"
    return path if path.is_file() else None


# ── Respaldo: OpenData (requiere api key) ──

def _opendata_analysis_url() -> Optional[str]:
    meta = _aemet_get("/api/mapasygraficos/analisis")
    if meta and meta.get("datos"):
        return meta["datos"]  # URL temporal: https://opendata.aemet.es/opendata/sh/XXX
    return None


def _opendata_analysis_b64() -> Optional[str]:
    """Mapa de análisis de OpenData como data URI (1 llamada + 1 descarga)."""
    temp_url = _opendata_analysis_url()
    if not temp_url:
        return None
    raw_bytes = _fetch_datos_url(temp_url, timeout=20, as_bytes=True)
    if not raw_bytes or len(raw_bytes) < 1000:
        print("❌ No se pudo descargar el mapa de análisis de OpenData")
        return None
    print(f"✅ Mapa análisis (OpenData): {len(raw_bytes)} bytes")
    return "data:image/png;base64," + base64.b64encode(raw_bytes).decode("ascii")


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

    print(f"\n2) Mapas significativos SIGWX (caché en {SIGWX_CACHE_DIR}):")
    print(f"   sync: {sync_sigwx_cache()}")
    for day in get_sigwx_listing():
        estado = " ".join(f"{s['utc_hour']}:{s['status']}" for s in day["slots"])
        print(f"   {day['label']:7} {day['date']}  {estado}")

    print(f"\n2b) VTPLOT viento/temperatura FL (caché en {VTPLOT_CACHE_DIR}):")
    print(f"   sync: {sync_vtplot_cache()}")
    for day in get_vtplot_listing()["days"]:
        for lv in VTPLOT_LEVELS:
            estado = " ".join(f"{s['utc_hour']}:{(s['maps'][lv] or {}).get('run', '--')}" for s in day["slots"])
            print(f"   {day['label']:7} FL{lv}  {estado}")

    print("\n3) Predicción Llanera:")
    pred = get_prediccion_llanera()
    if pred:
        print(f"   Municipio: {pred.get('nombre', 'N/A')}")
    else:
        print("   N/A")
