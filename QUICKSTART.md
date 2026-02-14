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
AI_MODEL=gpt-4o
AI_FALLBACK_MODEL=gpt-4o-mini
WEB_HOST=127.0.0.1
WEB_PORT=8000
AEMET_API_KEY=tu_aemet_key  # Recomendado (gratis en opendata.aemet.es)
```

## 🔐 Seguridad de tokens

- Si alguna clave se ha mostrado por terminal/chat, regénérala antes de subir a GitHub o desplegar.
- Variables sensibles típicas: `GITHUB_TOKEN`, `AEMET_API_KEY`, `WINDY_POINT_FORECAST_API_KEY`, `WINDY_MAP_FORECAST_API_KEY`.
- Mantén `.env` fuera de git y comparte solo `.env.example`.

## 3) Ejecuta la web

```bash
python web_app.py
```

Abre en navegador:

- http://127.0.0.1:8000

## 🔁 Política de actualización

La app refresca internamente la información en ciclos:
- 06:00
- 10:00
- 14:00
- 18:00
- 22:00

Zona horaria: Europe/Madrid.
