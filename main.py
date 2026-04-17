from datetime import datetime
import time
import json
import os
import asyncio
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes, TypeHandler
)

TOKEN = "8408563049:AAHIzyYz50wf5nf1gIbHkdIBrDIGAJcg3NA"
CHAT_ID = -1003342150417
TIMEZONE = ZoneInfo("Europe/Kyiv")
NIGHT_START = 23
NIGHT_END = 8
ALERT_TIME = 60 * 60       # 1 година тиші → алерт
REPEAT_ALERT = 60 * 60     # повторний алерт не частіше ніж раз на годину

# --- Персистентний стан через файл ---
# Зберігаємо на диск щоб Railway-рестарт не скидав таймер
STATE_FILE = "/tmp/bot_state.json"

def load_state() -> dict:
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(state: dict):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception as e:
        print(f"[STATE] Не вдалося зберегти стан: {e}")

# Ініціалізація — якщо є збережений стан, беремо його
# якщо немає — вважаємо що замовлення тільки щойно було (не спамимо при старті)
_state = load_state()
last_message_time: float = _state.get("last_message_time", time.time())
last_alert_time: float = _state.get("last_alert_time", 0)

def is_night_time() -> bool:
    """Повертає True якщо зараз нічний час (23:00 — 08:00 Kyiv)"""
    now_hour = datetime.now(TIMEZONE).hour
    # Коректна перевірка через північ
    return now_hour >= NIGHT_START or now_hour < NIGHT_END

async def handle_any_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ловимо будь-який апдейт і оновлюємо таймер якщо це наш чат"""
    global last_message_time

    # Збираємо повідомлення з усіх можливих полів апдейту
    msg = (
        update.message or
        update.channel_post or
        update.edited_message or
        update.edited_channel_post
    )

    if msg is None:
        # Може бути callback_query або інший тип — ігноруємо
        return

    chat_id = msg.chat.id  # .chat_id не існує, тільки .id

    sender = "невідомо"
    if msg.from_user:
        sender = f"user:{msg.from_user.id} (@{msg.from_user.username})"
    elif msg.sender_chat:
        sender = f"channel/anon:{msg.sender_chat.id}"

    text_preview = (msg.text or msg.caption or "(медіа/без тексту)")[:80]
    print(f"[UPDATE] chat={chat_id} | sender={sender} | text={text_preview}")

    if chat_id == CHAT_ID:
        last_message_time = time.time()
        save_state({"last_message_time": last_message_time, "last_alert_time": last_alert_time})
        print(f"[UPDATE] ✅ Таймер оновлено: {datetime.now(TIMEZONE).strftime('%H:%M:%S')}")
    else:
        print(f"[UPDATE] ⚠️ Чужий чат ({chat_id}), ігноруємо")

async def monitor(context: ContextTypes.DEFAULT_TYPE):
    """Кожні 30 секунд перевіряємо чи треба надіслати алерт"""
    global last_alert_time

    try:
        if is_night_time():
            now_str = datetime.now(TIMEZONE).strftime('%H:%M')
            print(f"[MONITOR] 🌙 Ніч ({now_str}) — пропуск")
            return

        now = time.time()
        silence = now - last_message_time
        silence_min = int(silence // 60)
        silence_sec = int(silence % 60)
        print(f"[MONITOR] ⏱ Тиша: {silence_min} хв {silence_sec} сек")

        if silence >= ALERT_TIME:
            time_since_last_alert = now - last_alert_time

            # Відправляємо якщо: ще жодного алерту АБО пройшла година після попереднього
            if last_alert_time == 0 or time_since_last_alert >= REPEAT_ALERT:
                print("[MONITOR] 🚨 Відправка алерту!")
                await context.bot.send_message(
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
                next_alert_in = int((REPEAT_ALERT - time_since_last_alert) // 60)
                print(f"[MONITOR] Алерт надіслано {int(time_since_last_alert // 60)} хв тому, наступний через ~{next_alert_in} хв")
        else:
            print(f"[MONITOR] ✅ Все ок, до алерту ще {int((ALERT_TIME - silence) // 60)} хв")

    except Exception as e:
        print(f"[MONITOR] ❌ ПОМИЛКА: {e}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # TypeHandler з group=-1 щоб спрацьовував ПЕРШИМ перед усіма іншими
    app.add_handler(TypeHandler(Update, handle_any_update), group=-1)

    # Моніторинг кожні 30 секунд
    app.job_queue.run_repeating(monitor, interval=30, first=10)

    print(f"[START] 🤖 Бот запущено. CHAT_ID={CHAT_ID}")
    print(f"[START] Завантажено стан: last_msg={datetime.fromtimestamp(last_message_time, TIMEZONE).strftime('%H:%M:%S')}")

    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        # ❌ Прибрали drop_pending_updates=True
        # Тепер замовлення що прийшли поки бот був офлайн — обробляться
        drop_pending_updates=False
    )

if __name__ == "__main__":
    main()
