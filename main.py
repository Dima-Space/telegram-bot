from datetime import datetime
import time
import json
import os
import asyncio
from zoneinfo import ZoneInfo
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telegram import Bot

API_ID = int(os.environ.get("TG_API_ID"))
API_HASH = os.environ.get("TG_API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TG_PHONE = os.environ.get("TG_PHONE")

# 🔥 СПИСОК ГРУП
CHAT_IDS = [
    -1003342150417,
      # друга група
]

TIMEZONE = ZoneInfo("Europe/Kyiv")
NIGHT_START = 23
NIGHT_END = 8
ALERT_TIME = 60 * 60
REPEAT_ALERT = 60 * 60

STATE_FILE = "/tmp/state.json"


# ---------- STATE ----------
def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump(chat_state, f)


# 🔥 тепер тут все по чатах
chat_state = load_state()

# якщо нема — ініціалізуємо
for chat_id in CHAT_IDS:
    if str(chat_id) not in chat_state:
        chat_state[str(chat_id)] = {
            "last_message_time": time.time(),
            "last_alert_time": 0,
            "alert_count": 0
        }


# ---------- TIME ----------
def is_night():
    h = datetime.now(TIMEZONE).hour
    return h >= NIGHT_START or h < NIGHT_END


# ---------- MONITOR ----------
async def monitor(bot):
    while True:
        await asyncio.sleep(30)

        if is_night():
            print("[MONITOR] ніч")
            continue

        now = time.time()

        for chat_id_str, data in chat_state.items():
            chat_id = int(chat_id_str)

            silence = now - data["last_message_time"]
            print(f"[MONITOR] {chat_id} тиша {int(silence)} сек")

            if silence >= ALERT_TIME:
                if now - data["last_alert_time"] >= REPEAT_ALERT:

                    print(f"[ALERT] {chat_id}")

                    text = f"⚠️ Немає замовлень {int(silence//60)} хв"

                    # 🔥 тег після 2-го алерта
                    data["alert_count"] += 1
                    if data["alert_count"] >= 2:
                        text += "\n@stasnislaavv @rumyantsev58 @cheeenazes"

                    await bot.send_message(chat_id=chat_id, text=text)

                    data["last_alert_time"] = now
                    save_state()


# ---------- MAIN ----------
async def main():
    bot = Bot(token=BOT_TOKEN)

    client = TelegramClient(
        StringSession(SESSION_STRING),
        API_ID,
        API_HASH
    )

    @client.on(events.NewMessage())
    async def handler(event):
        chat_id = event.chat_id

        if chat_id not in CHAT_IDS:
            return

        data = chat_state[str(chat_id)]

        print(f"[UPDATE] {chat_id}")

        data["last_message_time"] = time.time()
        data["alert_count"] = 0

        save_state()

    await client.start(phone=TG_PHONE)

    print("[START] userbot працює")

    asyncio.create_task(monitor(bot))

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
