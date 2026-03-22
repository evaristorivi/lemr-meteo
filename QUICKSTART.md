# 🚀 Inicio Rápido (Web)

## 1) Instala dependencias

```bash
pip install -r requirements.txt
```

## 2) Configura entorno

```bash
copy .env.example .env
```

Configura `.env` con al menos:

```env
AI_PROVIDER=github
GITHUB_TOKEN=tu_token_github
WEB_HOST=127.0.0.1
WEB_PORT=8000  # Para desarrollo local
AEMET_API_KEY=tu_aemet_key  # Recomendado (gratis en opendata.aemet.es)
```

> 🤖 **Modelos IA:** El sistema usa cascada automática (no necesitas configurar nada).


## 🔐 Seguridad de tokens

- Si alguna clave se ha mostrado por terminal/chat, regénérala antes de subir a GitHub o desplegar.
- Variables sensibles típicas: `GITHUB_TOKEN`, `AEMET_API_KEY`, `WINDY_POINT_FORECAST_API_KEY`.
- Mantén `.env` fuera de git y comparte solo `.env.example`.

## 3) Ejecuta la web

```bash
python web_app.py
```

Abre en navegador:

- http://127.0.0.1:8000

## � Despliegue en producción

Para desplegarlo en un servidor con Apache:

```bash
# Script interactivo que lo hace todo (recomendado)
sudo bash deploy-interactive.sh
```

Ver [DEPLOYMENT.md](DEPLOYMENT.md) para más detalles.

## �🔁 Política de actualización

La app tiene dos frecuencias de refresco independientes:

- **Cada 15 min** — METAR LEAS (oficial), condiciones actuales Open-Meteo y METAR sintético LEMR (viento, temp, nubosidad, visibilidad). Sin coste de IA.
- **Cada hora** (06:00 – 23:00) — Análisis completo: veredicto IA, pronóstico 4 días, Windy Point Forecast, mapas AEMET.

Zona horaria: Europe/Madrid.
