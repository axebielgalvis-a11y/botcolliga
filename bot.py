"""Bot de Telegram de la Liga Profesional de Fútbol Colombiano.

Uso:  python bot.py   (antes: python entrenar.py, y el token en el archivo .env)
Este archivo solo se encarga de hablar con Telegram; la inteligencia está en cerebro.py.
"""
import html
import logging
import os
import random

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import cerebro
from texto import DATOS, buscar_equipo

# ─── Configuración ──────────────────────────────────────

load_dotenv()  # lee el archivo .env
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise SystemExit("❌ Falta TELEGRAM_TOKEN. Crea el archivo .env con: TELEGRAM_TOKEN=tu_token")

logging.basicConfig(format="%(asctime)s | %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)  # oculta los mensajes internos de conexión
log = logging.getLogger("bot")


async def enviar(update: Update, texto: str):
    await update.effective_message.reply_text(texto, parse_mode=ParseMode.HTML)


# ─── Trivia con botones ─────────────────────────────────

async def enviar_trivia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numero = random.randrange(len(DATOS["trivia"]))
    pregunta = DATOS["trivia"][numero]
    # Cada botón lleva escondido: número de pregunta y opción elegida (ej. "trivia|3|1")
    botones = [
        [InlineKeyboardButton(opcion, callback_data=f"trivia|{numero}|{i}")]
        for i, opcion in enumerate(pregunta["opciones"])
    ]
    await update.effective_message.reply_text(
        f"🧠 <b>Trivia de la liga</b>\n\n{pregunta['pregunta']}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(botones),
    )


async def responder_trivia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Se ejecuta cuando el usuario toca un botón de la trivia."""
    consulta = update.callback_query
    await consulta.answer()  # le avisa a Telegram que recibimos el clic
    _, numero, elegida = consulta.data.split("|")
    pregunta = DATOS["trivia"][int(numero)]
    acerto = int(elegida) == pregunta["correcta"]

    resultado = "✅ <b>¡Correcto!</b>" if acerto else (
        f"❌ <b>No.</b> Era: {pregunta['opciones'][pregunta['correcta']]}"
    )
    await consulta.edit_message_text(
        f"🧠 {pregunta['pregunta']}\n\n{resultado}\n{pregunta['explicacion']}\n\n"
        "Escribe /trivia para otra pregunta.",
        parse_mode=ParseMode.HTML,
    )


# ─── Comandos ───────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = html.escape(update.effective_user.first_name)
    await enviar(update, f"¡Hola, {nombre}! ⚽\n\n" + cerebro.r_ayuda(None))


async def cmd_equipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/equipo millonarios  -> ficha del equipo"""
    equipo = buscar_equipo(" ".join(context.args))
    if equipo in cerebro.EQUIPOS:
        await enviar(update, cerebro.r_info_equipo(equipo))
    else:
        await enviar(update, "Escribe el comando con el nombre del equipo, por ejemplo: /equipo nacional")


def comando_simple(funcion):
    """Convierte una función de respuesta del cerebro en un comando de Telegram."""
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await enviar(update, funcion(None))
    return handler


# ─── Mensajes de texto libre (aquí actúa el modelo de ML) ─

async def mensaje_libre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    respuesta, intencion, confianza = cerebro.responder(texto)
    log.info(f"'{texto}' -> intención: {intencion} ({confianza:.0%})")

    if intencion == "trivia":
        await enviar_trivia(update, context)
    else:
        await enviar(update, respuesta)


async def manejar_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error(f"Error: {context.error}")
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("⚠️ Ocurrió un error. Intenta de nuevo.")


# ─── Inicio ─────────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ayuda", comando_simple(cerebro.r_ayuda)))
    app.add_handler(CommandHandler("campeones", comando_simple(cerebro.r_campeones_historicos)))
    app.add_handler(CommandHandler("ultimos", comando_simple(cerebro.r_ultimo_campeon)))
    app.add_handler(CommandHandler("equipos", comando_simple(cerebro.r_equipos_liga)))
    app.add_handler(CommandHandler("formato", comando_simple(cerebro.r_formato)))
    app.add_handler(CommandHandler("descenso", comando_simple(cerebro.r_descenso)))
    app.add_handler(CommandHandler("clasicos", comando_simple(cerebro.r_clasicos)))
    app.add_handler(CommandHandler("equipo", cmd_equipo))
    app.add_handler(CommandHandler("trivia", enviar_trivia))
    app.add_handler(CallbackQueryHandler(responder_trivia, pattern=r"^trivia\|"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje_libre))
    app.add_error_handler(manejar_error)

    print("🟢 Bot de la liga colombiana corriendo... (Ctrl + C para detenerlo)")
    app.run_polling()


if __name__ == "__main__":
    main()
