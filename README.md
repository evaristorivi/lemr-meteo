![Portada](portada.png)

# 🛩️ LEMR Meteo Web · La Morgal

## 🌐 **[Ver aplicación en vivo →](https://lemr-meteo.evaristorivieccio.com)**

Web moderna para pilotos ULM de La Morgal (Asturias), con:
- METAR de LEAS como referencia cercana
- Predicción local para LEMR (hoy, mañana y pasado mañana)
- Mapa AEMET incrustado por día
- Interpretación IA para novatos (centrada en Asturias/La Morgal)
- Actualización automática **cada 15 min** para condiciones en tiempo real (METAR LEAS + Open-Meteo) y **cada hora** para análisis IA completo (06:00 - 23:00 · Europe/Madrid)

## ✨ Qué hace esta aplicación

- Web moderna con interfaz responsive y dark theme.
- Combina Open-Meteo + METAR LEAS + análisis IA para inferir condiciones en LEMR.
- Incluye reglas operativas de La Morgal en el prompt de IA:
  - Invierno: 09:00 a 20:00
  - Verano: 09:00 a 21:45
- Las recomendaciones de “mejor hora” se limitan a horario diurno y horario del campo.

## 📍 Datos operativos de La Morgal

- Nombre: Aeródromo de La Morgal
- ICAO: LEMR
- Coordenadas: 43 25.833 N / 05 49.617 O
- Radio: 123.500
- Elevación: 545 ft / 180 m
- Pista: 10/28 · 890 m · asfalto

## 🚀 Arranque rápido

```bash
pip install -r requirements.txt
copy .env.example .env
```

Edita `.env` y define como mínimo:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=tu_key_de_aistudio
WEB_HOST=127.0.0.1
WEB_PORT=8000  # Para desarrollo local
```

> 📚 **Nota sobre modelos IA:** El sistema usa Gemini vía Google AI Studio y prueba automáticamente la cascada definida en `config.py` (`gemini-3.6-flash` → `gemini-3.5-flash` → `gemini-3.5-flash-lite` → `gemini-3.1-flash-lite` → `gemini-3-flash-preview` → `gemini-3.8-flash` → `gemini-3.7-flash`). Los dos últimos son los modelos más nuevos pero con alta demanda (503) en el tier gratuito; se dejan al final para no ralentizar cada análisis. No necesitas configurar los modelos uno a uno.


**Muy recomendado** (gratis en https://opendata.aemet.es):

```env
AEMET_API_KEY=tu_aemet_key
```

Sin esto funcionarán los mapas AEMET pero no las predicciones textuales de Asturias. La predicción de 4 días de La Morgal siempre está disponible (usa Open-Meteo).

**Opcional** — alertas en Telegram cuando falla alguna fuente o modelo IA:

```env
TELEGRAM_BOT_TOKEN=123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=123456789
```

Crea el bot con `@BotFather`, obtén el `chat_id` visitando `https://api.telegram.org/bot<TOKEN>/getUpdates`. Si no se configura, el sistema funciona con normalidad sin enviar alertas. Ver [DEPLOYMENT.md](DEPLOYMENT.md#-alertas-telegram-opcional) para la lista completa de eventos monitorizados.

Recomendación para publicación/despliegue:
- Regenera todos los tokens/claves si han estado expuestos (`GEMINI_API_KEY`, `AEMET_API_KEY`, `WINDY_POINT_FORECAST_API_KEY`).
- No subas nunca `.env` al repositorio (usa solo `.env.example`).

Ejecuta:

```bash
python web_app.py
```

Abre:

- http://127.0.0.1:8000

## 🧠 IA y mapas

La web muestra tres tipos de mapas AEMET. El **servidor** los descarga una sola
vez, los guarda en `cache/` y los sirve desde su propio dominio; el navegador
del usuario nunca se conecta a AEMET (así no le afecta el anti-bot de
ama.aemet.es). No necesitan `AEMET_API_KEY`.

