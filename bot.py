import asyncio
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API = "https://platform-api2.max.ru"

# Bothost:
# Переменная MAX_TOKEN должна содержать токен MAX-бота.
TOKEN = os.getenv("MAX_TOKEN", "").strip()

if not TOKEN:
    print("ОШИБКА: не задана переменная MAX_TOKEN")
    sys.exit(1)


def api_request(method: str, path: str, payload=None, timeout=100):
    url = API + path
    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json",
    }

    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = Request(url, data=data, headers=headers, method=method)

    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"MAX API HTTP {e.code}: {raw}") from e
    except URLError as e:
        raise RuntimeError(f"Ошибка соединения с MAX API: {e}") from e


def get_bot():
    return api_request("GET", "/me")


def get_updates(marker=None):
    params = "?limit=100&timeout=30"
    if marker is not None:
        params += f"&marker={marker}"
    return api_request("GET", "/updates" + params, timeout=40)


def send_message(chat_id, text, buttons=None):
    payload = {"text": text}

    if buttons:
        payload["attachments"] = [{
            "type": "inline_keyboard",
            "payload": {"buttons": buttons}
        }]

    return api_request(
        "POST",
        f"/messages?chat_id={chat_id}",
        payload
    )


def main_menu():
    return [
        [
            {"type": "callback", "text": "📐 Рассчитать", "payload": "calculate"},
            {"type": "callback", "text": "📋 Услуги", "payload": "services"},
        ],
        [
            {"type": "callback", "text": "📞 Связаться", "payload": "contact"},
            {"type": "callback", "text": "ℹ️ О нас", "payload": "about"},
        ],
    ]


def text_from_update(update):
    message = update.get("message") or {}
    body = message.get("body") or {}
    return (body.get("text") or "").strip()


def chat_id_from_update(update):
    message = update.get("message") or {}
    recipient = message.get("recipient") or {}
    return recipient.get("chat_id")


async def handle_update(update):
    if update.get("update_type") != "message_created":
        return

    chat_id = chat_id_from_update(update)
    if not chat_id:
        return

    text = text_from_update(update).lower()

    if text in ("/start", "start", "начать", "привет", "здравствуйте"):
        await asyncio.to_thread(
            send_message,
            chat_id,
            "🏗️ Строим Уют\n\nПривет! Я бот строительной компании.\n\nВыберите действие:",
            main_menu()
        )
        return

    await asyncio.to_thread(
        send_message,
        chat_id,
        "Я получил сообщение 👌\n\nВыберите действие в меню:",
        main_menu()
    )


async def main():
    print("=== MAX BOT START ===")
    print("Проверяю токен...")

    try:
        bot = await asyncio.to_thread(get_bot)
    except Exception as e:
        print("ОШИБКА ПРОВЕРКИ ТОКЕНА:")
        print(e)
        sys.exit(1)

    print("Токен принят MAX API.")
    print(f"Бот: {bot.get('name') or bot.get('username') or bot.get('user_id')}")
    print("Бот запущен. Жду сообщения...")

    marker = None

    while True:
        try:
            result = await asyncio.to_thread(get_updates, marker)
            marker = result.get("marker", marker)

            for update in result.get("updates", []):
                try:
                    await handle_update(update)
                except Exception as e:
                    print(f"Ошибка обработки обновления: {e}")

        except Exception as e:
            print(f"Ошибка получения обновлений: {e}")
            await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(main())
