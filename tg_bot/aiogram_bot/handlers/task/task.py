import logging

import aiohttp
from aiogram import types
from aiogram.types import Chat, InlineKeyboardButton, InlineKeyboardMarkup

from tg_bot import subscription_api, scheduler, user_channel_settings_api, user_channel_api, config
from tg_bot.aiogram_bot.keyboards.inline.subscription_payment.inline_button import subscription_payment_clb
from tg_bot.aiogram_bot.network.dto.response import Response
from tg_bot.aiogram_bot.network.dto.subscription import SubscriptionSchema
from tg_bot.aiogram_bot.network.dto.user_channel import UserChannelSchema
from tg_bot.aiogram_bot.utils.constants import Support


async def check_subscribers_and_subscription(channel_id: int, user_id: int):
    stop_task = False
    call = types.CallbackQuery.get_current()

    chat: Chat = await call.bot.get_chat(channel_id)
    member_count = await chat.get_member_count()

    subscription_response: Response[SubscriptionSchema] = Response[SubscriptionSchema].model_validate(
        await subscription_api.get_one_by_key_value(params={"key": "id", "value": 1})
    )

    try:
        member_status = await call.bot.get_chat_member(subscription_response.data.channel_name, user_id)
        if member_count > subscription_response.data.subscribers_quantity or member_status.status not in ['member']:
            stop_task = True
    except Exception as e:
        logging.error(f"Ошибка при получении статуса пользователя: {e}")
        stop_task = True

    if stop_task:
        try:
            scheduler.remove_job(f'check_sub_{channel_id}')
        except Exception as e:
            logging.error(str(e))

        success = Response[bool].model_validate(await user_channel_settings_api.update_subscription_id_by_channel_ids(
            data={
                "channel_ids": [channel_id],
                "new_subscription_id": None
            }
        ))

        markup = InlineKeyboardMarkup(row_width=1)

        text = f'''
<b>🚨 Превышены ограничения бесплатной версии!</b>\n
Не беспокойтесь, вы можете легко продлить свою подписку и продолжить наслаждаться всеми преимуществами!\n\n✅  Продолжайте использовать все наши премиальные функции.\n
✅ Получайте постоянные обновления и улучшения.\n\n✅ Поддерживайте нашу команду, чтобы мы могли продолжать создавать полезный контент.\n\nМы ценим каждого пользователя и надеемся, что вы останетесь с нами. Если у вас есть вопросы или пожелания, мы всегда готовы помочь!\n\nДля обратной связи: {Support}
                '''

        payment_button = InlineKeyboardButton(
            text="Оплатить подписку 💰",
            callback_data=subscription_payment_clb.new(
                a="c",
                p="n_dis",
                t="p"
            )
        )

        back_button = InlineKeyboardButton(
            text="⬅️ Перейти на бесплатную версию",
            callback_data=subscription_payment_clb.new(
                a="c",
                p="n_dis",
                t="f"
            )
        )

        markup.add(payment_button)
        markup.add(back_button)

        user_channel_response: Response[list[UserChannelSchema]] = Response[list[UserChannelSchema]].model_validate(
            await user_channel_api.find_by_channels_id(data={"ids": [channel_id]})
        )
        for user_channel in user_channel_response.data:
            try:
                await call.bot.send_message(user_channel.user_id, text, reply_markup=markup)
            except Exception as e:
                logging.error(f"check_subscribers_and_subscription {e}")


async def auto_delete_timer_job(message_id: int, channel_id: int):
    call = types.CallbackQuery.get_current()

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/one/key_value/",
                params={
                    "key": "id",
                    "value": message_id
                }) as response:
            message_response = await response.json()

    messages_id = message_response.get("data").get("message").get("message")
    if type(messages_id) is list:
        for msg_id in messages_id:
            await call.bot.delete_message(channel_id, int(msg_id))
    else:
        await call.bot.delete_message(channel_id, int(messages_id))

    data = {"id": message_id, "message": None}
    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/",
                               json=data) as response:
            response = await response.json()