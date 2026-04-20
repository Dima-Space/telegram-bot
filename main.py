from datetime import datetime
import time
import json
import os
import asyncio
from zoneinfo import ZoneInfo
from telethon import TelegramClient, events, functions
from telethon.sessions import StringSession
from telegram import Bot 

API_ID = int(os.environ.get("TG_API_ID"))
API_HASH = os.environ.get("TG_API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TG_PHONE = os.environ.get("TG_PHONE", "+380682836508")

CHAT_ID = -1003342150417
TIMEZONE = ZoneInfo("Europe/Kyiv")
NIGHT_START = 23
NIGHT_END = 8
ALERT_TIME = 60 * 10
REPEAT_ALERT = 60 * 10

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
        print("[STATE] Pomylka: " + str(e))

_state = load_state()
last_message_time = _state.get("last_message_time", time.time())
last_alert_time = _state.get("last_alert_time", 0)

def is_night_time():
    now_hour = datetime.now(TIMEZONE).hour
    return now_hour >= NIGHT_START or now_hour < NIGHT_END

async def monitor_loop(bot):
    global last_alert_time
    while True:
        await asyncio.sleep(30)
        try:
            if is_night_time():
                print("[MONITOR] Nich - propusk")
                continue

            now = time.time()
            silence = now - last_message_time
            silence_min = int(silence // 60)
            silence_sec = int(silence % 60)
            print("[MONITOR] Tysha: " + str(silence_min) + " hv " + str(silence_sec) + " sek")

            if silence >= ALERT_TIME:
                time_since_last_alert = now - last_alert_time
                if last_alert_time == 0 or time_since_last_alert >= REPEAT_ALERT:
                    print("[MONITOR] Vidpravka alertu!")
                    now_str = datetime.now(TIMEZONE).strftime("%H:%M")
                    msg_text = "Увага! Вже " + str(silence_min) + " хвилин немає нових замовлень! Час: " + now_str
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=msg_text
                    )
                    last_alert_time = now
                    save_state({
                        "last_message_time": last_message_time,
                        "last_alert_time": last_alert_time
                    })
                else:
                    print("[MONITOR] Alert vzhe nadsilavsia " + str(int(time_since_last_alert // 60)) + " hv tomu")
            else:
                print("[MONITOR] Do alertu shche " + str(int((ALERT_TIME - silence) // 60)) + " hv")

        except Exception as e:
            print("[MONITOR] POMYLKA: " + str(e))

async def main():
    global last_message_time

    bot = Bot(token=BOT_TOKEN)
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    @client.on(events.NewMessage())
    async def handler(event):
        global last_message_time
        if event.chat_id != CHAT_ID:
            return
        msg = event.message
        text_preview = (msg.text or "(media)")[:80]
        print("[UPDATE] sender_id=" + str(msg.sender_id) + " | " + text_preview)
        last_message_time = time.time()
        save_state({
            "last_message_time": last_message_time,
            "last_alert_time": last_alert_time
        })

    await client.start(phone=TG_PHONE)

    try:
        await client(functions.channels.GetFullChannelRequest(CHAT_ID))
        print("[START] Pidpyska na kanal uspishna")
    except Exception as e:
        print("[START] Pidpyska: " + str(e))

    print("[START] Userbot zapushcheno, slukhaemo chat " + str(CHAT_ID))

    asyncio.create_task(monitor_loop(bot))
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
