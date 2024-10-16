import aiohttp
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from tg_bot import config
from tg_bot.aiogram_bot.filters.is_admin import IsMediaGroup, IsAdmin


async def admin_statistic(message: types.Message, state: FSMContext):
    await state.reset_state()

    async with aiohttp.ClientSession() as session:
        async with session.get(url=f"http://{config.api.api_db}:{config.api.api_db_port}/admin_statistics/") as response:
            respons = await response.json()
            data = respons.get("data")

            all_users = int(data.get("users_quantity"))

            free_subscriptions = int(data.get("free_subscriptions_quantity"))
            free_subscription_rfm = data.get("free_subscription_rfm")
            active_user_quantity_free = int(data.get("active_user_quantity_free"))
            constant_active = int(free_subscription_rfm.get("constant_active"))
            leaving = int(free_subscription_rfm.get("leaving"))
            sleeping = int(free_subscription_rfm.get("sleeping"))

            paid_subscriptions = int(data.get("premium_subscriptions_quantity"))
            premium_subscription_rfm = data.get("premium_subscription_rfm")
            active_user_quantity_premium = int(data.get("active_user_quantity_premium"))
            premium_constant_active = int(premium_subscription_rfm.get("constant_active"))
            premium_leaving = int(premium_subscription_rfm.get("leaving"))
            premium_sleeping = int(premium_subscription_rfm.get("sleeping"))

            if data.get("telegram_parsed_posts") is not None:
                telegram_parsed_posts = int(data.get("telegram_parsed_posts"))
            else:
                telegram_parsed_posts = 0

    text = f"""
📈 Статистика
Общая аудитория: {all_users}

Кол-во бесплатных подписок: {free_subscriptions}
1. Активные: {constant_active}
2. Пассивные: {leaving}
3. Уходящие: {sleeping}
Активны за последние 24 часа: {active_user_quantity_free}

Кол-во платных подписок: {paid_subscriptions}
1. Активные: {premium_constant_active}
2. Пассивные: {premium_leaving}
3. Уходящие: {premium_sleeping}
Активны за последние 24 часа: {active_user_quantity_premium}

Спаршено постов 
Telegram: {telegram_parsed_posts}
"""
    msg = await message.bot.send_message(message.from_user.id, text)


def register_statistics(dp: Dispatcher):
    dp.register_message_handler(admin_statistic, IsAdmin(), text="Статистика", state="*")
    dp.register_message_handler(admin_statistic, IsAdmin(),  text="Статистика")

