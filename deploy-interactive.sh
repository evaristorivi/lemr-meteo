#!/bin/bash

# Script de despliegue interactivo para LEMR Meteo
# Ejecutar con: sudo bash deploy-interactive.sh

set -e

# Colores para mensajes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Sin color

# Variables
INSTALL_DIR="/var/www/lemr-meteo"
SERVICE_PORT="8001"
PYTHON_BIN="python3"
BACKUP_DIR="/var/backups/lemr-meteo-$(date +%Y%m%d-%H%M%S)"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   🛩️  LEMR METEO - Instalador Interactivo           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Por favor ejecuta este script como root${NC}"
    echo "   Usa: sudo bash deploy-interactive.sh"
    exit 1
fi

# Función para hacer preguntas
ask_question() {
    local question=$1
    local default=$2
    local response
    
    if [ -n "$default" ]; then
        read -p "$(echo -e ${YELLOW}"$question [$default]: "${NC})" response
        response=${response:-$default}
    else
        read -p "$(echo -e ${YELLOW}"$question: "${NC})" response
    fi
    
    echo "$response"
}

# Función para preguntas sí/no
ask_yes_no() {
    local question=$1
    local default=$2
    local response
    
    while true; do
        if [ "$default" = "y" ]; then
            read -p "$(echo -e ${YELLOW}"$question [S/n]: "${NC})" response
            response=${response:-y}
        else
            read -p "$(echo -e ${YELLOW}"$question [s/N]: "${NC})" response
            response=${response:-n}
        fi
        
        case "$response" in
            [yYsS]* ) return 0 ;;
            [nN]* ) return 1 ;;
            * ) echo -e "${RED}Por favor responde s (sí) o n (no)${NC}" ;;
        esac
    done
}

# Función para verificar si existe un sitio de Apache
check_apache_site() {
    local site_name=$1
    
    if [ -f "/etc/apache2/sites-available/${site_name}.conf" ]; then
        return 0
    fi
    return 1
}

# Función para hacer backup
make_backup() {
    local file=$1
    mkdir -p "$BACKUP_DIR"
    
    if [ -d "$file" ]; then
        # Es un directorio
        cp -r "$file" "$BACKUP_DIR/"
        echo -e "${GREEN}✓ Backup guardado: $BACKUP_DIR/$(basename $file)${NC}"
    elif [ -f "$file" ]; then
        # Es un archivo
        cp "$file" "$BACKUP_DIR/"
        echo -e "${GREEN}✓ Backup guardado: $BACKUP_DIR/$(basename $file)${NC}"
    else
        echo -e "${RED}❌ Error: $file no existe${NC}"
        return 1
    fi
}

# ============================================
# PASO 1: Recopilar información
# ============================================

echo -e "${BLUE}┌────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│  Paso 1: Configuración inicial        │${NC}"
echo -e "${BLUE}└────────────────────────────────────────┘${NC}"
echo ""

# Preguntar por el tipo de instalación
echo "¿Cómo quieres acceder a la aplicación?"
echo "  1) Subdominio dedicado (ej: meteo.tudominio.com)"
echo "  2) Subdirectorio (ej: tudominio.com/meteo)"
echo ""

INSTALL_TYPE=""
while [ -z "$INSTALL_TYPE" ]; do
    read -p "$(echo -e ${YELLOW}"Opción [1/2]: "${NC})" option
    case "$option" in
        1) INSTALL_TYPE="subdomain" ;;
        2) INSTALL_TYPE="subdirectory" ;;
        *) echo -e "${RED}Por favor elige 1 o 2${NC}" ;;
    esac
done

echo ""

# Preguntar por el dominio
if [ "$INSTALL_TYPE" = "subdomain" ]; then
    DOMAIN=$(ask_question "Introduce el subdominio completo (ej: meteo.tudominio.com)" "meteo.ejemplo.com")
    SITE_NAME="$DOMAIN"
    PATH_PREFIX="/"
