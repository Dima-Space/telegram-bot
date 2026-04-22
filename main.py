from datetime import datetime
import time
import os
import asyncio
import sqlite3
from zoneinfo import ZoneInfo
from telethon import TelegramClient, events, functions
from telethon.sessions import StringSession
from telegram import Bot

API_ID = int(os.environ.get("TG_API_ID"))
API_HASH = os.environ.get("TG_API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TG_PHONE = os.environ.get("TG_PHONE", "+380682836508")

TIMEZONE = ZoneInfo("Europe/Kyiv")
NIGHT_START = 23
NIGHT_END = 8

DB_FILE = "/tmp/bot_state.db"

# ===== НАЛАШТУВАННЯ ГРУП =====
CHATS = {
    -1003342150417: {
        "name": "Україна скло",
        "alert_time": 60 * 60,
        "repeat_alert": 60 * 60,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
    -1001234567890: {
        "name": "NEW Україна",
        "alert_time": 60 * 60,
        "repeat_alert": 60 * 60,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
    -1002261696626: {
        "name": "Польща",
        "alert_time": 60 * 60 * 2,
        "repeat_alert": 60 * 60 * 2,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
     -1002270006683: {
        "name": "Чехія",
        "alert_time": 60 * 60 * 3,
        "repeat_alert": 60 * 60 * 3,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
     -1002310052085: {
        "name": "Словаччина",
        "alert_time": 60 * 60 * 3,
        "repeat_alert": 60 * 60 * 3,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
     -4936972654: {
        "name": "Словенія",
        "alert_time": 60 * 60 * 3,
        "repeat_alert": 60 * 60 * 3,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
    -5179067596: {
        "name": "Болгарія",
        "alert_time": 60 * 60 * 5,
        "repeat_alert": 60 * 60 * 5,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
     -5249103915: {
        "name": "Португалія",
        "alert_time": 60 * 60 * 3,
        "repeat_alert": 60 * 60 * 3,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
     -5191839700: {
        "name": "Литва",
        "alert_time": 60 * 60 * 3,
        "repeat_alert": 60 * 60 * 3,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
    -4818710901: {
        "name": "Румунія",
        "alert_time": 60 * 60 * 2,
        "repeat_alert": 60 * 60 * 2,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
    -5023458941: {
        "name": "Латвія",
        "alert_time": 60 * 60 * 5,
        "repeat_alert": 60 * 60 * 5,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
    -5286153459: {
        "name": "Франція",
        "alert_time": 60 * 60 * 5,
        "repeat_alert": 60 * 60 * 5,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
    -5176746227: {
        "name": "Іспанія",
        "alert_time": 60 * 60 * 3,
        "repeat_alert": 60 * 60 * 3,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
    -1003983601225: {
        "name": "Австрія",
        "alert_time": 60 * 60 * 5,
        "repeat_alert": 60 * 60 * 5,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
    -4834145912: {
        "name": "Німеччина",
        "alert_time": 60 * 60 * 5,
        "repeat_alert": 60 * 60 * 5,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
    -5245803934: {
        "name": "Данія",
        "alert_time": 60 * 60 * 5,
        "repeat_alert": 60 * 60 * 5,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
     -5001379307: {
        "name": "Італія",
        "alert_time": 60 * 60 * 3,
        "repeat_alert": 60 * 60 * 3,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
     -4828212674: {
        "name": "Угорщина",
        "alert_time": 60 * 60 * 5,
        "repeat_alert": 60 * 60 * 5,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
     -1002342335330: {
        "name": "Пікасо",
        "alert_time": 60 * 60 * 4,
        "repeat_alert": 60 * 60 * 4,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
    -1002273397645: {
        "name": "Хорватія",
        "alert_time": 60 * 60 * 5,
        "repeat_alert": 60 * 60 * 5,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
    -5121283522: {
        "name": "Бельгія",
        "alert_time": 60 * 60 * 5,
        "repeat_alert": 60 * 60 * 5,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
    -5109854315: {
        "name": "Нідерланди",
        "alert_time": 60 * 60 * 5,
        "repeat_alert": 60 * 60 * 5,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
    -1002295396071: {
        "name": "М'які вікна",
        "alert_time": 60 * 60 * 1,
        "repeat_alert": 60 * 60 * 1,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
    -5105958051: {
        "name": "Ірландія",
        "alert_time": 60 * 60 * 5,
        "repeat_alert": 60 * 60 * 5,
        "mentions": "@stasnislaavv @rumyantsev58 @cheeenazes @pavloplotka",
    },
    # додавай скільки треба...
}
# ==============================


# ===== БАЗА ДАНИХ =====
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_state (
            chat_id INTEGER PRIMARY KEY,
            last_message_time REAL,
            last_alert_time REAL,
            alert_count INTEGER
        )
    """)
    conn.commit()
    conn.close()


def get_state(chat_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT last_message_time, last_alert_time, alert_count FROM chat_state WHERE chat_id = ?", (chat_id,))
    row = c.fetchone()
    conn.close()

    if row:
        return {
            "last_message_time": row[0],
            "last_alert_time": row[1],
            "alert_count": row[2],
        }
    else:
        default = {
            "last_message_time": time.time(),
            "last_alert_time": 0,
            "alert_count": 0,
        }
        save_state(chat_id, default)
        return default


def save_state(chat_id, state):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO chat_state (chat_id, last_message_time, last_alert_time, alert_count)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET
            last_message_time = excluded.last_message_time,
            last_alert_time = excluded.last_alert_time,
            alert_count = excluded.alert_count
    """, (chat_id, state["last_message_time"], state["last_alert_time"], state["alert_count"]))
    conn.commit()
    conn.close()
# ======================


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
                state = get_state(chat_id)
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

                    if state["last_alert_time"] == 0 or time_since_last_alert >= config["repeat_alert"]:
                        print("[MONITOR][" + config["name"] + "] Vidpravka alertu!")

                        now_str = datetime.now(TIMEZONE).strftime("%H:%M")
                        state["alert_count"] += 1

                        if state["alert_count"] == 1:
                            msg_text = (
                                "⚠️ Увага❗️ Вже "
                                + str(silence_min)
                                + " хвилин немає нових замовлень❗️ Час: "
                                + now_str
                            )
                        else:
                            msg_text = (
                                "🆘 Увага‼️ Вже "
                                + str(silence_min)
                                + " хвилин немає нових замовлень‼️ Час: "
                                + now_str
                                + "\n" + config["mentions"]
                            )

                        await bot.send_message(chat_id=chat_id, text=msg_text)

                        state["last_alert_time"] = now
                        save_state(chat_id, state)

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
    init_db()

    bot = Bot(token=BOT_TOKEN)
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    @client.on(events.NewMessage())
    async def handler(event):
        chat_id = event.chat_id

        if chat_id not in CHATS:
            return

        msg = event.message

        if msg.sender_id == 8408563049:
            return

        text_preview = (msg.text or "(media)")[:80]
        config = CHATS[chat_id]
        print("[UPDATE][" + config["name"] + "] sender_id=" + str(msg.sender_id) + " | " + text_preview)

        state = get_state(chat_id)
        state["last_message_time"] = time.time()
        state["alert_count"] = 0
        save_state(chat_id, state)

    await client.start(phone=TG_PHONE)

    for chat_id, config in CHATS.items():
        try:
            await client.get_entity(chat_id)
            print("[START] Pidpyska na " + config["name"] + " uspishna")
        except Exception as e:
            print("[START] Pidpyska na " + config["name"] + ": " + str(e))

    print("[START] Userbot zapushcheno, slukhaemo " + str(len(CHATS)) + " chaty")

    asyncio.create_task(monitor_loop(bot))

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
