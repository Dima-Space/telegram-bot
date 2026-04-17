from datetime import datetime
import time
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8408563049:AAFDAJNOhNa_uRHLqK6XOAbwo5bLgNtL4OE"
TIMEZONE = pytz.timezone("Europe/Kyiv")
NIGHT_START = 23
NIGHT_END = 8
ALERT_TIME = 60 * 60
REPEAT_ALERT = 60 * 60

last_message_time = time.time()
last_alert_time = 0
chat_id_global = None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_message_time, chat_id_global

    # Отримуємо chat_id з будь-якого типу повідомлення
    if update.effective_chat:
        chat_id_global = update.effective_chat.id
    elif update.channel_post:
        chat_id_global = update.channel_post.chat.id

    print(f"Повідомлення отримано, chat_id: {chat_id_global}")
    last_message_time = time.time()

async def monitor(context: ContextTypes.DEFAULT_TYPE):
    global last_message_time, last_alert_time, chat_id_global
    try:
        if chat_id_global is None:
            print("chat_id невідомий, пропускаємо")
            return

        now_kyiv = datetime.now(TIMEZONE)
        now_hour = now_kyiv.hour

        # Нічний режим: NIGHT_START=23, NIGHT_END=8 → перехід через північ
        if NIGHT_START > NIGHT_END:
            is_night = now_hour >= NIGHT_START or now_hour < NIGHT_END
        else:
            is_night = NIGHT_START <= now_hour < NIGHT_END

        if is_night:
            print(f"Нічний режим ({now_hour}:00), пропускаємо")
            return

        now = time.time()
        silence = now - last_message_time
        print(f"Тиша: {int(silence)} сек | chat_id: {chat_id_global}")

        if silence > ALERT_TIME:
            if now - last_alert_time > REPEAT_ALERT:
                print(f"АЛЕРТ! Тиша {int(silence)} сек")
                await context.bot.send_message(
                    chat_id=chat_id_global,
                    text="⚠️ Вже більше години немає нових замовлень!"
                )
                last_alert_time = now
    except Exception as e:
        print(f"Помилка в monitor: {e}")

app = ApplicationBuilder().token(TOKEN).build()

# Одного хендлера достатньо — filters.ALL покриває і channel_post теж
app.add_handler(MessageHandler(filters.ALL, handle_message))

app.job_queue.run_repeating(monitor, interval=60)  # перевірка раз на хвилину
app.run_polling(allowed_updates=Update.ALL_TYPES)
