import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from tg_bot import config, scheduler
from tg_bot.aiogram_bot.filters.is_admin import IsAdmin, IsMediaGroup, IsGroup, IsUserBot
from tg_bot.aiogram_bot.handlers.admins.admins_handler import register_admins_handler
from tg_bot.aiogram_bot.handlers.admins.calendar_admin import register_calendar_admin
from tg_bot.aiogram_bot.handlers.admins.statistics import register_statistics
from tg_bot.aiogram_bot.handlers.users.content.content_calendar_handler import register_content_calendar_handler
from tg_bot.aiogram_bot.handlers.users.content.content_plan import register_content_plan
from tg_bot.aiogram_bot.handlers.users.create.calendar_handler import register_calendar_handler
from tg_bot.aiogram_bot.handlers.users.create.create_post import register_create_post
from tg_bot.aiogram_bot.handlers.users.create.setting_media import register_setting_media
from tg_bot.aiogram_bot.handlers.users.parsing import register_parsing
from tg_bot.aiogram_bot.handlers.users.settings import register_settings
from tg_bot.aiogram_bot.handlers.users.start import register_start
from tg_bot.aiogram_bot.handlers.users.subscription_payment.subscription_payment import register_subscription_payment
from tg_bot.aiogram_bot.middlewares.language_mid import setup_middleware
from tg_bot.aiogram_bot.misc.notify_admins import on_startup_notify
from tg_bot.aiogram_bot.misc.set_bot_commands import set_default_commands

logger = logging.getLogger(__name__)


def register_all_filters(dp):
    dp.filters_factory.bind(IsAdmin)
    dp.filters_factory.bind(IsMediaGroup)
    dp.filters_factory.bind(IsGroup)
    dp.filters_factory.bind(IsUserBot)


def register_all_handlers(dp):
    register_start(dp)

    register_statistics(dp)
    register_admins_handler(dp)
    register_calendar_admin(dp)

    register_settings(dp)
    register_setting_media(dp)
    register_calendar_handler(dp)
    register_content_plan(dp)
    register_content_calendar_handler(dp)
    register_subscription_payment(dp)
    register_parsing(dp)
    register_create_post(dp)


async def main():
    storage = MemoryStorage()
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp = Dispatcher(bot, storage=storage)

    i18n = setup_middleware(dp)
    lang = i18n.gettext

    bot['config'] = config
    bot['lang'] = lang

    register_all_filters(dp)
    register_all_handlers(dp)

    await set_default_commands(dp)
    await on_startup_notify(dp)

    try:
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    scheduler.start()
    loop.run_until_complete(main())
