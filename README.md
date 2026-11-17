# СтройПроект — MAX бот

Стартовая версия строительного бота.

## Файлы

- `bot.py` — код бота
- `prices.json` — цены
- `requirements.txt` — зависимости
- `.env.example` — пример переменной токена
- `.gitignore` — не даёт загрузить `.env` в GitHub

## Первый запуск

1. Установить зависимости:
```bash
pip install -r requirements.txt
```

2. Создать рядом с `bot.py` файл `.env`:
```env
MAX_BOT_TOKEN=ваш_токен_MAX
```

3. Запустить:
```bash
python bot.py
```

Для первого теста используется Long Polling. Для production MAX рекомендует Webhook.
