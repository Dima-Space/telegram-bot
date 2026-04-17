from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from zoneinfo import ZoneInfo
import time
from datetime import datetime

TOKEN = "8408563049:AAFDAJNOhNa_uRHLqK6XOAbwo5bLgNtL4OE"
CHAT_ID = -1003342150417  # хардкодимо — вже знаємо з логів
TIMEZONE = ZoneInfo("Europe/Kyiv")
NIGHT_START = 23
NIGHT_END = 8
ALERT_TIME = 60 * 60
REPEAT_ALERT = 60 * 60

last_message_time = 0
last_alert_time = 0

# Фільтр який пропускає ВСІ повідомлення включно з ботами
class AllowBots(filters.MessageFilter):
    def filter(self, message):
        return True

allow_bots_filter = AllowBots()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_message_time
    print(f"Повідомлення від: {update.effective_user}, chat: {update.effective_chat.id if update.effective_chat else 'N/A'}")
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
                    text="⚠️ Вже більше години немає нових замовлень!"
                )
                last_alert_time = now
    except Exception as e:
        print(f"Помилка: {e}")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(allow_bots_filter, handle_message))

app.job_queue.run_repeating(monitor, interval=60)
app.run_polling(allowed_updates=Update.ALL_TYPES)

