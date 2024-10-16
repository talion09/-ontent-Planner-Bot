from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

m_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Создать пост"),
            KeyboardButton(text="Контент-план")
        ],
        [
            KeyboardButton(text="Парсинг"),
            KeyboardButton(text="Настройки")
        ]
    ],
    resize_keyboard=True)


admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Создать пост"),
            KeyboardButton(text="Контент-план")
        ],
        [
            KeyboardButton(text="Парсинг"),
            KeyboardButton(text="Настройки")
        ],
        [
            KeyboardButton(text="Рекламный пост"),
            KeyboardButton(text="Статистика")
        ]
        # [
        #     KeyboardButton(text="💰 Оплата подписки")
        # ]
    ],
    resize_keyboard=True)
