"""
Bot de Telegram para reportes meteorológicos aeronáuticos
Obtiene METAR de LEAS y pronóstico para La Morgal, Asturias
"""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import config
from metar_service import get_metar, get_taf, parse_metar_components
from weather_service import get_weather_forecast, format_weather_report
from ai_service import interpret_metar_with_ai, interpret_weather_with_ai, create_combined_report

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start - Mensaje de bienvenida"""
    welcome_message = """🪂 **Bot Meteorológico para Aviación ULM** ✈️

Este bot proporciona información meteorológica especializada para ultraligeros (ULM):
• ✈️ Aeropuerto de Asturias (LEAS) - METAR y TAF con análisis ULM
• 🏔️ La Morgal, Asturias - Pronóstico 3 días específico para vuelo ULM

**Comandos disponibles:**

/metar - METAR de LEAS con EXPLICACIÓN detallada para ULM
/taf - TAF de LEAS con interpretación educativa
/morgal - Pronóstico ULM para HOY, MAÑANA y PASADO MAÑANA
/completo - Reporte completo optimizado para ULM
/help - Muestra este mensaje de ayuda

**Análisis especializado ULM incluye:**
✅ Evaluación según límites típicos ULM
✅ Pronóstico para 3 días con veredictos claros
✅ Horarios de amanecer/atardecer (solo vuelo diurno - obligatorio)
✅ Análisis de térmicas y turbulencias
✅ Veredicto por día: APTO ULM/PRECAUCIÓN/NO APTO
✅ Explicación educativa de METAR y TAF
✅ Conversiones precisas de unidades (kt/km/h)

**LEGISLACIÓN ULM (obligatorio):**
- Solo vuelo diurno (amanecer a atardecer)
- Solo condiciones VFR
- Consultar siempre el manual de tu modelo específico

¡Usa /completo para planificar tu vuelo! 🚀"""
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /help - Muestra ayuda"""
    await start(update, context)


async def metar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /metar - Obtiene e interpreta el METAR de LEAS para ULM"""
    await update.message.reply_text("🔄 Obteniendo METAR de LEAS para análisis ULM...")
    
    try:
        # Obtener METAR
        metar = get_metar(config.LEAS_ICAO)
        
        if not metar:
            await update.message.reply_text(
                "❌ No se pudo obtener el METAR de LEAS. Por favor, inténtalo más tarde."
            )
            return
        
        # Formatear respuesta
        response = f"✈️ **METAR - Aeropuerto de Asturias (LEAS)** ✈️\n\n"
        response += f"```\n{metar}\n```\n\n"
        
        # Parsear componentes
        components = parse_metar_components(metar)
        if components['wind']:
            response += f"💨 Viento: `{components['wind']}`\n"
        if components['temperature']:
            response += f"🌡️ Temperatura/Punto rocío: `{components['temperature']}`\n"
        if components['pressure']:
            response += f"🔽 Presión: `{components['pressure']}`\n"
        
        response += "\n🤖 **Análisis para AVIACIÓN ULM:**\n\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
        # Obtener interpretación de IA especializada en ULM
        interpretation = interpret_metar_with_ai(metar, config.LEAS_ICAO)
        
        if interpretation:
            await update.message.reply_text(interpretation, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                "⚠️ No se pudo generar la interpretación con IA. Verifica la configuración."
            )
        
    except Exception as e:
        logger.error(f"Error en comando /metar: {e}")
        await update.message.reply_text(
            f"❌ Error al procesar el METAR: {str(e)}"
        )


async def taf_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /taf - Obtiene el TAF de LEAS con explicación"""
    await update.message.reply_text("🔄 Obteniendo TAF de LEAS...")
    
    try:
        # Obtener TAF
        taf = get_taf(config.LEAS_ICAO)
        
        if not taf:
            await update.message.reply_text(
                "❌ No se pudo obtener el TAF de LEAS. Es posible que no esté disponible en este momento."
            )
            return
        
        # Formatear respuesta
        response = f"✈️ **TAF - Aeropuerto de Asturias (LEAS)** ✈️\n\n"
        response += f"```\n{taf}\n```\n\n"
        response += "📋 **¿Qué es el TAF?**\n"
        response += "Terminal Aerodrome Forecast - Pronóstico oficial del aeródromo para las próximas 24-30 horas.\n\n"
        response += "🤖 **Explicación del TAF:**\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
        # Generar explicación con IA
        taf_explanation = f"""Explica este TAF de forma EDUCATIVA para pilotos ULM:

{taf}

Proporciona:
1. **TRADUCCIÓN**: Explica cada línea del TAF (TEMPO, BECMG, FM, etc.)
2. **EVOLUCIÓN PREVISTA**: Cómo cambiarán las condiciones
3. **PERIODOS CRÍTICOS**: Identifica cuándo las condiciones serán peores/mejores para ULM
4. **VENTANAS DE VUELO**: Mejores periodos para volar (solo horario diurno)
5. **ALERTAS ULM**: Periodos donde NO volar según condiciones previstas"""
        
        try:
            from ai_service import get_ai_client, SYSTEM_PROMPT, _create_chat_completion_with_fallback
            
            client_info = get_ai_client()
            if client_info:
                provider, client = client_info
                
                response_ai = _create_chat_completion_with_fallback(
                    client=client,
                    provider=provider,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": taf_explanation}
                    ],
                    temperature=0.7,
                    max_tokens=1500,
                    model=config.AI_MODEL,
                )
                
                explanation = response_ai.choices[0].message.content
                await update.message.reply_text(explanation, parse_mode='Markdown')
            else:
                await update.message.reply_text("⚠️ No se pudo generar la explicación con IA.")
        except Exception as e:
            logger.error(f"Error explicando TAF: {e}")
            await update.message.reply_text("⚠️ Error al generar explicación del TAF.")
        
    except Exception as e:
        logger.error(f"Error en comando /taf: {e}")
        await update.message.reply_text(
            f"❌ Error al procesar el TAF: {str(e)}"
        )


