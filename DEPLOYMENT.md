# 🚀 Guía Rápida de Despliegue en Producción

Esta guía te ayudará a desplegar LEMR Meteo en tu servidor con Apache.

> ✅ **[Usa este checklist para no olvidar ningún paso →](DEPLOYMENT-CHECKLIST.md)**

## 📋 Pre-requisitos

- Servidor Linux (Ubuntu/Debian recomendado)
- Apache instalado y funcionando
- Acceso SSH con permisos sudo
- Dominio o subdominio configurado (ej: `meteo.tudominio.com`)

## 🎯 Instalación Rápida con Script Interactivo (Recomendado)

### 🌟 Opción 1: Script Interactivo (¡Más fácil y seguro!)

```bash
ssh tu-usuario@tu-servidor.com
cd /var/www
sudo git clone https://github.com/tu-usuario/lemr-meteo.git
cd lemr-meteo
sudo bash deploy-interactive.sh
```

> 💡 **Nota:** El script detecta automáticamente si ya estás en `/var/www/lemr-meteo` (recomendado) o si necesita copiar archivos desde otra ubicación. Si ejecutas una actualización y el directorio ya existe, te dará opciones claras.

**El script interactivo te preguntará todo** y configurará automáticamente:
- ✅ Te pregunta el tipo de instalación (subdominio o subdirectorio)
- ✅ Te pregunta el dominio/subdominio
- ✅ Te pregunta el puerto
- ✅ Te pide las credenciales (GitHub token, AEMET API)
- ✅ **Detecta configuraciones Apache existentes y hace backup automático**
- ✅ Instala dependencias, crea el servicio, configura Apache
- ✅ Verifica que todo funcione
- ✅ Te da un resumen completo al final

**¡Listo en 5 minutos!** No necesitas configurar nada manualmente.

---

### 🔧 Opción 2: Script Automatizado Básico

Si prefieres configurar Apache manualmente después:

```bash
ssh tu-usuario@tu-servidor.com
cd /var/www
sudo git clone https://github.com/tu-usuario/lemr-meteo.git
cd lemr-meteo
sudo bash install-production.sh
```

El script instalará todo lo necesario automáticamente.

**Después necesitarás configurar Apache manualmente** (ver más abajo).

### 3️⃣ Configurar credenciales

> **Nota:** Si usaste el script interactivo (`deploy-interactive.sh`), ya tienes esto configurado. Salta al paso de verificación.

Edita el archivo `.env` con tus datos:

```bash
sudo nano /var/www/lemr-meteo/.env
```

Variables **obligatorias**:

```env
# Token de GitHub (gratis)
GITHUB_TOKEN=ghp_tu_token_aqui

# Puerto para la app (no usar 80 o 443, Apache los usa)
WEB_PORT=8001
WEB_HOST=127.0.0.1

# Modelo de IA
AI_PROVIDER=github
AI_MODEL=gpt-4o
AI_FALLBACK_MODEL=gpt-4o-mini
```

Variables **opcionales** pero recomendadas:

```env
# API de AEMET (gratis en https://opendata.aemet.es)
# SIN ESTO: faltarán predicciones textuales de Asturias y Llanera
# CON ESTO: tendrás predicciones oficiales AEMET completas
AEMET_API_KEY=tu_aemet_key_aqui
```

Guarda con `Ctrl+O`, `Enter`, `Ctrl+X`.

### 4️⃣ Iniciar el servicio

```bash
sudo systemctl start lemr-meteo
sudo systemctl status lemr-meteo
```

Deberías ver: **`Active: active (running)`** ✅

Si hay errores, revisa los logs:
```bash
sudo journalctl -u lemr-meteo -f
```

### 5️⃣ Configurar Apache

Tienes **dos opciones**:

#### Opción A: Subdominio dedicado (`meteo.tudominio.com`)

```bash
sudo nano /etc/apache2/sites-available/meteo.tudominio.com.conf
```

Pega esto (cambia `meteo.tudominio.com` por tu dominio):

```apache
<VirtualHost *:80>
    ServerName meteo.tudominio.com
    
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8001/
    ProxyPassReverse / http://127.0.0.1:8001/
    
    ErrorLog ${APACHE_LOG_DIR}/lemr-meteo-error.log
    CustomLog ${APACHE_LOG_DIR}/lemr-meteo-access.log combined
</VirtualHost>
```

Activa el sitio:

```bash
sudo a2ensite meteo.tudominio.com.conf
sudo systemctl reload apache2
```