else
    DOMAIN=$(ask_question "Introduce el dominio principal (ej: tudominio.com)" "ejemplo.com")
    SUBDIRECTORY=$(ask_question "Introduce el nombre del subdirectorio" "meteo")
    SITE_NAME="$DOMAIN"
    PATH_PREFIX="/$SUBDIRECTORY"
fi

echo ""

# Verificar si ya existe una configuración
if check_apache_site "$SITE_NAME"; then
    echo -e "${YELLOW}⚠️  Ya existe una configuración de Apache para: $SITE_NAME${NC}"
    echo ""
    
    if [ "$INSTALL_TYPE" = "subdomain" ]; then
        echo "El archivo existe en: /etc/apache2/sites-available/${SITE_NAME}.conf"
        echo ""
        
        if ask_yes_no "¿Quieres hacer un backup y sobreescribirlo?" "n"; then
            OVERWRITE_CONFIG=true
            make_backup "/etc/apache2/sites-available/${SITE_NAME}.conf"
        else
            echo -e "${RED}❌ Instalación cancelada. No se modificará la configuración existente.${NC}"
            echo ""
            echo "Si quieres modificar manualmente la configuración:"
            echo "  sudo nano /etc/apache2/sites-available/${SITE_NAME}.conf"
            exit 1
        fi
    else
        echo "Archivo: /etc/apache2/sites-available/${SITE_NAME}.conf"
        echo ""
        echo -e "${YELLOW}En modo subdirectorio, necesitaremos MODIFICAR el archivo existente${NC}"
        echo "Se añadirán las líneas necesarias para $PATH_PREFIX"
        echo ""
        
        if ask_yes_no "¿Continuar? Se hará backup automático" "y"; then
            MODIFY_CONFIG=true
            make_backup "/etc/apache2/sites-available/${SITE_NAME}.conf"
        else
            echo -e "${RED}❌ Instalación cancelada${NC}"
            exit 1
        fi
    fi
else
    OVERWRITE_CONFIG=false
    MODIFY_CONFIG=false
fi

echo ""

# Preguntar por el puerto
SERVICE_PORT=$(ask_question "Puerto interno para la aplicación" "8001")

echo ""
echo -e "${GREEN}✓ Configuración recopilada:${NC}"
echo "  - Tipo: $([ "$INSTALL_TYPE" = "subdomain" ] && echo "Subdominio" || echo "Subdirectorio")"
echo "  - Dominio: $SITE_NAME"
echo "  - Ruta: $PATH_PREFIX"
echo "  - Puerto: $SERVICE_PORT"
echo ""

if ! ask_yes_no "¿Continuar con la instalación?" "y"; then
    echo -e "${RED}❌ Instalación cancelada${NC}"
    exit 1
fi

# ============================================
# PASO 2: Instalar dependencias
# ============================================

echo ""
echo -e "${BLUE}┌────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│  Paso 2: Instalando dependencias      │${NC}"
echo -e "${BLUE}└────────────────────────────────────────┘${NC}"
echo ""

echo "📦 Actualizando sistema..."
apt update -qq

echo "📦 Instalando Apache, Python y herramientas..."
apt install -y python3 python3-pip python3-venv apache2 curl >/dev/null 2>&1

echo -e "${GREEN}✓ Dependencias instaladas${NC}"

# ============================================
# PASO 3: Copiar aplicación
# ============================================

echo ""
echo -e "${BLUE}┌────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│  Paso 3: Instalando aplicación        │${NC}"
echo -e "${BLUE}└────────────────────────────────────────┘${NC}"
echo ""

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📁 Ubicación actual del script: $REPO_DIR"
echo "📁 Directorio de instalación destino: $INSTALL_DIR"
echo ""

if [ "$REPO_DIR" = "$INSTALL_DIR" ]; then
    echo -e "${GREEN}✓ El repositorio ya está en el directorio correcto${NC}"
    echo "  No es necesario copiar archivos."
