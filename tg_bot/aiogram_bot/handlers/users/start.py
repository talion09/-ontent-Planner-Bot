import json
from datetime import datetime, timedelta, timezone

import aiohttp
from aiogram import Dispatcher
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart

from tg_bot import config, user_api
from tg_bot.aiogram_bot.keyboards.default.language import lang
from tg_bot.aiogram_bot.keyboards.default.main_menu import m_menu, admin_menu
from tg_bot.aiogram_bot.network.dto.response import Response
from tg_bot.aiogram_bot.network.dto.user import UserSchema
from tg_bot.aiogram_bot.states.users import User
from tg_bot.aiogram_bot.utils.constants import NewsChannel


async def bot_start(message: types.Message, state: FSMContext):
    await state.reset_state()

    params = {"key": "id",
              "value": message.from_user.id}
    user_response: Response[UserSchema] = Response[UserSchema].model_validate(
        await user_api.get_one_by_key_value(params=params))

    status = user_response.status

    _ = message.bot.get("lang")
    text = _("<b>Harvestly</b> - это простой и удобный бот для отложенного постинга, поддерживающий работу парсингом и ChatGPT\n\n \
<b>Бот позволяет:</b>\n\n \
🕕 Планировать выход публикаций в ваших каналах\n\n \
🗑 Автоматически удалять их по расписанию \n\n \
🧑‍🎨 Создавать и настраивать посты любого формата \n\n \
📡 Пользоваться парсингом из других каналов в Telegram \n\n \
⛓ Использовать и добаялять промпты ChatGPT для редактирвоания постов \n\n \
Новости сервиса - {}").format(NewsChannel)

    user_id = message.from_user.id
    if status == "success":
        # admins_list = [1574853044, 1696518783]
        admins_list = [1696518783]
        if user_id in admins_list:
            menu = admin_menu
        else:
            menu = m_menu
        await message.bot.send_message(user_id, f"{text}", reply_markup=menu)
        # await message.bot.send_message(user_id, f"{test}")
    else:
        # await message.bot.send_message(user_id, f"{text}")
        await message.answer(
            f"Здравствуйте! {message.from_user.full_name}\nВыберите язык:\n\nAssalomu alaykum!\nTilni tanlang:",
            reply_markup=lang)
        await User.Lang.set()


# User.Lang
async def info_lang(message: types.Message, state: FSMContext):
    if message.text == "🇷🇺 Ru":
        language = "ru"
    else:
        language = "uz"
    await state.update_data(lang=language)
    await User.Next.set()
    await info_next(message, state)


# User.Next
async def info_next(message: types.Message, state: FSMContext):
    data = await state.get_data()
    language = data.get("lang")
    data = {"id": message.from_user.id, "time_zone": 0, "lang": language}
    user_response: Response[UserSchema] = Response[UserSchema].model_validate(await user_api.post_add(data=data))
    await bot_start(message, state)


def register_start(dp: Dispatcher):
    dp.register_message_handler(bot_start, CommandStart(), state="*")
    dp.register_message_handler(info_lang, state=User.Lang, text=["🇺🇿 Uz", "🇷🇺 Ru"])
    dp.register_message_handler(info_next, state=User.Next)
