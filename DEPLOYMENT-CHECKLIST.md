# ✅ Checklist de Despliegue - LEMR Meteo

Usa este checklist para asegurarte de que no te saltas ningún paso.

## Pre-despliegue

- [ ] Tengo acceso SSH a mi servidor
- [ ] Mi servidor tiene Ubuntu/Debian (o similar)
- [ ] Apache está instalado y funcionando
- [ ] Tengo permisos sudo
- [ ] Tengo una API key de Gemini en Google AI Studio (https://aistudio.google.com/app/apikey)
- [ ] Tengo API key de AEMET (https://opendata.aemet.es) - gratis y recomendada
- [ ] He decidido entre:
  - [ ] Usar subdominio dedicado (ej: meteo.midominio.com)
  - [ ] Usar subdirectorio (ej: midominio.com/meteo)

## Instalación en el servidor

### 🌟 Opción A: Script Interactivo (Recomendado)

- [ ] He conectado por SSH: `ssh usuario@miservidor.com`
- [ ] He clonado el repo en `/var/www`: `cd /var/www && sudo git clone ...`
- [ ] He ejecutado el script interactivo: `sudo bash deploy-interactive.sh`
- [ ] He respondido a todas las preguntas del script (dominio, tipo, puerto, credenciales)
- [ ] El script terminó sin errores mostrando ✅
- [ ] He verificado que todo funciona según el resumen del script

**¡Si usaste el script interactivo, puedes saltar directamente a "Verificación"!**

---

### 🔧 Opción B: Script Básico + Configuración Manual

- [ ] He conectado por SSH: `ssh usuario@miservidor.com`
- [ ] He clonado el repo en `/var/www`: `cd /var/www && sudo git clone ...`
- [ ] He ejecutado el script de instalación: `sudo bash install-production.sh`
- [ ] El script terminó sin errores
- [ ] He editado el archivo `.env`: `sudo nano /var/www/lemr-meteo/.env`
- [ ] He configurado `GEMINI_API_KEY` en el `.env`
- [ ] He configurado `WEB_PORT=8001` (u otro puerto libre)
- [ ] He configurado `WEB_HOST=127.0.0.1`
- [ ] He configurado `AEMET_API_KEY` (recomendado para predicciones textuales)
- [ ] He guardado el archivo `.env`

## Servicio systemd (solo si usaste Opción B)

> **Nota:** Si usaste el script interactivo, esto ya está hecho automáticamente.

- [ ] He iniciado el servicio: `sudo systemctl start lemr-meteo`
- [ ] He verificado el estado: `sudo systemctl status lemr-meteo`
- [ ] El servicio muestra "active (running)" ✅
- [ ] Si hay errores, he revisado los logs: `sudo journalctl -u lemr-meteo -f`

## Configuración de Apache (solo si usaste Opción B)

> **Nota:** Si usaste el script interactivo, esto ya está configurado automáticamente.

### Si usé subdominio dedicado:

- [ ] He creado el archivo VirtualHost en `/etc/apache2/sites-available/meteo.midominio.com.conf`
- [ ] He configurado `ServerName meteo.midominio.com`
- [ ] He configurado el proxy a `http://127.0.0.1:8001/`
- [ ] He habilitado el sitio: `sudo a2ensite meteo.midominio.com.conf`
- [ ] He recargado Apache: `sudo systemctl reload apache2`
- [ ] Apache se recargó sin errores

### Si usé subdirectorio:

- [ ] He editado mi VirtualHost existente
- [ ] He añadido la sección `<Location /meteo>`
- [ ] He configurado el proxy a `http://127.0.0.1:8001/`
- [ ] He recargado Apache: `sudo systemctl reload apache2`
- [ ] Apache se recargó sin errores

## Verificación

- [ ] He abierto la URL en el navegador (http://meteo.midominio.com o http://midominio.com/meteo)
- [ ] La web carga correctamente ✅
- [ ] Veo los datos meteorológicos
- [ ] No hay errores en la consola del navegador (F12)

## SSL (HTTPS)

- [ ] He instalado certbot: `sudo apt install certbot python3-certbot-apache -y`
- [ ] He ejecutado: `sudo certbot --apache -d meteo.midominio.com`
- [ ] El certificado se instaló correctamente
- [ ] La web funciona con HTTPS ✅

## Post-despliegue

- [ ] He verificado que el servicio se inicia automáticamente al reiniciar: `sudo systemctl enable lemr-meteo`
- [ ] He documentado mi configuración (puerto, dominio, etc.)
- [ ] He guardado las credenciales en un lugar seguro
- [ ] He eliminado el `.env` del repositorio local (NUNCA subirlo a GitHub)

## Mantenimiento futuro

- [ ] Sé cómo ver los logs: `sudo journalctl -u lemr-meteo -f`
- [ ] Sé cómo reiniciar el servicio: `sudo systemctl restart lemr-meteo`
- [ ] Sé cómo actualizar la app:
  ```bash
  cd /var/www/lemr-meteo
  sudo git pull
  source venv/bin/activate
  pip install -r requirements.txt
  sudo systemctl restart lemr-meteo
  ```

## 🎉 ¡Completado!

Si has marcado todo ✅, ¡tu instalación está lista!

**URL de acceso:** _______________________________________________

**Usuario servidor:** _______________________________________________

**Notas adicionales:**

___________________________________________________________________

___________________________________________________________________

___________________________________________________________________