elif [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}⚠️  El directorio $INSTALL_DIR ya existe${NC}"
    echo ""
    echo "Opciones:"
    echo "  1) Hacer backup y reemplazar con el contenido actual"
    echo "  2) Usar el directorio existente (no copiar nada)"
    echo "  3) Cancelar instalación"
    echo ""
    
    read -p "$(echo -e ${YELLOW}"Elige una opción [1/2/3]: "${NC})" install_option
    
    case "$install_option" in
        1)
            echo "📦 Haciendo backup del directorio existente..."
            make_backup "$INSTALL_DIR"
            rm -rf "$INSTALL_DIR"
            mkdir -p /var/www
            echo "📋 Copiando archivos nuevos..."
            cp -r "$REPO_DIR" "$INSTALL_DIR"
            echo -e "${GREEN}✓ Archivos copiados${NC}"
            ;;
        2)
            echo -e "${GREEN}✓ Usando directorio existente${NC}"
            ;;
        3)
            echo -e "${RED}❌ Instalación cancelada${NC}"
            exit 1
            ;;
        *)
            echo -e "${RED}Opción no válida. Instalación cancelada.${NC}"
            exit 1
            ;;
    esac
else
    echo "📋 Copiando archivos a $INSTALL_DIR..."
    mkdir -p /var/www
    cp -r "$REPO_DIR" "$INSTALL_DIR"
    echo -e "${GREEN}✓ Archivos copiados${NC}"
fi

cd "$INSTALL_DIR"

# Crear entorno virtual
echo "🐍 Creando entorno virtual Python..."
$PYTHON_BIN -m venv venv
source venv/bin/activate

echo "📦 Instalando dependencias Python..."
pip install --upgrade pip >/dev/null 2>&1
pip install -r requirements.txt >/dev/null 2>&1

echo "🚀 Instalando Gunicorn (servidor de producción)..."
pip install gunicorn==21.2.0 >/dev/null 2>&1

echo -e "${GREEN}✓ Aplicación instalada con Gunicorn${NC}"

# ============================================
# PASO 4: Configurar credenciales
# ============================================

echo ""
echo -e "${BLUE}┌────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│  Paso 4: Configuración de credenciales│${NC}"
echo -e "${BLUE}└────────────────────────────────────────┘${NC}"
echo ""

if [ -f "$INSTALL_DIR/.env" ]; then
    echo "⚠️  Ya existe un archivo .env"
    if ! ask_yes_no "¿Mantener el archivo existente?" "y"; then
        rm "$INSTALL_DIR/.env"
        CREATE_ENV=true
    else
        CREATE_ENV=false
    fi
else
    CREATE_ENV=true
fi

if [ "$CREATE_ENV" = true ]; then
    echo "⚙️ Creando archivo .env..."
    
    GEMINI_API_KEY=$(ask_question "API key de Gemini / Google AI Studio (obligatoria)" "")
    AEMET_KEY=$(ask_question "API Key de AEMET (opcional, Enter para omitir)" "")
    
    cat > "$INSTALL_DIR/.env" << EOF
# Configuración generada por deploy-interactive.sh
# $(date)

# Gemini API key (obligatoria)
GEMINI_API_KEY=$GEMINI_API_KEY

# Puerto y host
WEB_PORT=$SERVICE_PORT
WEB_HOST=127.0.0.1

# Proveedor de IA (cascada automática de modelos)
AI_PROVIDER=gemini

# AEMET API (opcional pero recomendado)
EOF
    
    if [ -n "$AEMET_KEY" ]; then
        echo "AEMET_API_KEY=$AEMET_KEY" >> "$INSTALL_DIR/.env"
    else
        echo "# AEMET_API_KEY=tu_key_aqui" >> "$INSTALL_DIR/.env"
    fi
    
    echo -e "${GREEN}✓ Archivo .env creado${NC}"
fi

# Ajustar permisos
chown -R www-data:www-data "$INSTALL_DIR"
chmod 600 "$INSTALL_DIR/.env"

# ============================================
# PASO 5: Configurar servicio systemd
# ============================================

echo ""
echo -e "${BLUE}┌────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│  Paso 5: Configurando servicio        │${NC}"
echo -e "${BLUE}└────────────────────────────────────────┘${NC}"
echo ""