| Mapa | Origen | Se sirve en | Se guarda |
|------|--------|-------------|-----------|
| Significativo SIGWX Península (SFC–FL150) | `ama.aemet.es/.../QGQE70LEMM{HH}00________{YYYYMMDD}.png` | `/sigwx/AAAAMMDD/HH.png` | ayer, hoy y mañana (00/06/12/18 UTC) |
| Viento y temperatura FL020/050/100 (HMAR) | `ama.aemet.es/.../atap/.../VTPLOT_FL{NNN}__.1.png` | `/vtplot/<pasada>/<nivel>/<paso>.png` | hoy y mañana, cada 3 h, pasada más reciente |
| Análisis en superficie (frentes) | página `www.aemet.es/es/eltiempo/prediccion/mapa_frentes` | `/analisis/AAAAMMDDHH.gif` | solo el último |

- Un hilo de la app revisa cada 5 min qué falta y lo descarga (~4 descargas/día de SIGWX, ~36 por pasada HMAR, la página de frentes como mucho cada 30 min).
- Lo que ya no se muestra se borra solo: la caché ocupa unos 10 MB estables.
- Las peticiones se identifican como `LEMR-Meteo/1.0`. Si AEMET bloquea al servidor (HTTP 403), **no** se suplanta un navegador: llega una alerta Telegram y hay que contactar con AEMET.
- Las imágenes llevan el pie "© AEMET… citando a AEMET como autora": no recortarlo (es la condición de reutilización).
- La carpeta de caché debe ser escribible por el usuario del servicio (ver [DEPLOYMENT.md](DEPLOYMENT.md#los-mapas-aemet-no-aparecen)). Se puede cambiar con `SIGWX_CACHE_DIR`, `VTPLOT_CACHE_DIR` y `ANALISIS_CACHE_DIR` en `.env`.

La `AEMET_API_KEY` (OpenData) se sigue usando para los avisos CAP de Asturias
que lee la IA y como respaldo del mapa de análisis.

Además, la IA analiza el mapa para pilotos novatos y lo traduce a impacto operativo ULM en La Morgal.

## 🌐 Despliegue en producción (servidor con Apache)

> 📚 **[Ver guía completa de despliegue paso a paso →](DEPLOYMENT.md)**

### 🎯 Opción recomendada: Script interactivo

```bash
# En tu servidor (SSH)
cd /var/www
sudo git clone https://github.com/tu-usuario/lemr-meteo.git
cd lemr-meteo
sudo bash deploy-interactive.sh
```

> 💡 **Tip:** Si ya has clonado el repo en otra ubicación, puedes ejecutar el script desde ahí y él se encargará de copiar los archivos a `/var/www/lemr-meteo` automáticamente.

**Este script te guiará paso a paso** preguntándote:
- ✅ Dominio o subdominio
- ✅ Tipo de instalación (subdominio dedicado vs subdirectorio)
- ✅ Puerto de la aplicación
- ✅ Credenciales (Gemini API key, AEMET API)
- ✅ Detecta y hace backup de configuraciones Apache existentes
- ✅ Verifica que todo funcione correctamente

**¡Todo de forma segura sin sobreescribir tu configuración actual!**

### Opción alternativa: Script básico (sin configurar Apache)

```bash
# En tu servidor (SSH)
cd /var/www
sudo git clone https://github.com/tu-usuario/lemr-meteo.git
cd lemr-meteo
sudo bash install-production.sh
```

**Solo instala la aplicación**, NO configura Apache automáticamente:
- ✅ Instala dependencias (Python, Apache, Gunicorn)
- ✅ Crea entorno virtual
- ✅ Instala servicio systemd
- ✅ Configura permisos
- ❌ **NO configura Apache** (lo haces tú manualmente)

Después necesitas:
1. Editar el archivo `.env` con tus credenciales
2. **Configurar Apache VirtualHost MANUALMENTE** (ver ejemplos abajo)
3. Iniciar el servicio: `sudo systemctl start lemr-meteo`

> 💡 **Recomendación:** Usa mejor `deploy-interactive.sh` que lo hace todo automáticamente.

### Instalación manual (paso a paso)

Si prefieres hacerlo manualmente o el script da problemas:

### Requisitos del servidor

- Python 3.8 o superior
- Apache con `mod_proxy` y `mod_proxy_http`
- Git (para clonar el repositorio)

### Paso 1: Preparar el servidor

```bash
# En tu servidor (SSH)
cd /var/www
sudo git clone https://github.com/tu-usuario/lemr-meteo.git
cd lemr-meteo

# Instalar dependencias Python
sudo apt update
sudo apt install python3-pip python3-venv -y

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Paso 2: Configurar el entorno

```bash
# Copiar y editar el archivo de configuración
cp .env.example .env
nano .env
```

Configura las variables para producción:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=tu_key_de_aistudio
AEMET_API_KEY=tu_api_key_aemet
WEB_HOST=127.0.0.1
WEB_PORT=8001
```

> 📚 El sistema usa cascada automática de modelos IA.


### Paso 3: Crear servicio systemd

Usa el archivo incluido `lemr-meteo.service` como plantilla:

```bash
sudo cp lemr-meteo.service /etc/systemd/system/
sudo nano /etc/systemd/system/lemr-meteo.service
```

Activar el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable lemr-meteo
sudo systemctl start lemr-meteo
sudo systemctl status lemr-meteo
```

### Paso 4: Configurar Apache como proxy reverso

Habilita los módulos necesarios:

```bash
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo systemctl restart apache2
```

Puedes usar el archivo `apache-vhost.example.conf` como referencia. 

**Opción A: Subdominio dedicado** (ej: `meteo.tudominio.com`)

Crea `/etc/apache2/sites-available/meteo.tudominio.com.conf`:

```apache
<VirtualHost *:80>
    ServerName meteo.tudominio.com
    
    # Proxy para la aplicación Flask
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8001/
    ProxyPassReverse / http://127.0.0.1:8001/
    
    # Logs
    ErrorLog ${APACHE_LOG_DIR}/lemr-meteo-error.log
    CustomLog ${APACHE_LOG_DIR}/lemr-meteo-access.log combined
</VirtualHost>
```

**Opción B: Subdirectorio en dominio existente** (ej: `tudominio.com/meteo`)

Edita tu VirtualHost actual de WordPress y añade:

```apache
<VirtualHost *:80>
    ServerName tudominio.com
    
    # Tu WordPress existente
    DocumentRoot /var/www/html
    
    # Subdirectorio para LEMR Meteo
    ProxyPass /meteo http://127.0.0.1:8001/
    ProxyPassReverse /meteo http://127.0.0.1:8001/
    
    # Resto de configuración WordPress...
</VirtualHost>
```

Activa el sitio y recarga Apache:

```bash
# Solo si usaste Opción A (subdominio dedicado)
sudo a2ensite meteo.tudominio.com.conf

# En ambos casos, recarga Apache
sudo systemctl reload apache2
```

### Paso 5: SSL con Let's Encrypt (Recomendado)

```bash
sudo apt install certbot python3-certbot-apache -y
sudo certbot --apache -d meteo.tudominio.com
```

### Verificar el despliegue

- Comprueba que el servicio está corriendo: `sudo systemctl status lemr-meteo`
- Verifica los logs: `sudo journalctl -u lemr-meteo -f`
- Accede desde el navegador: `http://meteo.tudominio.com`

### Actualizar la aplicación

```bash
cd /var/www/lemr-meteo
sudo git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart lemr-meteo
```

## 📁 Estructura

- `web_app.py`: backend Flask + caché por ciclos
- `templates/index.html`: UI moderna
- `ai_service.py`: prompts y análisis IA (METAR, previsión y mapa)
- `metar_service.py`: METAR/TAF
- `weather_service.py`: Open-Meteo
- `config.py`: configuración y metadatos del campo

## ⚠️ Nota de seguridad operacional

La salida de la IA es un apoyo a las decisiones, no sustituyen al briefing oficial ni al manual de vuelo del ULM.
Ante duda, **NO VOLAR**.

---

## ⚠️ Aviso legal

Proyecto personal y experimental desarrollado por [Evaristo R.](https://www.evaristorivieccio.com/) para investigar aplicaciones de IA en meteorología.

Aunque utiliza datos de fuentes oficiales, los análisis generados por IA **no constituyen información oficial** y pueden contener errores.

Este sitio no está afiliado ni respaldado por LEMR, La Morgal ni ninguna entidad oficial.  
Contenido únicamente informativo y educativo.

El uso de la información se realiza bajo responsabilidad del usuario.

---
