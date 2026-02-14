#!/bin/bash

# Script de instalación para despliegue en producción de LEMR Meteo
# Ejecutar con: sudo bash install-production.sh

set -e

echo "🛩️ Instalación de LEMR Meteo en producción"
echo "============================================"
echo ""

# Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Por favor ejecuta este script como root (sudo bash install-production.sh)"
    exit 1
fi

# Variables configurables
INSTALL_DIR="/var/www/lemr-meteo"
SERVICE_PORT="8001"
PYTHON_BIN="python3"

# Obtener el directorio actual (donde está el repo)
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📁 Directorio del repositorio: $REPO_DIR"
echo "📁 Directorio de instalación: $INSTALL_DIR"
echo ""

# Paso 1: Instalar dependencias del sistema
echo "📦 Instalando dependencias del sistema..."
apt update
apt install -y python3 python3-pip python3-venv apache2

# Paso 2: Copiar archivos si no estamos ya en /var/www
if [ "$REPO_DIR" != "$INSTALL_DIR" ]; then
    echo "📋 Copiando archivos a $INSTALL_DIR..."
    mkdir -p /var/www
    cp -r "$REPO_DIR" "$INSTALL_DIR"
else
    echo "✓ Ya estamos en el directorio de instalación"
fi

cd "$INSTALL_DIR"

# Paso 3: Crear entorno virtual
echo "🐍 Creando entorno virtual..."
$PYTHON_BIN -m venv venv
source venv/bin/activate

# Paso 4: Instalar dependencias Python
echo "📦 Instalando dependencias Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo "📦 Instalando Gunicorn (servidor de producción)..."
pip install gunicorn==21.2.0

# Paso 5: Configurar .env si no existe
if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo "⚙️ Creando archivo .env..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANTE: Debes editar $INSTALL_DIR/.env con tus credenciales"
    echo "   Usa: sudo nano $INSTALL_DIR/.env"
    echo ""
else
    echo "✓ Archivo .env ya existe"
fi

# Paso 6: Ajustar permisos
echo "🔒 Ajustando permisos..."
chown -R www-data:www-data "$INSTALL_DIR"
chmod 600 "$INSTALL_DIR/.env"

# Paso 7: Instalar servicio systemd
echo "⚙️ Instalando servicio systemd..."
cp "$INSTALL_DIR/lemr-meteo.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable lemr-meteo

# Paso 8: Habilitar módulos Apache
echo "🌐 Configurando Apache..."
a2enmod proxy
a2enmod proxy_http

echo ""
echo "✅ Instalación completada!"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Edita las credenciales: sudo nano $INSTALL_DIR/.env"
echo "   2. Inicia el servicio: sudo systemctl start lemr-meteo"
echo "   3. Verifica el estado: sudo systemctl status lemr-meteo"
echo "   4. Configura Apache VirtualHost MANUALMENTE (ver ejemplos abajo)"
echo "   5. Instala SSL: sudo certbot --apache -d tudominio.com"
echo ""
echo "📡 Nota: El servicio usa Gunicorn (servidor de producción) automáticamente"
echo "      Ya no verás warnings sobre 'development server'"
echo ""
echo "📚 Configuración de Apache (TIENES QUE HACERLO MANUALMENTE):"
echo "   Ver ejemplos en: $INSTALL_DIR/apache-vhost.example.conf"
echo "   O usa el script interactivo: sudo bash deploy-interactive.sh"
echo ""
echo "💡 Consejo: Si quieres que Apache se configure automáticamente,"
echo "   usa mejor: sudo bash deploy-interactive.sh"
echo ""
