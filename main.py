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

CHAT_ID = -1003342150417
TIMEZONE = ZoneInfo("Europe/Kyiv")
NIGHT_START = 23
NIGHT_END = 8
ALERT_TIME = 60 * 60
REPEAT_ALERT = 60 * 60

STATE_FILE = "/tmp/bot_state.json"

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception as e:
        print(f"[STATE] Помилка: {e}")

_state = load_state()
last_message_time: float = _state.get("last_message_time", time.time())
last_alert_time: float = _state.get("last_alert_time", 0)

def is_night_time():
    now_hour = datetime.now(TIMEZONE).hour
    return now_hour >= NIGHT_START or now_hour < NIGHT_END

async def monitor_loop(bot: Bot):
    global last_alert_time
    while True:
        await asyncio.sleep(30)
        try:
            if is_night_time():
                print("[MONITOR] 🌙 Ніч — пропуск")
                continue

            now = time.time()
            silence = now - last_message_time
            silence_min = int(silence // 60)
            print(f"[MONITOR] ⏱ Тиша: {silence_min} хв {int(silence % 60)} сек")

            if silence >= ALERT_TIME:
                time_since_last_alert = now - last_alert_time
                if last_alert_time == 0 or time_since_last_alert >= REPEAT_ALERT:
                    print("[MONITOR] 🚨 Відправка алерту!")
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=(
                            f"⚠️ *Увага!* Вже *{silence_min} хвилин* немає нових замовлень!\n"
                            f"Час: {datetime.now(TIMEZONE).strftime('%H:%M')}"
                        ),
                        parse_mode="Markdown"
                    )
                    last_alert_time = now
                    save_state({
                        "last_message_time": last_message_time,
                        "last_alert_time": last_alert_time
                    })
                else:
                    print(f"[MONITOR] Алерт надсилався {int(time_since_last_alert // 60)} хв тому")
            else:
                print(f"[MONITOR] ✅ До алерту ще {int((ALERT_TIME - silence) // 60)} хв")

        except Exception as e:
            print(f"[MONITOR] ❌ ПОМИЛКА: {e}")

async def main():
    global last_message_time

    bot = Bot(token=BOT_TOKEN)
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    @client.on(events.NewMessage(chats=CHAT_ID))
    async def handler(event):
        global last_message_time
        sender = await event.get_sender()
        name = getattr(sender, 'username', None) or getattr(sender, 'title', '?')
        print(f"[UPDATE] ✅ Повідомлення від: {name} | {(event.message.text or '(медіа)')[:80]}")
        last_message_time = time.time()
        save_state({
            "last_message_time": last_message_time,
            "last_alert_time": last_alert_time
        })

    await client.start()
    print(f"[START] 👤 Userbot запущено, слухаємо чат {CHAT_ID}")
    print(f"[START] last_msg={datetime.fromtimestamp(last_message_time, TIMEZONE).strftime('%H:%M:%S')}")

    asyncio.create_task(monitor_loop(bot))
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
