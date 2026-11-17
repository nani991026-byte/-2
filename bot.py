import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://platform-api2.max.ru"
TOKEN = os.getenv("MAX_TOKEN", "").strip()

BASE_DIR = Path(__file__).resolve().parent
PHOTO = BASE_DIR / "assets" / "main.jpg"

if not TOKEN:
    print("ОШИБКА: в Bothost не задана переменная MAX_TOKEN")
    sys.exit(1)

# В текущем окружении Bothost оставляем совместимость
# с уже работающим подключением к MAX.
SSL_CONTEXT = ssl._create_unverified_context()


def request(method, path, data=None, timeout=40):
    url = API + path
    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    body = None
    if data is not None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method,
    )

    with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def keyboard(rows):
    return {
        "type": "inline_keyboard",
        "payload": {"buttons": rows},
    }


def button(text, payload):
    return {
        "type": "callback",
        "text": text,
        "payload": payload,
    }


def link_button(text, url):
    return {
        "type": "link",
        "text": text,
        "url": url,
    }


def send_message(chat_id, text, attachments=None):
    body = {"text": text}
    if attachments:
        body["attachments"] = attachments

    return request(
        "POST",
        "/messages?chat_id=" + urllib.parse.quote(str(chat_id)),
        body,
    )


def answer_callback(callback_id):
    try:
        request(
            "POST",
            "/answers?callback_id=" + urllib.parse.quote(str(callback_id)),
            {"notification": "Готово"},
        )
    except Exception as e:
        print("Не удалось подтвердить callback:", e)


def upload_image():
    if not PHOTO.exists():
        return None

    # Получаем URL загрузки у MAX.
    info = request("POST", "/uploads?type=image")
    upload_url = info.get("url")
    if not upload_url:
        print("MAX не вернул URL загрузки изображения:", info)
        return None

    boundary = "----StroyUyutBoundary7MA4YWxkTrZu0gW"
    file_data = PHOTO.read_bytes()
    filename = PHOTO.name

    head = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="data"; filename="{filename}"\r\n'
        "Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8")
    tail = f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        upload_url,
        data=head + file_data + tail,
        headers={
            "Authorization": TOKEN,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=60) as response:
        result = json.loads(response.read().decode("utf-8"))

    # Формат ответа MAX для изображений может содержать token
    # внутри photos/photoIds. Достаём первый найденный токен.
    token = result.get("token")
    if token:
        return token

    photos = result.get("photos", {})
    if isinstance(photos, dict):
        for value in photos.values():
            if isinstance(value, dict) and value.get("token"):
                return value["token"]
            if isinstance(value, str):
                return value

    print("Не удалось получить token изображения:", result)
    return None


def main_menu():
    return keyboard([
        [button("🧮 Рассчитать стоимость", "calc")],
        [
            button("🏠 Наши услуги", "services"),
            button("📅 Записаться на замер", "measure"),
        ],
        [
            button("📋 Мои заявки", "requests"),
            button("📄 Договор", "contract"),
        ],
        [
            button("🌐 Наш сайт", "site"),
            button("📞 Связаться", "contact"),
        ],
    ])


def back_menu():
    return keyboard([[button("⬅️ Назад", "home")]])


def send_home(chat_id):
    text = (
        "**СТРОИМ УЮТ**\n\n"
        "Строительство и ремонт под ключ.\n"
        "Рассчитаем стоимость, запишем на замер "
        "и поможем оформить заказ.\n\n"
        "Выберите действие 👇"
    )

    attachments = []

    # Картинка должна быть предварительно загружена в MAX.
    # Токен сохраняем в .image_token, чтобы не загружать фото каждый раз.
    token_file = BASE_DIR / ".image_token"

    image_token = token_file.read_text(encoding="utf-8").strip() if token_file.exists() else ""

    if PHOTO.exists() and not image_token:
        try:
            image_token = upload_image() or ""
            if image_token:
                token_file.write_text(image_token, encoding="utf-8")
                time.sleep(2)
        except Exception as e:
            print("Ошибка загрузки главной фотографии:", e)

    if image_token:
        attachments.append({
            "type": "image",
            "payload": {"token": image_token},
        })

    attachments.append(main_menu())
    send_message(chat_id, text, attachments)


