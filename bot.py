import asyncio
import logging
import os
import json
from pathlib import Path

from dotenv import load_dotenv
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, CommandStart, MessageCreated, MessageButton, ButtonsPayload

load_dotenv()

if not os.getenv("MAX_BOT_TOKEN"):
    raise RuntimeError(
        "MAX_BOT_TOKEN не найден. Создайте файл .env и добавьте туда токен MAX."
    )

logging.basicConfig(level=logging.INFO)

bot = Bot()
dp = Dispatcher()

BASE_DIR = Path(__file__).resolve().parent
PRICES_FILE = BASE_DIR / "prices.json"


def load_prices():
    with open(PRICES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def main_menu():
    buttons = [
        [
            MessageButton(text="🧮 Рассчитать стоимость"),
            MessageButton(text="🏠 Наши услуги"),
        ],
        [
            MessageButton(text="📅 Записаться на замер"),
            MessageButton(text="📄 Оформить договор"),
        ],
        [
            MessageButton(text="📋 Мои заявки"),
            MessageButton(text="📞 Связаться с менеджером"),
        ],
    ]
    return ButtonsPayload(buttons=buttons).pack()


@dp.bot_started()
async def bot_started(event: BotStarted):
    await event.bot.send_message(
        chat_id=event.chat_id,
        text=(
            "🏗️ <b>СтройПроект</b>\n\n"
            "Помогу рассчитать стоимость работ, записаться на замер "
            "и подготовить данные для договора.\n\n"
            "Выберите действие 👇"
        ),
        format="html",
        attachments=[main_menu()],
    )


@dp.message_created(CommandStart())
async def start(event: MessageCreated):
    await event.message.answer(
        text=(
            "🏗️ <b>СтройПроект</b>\n\n"
            "Добро пожаловать! Что хотите сделать?"
        ),
        format="html",
        attachments=[main_menu()],
    )


@dp.message_created()
async def messages(event: MessageCreated):
    text = (event.message.body.text or "").strip()

    if text == "🏠 Наши услуги":
        prices = load_prices()
        lines = [
            f"• {item['name']} — от {item['price']} ₽/{item['unit']}"
            for item in prices.values()
        ]
        await event.message.answer(
            text="🏠 <b>Наши услуги</b>\n\n" + "\n".join(lines),
            format="html",
            attachments=[main_menu()],
        )

    elif text == "🧮 Рассчитать стоимость":
        await event.message.answer(
            text=(
                "🧮 <b>Расчёт стоимости</b>\n\n"
                "Для первого теста напишите:\n"
                "<code>площадь 50</code>\n\n"
                "Получите предварительную стоимость штукатурки."
            ),
            format="html",
            attachments=[main_menu()],
        )

    elif text.lower().startswith("площадь "):
        try:
            area = float(text.split(" ", 1)[1].replace(",", "."))
            price = float(load_prices()["plaster"]["price"])
            total = area * price

            await event.message.answer(
                text=(
                    f"📐 Площадь: <b>{area:g} м²</b>\n"
                    f"💰 Ориентировочная стоимость: <b>{total:,.0f} ₽</b>\n\n"
                    "⚠️ Предварительный расчёт. Точная стоимость "
                    "определяется после замера."
                ).replace(",", " "),
                format="html",
                attachments=[main_menu()],
            )
        except (ValueError, KeyError):
            await event.message.answer(
                text="Не понял площадь. Пример: <code>площадь 50</code>",
                format="html",
                attachments=[main_menu()],
            )

    elif text == "📅 Записаться на замер":
        await event.message.answer(
            text=(
                "📅 <b>Запись на замер</b>\n\n"
                "Напишите одним сообщением:\n"
                "1. Имя\n"
                "2. Телефон\n"
                "3. Адрес\n"
                "4. Желаемая дата\n\n"
                "Следующим этапом сделаем пошаговую запись "
                "с выбором даты и времени."
            ),
            format="html",
            attachments=[main_menu()],
        )

    elif text == "📄 Оформить договор":
        await event.message.answer(
            text=(
                "📄 <b>Оформление договора</b>\n\n"
                "Здесь будет автоматическое формирование договора "
                "из данных заявки: заказчик, объект, работы, стоимость, "
                "сроки и реквизиты исполнителя.\n\n"
                "Пока это тестовый экран."
            ),
            format="html",
            attachments=[main_menu()],
        )

    elif text == "📋 Мои заявки":
        await event.message.answer(
            text=(
                "📋 <b>Мои заявки</b>\n\n"
                "Пока заявок нет. После подключения базы здесь "
                "будут отображаться ваши заявки."
            ),
            format="html",
            attachments=[main_menu()],
        )

    elif text == "📞 Связаться с менеджером":
        await event.message.answer(
            text="📞 Напишите сообщение — менеджер свяжется с вами.",
            attachments=[main_menu()],
        )

    else:
        await event.message.answer(
            text="Выберите действие в меню 👇",
            attachments=[main_menu()],
        )


async def main():
    # Long Polling используем только для первого теста.
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
