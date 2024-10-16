# Harvester bot

## Виртуальное окружение и зависимости

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

## Переменные окружения

NUL> .env

#### Добавить DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS, BOT_TOKEN, ADMIN_IDS, API_ID, API_HASH, API_KEY

## Миграции

alembic init migrations

alembic revision --autogenerate -m "Create database"

alembic upgrade head

## Запуск

python -m src.bot.dispatcher

## Для локального теста

файл .env поменять BOT_TOKEN
использовать сессию юзер бота под другим номером