#### Opción B: Subdirectorio en dominio existente (`tudominio.com/meteo`)

Edita tu VirtualHost existente:

```bash
sudo nano /etc/apache2/sites-available/tudominio.com.conf
```

**Añade estas líneas** dentro del `<VirtualHost>`, antes de cerrar `</VirtualHost>`:

```apache
    # LEMR Meteo
    <Location /meteo>
        ProxyPass http://127.0.0.1:8001/
        ProxyPassReverse http://127.0.0.1:8001/
    </Location>
</VirtualHost>
```

Recarga Apache:

```bash
sudo systemctl reload apache2
```

## 🔒 Seguridad: Instalar certificado SSL

```bash
sudo apt install certbot python3-certbot-apache -y
sudo certbot --apache -d meteo.tudominio.com
```

Certbot configurará HTTPS automáticamente.

## ✅ Verificar que funciona

1. Abre tu navegador
2. Ve a: `http://meteo.tudominio.com` (o `http://tudominio.com/meteo`)
3. Deberías ver la web de LEMR Meteo funcionando

## 🔧 Comandos útiles

```bash
# Ver estado del servicio
sudo systemctl status lemr-meteo

# Reiniciar el servicio
sudo systemctl restart lemr-meteo

# Ver logs en tiempo real
sudo journalctl -u lemr-meteo -f

# Actualizar la aplicación (después de hacer git pull)
cd /var/www/lemr-meteo
sudo git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart lemr-meteo
```

## ❌ Solución de problemas comunes

### El servicio no arranca

```bash
# Ver el error exacto
sudo journalctl -u lemr-meteo --no-pager -n 50

# Revisar permisos
sudo chown -R www-data:www-data /var/www/lemr-meteo
```

### Apache da error 502 Bad Gateway

- Verifica que el servicio está corriendo: `sudo systemctl status lemr-meteo`
- Verifica que el puerto en `.env` coincide con el del VirtualHost (8001)
- Comprueba que Apache tiene los módulos proxy habilitados:
  ```bash
  sudo a2enmod proxy
  sudo a2enmod proxy_http
  sudo systemctl restart apache2
  ```

### No aparece nada al acceder a la URL

- Verifica que el DNS apunta a tu servidor
- Si usas subdirectorio, asegúrate de que la ruta `/meteo` está correctamente configurada
- Revisa los logs de Apache: `sudo tail -f /var/log/apache2/error.log`

## 📚 Más información

Ver [README.md](README.md) para documentación completa.

## ❓ Preguntas frecuentes (FAQs)

### ¿Por qué usar el puerto 8001 si luego no se usa?

El puerto 8001 es **interno**, solo accesible dentro del servidor. Apache lo usa para comunicarse con la app, pero desde internet **solo se accede por los puertos 80/443** que Apache gestiona. Es una configuración estándar de seguridad.

### ¿Puedo usar otro puerto en vez de 8001?

Sí, cualquier puerto libre entre 8000-9000. Cambia `WEB_PORT` en el `.env` y ajusta el VirtualHost de Apache para que apunte al mismo puerto.

### ¿Necesito un dominio/subdominio propio para LEMR Meteo?

No necesariamente. Puedes usar:
- Un subdirectorio: `tudominio.com/meteo` (más fácil)
- Un subdominio: `meteo.tudominio.com` (más profesional, requiere configurar DNS)

### ¿Consume muchos recursos?

No. LEMR Meteo es una app Flask ligera que:
- Cachea los datos meteorológicos
- Solo actualiza 5 veces al día (06:00, 10:00, 14:00, 18:00, 22:00)
- Usa muy poca memoria (~50-100 MB)

### ¿Puedo usar la app sin AEMET_API_KEY?

Sí, pero **perderás funcionalidades**:
- ✅ **Funcionarán**: METAR, predicción Open-Meteo, análisis IA, mapas significativos AEMET
- ❌ **NO funcionarán**: Predicciones textuales oficiales de AEMET para Asturias y Llanera

La API de AEMET es **gratuita** (regístrate en https://opendata.aemet.es). Se recomienda usarla para obtener todas las funcionalidades.

## 🆘 ¿Necesitas ayuda?

Revisa los logs:
```bash
# Logs del servicio Python
sudo journalctl -u lemr-meteo -f

# Logs de Apache
sudo tail -f /var/log/apache2/error.log
sudo tail -f /var/log/apache2/lemr-meteo-error.log
```
