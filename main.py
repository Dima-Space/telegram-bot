from datetime import datetime
import time
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8408563049:AAE6OZeUQ0bs4fT-jTXCt0s9xavsfeX8VjI"
CHAT_ID = -1003342150417
TIMEZONE = ZoneInfo("Europe/Kyiv")
NIGHT_START = 23
NIGHT_END = 8
ALERT_TIME = 60 * 60
REPEAT_ALERT = 60 * 60

last_message_time = 0
last_alert_time = 0

class AllowBots(filters.MessageFilter):
    def filter(self, message):
        return True

allow_bots_filter = AllowBots()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_message_time
    print(f"UPDATE TYPE: {update.effective_message}")
    print(f"CHANNEL POST: {update.channel_post}")
    print(f"MESSAGE: {update.message}")
    last_message_time = time.time()

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_message_time
    print(f"CHANNEL POST ОТРИМАНО: {update.channel_post}")
    last_message_time = time.time()

async def monitor(context: ContextTypes.DEFAULT_TYPE):
    global last_message_time, last_alert_time
    try:
        now_kyiv = datetime.now(TIMEZONE)
        now_hour = now_kyiv.hour

        is_night = now_hour >= NIGHT_START or now_hour < NIGHT_END
        if is_night:
            return

        now = time.time()
        silence = now - last_message_time
        print(f"Тиша: {int(silence)} сек")

        if silence > ALERT_TIME:
            if now - last_alert_time > REPEAT_ALERT:
                await context.bot.send_message(
                    chat_id=CHAT_ID,
                    text="⚠️ Немає нових замовлень!"
                )
                last_alert_time = now
    except Exception as e:
        print(f"Помилка: {e}")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(allow_bots_filter, handle_message))
app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, handle_channel_post))

app.job_queue.run_repeating(monitor, interval=60)
app.run_polling(
    allowed_updates=Update.ALL_TYPES,
    drop_pending_updates=True
)
