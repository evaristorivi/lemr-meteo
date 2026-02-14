# 🛩️ LEMR Meteo Web · La Morgal

Web moderna para pilotos ULM de La Morgal (Asturias), con:
- METAR de LEAS como referencia cercana
- Predicción local para LEMR (hoy, mañana y pasado mañana)
- Mapa AEMET incrustado por día
- Interpretación IA para novatos (centrada en Asturias/La Morgal)
- Actualización automática **5 veces al día** (06:00, 10:00, 14:00, 18:00, 22:00 · Europe/Madrid)

## ✨ Qué hace esta versión

- Sustituye el enfoque de Telegram por una interfaz web.
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
AI_PROVIDER=github
GITHUB_TOKEN=tu_token
AI_MODEL=gpt-4o
AI_FALLBACK_MODEL=gpt-4o-mini
WEB_HOST=127.0.0.1
WEB_PORT=8000
```

**Muy recomendado** (gratis en https://opendata.aemet.es):

```env
AEMET_API_KEY=tu_aemet_key
```

Sin esto funcionarán los mapas AEMET pero no las predicciones textuales de Asturias y Llanera.

Recomendación para publicación/despliegue:
- Regenera todos los tokens/claves si han estado expuestos (`GITHUB_TOKEN`, `AEMET_API_KEY`, `WINDY_POINT_FORECAST_API_KEY`, `WINDY_MAP_FORECAST_API_KEY`).
- No subas nunca `.env` al repositorio (usa solo `.env.example`).

Ejecuta:

```bash
python web_app.py
```

Abre:

- http://127.0.0.1:8000

## 🧠 IA y mapas

La web muestra mapas AEMET por día usando la plantilla:

- `https://ama.aemet.es/o/estaticos/bbdd/imagenes/QGQE70LEMM1800________YYYYMMDD.png`

Además, la IA analiza el mapa para pilotos novatos y lo traduce a impacto operativo ULM en La Morgal.

## 🌐 Despliegue en producción (servidor con Apache)

> 📚 **[Ver guía completa de despliegue paso a paso →](DEPLOYMENT.md)**

### 🎯 Opción recomendada: Script interactivo

```bash
# En tu servidor (SSH)
cd /ruta/donde/clonaste/lemr-meteo
sudo bash deploy-interactive.sh
```

**Este script te guiará paso a paso** preguntándote:
- ✅ Dominio o subdominio
- ✅ Tipo de instalación (subdominio dedicado vs subdirectorio)
- ✅ Puerto de la aplicación
- ✅ Credenciales (GitHub token, AEMET API)
- ✅ Detecta y hace backup de configuraciones Apache existentes
- ✅ Verifica que todo funcione correctamente

**¡Todo de forma segura sin sobreescribir tu configuración actual!**

### Opción alternativa: Script automatizado básico

```bash
# En tu servidor (SSH)
cd /ruta/donde/clonaste/lemr-meteo
sudo bash install-production.sh
```

El script instalará automáticamente:
- Dependencias del sistema (Python, Apache)
- Entorno virtual y dependencias Python
- Servicio systemd
- Configurará permisos

Después solo necesitas:
1. Editar el archivo `.env` con tus credenciales
2. Configurar Apache VirtualHost manualmente (ver ejemplos abajo)
3. Iniciar el servicio: `sudo systemctl start lemr-meteo`

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
AI_PROVIDER=github
GITHUB_TOKEN=tu_token_regenerado
AI_MODEL=gpt-4o
AI_FALLBACK_MODEL=gpt-4o-mini
AEMET_API_KEY=tu_api_key_aemet
WEB_HOST=127.0.0.1
WEB_PORT=8001
```

**⚠️ Importante:** Usa un puerto diferente al de WordPress (típicamente 80/443), como 8001.

### Paso 3: Crear servicio systemd

Usa el archivo incluido `lemr-meteo.service` como plantilla:

```bash
sudo cp lemr-meteo.service /etc/systemd/system/
sudo nano /etc/systemd/system/lemr-meteo.service
```

Ajusta las rutas si es necesario. Contenido del archivo:

```ini
[Unit]
Description=LEMR Meteo Web Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/lemr-meteo
Environment="PATH=/var/www/lemr-meteo/venv/bin"
ExecStart=/var/www/lemr-meteo/venv/bin/python web_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
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

La salida es apoyo a la decisión, no sustituye briefing oficial ni manual de vuelo del ULM.
Ante duda, **NO VOLAR**.