# Actualizar el archivo de servicio systemd
if [ ! -f "/etc/systemd/system/lemr-meteo.service" ]; then
    echo "⚙️ Instalando servicio systemd..."
    cp "$INSTALL_DIR/lemr-meteo.service" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable lemr-meteo >/dev/null 2>&1
    echo -e "${GREEN}✓ Servicio configurado${NC}"
else
    echo "⚙️ Actualizando servicio systemd..."
    cp "$INSTALL_DIR/lemr-meteo.service" /etc/systemd/system/
    systemctl daemon-reload
    echo -e "${GREEN}✓ Servicio actualizado${NC}"
    
    if ask_yes_no "¿Reiniciar el servicio con la nueva configuración?" "y"; then
        systemctl restart lemr-meteo
    fi
fi

# ============================================
# PASO 6: Configurar Apache
# ============================================

echo ""
echo -e "${BLUE}┌────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│  Paso 6: Configurando Apache          │${NC}"
echo -e "${BLUE}└────────────────────────────────────────┘${NC}"
echo ""

# Habilitar módulos necesarios
echo "🌐 Habilitando módulos de Apache..."
a2enmod proxy >/dev/null 2>&1
a2enmod proxy_http >/dev/null 2>&1

if [ "$INSTALL_TYPE" = "subdomain" ]; then
    # Crear configuración para subdominio
    echo "📝 Creando configuración de VirtualHost..."
    
    cat > "/etc/apache2/sites-available/${SITE_NAME}.conf" << EOF
# LEMR Meteo - Configuración generada automáticamente
# $(date)
# Subdominio: $SITE_NAME

<VirtualHost *:80>
    ServerName $SITE_NAME
    
    # Proxy para la aplicación Flask
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:$SERVICE_PORT/
    ProxyPassReverse / http://127.0.0.1:$SERVICE_PORT/
    
    # Logs
    ErrorLog \${APACHE_LOG_DIR}/lemr-meteo-error.log
    CustomLog \${APACHE_LOG_DIR}/lemr-meteo-access.log combined
</VirtualHost>

# Después de instalar SSL con certbot, se creará automáticamente la versión HTTPS
EOF
    
    echo -e "${GREEN}✓ Configuración creada: /etc/apache2/sites-available/${SITE_NAME}.conf${NC}"
    
    # Habilitar sitio
    if a2ensite "$SITE_NAME" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Sitio habilitado${NC}"
    fi
    
else
    # Modificar configuración existente para subdirectorio
    echo "📝 Modificando configuración existente..."
    
    CONFIG_FILE="/etc/apache2/sites-available/${SITE_NAME}.conf"
    
    # Verificar si ya existe la configuración del proxy
    if grep -q "ProxyPass $PATH_PREFIX" "$CONFIG_FILE"; then
        echo -e "${YELLOW}⚠️  La configuración del proxy ya existe en el archivo${NC}"
    else
        # Buscar el </VirtualHost> y añadir antes de él
        PROXY_CONFIG="
    # LEMR Meteo - Añadido por deploy-interactive.sh $(date)
    <Location $PATH_PREFIX>
        ProxyPass http://127.0.0.1:$SERVICE_PORT/
        ProxyPassReverse http://127.0.0.1:$SERVICE_PORT/
    </Location>
"
        
        # Insertar antes del primer </VirtualHost>
        sed -i "0,/<\/VirtualHost>/s|<\/VirtualHost>|$PROXY_CONFIG\n</VirtualHost>|" "$CONFIG_FILE"
        
        echo -e "${GREEN}✓ Configuración añadida al archivo existente${NC}"
    fi
fi

# Verificar configuración de Apache
echo "🔍 Verificando configuración de Apache..."
if apache2ctl configtest >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Configuración válida${NC}"
else
    echo -e "${RED}❌ Error en la configuración de Apache${NC}"
    echo "Ejecuta: sudo apache2ctl configtest"
    exit 1
fi

# Reiniciar Apache
if ask_yes_no "¿Reiniciar Apache para aplicar cambios?" "y"; then
    systemctl restart apache2
    echo -e "${GREEN}✓ Apache reiniciado${NC}"
fi

