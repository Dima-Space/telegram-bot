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

# ===== НАЛАШТУВАННЯ ДВА ЧАТИ =====
CHATS = {
    -1003342150417: {
        "name": "Україна скло",
        "alert_time": 60 * 60,       # через скільки секунд надсилати алерт
        "repeat_alert": 60 * 60,     # через скільки повторювати алерт
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes",
    },
    -1002411854408: {                 # <-- ЗАМІНИ на ID другої групи
        "name": "NEW Україна",
        "alert_time": 60 * 60,
        "repeat_alert": 60 * 60,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes",  # <-- можна змінити
    },
}
# ==================================

TIMEZONE = ZoneInfo("Europe/Kyiv")
NIGHT_START = 23
NIGHT_END = 8

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


# Ініціалізація стану для кожного чату
_state = load_state()
chat_states = {}

for chat_id in CHATS:
    key = str(chat_id)
    chat_states[chat_id] = {
        "last_message_time": _state.get(key, {}).get("last_message_time", time.time()),
        "last_alert_time": _state.get(key, {}).get("last_alert_time", 0),
        "alert_count": _state.get(key, {}).get("alert_count", 0),
    }


def save_all_states():
    data = {}
    for chat_id, state in chat_states.items():
        data[str(chat_id)] = state
    save_state(data)


def is_night_time():
    now_hour = datetime.now(TIMEZONE).hour
    return now_hour >= NIGHT_START or now_hour < NIGHT_END


async def monitor_loop(bot):
    while True:
        await asyncio.sleep(30)

        try:
            if is_night_time():
                print("[MONITOR] Nich - propusk")
                continue

            now = time.time()

            for chat_id, config in CHATS.items():
                state = chat_states[chat_id]
                silence = now - state["last_message_time"]

                silence_min = int(silence // 60)
                silence_sec = int(silence % 60)

                print(
                    "[MONITOR][" + config["name"] + "] Tysha: "
                    + str(silence_min) + " hv " + str(silence_sec) + " sek"
                )

                if silence >= config["alert_time"]:
                    time_since_last_alert = now - state["last_alert_time"]

                    if state["last_alert_time"] == 0 or time_since_last_alert >= config["repeat_alert"]:
                        print("[MONITOR][" + config["name"] + "] Vidpravka alertu!")

                        now_str = datetime.now(TIMEZONE).strftime("%H:%M")
                        state["alert_count"] += 1

                        mention = "\n" + config["mentions"] if state["alert_count"] >= 2 else ""

                        msg_text = (
                            "⚠️Увага! Вже "
                            + str(silence_min)
                            + " хвилин немає нових замовлень! Час: "
                            + now_str
                            + mention
                        )

                        await bot.send_message(chat_id=chat_id, text=msg_text)

                        state["last_alert_time"] = now
                        save_all_states()

                    else:
                        print(
                            "[MONITOR][" + config["name"] + "] Alert vzhe nadsilavsia "
                            + str(int(time_since_last_alert // 60)) + " hv tomu"
                        )
                else:
                    print(
                        "[MONITOR][" + config["name"] + "] Do alertu shche "
                        + str(int((config["alert_time"] - silence) // 60)) + " hv"
                    )

        except Exception as e:
            print("[MONITOR] POMYLKA: " + str(e))


async def main():
    bot = Bot(token=BOT_TOKEN)
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    @client.on(events.NewMessage())
    async def handler(event):
        chat_id = event.chat_id

        # Ігноруємо повідомлення не з наших груп
        if chat_id not in CHATS:
            return

        msg = event.message

        # Ігноруємо повідомлення від самого бота
        if msg.sender_id == 8408563049:
            return

        text_preview = (msg.text or "(media)")[:80]
        config = CHATS[chat_id]
        print("[UPDATE][" + config["name"] + "] sender_id=" + str(msg.sender_id) + " | " + text_preview)

        # Оновлюємо стан ТІЛЬКИ для тієї групи, де прийшло повідомлення
        chat_states[chat_id]["last_message_time"] = time.time()
        chat_states[chat_id]["alert_count"] = 0

        save_all_states()

    await client.start(phone=TG_PHONE)

    # Перевірка підписки на обидва чати
    for chat_id, config in CHATS.items():
        try:
            await client(functions.channels.GetFullChannelRequest(chat_id))
            print("[START] Pidpyska na " + config["name"] + " uspishna")
        except Exception as e:
            print("[START] Pidpyska na " + config["name"] + ": " + str(e))

    print("[START] Userbot zapushcheno, slukhaemo " + str(len(CHATS)) + " chaty")

    asyncio.create_task(monitor_loop(bot))

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