async def morgal_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /morgal - Obtiene pronóstico ULM para La Morgal"""
    await update.message.reply_text("🔄 Obteniendo pronóstico ULM para La Morgal...")
    
    try:
        # Obtener datos meteorológicos
        weather_data = get_weather_forecast(
            config.LA_MORGAL_COORDS['lat'],
            config.LA_MORGAL_COORDS['lon'],
            config.LA_MORGAL_COORDS['name']
        )
        
        if not weather_data:
            await update.message.reply_text(
                "❌ No se pudieron obtener datos meteorológicos de La Morgal."
            )
            return
        
        # Formatear reporte básico
        response = format_weather_report(weather_data)
        await update.message.reply_text(response, parse_mode='Markdown')
        
        # Obtener análisis de IA especializado en ULM
        await update.message.reply_text("🤖 Generando análisis ULM con IA...")
        
        interpretation = interpret_weather_with_ai(
            weather_data,
            config.LA_MORGAL_COORDS['name']
        )
        
        if interpretation:
            await update.message.reply_text(interpretation, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                "⚠️ No se pudo generar el análisis con IA."
            )
        
    except Exception as e:
        logger.error(f"Error en comando /morgal: {e}")
        await update.message.reply_text(
            f"❌ Error al procesar datos meteorológicos: {str(e)}"
        )


async def completo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /completo - Reporte completo con METAR y pronóstico La Morgal"""
    await update.message.reply_text("🔄 Generando reporte meteorológico completo...\nEsto puede tomar unos segundos ⏳")
    
    try:
        # Obtener METAR
        metar = get_metar(config.LEAS_ICAO)
        
        # Obtener datos de La Morgal
        weather_data = get_weather_forecast(
            config.LA_MORGAL_COORDS['lat'],
            config.LA_MORGAL_COORDS['lon'],
            config.LA_MORGAL_COORDS['name']
        )
        
        if not metar and not weather_data:
            await update.message.reply_text(
                "❌ No se pudieron obtener datos meteorológicos. Por favor, inténtalo más tarde."
            )
            return
        
        # Crear reporte combinado
        if metar and weather_data:
            # Enviar METAR
            metar_msg = f"✈️ **AEROPUERTO DE ASTURIAS (LEAS)** ✈️\n\n```\n{metar}\n```"
            await update.message.reply_text(metar_msg, parse_mode='Markdown')
            
            # Interpretación METAR
            await update.message.reply_text("🤖 Analizando METAR...")
            metar_interp = interpret_metar_with_ai(metar, config.LEAS_ICAO)
            if metar_interp:
                await update.message.reply_text(metar_interp, parse_mode='Markdown')
            
            # Separador
            await update.message.reply_text("━━━━━━━━━━━━━━━━━━━━")
            
            # La Morgal
            weather_msg = format_weather_report(weather_data)
            await update.message.reply_text(weather_msg, parse_mode='Markdown')
            
            # Interpretación La Morgal
            await update.message.reply_text("🤖 Analizando condiciones en La Morgal...")
            weather_interp = interpret_weather_with_ai(weather_data, config.LA_MORGAL_COORDS['name'])
            if weather_interp:
                await update.message.reply_text(weather_interp, parse_mode='Markdown')
            
            await update.message.reply_text("\n✅ **Reporte completo generado**")
            
        elif metar:
            # Solo METAR disponible
            await update.message.reply_text(
                "⚠️ Solo se pudo obtener información del aeropuerto LEAS"
            )
            await metar_command(update, context)
            
        elif weather_data:
            # Solo La Morgal disponible
            await update.message.reply_text(
                "⚠️ Solo se pudo obtener información de La Morgal"
            )
            await morgal_command(update, context)
        
    except Exception as e:
        logger.error(f"Error en comando /completo: {e}")
        await update.message.reply_text(
            f"❌ Error al generar reporte completo: {str(e)}"
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja errores generales"""
    logger.error(f"Error: {context.error}")
    
    if update and update.message:
        await update.message.reply_text(
            "❌ Ha ocurrido un error. Por favor, inténtalo de nuevo más tarde."
        )


def main() -> None:
    """Función principal - Inicia el bot"""
    
    # Verificar configuración
    if not config.TELEGRAM_BOT_TOKEN:
        print("❌ ERROR: No se ha configurado TELEGRAM_BOT_TOKEN")
        print("Por favor, crea un archivo .env con tu token de Telegram")
        return
    
    # Crear aplicación
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # Registrar comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("metar", metar_command))
    application.add_handler(CommandHandler("taf", taf_command))
    application.add_handler(CommandHandler("morgal", morgal_command))
    application.add_handler(CommandHandler("completo", completo_command))
    
    # Registrar manejador de errores
    application.add_error_handler(error_handler)
    
    # Iniciar bot
    logger.info("🤖 Bot iniciado. Presiona Ctrl+C para detener.")
    print("🤖 Bot meteorológico iniciado correctamente!")
    print("📡 Esperando comandos...")
    print("\nComandos disponibles:")
    print("  /start - Mensaje de bienvenida")
    print("  /metar - METAR de LEAS con explicación")
    print("  /taf - TAF de LEAS con explicación educativa")
    print("  /morgal - Pronóstico La Morgal (HOY, MAÑANA, PASADO)")
    print("  /completo - Reporte completo ULM")
    print("\n🛑 Presiona Ctrl+C para detener el bot\n")
    
    # Ejecutar bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
