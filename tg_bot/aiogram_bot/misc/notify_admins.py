import logging

from aiogram import Dispatcher

from tg_bot import config


async def on_startup_notify(dp: Dispatcher):
    ADMINS = config.tg_bot.admin_ids
    try:
        await dp.bot.send_message(int(ADMINS), "Бот Запущен")
    except Exception as err:
        logging.exception(err)