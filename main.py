from datetime import datetime
import time
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8408563049:AAEx5IvAaUtzAVDW6Dq86mF-5ofTpc0zqio"
CHAT_ID = -1003342150417
TIMEZONE = ZoneInfo("Europe/Kyiv")
NIGHT_START = 23
NIGHT_END = 8
ALERT_TIME = 60 * 60
REPEAT_ALERT = 60 * 60

last_message_time = time.time()
last_alert_time = 0

def is_night_time() -> bool:
    now_hour = datetime.now(TIMEZONE).hour
    return now_hour >= NIGHT_START or now_hour < NIGHT_END

async def handle_any_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ловимо БУДЬ-ЯКЕ оновлення і перевіряємо чи є повідомлення"""
    global last_message_time

    # Перевіряємо всі можливі типи повідомлень
    msg = (
        update.message or
        update.channel_post or
        update.edited_message or
        update.edited_channel_post
    )

    if msg is None:
        return

    chat_id = msg.chat.chat_id if hasattr(msg.chat, 'chat_id') else msg.chat.id

    # Логуємо детально щоб бачити що саме приходить
    sender = None
    if msg.from_user:
        sender = f"user:{msg.from_user.id}"
    elif msg.sender_chat:
        sender = f"sender_chat:{msg.sender_chat.id}"  # анонімний адмін або канал

    print(f"[UPDATE] chat={chat_id} sender={sender} text={msg.text or msg.caption or '(медіа)'}")

    # Оновлюємо таймер тільки для нашого чату
    if chat_id == CHAT_ID:
        last_message_time = time.time()
        print(f"[UPDATE] ✅ Таймер оновлено")
    else:
        print(f"[UPDATE] ⚠️ Інший чат, ігноруємо")

async def monitor(context: ContextTypes.DEFAULT_TYPE):
    global last_message_time, last_alert_time
    try:
        if is_night_time():
            print("[MONITOR] Ніч — пропуск")
            return

        now = time.time()
        silence = now - last_message_time
        print(f"[MONITOR] Тиша: {int(silence // 60)} хв {int(silence % 60)} сек")

        if silence >= ALERT_TIME:
            time_since_last_alert = now - last_alert_time
            if last_alert_time == 0 or time_since_last_alert >= REPEAT_ALERT:
                print("[MONITOR] 🚨 Відправка алерту")
                await context.bot.send_message(
                    chat_id=CHAT_ID,
                    text="⚠️ Вже більше години немає нових замовлень!"
                )
                last_alert_time = now
            else:
                print(f"[MONITOR] Алерт вже надсилався {int(time_since_last_alert // 60)} хв тому")

    except Exception as e:
        print(f"[MONITOR] ПОМИЛКА: {e}")

app = ApplicationBuilder().token(TOKEN).build()

# Один handler на ВСЕ без жодних фільтрів
app.add_handler(MessageHandler(filters.ALL, handle_any_update))

app.job_queue.run_repeating(monitor, interval=30)

app.run_polling(
    allowed_updates=Update.ALL_TYPES,
    drop_pending_updates=True
)
