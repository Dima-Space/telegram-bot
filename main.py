from datetime import datetime
import time
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8408563049:AAFE6EeTRbc_wFbX7b0wRYrohgEnVRWBBzE"
CHAT_ID = -1003342150417

TIMEZONE = ZoneInfo("Europe/Kyiv")

NIGHT_START = 23
NIGHT_END = 8

ALERT_TIME = 60 * 60      # 1 година
REPEAT_ALERT = 60 * 60    # повтор через 1 годину

last_message_time = time.time()
last_alert_time = 0


# ✅ ЛОВИМО ВСЕ (і повідомлення, і канал)
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_message_time

    msg = update.effective_message
    if not msg:
        return

    print("ОТРИМАНО:", msg.text if msg.text else "non-text")

    # 🔥 ГОЛОВНЕ — СКИДАЄМО ТАЙМЕР
    last_message_time = time.time()


# ✅ ПЕРЕВІРКА
async def monitor(context: ContextTypes.DEFAULT_TYPE):
    global last_message_time, last_alert_time

    try:
        now_kyiv = datetime.now(TIMEZONE)
        now_hour = now_kyiv.hour

        # ✅ правильна нічна логіка
        if NIGHT_START < NIGHT_END:
            is_night = NIGHT_START <= now_hour < NIGHT_END
        else:
            is_night = now_hour >= NIGHT_START or now_hour < NIGHT_END

        if is_night:
            print("НІЧ — пропуск")
            return

        now = time.time()
        silence = now - last_message_time

        print(f"ТИША: {int(silence)} сек")

        # ✅ якщо нема повідомлень
        if silence >= ALERT_TIME:
            if now - last_alert_time >= REPEAT_ALERT:

                print("🚨 ВІДПРАВКА АЛЕРТУ")

                await context.bot.send_message(
                    chat_id=CHAT_ID,
                    text="⚠️ Немає нових замовлень!"
                )

                last_alert_time = now

    except Exception as e:
        print("ПОМИЛКА:", e)


app = ApplicationBuilder().token(TOKEN).build()

# ✅ один універсальний handler
app.add_handler(MessageHandler(filters.ALL, handle_all))

# ✅ перевірка кожні 30 сек (можеш 10 поставити)
app.job_queue.run_repeating(monitor, interval=30)

app.run_polling(
    allowed_updates=Update.ALL_TYPES,
    drop_pending_updates=True
)
