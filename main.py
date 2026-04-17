from datetime import datetime
import time
import json
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters
)

TOKEN = "8408563049:AAHM6D3iNsze707zUmgRXRnPx1xkVQXFhnw"
CHAT_ID = -1003342150417

TIMEZONE = ZoneInfo("Europe/Kyiv")

NIGHT_START = 23
NIGHT_END = 8

ALERT_TIME = 60 * 60
REPEAT_ALERT = 60 * 60

STATE_FILE = "/tmp/bot_state.json"


# --- STATE ---
def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump({
            "last_message_time": last_message_time,
            "last_alert_time": last_alert_time
        }, f)


_state = load_state()

last_message_time = _state.get("last_message_time", time.time())
last_alert_time = _state.get("last_alert_time", 0)


# --- NIGHT CHECK ---
def is_night():
    h = datetime.now(TIMEZONE).hour
    return h >= NIGHT_START or h < NIGHT_END


# --- HANDLE MESSAGES ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_message_time

    msg = update.effective_message
    if not msg:
        return

    chat_id = msg.chat.id

    print(f"[MSG] chat={chat_id} text={msg.text}")

    if chat_id == CHAT_ID:
        last_message_time = time.time()
        save_state()
        print("[MSG] ✅ Таймер оновлено")


# --- MONITOR ---
async def monitor(context: ContextTypes.DEFAULT_TYPE):
    global last_alert_time

    try:
        if is_night():
            print("[MONITOR] 🌙 ніч")
            return

        now = time.time()
        silence = now - last_message_time

        print(f"[MONITOR] тиша {int(silence)} сек")

        if silence >= ALERT_TIME:
            if now - last_alert_time >= REPEAT_ALERT:

                print("[MONITOR] 🚨 АЛЕРТ")

                await context.bot.send_message(
                    chat_id=CHAT_ID,
                    text="⚠️ Немає нових замовлень!"
                )

                last_alert_time = now
                save_state()

    except Exception as e:
        print("ERROR:", e)


# --- MAIN ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(filters.Chat(CHAT_ID), handle_message)
    )

    app.job_queue.run_repeating(monitor, interval=30, first=10)

    print("БОТ ЗАПУЩЕНО")

    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=False
    )


if __name__ == "__main__":
    main()