def send_section(chat_id, title, text, rows=None):
    attachments = [keyboard(rows or [[button("⬅️ Назад", "home")]])]
    send_message(chat_id, f"**{title}**\n\n{text}", attachments)


def handle_callback(update):
    callback = update.get("callback", {})
    callback_id = callback.get("callback_id") or update.get("callback_id")
    payload = callback.get("payload")

    if callback_id:
        answer_callback(callback_id)

    message = update.get("message") or {}
    recipient = message.get("recipient") or {}
    chat_id = recipient.get("chat_id")

    if not chat_id:
        chat_id = update.get("chat_id")

    if not chat_id:
        return

    if payload == "home":
        send_home(chat_id)

    elif payload == "calc":
        send_section(
            chat_id,
            "🧮 Рассчитать стоимость",
            "Что будем рассчитывать?\n\nВыберите вид работ:",
            [
                [
                    button("🧱 Кладка", "calc_masonry"),
                    button("🧱 Плитка", "calc_tile"),
                ],
                [
                    button("🎨 Отделка", "calc_finish"),
                    button("⚡ Электрика", "calc_electric"),
                ],
                [button("🔧 Другое", "calc_other")],
                [button("⬅️ Назад", "home")],
            ],
        )

    elif payload == "services":
        send_section(
            chat_id,
            "🏠 Наши услуги",
            "• Кладочные работы\n"
            "• Укладка плитки\n"
            "• Отделочные работы\n"
            "• Электромонтаж\n"
            "• Ремонт помещений\n"
            "• Строительство под ключ",
        )

    elif payload == "measure":
        send_section(
            chat_id,
            "📅 Записаться на замер",
            "Оставьте заявку — менеджер свяжется с вами "
            "и согласует удобную дату и время.",
            [
                [button("📞 Оставить заявку", "contact")],
                [button("⬅️ Назад", "home")],
            ],
        )

    elif payload == "requests":
        send_section(
            chat_id,
            "📋 Мои заявки",
            "Пока сохранённых заявок нет.\n\n"
            "После добавления настоящего калькулятора "
            "здесь будет история ваших обращений.",
        )

    elif payload == "contract":
        send_section(
            chat_id,
            "📄 Договор",
            "Здесь будет отображаться договор по вашей заявке.\n\n"
            "В следующем этапе подключим автоматическое "
            "заполнение договора данными клиента и компании.",
        )

    elif payload == "site":
        send_section(
            chat_id,
            "🌐 Наш сайт",
            "Ссылка на сайт добавится сюда после его запуска.",
        )

    elif payload == "contact":
        send_section(
            chat_id,
            "📞 Связаться с нами",
            "Напишите нам — менеджер свяжется с вами.",
        )

    elif isinstance(payload, str) and payload.startswith("calc_"):
        send_section(
            chat_id,
            "📐 Расчёт стоимости",
            "Вы выбрали этот вид работ.\n\n"
            "Следующим обновлением добавим вопросы про площадь, "
            "объём и параметры работ, после чего бот будет "
            "считать предварительную стоимость.",
            [
                [button("⬅️ К выбору работ", "calc")],
                [button("🏠 Главное меню", "home")],
            ],
        )


def handle_message(update):
    message = update.get("message") or {}
    recipient = message.get("recipient") or {}
    chat_id = recipient.get("chat_id")
    body = message.get("body") or {}
    text = (body.get("text") or "").strip()

    if not chat_id:
        return

    if text in ("/start", "Старт", "Строим Уют"):
        send_home(chat_id)
    elif text:
        send_message(
            chat_id,
            "Выберите действие в меню 👇",
            [main_menu()],
        )


def main():
    print("Строим Уют: бот запущен")

    marker = None

    while True:
        try:
            params = {
                "limit": 100,
                "timeout": 30,
            }
            if marker is not None:
                params["marker"] = marker

            query = urllib.parse.urlencode(params)
            result = request("GET", "/updates?" + query, timeout=40)

            marker = result.get("marker", marker)

            for update in result.get("updates", []):
                update_type = update.get("update_type")

                if update_type == "message_created":
                    handle_message(update)

                elif update_type == "message_callback":
                    handle_callback(update)

        except Exception as e:
            print("Ошибка цикла MAX:", repr(e))
            time.sleep(3)


if __name__ == "__main__":
    main()
