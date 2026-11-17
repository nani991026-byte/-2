import asyncio
import logging
import os

from dotenv import load_dotenv
from maxapi import Bot, Dispatcher
from maxapi.types import MessageCreated, CommandStart, MessageButton, ButtonsPayload

load_dotenv()

# Bothost у нас уже содержит MAX_BOT_TOKEN.
# Оставляем несколько вариантов на случай разных настроек.
TOKEN = (
    os.getenv("MAX_BOT_TOKEN")
    or os.getenv("BOT_TOKEN")
    or os.getenv("MAX_TOKEN")
)

if not TOKEN:
    raise RuntimeError("Токен MAX не найден. Проверь переменные окружения Bothost.")

logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN)
dp = Dispatcher()


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


@dp.message_created(CommandStart())
async def start(event: MessageCreated):
    await event.message.answer(
        text=(
            "🏗️ <b>СтройУют</b>\n\n"
            "Бот строительной компании.\n"
            "Выберите нужное действие:"
        ),
        attachments=[main_menu()],
    )


@dp.message_created()
async def all_messages(event: MessageCreated):
    # /start уже обработан выше
    text = getattr(event.message.body, "text", "") or ""

    if text.startswith("/start"):
        return

    replies = {
        "🧮 Рассчитать стоимость":
            "🧮 Расчёт стоимости подключим следующим этапом.",
        "🏠 Наши услуги":
            "🏠 Здесь будет список строительных услуг и цен.",
        "📅 Записаться на замер":
            "📅 Здесь клиент сможет выбрать дату и время замера.",
        "📄 Оформить договор":
            "📄 Здесь будет автоматическое оформление договора.",
        "📋 Мои заявки":
            "📋 Здесь будут отображаться заявки клиента.",
        "📞 Связаться с менеджером":
            "📞 Напишите свой вопрос — менеджер свяжется с вами.",
    }

    answer = replies.get(
        text,
        "Выберите действие в меню 👇"
    )

    await event.message.answer(
        text=answer,
        attachments=[main_menu()],
    )


async def main():
    logging.info("СтройУют: бот запущен и ожидает сообщения.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
