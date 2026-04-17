from datetime import datetime
import time
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8408563049:AAEEbVX0z8Z0LhAr81N-2BvH8tuTLayfJjk"
CHAT_ID = -1003342150417
TIMEZONE = ZoneInfo("Europe/Kyiv")
NIGHT_START = 23
NIGHT_END = 8
ALERT_TIME = 60 * 60    # 1 година тиші → алерт
REPEAT_ALERT = 60 * 60  # повторювати не частіше ніж раз на годину

# Правильно — відлік з моменту запуску
last_message_time = time.time()
last_alert_time = 0

def is_night_time() -> bool:
    """ВИПРАВЛЕННЯ 3: винесено в окрему функцію, логіка спрощена і очевидна"""
    now_hour = datetime.now(TIMEZONE).hour
    # NIGHT_START=23, NIGHT_END=8 → ніч: 23,0,1,2,...,7
    return now_hour >= NIGHT_START or now_hour < NIGHT_END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Звичайні повідомлення в групі (від людей, ботів)"""
    global last_message_time
    msg = update.effective_message
    if not msg:
        return
    print(f"[MESSAGE] {msg.text or msg.caption or '(без тексту)'}")
    last_message_time = time.time()

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ВИПРАВЛЕННЯ 4: окремий handler для channel_post (саме так Tilda надсилає замовлення)"""
    global last_message_time
    post = update.channel_post
    if not post:
        return
    print(f"[CHANNEL_POST] {post.text or post.caption or '(без тексту)'}")
    last_message_time = time.time()

async def monitor(context: ContextTypes.DEFAULT_TYPE):
    global last_message_time, last_alert_time
    try:
        if is_night_time():
            print("[MONITOR] Ніч — пропуск")
            return

        now = time.time()

        # Якщо last_message_time=0 (бот щойно запустився) — вважаємо що тиша з початку дня
        # Але не надсилаємо одразу — чекаємо ALERT_TIME
        if last_message_time == 0:
            print("[MONITOR] Початковий стан, тиша ще не відраховується")
            last_message_time = now  # починаємо відлік від запуску
            return

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

# ВИПРАВЛЕННЯ 1 + 4: два окремі handlers — для звичайних повідомлень і для channel_post
app.add_handler(MessageHandler(
    filters.ALL & (~filters.COMMAND),
    handle_message
))

# ВИПРАВЛЕННЯ 4: ловимо channel_post окремо (Tilda надсилає саме так)
app.add_handler(MessageHandler(
    filters.UpdateType.CHANNEL_POSTS,
    handle_channel_post
))

app.job_queue.run_repeating(monitor, interval=30)

app.run_polling(
    allowed_updates=Update.ALL_TYPES,
    drop_pending_updates=True
)
