from datetime import datetime
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8408563049:AAE_jPsUxRM96MUe5eZd6kXggDo0wnC3btg"

NIGHT_START = 23
NIGHT_END = 8

ALERT_TIME = 60 * 60
REPEAT_ALERT = 60 * 60

last_message_time = time.time()
last_alert_time = 0
chat_id_global = None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_message_time, chat_id_global

    chat_id_global = update.effective_chat.id

    print("АПДЕЙТ:", update)

    # 🔥 будь-яке повідомлення = скидаємо таймер
    last_message_time = time.time()


async def monitor(context: ContextTypes.DEFAULT_TYPE):
    global last_message_time, last_alert_time, chat_id_global

    try:
        if chat_id_global is None:
            return

        now_time = datetime.now().hour

        # 🌙 нічний режим (ПРАВИЛЬНИЙ)
        if NIGHT_START < NIGHT_END:
            if NIGHT_START <= now_time < NIGHT_END:
                return
        else:
            if now_time >= NIGHT_START or now_time < NIGHT_END:
                return

        now = time.time()
        silence = now - last_message_time

        print("ПЕРЕВІРКА:", now, "тишина:", silence)

        # 🔥 якщо нема повідомлень годину
        if silence > ALERT_TIME:
            # 🔥 щоб не спамив
            if now - last_alert_time > REPEAT_ALERT:
                print("АЛЕРТ! тиша:", silence)

                await context.bot.send_message(
                    chat_id=chat_id_global,
                    text="⚠️ Немає нових замовлень!"
                )

                last_alert_time = now

    except Exception as e:
        print("Помилка:", e)


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.ALL, handle_message))
app.add_handler(MessageHandler(filters.ALL, handle_message), group=1)

app.job_queue.run_repeating(monitor, interval=10)

app.run_polling()
