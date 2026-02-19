"""
Sistema de monitorización vía Telegram para LEMR-Meteo.

Envía alertas cuando hay errores reales en fuentes de datos o en el análisis IA.
Anti-spam: máximo 1 alerta por fuente cada 30 minutos.

Configurar en .env:
    TELEGRAM_BOT_TOKEN=<token de @BotFather>
    TELEGRAM_CHAT_ID=<tu chat_id (puede ser negativo para grupos)>
"""
import time
import traceback
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import requests as _requests

_MADRID_TZ = ZoneInfo("Europe/Madrid")

# Anti-spam: guarda timestamp del último envío por fuente
_last_alert: dict[str, float] = {}
_MIN_INTERVAL = 1800  # 30 minutos entre alertas de la misma fuente


def send_alert(
    message: str,
    source: str = "general",
    level: str = "ERROR",
    exc: Optional[Exception] = None,
) -> bool:
    """
    Envía un mensaje de alerta al bot de Telegram.

    Args:
        message:  Descripción del error.
        source:   Identificador de la fuente ('openmeteo', 'windy', 'aemet', 'ia', 'general').
        level:    'ERROR' o 'WARNING'.
        exc:      Excepción opcional — se incluye el traceback.

    Returns:
        True si el mensaje se envió correctamente.
    """
    # Importación diferida para evitar ciclo al cargar config
    try:
        import config
        token = getattr(config, "TELEGRAM_BOT_TOKEN", "") or ""
        chat_id = getattr(config, "TELEGRAM_CHAT_ID", "") or ""
    except Exception:
        return False

    if not token or not chat_id:
        # No configurado, silencio total
        return False

    # Anti-spam
    now = time.time()
    if now - _last_alert.get(source, 0) < _MIN_INTERVAL:
        print(f"📵 Telegram: alerta suprimida por anti-spam (fuente={source})")
        return False
    _last_alert[source] = now

    # Construir texto
    now_str = datetime.now(_MADRID_TZ).strftime("%Y-%m-%d %H:%M")
    emoji = "🔴" if level == "ERROR" else "🟠"
    lines = [
        f"{emoji} *LEMR\\-METEO {level}*",
        f"🕐 `{now_str}`  \\|  fuente: `{source}`",
        "",
        _escape_md(message),
    ]
    if exc:
        tb = traceback.format_exc()
        # Limitar a las últimas 3 líneas del traceback
        tb_short = "\n".join(tb.strip().splitlines()[-4:])
        lines += ["", f"```\n{tb_short[:500]}\n```"]

    text = "\n".join(lines)

    try:
        resp = _requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "MarkdownV2",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            print(f"📱 Telegram: alerta enviada (fuente={source})")
            return True
        else:
            print(f"⚠️ Telegram HTTP {resp.status_code}: {resp.text[:120]}")
            return False
    except Exception as send_exc:
        print(f"⚠️ Telegram send_alert falló: {send_exc}")
        return False


def _escape_md(text: str) -> str:
    """Escapa caracteres reservados de MarkdownV2."""
    reserved = r"\_*[]()~`>#+-=|{}.!"
    for ch in reserved:
        text = text.replace(ch, f"\\{ch}")
    return text