# ============================================
# PASO 7: Iniciar servicio
# ============================================

echo ""
echo -e "${BLUE}┌────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│  Paso 7: Iniciando servicio           │${NC}"
echo -e "${BLUE}└────────────────────────────────────────┘${NC}"
echo ""

if systemctl is-active lemr-meteo >/dev/null 2>&1; then
    echo "✓ El servicio ya está activo"
    
    if ask_yes_no "¿Reiniciar el servicio?" "y"; then
        systemctl restart lemr-meteo
        echo -e "${GREEN}✓ Servicio reiniciado${NC}"
    fi
else
    echo "🚀 Iniciando servicio..."
    systemctl start lemr-meteo
    sleep 2
    
    if systemctl is-active lemr-meteo >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Servicio iniciado correctamente${NC}"
    else
        echo -e "${RED}❌ Error al iniciar el servicio${NC}"
        echo "Ver logs: sudo journalctl -u lemr-meteo -f"
        exit 1
    fi
fi

# ============================================
# RESUMEN FINAL
# ============================================

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅ Instalación completada exitosamente              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}📋 Resumen de la instalación:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📁 Directorio: $INSTALL_DIR"
echo "  🌐 Tipo: $([ "$INSTALL_TYPE" = "subdomain" ] && echo "Subdominio" || echo "Subdirectorio")"
echo "  🔗 URL: http://$SITE_NAME$PATH_PREFIX"
echo "  🔌 Puerto interno: $SERVICE_PORT"
echo "  ⚙️  Servicio: lemr-meteo (Gunicorn)"
echo "  🚀 Servidor: Gunicorn con 2 workers"

if [ -d "$BACKUP_DIR" ]; then
    echo "  💾 Backups: $BACKUP_DIR"
fi

echo ""
echo -e "${BLUE}🔍 Verificación:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verificar servicio
SERVICE_STATUS=$(systemctl is-active lemr-meteo)
if [ "$SERVICE_STATUS" = "active" ]; then
    echo -e "  ✅ Servicio: ${GREEN}Activo${NC}"
else
    echo -e "  ❌ Servicio: ${RED}$SERVICE_STATUS${NC}"
fi

# Verificar Apache
APACHE_STATUS=$(systemctl is-active apache2)
if [ "$APACHE_STATUS" = "active" ]; then
    echo -e "  ✅ Apache: ${GREEN}Activo${NC}"
else
    echo -e "  ❌ Apache: ${RED}$APACHE_STATUS${NC}"
fi

echo -e "  ℹ️  Servidor: Gunicorn (producción-ready, sin warnings)"

echo ""
echo -e "${BLUE}📝 Próximos pasos:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  1. Prueba la aplicación: http://$SITE_NAME$PATH_PREFIX"
echo ""
echo "  2. Instalar SSL con Let's Encrypt (recomendado):"
echo "     sudo apt install certbot python3-certbot-apache"
echo "     sudo certbot --apache -d $SITE_NAME"
echo ""
echo "  3. Ver logs del servicio:"
echo "     sudo journalctl -u lemr-meteo -f"
echo ""
echo "  4. Ver logs de Apache:"
echo "     sudo tail -f /var/log/apache2/lemr-meteo-error.log"
echo ""
echo "  5. Editar configuración (.env):"
echo "     sudo nano $INSTALL_DIR/.env"
echo "     sudo systemctl restart lemr-meteo"
echo ""

echo -e "${BLUE}🛠️  Comandos útiles:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Estado:     sudo systemctl status lemr-meteo"
echo "  Reiniciar:  sudo systemctl restart lemr-meteo"
echo "  Parar:      sudo systemctl stop lemr-meteo"
echo "  Logs:       sudo journalctl -u lemr-meteo -f"
echo ""

if [ -d "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}💾 Se han guardado backups en: $BACKUP_DIR${NC}"
    echo ""
fi

echo -e "${GREEN}¡Listo! Tu aplicación debería estar funcionando en:${NC}"
echo -e "${GREEN}${BOLD}http://$SITE_NAME$PATH_PREFIX${NC}"
echo ""
