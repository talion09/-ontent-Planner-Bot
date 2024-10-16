from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

lang = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🇷🇺 Ru"),
            KeyboardButton(text="🇺🇿 Uz")
        ]
    ], resize_keyboard=True)