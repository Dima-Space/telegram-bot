from datetime import datetime
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8408563049:AAEjYkMSSA-NVsnnVWAk0NxUWJOrg72IDKs"
NIGHT_START = 23
NIGHT_END = 8

ALERT_TIME = 3200
REPEAT_ALERT = 3200

last_message_time = time.time()
last_alert_time = 0
chat_id_global = None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_message_time, chat_id_global
    last_message_time = time.time()
    chat_id_global = update.effective_chat.id

async def monitor(context: ContextTypes.DEFAULT_TYPE):
    global last_message_time, last_alert_time, chat_id_global

    if chat_id_global is None:
        return

    now_time = datetime.now().hour

    # нічний режим
    if NIGHT_START <= now_time or now_time < NIGHT_END:
        return

    now = time.time()
    silence = now - last_message_time

    if silence > ALERT_TIME:
        if now - last_alert_time > REPEAT_ALERT:
            await context.bot.send_message(
                chat_id=chat_id_global,
                text="⚠️ Немає нових замовлень!"
            )
            last_alert_time = now

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.ALL, handle_message))
app.job_queue.run_repeating(monitor, interval=60)

app.run_polling()
