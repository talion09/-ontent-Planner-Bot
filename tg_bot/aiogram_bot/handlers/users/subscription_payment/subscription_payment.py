import logging
from datetime import datetime, timedelta
from typing import Union, Optional

import pytz
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dateutil.relativedelta import relativedelta

from tg_bot import subscription_api, channel_api, user_channel_settings_api, user_api, payment_api, scheduler, config, \
    paywave_api, user_channel_api, mail_api, payment_db_api
from tg_bot.aiogram_bot.handlers.task.task import check_subscribers_and_subscription
from tg_bot.aiogram_bot.handlers.users.content.content_plan import back_to_content
from tg_bot.aiogram_bot.handlers.users.create.create_post import back_to_creating
from tg_bot.aiogram_bot.handlers.users.parsing import parsing_user_channel
from tg_bot.aiogram_bot.handlers.users.settings import chatgpt_settings, back_to_user_settings
from tg_bot.aiogram_bot.handlers.users.subscription_payment.finished import subscription_finished
from tg_bot.aiogram_bot.handlers.users.subscription_payment.state import SubscriptionPaymentState
from tg_bot.aiogram_bot.keyboards.inline.subscription_payment.inline_button import subscription_payment_clb, \
    subscription_payment_back_clb, \
    subscription_payment_channel_tap_clb, subscription_payment_check_invoice_clb, subscription_payment_month_tap_clb, \
    subscription_payment_free_clb, \
    subscription_payment_trial_clb
from tg_bot.aiogram_bot.network.dto.channel import ChannelSchema
from tg_bot.aiogram_bot.network.dto.payment import InvoiceSchema, PaywaveInvoiceSchema, \
    PaywaveInvoiceStatusSchema
from tg_bot.aiogram_bot.network.dto.payment_db import PaymentDbSchema
from tg_bot.aiogram_bot.network.dto.paywave import PaywaveSchema
from tg_bot.aiogram_bot.network.dto.response import Response
from tg_bot.aiogram_bot.network.dto.subscription import SubscriptionSchema
from tg_bot.aiogram_bot.network.dto.user import UserSchema
from tg_bot.aiogram_bot.network.dto.user_channel import UserChannelSchema
from tg_bot.aiogram_bot.network.dto.user_channel_settings import UserChannelSettingsSchema
from tg_bot.aiogram_bot.utils.constants import FreeSubscription, TrialSubscription, PremiumSubscription, MonthOffer
from tg_bot.aiogram_bot.utils.utils import days_in_current_month, generate_sign


async def subscription_payment_handler(message_or_callback: Union[types.Message, CallbackQuery],
                                       state: FSMContext,
                                       callback_data: Optional[dict] = None):
    await state.reset_state()
    await SubscriptionPaymentState.Get_Message.set()

    row_width = 2

    keyboard = InlineKeyboardMarkup(row_width=row_width)

    s_p_free = InlineKeyboardButton(text="🆓 Хочу пользоваться бесплатно",
                                    callback_data=subscription_payment_clb.new(
                                        a="c",
                                        p=callback_data['p'] if callback_data is not None else "None",
                                        t="f"
                                    )
                                    )
    s_p_next = InlineKeyboardButton(text="➡️ Далее",
                                    callback_data=subscription_payment_clb.new(
                                        a="s_p_n",
                                        p=callback_data['p'] if callback_data is not None else "None",
                                        t='p'
                                    ))
    keyboard.add(s_p_free)

    text = f'''<b>💰 ОПЛАТА ПОДПИСКИ</b>\n\nЧтобы пользоваться Harvestly, необходима платная подписка. Чтобы подключить подписку для ваших каналов, нажмите <b>«Далее»</b>.\n\nИли попробуйте бесплатную версию:<a href="{FreeSubscription}">&#8203;</a>'''

    if callback_data is not None:
        if callback_data['p'] != "None":
            s_p_back = InlineKeyboardButton(text="⬅️ Назад",
                                            callback_data=subscription_payment_back_clb.new(
                                                a='s_p_b',
                                                p=callback_data['p'],
                                                t=callback_data['t'] if 't' in callback_data else "None",
                                            ))
            keyboard.row(s_p_back, s_p_next)
        else:
            keyboard.add(s_p_next)

    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.answer()
        await message_or_callback.bot.edit_message_text(
            text=text,
            chat_id=message_or_callback.from_user.id,
            message_id=message_or_callback.message.message_id,
            reply_markup=keyboard,
            parse_mode="HTML")

    else:
        keyboard.add(s_p_next)
        await message_or_callback.bot.send_message(
            chat_id=message_or_callback.from_user.id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


async def subscription_payment_next_handler(call: CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()

    trial_used: Response[bool] = Response[bool].model_validate(await user_channel_settings_api.trial_used(
        params={"user_id": call.from_user.id}
    ))

    if trial_used.data:
        await subscription_payment_type_handler(call=call, state=state, callback_data=callback_data)

    else:
        keyboard = InlineKeyboardMarkup(row_width=3)
        trial_button = InlineKeyboardButton(text=f"Попробовать TRIAL 🎁",
                                            callback_data=subscription_payment_clb.new(
                                                a="c",
                                                p=callback_data['p'],
                                                t="t"
                                            ))

        purchase_button = InlineKeyboardButton(text=f"Перейти к оплате 💰",
                                               callback_data=subscription_payment_clb.new(
                                                   a="c",
                                                   p=callback_data['p'],
                                                   t="p"
                                               ))

        back = InlineKeyboardButton(text="⬅️ Назад",
                                    callback_data=subscription_payment_back_clb.new(
                                        a="s_p",
                                        p=callback_data['p'],
                                        t=callback_data['t']
                                    ))

        keyboard.add(trial_button)
        keyboard.add(purchase_button)
        keyboard.add(back)

        text = f'''<b>🎁 БЕСПЛАТНЫЙ TRIAL 14 ДНЕЙ</b>\n\nМы рады предложить тебе уникальную возможность – бесплатно попробовать нашу <b>премиальную подписку на 14 дней!</b>\n\nЕсли TRIAL не нужен, то нажмите <b>“Перейти к оплате”</b><a href="{TrialSubscription}">&#8203;</a>'''

        await call.bot.edit_message_text(
            text=text,
            chat_id=call.from_user.id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode="HTML")


async def subscription_payment_type_handler(call: CallbackQuery,
                                            state: FSMContext,
                                            callback_data: dict,
                                            ):
    await call.answer()

    markup = InlineKeyboardMarkup(row_width=1)

    data = await state.get_data()
    if "channel_ids" in data:
        amount = len(data['channel_ids'])
        channel_ids = data['channel_ids']
    else:
        amount = 0
        channel_ids = []

    if callback_data['p'] == 'dis':
        if "dis" not in await state.get_data():
            await state.reset_state()
            await SubscriptionPaymentState.Get_Message.set()
            await state.update_data(dis=True)
    elif callback_data['p'] == 'n_dis':
        if "n_dis" not in await state.get_data():
            await state.reset_state()
            await SubscriptionPaymentState.Get_Message.set()
            await state.update_data(n_dis=True)
    elif callback_data['t'] == "g":
        if "g" not in await state.get_data():
            await state.reset_state()
            await SubscriptionPaymentState.Get_Message.set()
            await state.update_data(g=True)

    if callback_data['t'] == "f":
        if callback_data['p'] == "dis" or callback_data['p'] == "n_dis":
            back = callback_data['p']
        else:
            back = "s_p"

        channel_button = InlineKeyboardButton(text=f"Каналы: {amount}",
                                              callback_data=subscription_payment_clb.new(
                                                  a="ch_s",  # channels
                                                  p=callback_data['p'],
                                                  t=callback_data['t']
                                              ))

        next_button = InlineKeyboardButton(text=f"➡️ Далее",
                                           callback_data=subscription_payment_clb.new(
                                               a="s_p_t_n",
                                               p=callback_data['p'],
                                               t=callback_data['t']
                                           )
                                           )

        back_button = InlineKeyboardButton(text="⬅️ Назад",
                                           callback_data=subscription_payment_back_clb.new(
                                               a=back,
                                               p=callback_data['p'],
                                               t=callback_data['t']
                                           ))

        markup.add(channel_button)
        markup.row(back_button, next_button)
        text = f'Выберите каналы, которыми хотите пользоваться бесплатно<a href="{FreeSubscription}">&#8203;</a>'

        await call.bot.edit_message_text(
            text=text,
            chat_id=call.from_user.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML")

    elif callback_data['t'] == "g":
        month = 1
        month_text = "1 месяц"

        if "month" in data:
            if data['month'] is None or data['month'] == 1:
                month_text = "1 месяц"
            elif data['month'] == 3:
                month_text = "3 месяца"
            elif data['month'] == 6:
                month_text = "6 месяцев"
            elif data['month'] == 12:
                month_text = "1 год"

            month = data['month'] if data['month'] is not None else 1

        channel_button = InlineKeyboardButton(text=f"Каналы: {amount}",
                                              callback_data=subscription_payment_clb.new(
                                                  a="ch_s",  # channels
                                                  p=callback_data['p'],
                                                  t=callback_data['t']
                                              ))

        next_button = InlineKeyboardButton(text=f"К оплате 💰",
                                           callback_data=subscription_payment_clb.new(
                                               a="s_p_t_n",
                                               p=callback_data['p'],
                                               t=callback_data['t']
                                           )
                                           )

        month_button = InlineKeyboardButton(text=f"Длительность: {month_text}",
                                            callback_data=subscription_payment_clb.new(
                                                a="m",
                                                p=callback_data['p'],
                                                t=callback_data['t']
                                            ))

        back_button = InlineKeyboardButton(text="⬅️ Назад",
                                           callback_data=subscription_payment_back_clb.new(
                                               a="g",
                                               p=callback_data['p'],
                                               t=callback_data['t']
                                           ))

        markup.add(channel_button)
        markup.add(month_button)
        markup.row(back_button, next_button)

        subscription_response: Response[SubscriptionSchema] = Response[SubscriptionSchema].model_validate(
            await subscription_api.get_one_by_key_value(
                params={"key": "id", "value": 2}
            ))

        month_price = subscription_response.data.price[str(month)]

        total_price = amount * month_price
        text = f'''<b>💰 ОПЛАТА ПОДПИСКИ</b>\n\nВыберите каналы и длительность подписки, а затем нажмите «К оплате».<a href="{PremiumSubscription}">&#8203;</a>'''

        await state.update_data(total_price=total_price)

        await call.bot.edit_message_text(
            text=text,
            chat_id=call.from_user.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML")

    elif callback_data['t'] == 'p':
        trial_used: Response[bool] = Response[bool].model_validate(await user_channel_settings_api.trial_used(
            params={"user_id": call.from_user.id}
        ))

        if callback_data['p'] == "dis" or callback_data['p'] == "n_dis":
            back = callback_data['p']
        elif trial_used.data:
            back = "s_p"
        else:
            back = "s_p_n"

        month = 1
        month_text = "1 месяц"

        if "month" in data:
            if data['month'] is None or data['month'] == 1:
                month_text = "1 месяц"
            elif data['month'] == 3:
                month_text = "3 месяца"
            elif data['month'] == 6:
                month_text = "6 месяцев"
            elif data['month'] == 12:
                month_text = "1 год"

            month = data['month'] if data['month'] is not None else 1

        channel_button = InlineKeyboardButton(text=f"Каналы: {amount}",
                                              callback_data=subscription_payment_clb.new(
                                                  a="ch_s",  # channels
                                                  p=callback_data['p'],
                                                  t=callback_data['t']
                                              ))

        next_button = InlineKeyboardButton(text=f"К оплате 💰",
                                           callback_data=subscription_payment_clb.new(
                                               a="s_p_t_n",
                                               p=callback_data['p'],
                                               t=callback_data['t']
                                           )
                                           )

        month_button = InlineKeyboardButton(text=f"Длительность: {month_text}",
                                            callback_data=subscription_payment_clb.new(
                                                a="m",
                                                p=callback_data['p'],
                                                t=callback_data['t']
                                            ))

        back_button = InlineKeyboardButton(text="⬅️ Назад",
                                           callback_data=subscription_payment_back_clb.new(
                                               a=back,
                                               p=callback_data['p'],
                                               t=callback_data['t']
                                           ))

        markup.add(channel_button)
        markup.add(month_button)
        markup.row(back_button, next_button)

        subscription_response: Response[SubscriptionSchema] = Response[SubscriptionSchema].model_validate(
            await subscription_api.get_one_by_key_value(
                params={"key": "id", "value": 2}
            ))

        month_price = subscription_response.data.price[str(month)]

        if callback_data['p'] == "dis":
            total_price = amount * month_price / 2
            text = f'''<b>💰 ОПЛАТА ПОДПИСКИ</b>\n\nВыберите каналы для подписки со скидкой <b>50% на 1 месяц</b>, а затем нажмите «К оплате».<a href="{PremiumSubscription}">&#8203;</a>'''
        else:
            total_price = amount * month_price
            text = f'''<b>💰 ОПЛАТА ПОДПИСКИ</b>\n\nВыберите каналы и длительность подписки, а затем нажмите «К оплате».<a href="{PremiumSubscription}">&#8203;</a>'''

        await state.update_data(total_price=total_price)

        await call.bot.edit_message_text(
            text=text,
            chat_id=call.from_user.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML")

    elif callback_data['t'] == 't':
        back = "s_p_n"

        user_channel_response: Response[list[ChannelSchema]] = Response[list[ChannelSchema]].model_validate(
            await channel_api.get_user_channels_with_certain_subscriptions(data={
                "user_id": call.from_user.id,
                "subscriptions": [
                    1,
                    None
                ],
                "disabled": False
            }))

        for user_channel in user_channel_response.data:
            markup.insert(InlineKeyboardButton(
                text=f"{user_channel.title}" if user_channel.id not in channel_ids else f"✅ {user_channel.title}",
                callback_data=subscription_payment_channel_tap_clb.new(  # s_p_channel_tap
                    t_ch=user_channel.id,  # tapped_channel
                    p=callback_data['p'],
                    t=callback_data['t'])))

        next_button = InlineKeyboardButton(text=f"Подключить 🎁",
                                           callback_data=subscription_payment_trial_clb.new(
                                               a="c",
                                               p=callback_data['p']
                                           )
                                           )

        back_button = InlineKeyboardButton(text="⬅️ Назад",
                                           callback_data=subscription_payment_back_clb.new(
                                               a=back,
                                               p=callback_data['p'],
                                               t=callback_data['t']
                                           ))

        markup.row(back_button, next_button)
        text = f"🎁 <b>БЕСПЛАТНЫЙ TRIAL 14 ДНЕЙ</b>\n\nВыберите <b>1 канал</b> для подписки на премиальную подписку на <b>14 дней!</b>"

        await call.bot.edit_message_text(
            text=text,
            chat_id=call.from_user.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML")


async def subscription_payment_channels_handler(call: CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()

    markup = InlineKeyboardMarkup(row_width=1)

    data = await state.get_data()
    if "channel_ids" in data:
        channel_ids = data['channel_ids']
    else:
        channel_ids = []

    if callback_data['t'] == "p":
        user_channel_response: Response[list[ChannelSchema]] = Response[list[ChannelSchema]].model_validate(
            await channel_api.get_user_channels_with_certain_subscriptions(data={
                "user_id": call.from_user.id,
                "subscriptions": [
                    1,
                    None
                ],
                "disabled": False
            }))

        for user_channel in user_channel_response.data:
            markup.insert(InlineKeyboardButton(
                text=f"{user_channel.title}" if user_channel.id not in channel_ids else f"✅ {user_channel.title}",
                callback_data=subscription_payment_channel_tap_clb.new(
                    t_ch=user_channel.id,
                    p=callback_data['p'],
                    t=callback_data['t'])))

        markup.add(InlineKeyboardButton(text="⏫ Выбрать ⏫",
                                        callback_data=subscription_payment_clb.new(
                                            a="c",
                                            p=callback_data['p'],
                                            t=callback_data['t'])
                                        ))

        await call.bot.edit_message_text(
            text=call.message.text,
            chat_id=call.from_user.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML")

    elif callback_data['t'] == "g":
        user_channel_response: Response[list[ChannelSchema]] = Response[list[ChannelSchema]].model_validate(
            await channel_api.get_user_channels_with_certain_subscriptions(data={
                "user_id": call.from_user.id,
                "subscriptions": [
                    1,
                    None
                ],
                "disabled": False
            }))

        for user_channel in user_channel_response.data:
            markup.insert(InlineKeyboardButton(
                text=f"{user_channel.title}" if user_channel.id not in channel_ids else f"✅ {user_channel.title}",
                callback_data=subscription_payment_channel_tap_clb.new(
                    t_ch=user_channel.id,
                    p=callback_data['p'],
                    t=callback_data['t'])))

        markup.add(InlineKeyboardButton(text="⏫ Выбрать ⏫",
                                        callback_data=subscription_payment_clb.new(
                                            a="c",
                                            p=callback_data['p'],
                                            t=callback_data['t'])
                                        ))

        await call.bot.edit_message_text(
            text=call.message.text,
            chat_id=call.from_user.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML")

    elif callback_data['t'] == "f":
        user_channel_response: Response[list[ChannelSchema]] = Response[list[ChannelSchema]].model_validate(
            await channel_api.get_user_channels_with_certain_subscriptions(data={
                "user_id": call.from_user.id,
                "subscriptions": [
                    None
                ],
                "disabled": False
            }))

        for user_channel in user_channel_response.data:
            markup.insert(InlineKeyboardButton(
                text=f"{user_channel.title}" if user_channel.id not in channel_ids else f"✅ {user_channel.title}",
                callback_data=subscription_payment_channel_tap_clb.new(  # s_p_channel_tap
                    t_ch=user_channel.id,  # tapped_channel
                    p=callback_data['p'],
                    t=callback_data['t'])))

        markup.add(InlineKeyboardButton(text="⏫ Выбрать ⏫",
                                        callback_data=subscription_payment_clb.new(
                                            a="c",
                                            p=callback_data['p'],
                                            t=callback_data['t'])
                                        ))

        await call.bot.edit_message_text(
            text=call.message.text,
            chat_id=call.from_user.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML")


async def subscription_payment_channel_tap_handler(call: CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()

    tapped_channel = int(callback_data['t_ch'])
    type = callback_data['t']

    data = await state.get_data()

    if "channel_ids" in data:
        channel_ids: list = data['channel_ids']
    else:
        channel_ids = []

    if type == "p":
        if tapped_channel in channel_ids:
            channel_ids.remove(tapped_channel)
        else:
            channel_ids.append(tapped_channel)
    elif type == "g":
        if tapped_channel in channel_ids:
            channel_ids.remove(tapped_channel)
        else:
            channel_ids.append(tapped_channel)
    elif type == "f":
        if tapped_channel in channel_ids:
            channel_ids.remove(tapped_channel)
        else:
            channel_ids.append(tapped_channel)
    elif type == "t":
        if tapped_channel in channel_ids:
            channel_ids = []
        else:
            channel_ids = [tapped_channel]

    await state.update_data(channel_ids=channel_ids)

    if callback_data['t'] == 'f':
        await subscription_payment_channels_handler(call=call, state=state, callback_data=callback_data)
    elif callback_data['t'] == 'p':
        await subscription_payment_channels_handler(call=call, state=state, callback_data=callback_data)
    elif callback_data['t'] == "g":
        await subscription_payment_channels_handler(call=call, state=state, callback_data=callback_data)
    elif callback_data['t'] == 't':
        await subscription_payment_type_handler(call=call, state=state, callback_data=callback_data)


async def trial_connect_handler(call: CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()

    data = await state.get_data()
    channel_ids = data['channel_ids']

    created = datetime.utcnow()

    success = Response[bool].model_validate(await user_channel_settings_api.update_subscription_id_by_channel_ids(
        data={
            "channel_ids": channel_ids,
            "new_subscription_id": 2,
            'created': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            'finished': (created + timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
        }
    ))

    if not success:
        return

    channel_info = await call.bot.get_chat(channel_ids[0])
    text = f'✅ Бесплатный TRIAL на канал {channel_info.title} успешно подключен'

    user_channel_response: Response[list[UserChannelSchema]] = Response[list[UserChannelSchema]].model_validate(
        await user_channel_api.find_by_channels_id(data={"ids": channel_ids})
    )

    user_channel_settings_id = user_channel_response.data[0].user_channel_settings_id
    user_channel_settings_response: Response[UserChannelSettingsSchema] = Response[
        UserChannelSettingsSchema].model_validate(
        await user_channel_settings_api.put(
            data={
                "id": user_channel_settings_id,
                "trial_used": True
            })
    )

    for user_channel in user_channel_response.data:
        if user_channel.user_id != call.from_user.id:
            try:
                await call.bot.send_message(
                    chat_id=user_channel.user_id,
                    text=text
                )
            except Exception as e:
                logging.error(f"trial_connect_handler {e}")

    await call.bot.edit_message_text(
        text=text,
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        parse_mode="HTML")

    job = scheduler.add_job(subscription_finished, 'date', args=[state, 'dis'],
                            run_date=(created + timedelta(days=14)).replace(tzinfo=pytz.utc))


async def subscription_payment_month_handler(call: CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()

    data = await state.get_data()
    month = None

    if 'month' in data:
        month = data["month"]

    markup = InlineKeyboardMarkup(row_width=1)

    markup.add(InlineKeyboardButton(text="1 месяц" if month != 1 else "✅ 1 месяц",
                                    callback_data=subscription_payment_month_tap_clb.new(
                                        m=1,
                                        p=callback_data['p'],
                                        t=callback_data['t']
                                    )
                                    ))

    markup.add(InlineKeyboardButton(text="3 месяца" if month != 3 else "✅ 3 месяца",
                                    callback_data=subscription_payment_month_tap_clb.new(
                                        m=3,
                                        p=callback_data['p'],
                                        t=callback_data['t']
                                    )
                                    ))

    markup.add(InlineKeyboardButton(text="6 месяцев" if month != 6 else "✅ 6 месяцев",
                                    callback_data=subscription_payment_month_tap_clb.new(
                                        m=6,
                                        p=callback_data['p'],
                                        t=callback_data['t']
                                    )
                                    ))

    markup.add(InlineKeyboardButton(text="1 год" if month != 12 else "✅ 1 год",
                                    callback_data=subscription_payment_month_tap_clb.new(
                                        m=12,
                                        p=callback_data['p'],
                                        t=callback_data['t']
                                    )
                                    ))

    markup.add(InlineKeyboardButton(text="⏫ Выбрать ⏫",
                                    callback_data=subscription_payment_clb.new(
                                        a="c",
                                        p=callback_data['p'],
                                        t=callback_data['t'])
                                    ))

    await call.bot.edit_message_text(
        text=f'Выберите длительность подписки. Дешевле брать подписку на больший срок.<a href="{MonthOffer}">&#8203;</a>',
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode="HTML")


async def subscription_payment_month_pressed_handler(call: CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()

    data = await state.get_data()
    month = None

    if 'month' in data:
        month = data["month"]

    month_chosen = callback_data['m']
    if month_chosen == month:
        await state.update_data(month=None)
    else:
        await state.update_data(month=int(month_chosen))

    await subscription_payment_month_handler(call=call, state=state, callback_data=callback_data)


async def subscription_payment_type_next_button_handler(call: CallbackQuery, state: FSMContext, callback_data: dict):
    if callback_data['t'] == "f":
        await subscription_payment_choose_free_handler(call=call, state=state, callback_data=callback_data)
    elif callback_data['t'] == "p":
        await subscription_payment_services_handler(call=call, state=state, callback_data=callback_data)
    elif callback_data['t'] == "g":
        await subscription_payment_services_handler(call=call, state=state, callback_data=callback_data)


async def subscription_payment_choose_free_handler(call: CallbackQuery, state: FSMContext, callback_data: dict):
    subscription_response: Response[SubscriptionSchema] = Response[SubscriptionSchema].model_validate(
        await subscription_api.get_one_by_key_value(params={"key": "id", "value": 1})
    )
    channel_name = subscription_response.data.channel_name

    text = f'<b>🚨 УСЛОВИЯ БЕСПЛАТНОЙ ПОДПИСКИ</b>\n\nЧтобы пользвоаться Hаrvestly бесплатно, вам нужно подписаться на наш канал {channel_name}'

    markup = InlineKeyboardMarkup(row_width=2)

    markup.add(InlineKeyboardButton(text="Проверить подписку",
                                    callback_data=subscription_payment_free_clb.new(
                                        a='ch_s',  # check subscription
                                        p=callback_data['p'],
                                        t=callback_data['t']
                                    )
                                    ))

    markup.add(InlineKeyboardButton(text="⬅️ Назад",
                                    callback_data=subscription_payment_clb.new(
                                        a='c',
                                        p=callback_data['p'],
                                        t=callback_data['t']
                                    )
                                    ))

    await state.update_data(channel_name=channel_name)

    await call.bot.edit_message_text(
        text=text,
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode="HTML")


async def subscription_payment_check_free_subscription(call: CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()

    data = await state.get_data()
    channel_name = data['channel_name']
    channel_ids = data['channel_ids']

    user_channels = ""
    is_member = False

    member = await call.bot.get_chat_member(chat_id=channel_name, user_id=call.from_user.id)
    if member.status == types.ChatMemberStatus.MEMBER or member.status == types.ChatMemberStatus.OWNER or member.status == types.ChatMemberAdministrator:
        is_member = True

    if not is_member:
        markup = InlineKeyboardMarkup(row_width=2)

        markup.add(InlineKeyboardButton(text="Проверить подписку",
                                        callback_data=subscription_payment_free_clb.new(
                                            a='ch_s',  # check subscription
                                            p=callback_data['p'],
                                            t=callback_data['t']
                                        )
                                        ))

        markup.add(InlineKeyboardButton(text="⬅️ Назад",
                                        callback_data=subscription_payment_clb.new(
                                            a='c',
                                            p=callback_data['p'],
                                            t=callback_data['t']
                                        )
                                        ))

        await call.bot.edit_message_text(
            text=f'<b>🚨 ВЫ НЕ ПОДПИСАНЫ</b>\n\nЧтобы пользвоаться Hаrvestly бесплатно, вам нужно подписаться на наш канал {channel_name}',
            chat_id=call.from_user.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML")

        return

    for channel in channel_ids:
        channel_info = await call.bot.get_chat(channel)
        user_channels = user_channels + f"{channel_info.title}, "

    success = Response[bool].model_validate(await user_channel_settings_api.update_subscription_id_by_channel_ids(
        data={
            "channel_ids": channel_ids,
            "new_subscription_id": 1
        }
    ))

    if not success:
        return

    user_channels = user_channels[:-2]
    text = f'<b>🎁 ПОДАРОЧНАЯ ПОДПИСКА</b>\n\nВы успешно подключили канал {user_channels} к Harvestly<a href="{FreeSubscription}">&#8203;</a>'

    user_channel_response: Response[list[UserChannelSchema]] = Response[list[UserChannelSchema]].model_validate(
        await user_channel_api.find_by_channels_id(data={"ids": channel_ids})
    )

    for user_channel in user_channel_response.data:
        if user_channel.user_id != call.from_user.id:
            await call.bot.send_message(
                chat_id=user_channel.user_id,
                text=text
            )

    await call.bot.edit_message_text(
        text=text,
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        parse_mode="HTML")

    for channel_id in channel_ids:
        scheduler.add_job(check_subscribers_and_subscription, 'cron', hour=12, minute=0,
                          id=f'check_sub_{channel_id}', args=[channel_id, call.from_user.id])


async def subscription_payment_services_handler(call: CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()

    markup = subscription_payment_services_markup(callback_data)
    text = f'<b>💰 ОПЛАТА ПОДПИСКИ</b>\n\nВыберите способ оплаты.\n\nОплачивая подписку, вы принимаете условия пользовательского соглашения и политики конфиденциальности.'
    await state.update_data(text=text)
    await call.bot.edit_message_text(
        text=text,
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode="HTML")


def subscription_payment_services_markup(callback_data: dict):
    markup = InlineKeyboardMarkup(row_width=3)

    markup.add(InlineKeyboardButton(text="🪙 Cryptobot",
                                    callback_data=subscription_payment_clb.new(
                                        a="Cryptobot",
                                        p=callback_data['p'],
                                        t=callback_data['t'])
                                    ))

    markup.add(InlineKeyboardButton(text="💳 Оплатить картой",
                                    callback_data=subscription_payment_clb.new(
                                        a="Карта",
                                        p=callback_data['p'],
                                        t=callback_data['t'])
                                    ))

    markup.add(InlineKeyboardButton(text="⬅️ Назад",
                                    callback_data=subscription_payment_clb.new(
                                        a='c',
                                        p=callback_data['p'],
                                        t=callback_data['t']
                                    )))

    return markup


async def subscription_payment_choosen_service_handler(call: CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    data = await state.get_data()

    quantity_of_channels = 0
    month = '1 месяц'
    total_price = 0

    if 'month' in data:
        month = data['month'] if data['month'] != None else "1 месяц"
    if 'channel_ids' in data:
        quantity_of_channels = len(data['channel_ids'])
    if 'total_price' in data:
        total_price = data['total_price']

    user_response: Response[UserSchema] = Response[UserSchema].model_validate(
        await user_api.get_one_by_key_value(params={"key": "id", "value": call.from_user.id})
    )

    if user_response.data.mail is None:
        await subscription_payment_change_mail_clb_handler(call=call, state=state, callback_data=callback_data)
        return

    markup = InlineKeyboardMarkup(row_width=3)
    action = callback_data['a']

    if action == "Cryptobot":
        btc = InlineKeyboardButton(text="BTC",
                                   callback_data=subscription_payment_clb.new(
                                       a="BTC",
                                       p=callback_data['p'],
                                       t=callback_data['t']
                                   )
                                   )
        usdt = InlineKeyboardButton(text="USDT",
                                    callback_data=subscription_payment_clb.new(
                                        a="USDT",
                                        p=callback_data['p'],
                                        t=callback_data['t']
                                    )
                                    )
        ltc = InlineKeyboardButton(text="LTC",
                                   callback_data=subscription_payment_clb.new(
                                       a="LTC",
                                       p=callback_data['p'],
                                       t=callback_data['t']
                                   )
                                   )
        ton = InlineKeyboardButton(text="TON",
                                   callback_data=subscription_payment_clb.new(
                                       a="TON",
                                       p=callback_data['p'],
                                       t=callback_data['t']
                                   )
                                   )
        markup.row(btc, usdt)
        markup.row(ltc, ton)

    elif action == "Карта":
        visa_master_mir = InlineKeyboardButton(text="Visa/Mastercard/Mir",
                                               callback_data=subscription_payment_clb.new(
                                                   a="v_m_m",
                                                   p=callback_data['p'],
                                                   t=callback_data['t']
                                               )
                                               )
        uz_card_xumo = InlineKeyboardButton(text="Uzcard/Humo",
                                            callback_data=subscription_payment_clb.new(
                                                a="u_h",
                                                p=callback_data['p'],
                                                t=callback_data['t']
                                            )
                                            )
        markup.add(visa_master_mir)
        markup.add(uz_card_xumo)

    markup.add(InlineKeyboardButton(text="⬅️ Назад",
                                    callback_data=subscription_payment_back_clb.new(
                                        a="b_t_p_s",
                                        p=callback_data['p'],
                                        t=callback_data['t']
                                    )
                                    ))

    text = f"<b>💰 ОПЛАТА ПОДПИСКИ</b>\n\nК оплате: {total_price}₽\n\nДлительность: {month}\n\nКаналов: {quantity_of_channels} шт.\n\nE-mail для отправки чека: {user_response.data.mail}"
    await state.update_data(mail=user_response.data.mail)
    await call.bot.edit_message_text(
        text=text,
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode="HTML")


async def subscription_payment_cryptobot_clb_handler(call: CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()

    data = await state.get_data()

    action = callback_data['a']
    check_action = ""

    total_price = 0
    url = ""
    id = ""

    if 'total_price' in data:
        total_price = data['total_price']

    if action == "BTC" or action == "LTC" or action == "TON" or action == "USDT":
        check_action = "c_b"  # cryptobot

        invoice: Response[InvoiceSchema] = Response[InvoiceSchema].model_validate(
            await payment_api.invoice(data={"amount": total_price, "accepted_assets": [action]})
        )
        id = invoice.data.invoice_id
        url = invoice.data.bot_invoice_url

    elif action == "v_m_m" or action == "u_h":
        check_action = "c_p"  # card_paywave

        paywave_response: Response[PaywaveSchema] = Response[PaywaveSchema].model_validate(
            await paywave_api.post_add(data={"user_id": call.from_user.id})
        )
        id = paywave_response.data.id
        currency = "643" if action == "v_m_m" else "860"

        if config.paywave.system == "TEST":
            paysystem = "16"
        else:
            paysystem = "15" if action == "v_m_m" else "32"

        if action == "u_h":
            rub_uzs: Response[int] = Response[int].model_validate(await payment_api.rub_uzs())
            paywave_amount = rub_uzs.data * total_price
        else:
            paywave_amount = total_price

        oper_id = f"{config.paywave.prefix}_{id}"
        note = f"{config.paywave.prefix}_{id}"
        sign = generate_sign(currency=currency,
                             paysystem=paysystem,
                             oper_id=oper_id,
                             amount=str(paywave_amount),
                             pass1=config.paywave.pass1)

        response = await payment_api.paywave_invoice(
            data={
                "currency": currency,
                "paysystem": paysystem,
                "amount": str(paywave_amount),
                "oper_id": oper_id,
                "note": note,
                "sign": sign
            })

        invoice: Response[PaywaveInvoiceSchema] = Response[PaywaveInvoiceSchema].model_validate(response)
        id = invoice.data.optoken
        url = invoice.data.url

    # text_to_change = call.message.text.split("К оплате: ")[-1].split("\n")[0]
    # text = call.message.text.replace(text_to_change, f"{total_price} ₽")
    text = call.message.text
    mail_to_change = text.split(":")[-1]
    mail = f"\n{data['mail']}"

    text = text.replace(mail_to_change, mail)

    await state.update_data(text=text)
    await state.update_data(url=url)
    await state.update_data(id=id)
    await state.update_data(check_action=check_action)

    markup = payment_service_markup(callback_data, action=check_action, url=url)

    await call.bot.edit_message_text(
        text=text,
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode="HTML")


def payment_service_markup(callback_data: dict, action: str, url: str):
    markup = InlineKeyboardMarkup(row_width=1)

    url_button = InlineKeyboardButton(text="Оплатить", url=url)

    payment_check_button = InlineKeyboardButton(
        text="Проверить оплату",
        callback_data=subscription_payment_check_invoice_clb.new(
            a=action
        )
    )

    change_mail_button = InlineKeyboardButton(
        text="Изменить e-mail",
        callback_data=subscription_payment_clb.new(
            a=f"c_m",
            p=callback_data['p'],
            t=callback_data['t']
        )
    )

    back = ""
    if callback_data['a'] == "v_m_m" or callback_data['a'] == "u_h":
        back = "Карта"
    elif callback_data['a'] == "BTC" or callback_data['a'] == 'LTC' or callback_data['a'] == "TON" or callback_data[
        'a'] == "USDT":
        back = "Cryptobot"

    back_button = InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data=subscription_payment_back_clb.new(
            a=back,
            p=callback_data['p'],
            t=callback_data['t']
        )
    )

    markup.add(url_button)
    markup.add(payment_check_button)
    markup.add(change_mail_button)
    markup.add(back_button)

    return markup


async def subscription_payment_check_invoice_clb_handler(call: CallbackQuery, state: FSMContext,
                                                         callback_data: dict):
    await call.answer()

    await call.message.delete()

    data = await state.get_data()
    invoice_id = data['id']

    success = False

    action = callback_data['a']

    if 'c_b' == action:
        invoice: Response[InvoiceSchema] = Response[InvoiceSchema].model_validate(
            await payment_api.get_invoice(id=invoice_id)
        )

        if invoice.data.status == "paid":
            success = True

    elif action == "c_p":
        invoice: Response[PaywaveInvoiceStatusSchema] = Response[PaywaveInvoiceStatusSchema].model_validate(
            await payment_api.paywave_check_status(data={
                "optoken": invoice_id
            })
        )

        if invoice.data.status == "paid":
            success = True

    if success:
        # days_in_month = days_in_current_month()
        created = datetime.utcnow()

        duration = 1
        if 'month' in data:
            duration = data['month']

        update_subscription_id_by_channel_ids_response: Response[bool] = Response[bool].model_validate(
            await user_channel_settings_api.update_subscription_id_by_channel_ids(
                data={
                    'channel_ids': data['channel_ids'],
                    'new_subscription_id': 2,
                    'created': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    'finished': (created + relativedelta(months=+duration)).strftime("%Y-%m-%d %H:%M:%S")
                }
            ))

        payment_response: Response[PaymentDbSchema] = Response[PaymentDbSchema].model_validate(
            await payment_db_api.post_add(data={
                "user_id": call.from_user.id,
                "type": "paywave" if action == "c_p" else "crypto_bot",
                "channels": data['channel_ids'],
                "duration": duration
            })
        )

        job = scheduler.add_job(subscription_finished, 'date', args=[state, 'n_dis'],
                                run_date=(created + relativedelta(months=+duration)).replace(tzinfo=pytz.utc))

        text = call.message.text
        text = text.replace("💰 ОПЛАТА ПОДПИСКИ", "✅ Оплата прошла успешно:")
        text = text.replace("🚨 Не оплачено:", "✅ Оплата прошла успешно:")

        user_channel_response: Response[list[UserChannelSchema]] = Response[list[UserChannelSchema]].model_validate(
            await user_channel_api.find_by_channels_id(data={"ids": data['channel_ids']})
        )
        for user_channel in user_channel_response.data:
            try:
                await call.bot.send_message(
                    chat_id=user_channel.user_id,
                    text=text
                )
            except Exception as e:
                logging.error(f"subscription_payment_check_invoice_clb_handler {e}")

        user_response: Response[UserSchema] = Response[UserSchema].model_validate(
            await user_api.get_one_by_key_value(params={
                "key": "id",
                "value": call.from_user.id
            })
        )

        username = call.from_user.username

        mail_response: Response[str] = Response[str].model_validate(
            await mail_api.send_mail(data={
                "username": username,
                "to": user_response.data.mail
            })
        )

        logging.info(f"MAIL = {mail_response}")
        return

    text = call.message.text
    text = text.replace("💰 ОПЛАТА ПОДПИСКИ", "🚨 Не оплачено:")

    await call.message.answer(
        text=text,
        reply_markup=call.message.reply_markup
    )


async def subscription_payment_back_clb_handler(call: CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()

    action = callback_data['a']
    prefix = callback_data['p']

    if action == "s_p_b":
        if prefix == "creating":
            await back_to_creating(call=call, callback_data=callback_data, state=state)
        elif prefix == "co_pl":
            await back_to_content(call=call, state=state)
        elif prefix.isdigit():
            await state.reset_state()
            await chatgpt_settings(call=call, callback_data={"channel_id": f"-100{prefix}"})
        elif prefix == "settings":
            await state.reset_state()
            await back_to_user_settings(call=call)
    elif action == "g":
        await state.reset_state()
        await parsing_user_channel(call=call, callback_data={"channel_id": f"-100{prefix}"})
    elif action == "dis":
        await state.reset_state()
        await SubscriptionPaymentState.Get_Message.set()
        await subscription_finished(state=state, p="dis")
    elif action == "n_dis":
        await state.reset_state()
        await SubscriptionPaymentState.Get_Message.set()
        await subscription_finished(state=state, p="n_dis")
    elif action == "s_p":
        await subscription_payment_handler(call, state, callback_data)
    elif action == "s_p_n":
        await subscription_payment_next_handler(call, state, callback_data)
    elif action == "b_t_p_s":
        await subscription_payment_type_next_button_handler(call, state, callback_data)
    elif action == "Cryptobot" or action == "Карта":
        await subscription_payment_choosen_service_handler(call, state, callback_data)
    elif action == "b_t_p_s_f_m":
        await state.reset_state(with_data=False)
        await state.set_state(SubscriptionPaymentState.Get_Message)
        await subscription_payment_type_next_button_handler(call, state, callback_data)


async def subscription_payment_change_mail_clb_handler(call: CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()

    await SubscriptionPaymentState.Change_Email.set()
    await state.update_data(callback_data=callback_data)

    markup = InlineKeyboardMarkup(row_width=1)

    back_button = InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data=subscription_payment_back_clb.new(
            a="b_t_p_s_f_m",
            p=callback_data['p'],
            t=callback_data['t']
        )
    )

    markup.add(back_button)

    await call.bot.edit_message_text(
        text="Отправьте e-mail для чека",
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode="HTML")


async def subscription_payment_change_mail_message_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()

    user_id = message.from_user.id
    user_response: Response[UserSchema] = Response[UserSchema].model_validate(await user_api.put(
        data={"id": user_id, "mail": message.text}
    ))

    text = data['text']
    if 'url' in data and 'id' in data:
        check_action = data['check_action']
        url = data['url']

        markup = payment_service_markup(callback_data=data['callback_data'], action=check_action, url=url)

        old_mail = text.split(":")[-1]
        text = text.replace(old_mail, user_response.data.mail)
    else:
        markup = subscription_payment_services_markup(data['callback_data'])

    await state.reset_state(with_data=False)
    await state.set_state(SubscriptionPaymentState.Get_Message)

    await message.bot.delete_message(message.chat.id, message.message_id - 1)
    await message.answer(
        text=text,
        reply_markup=markup,
        parse_mode="HTML")


def register_subscription_payment(dp: Dispatcher):
    # dp.register_message_handler(
    #     subscription_payment_handler,
    #     text="💰 Оплата подписки",
    #     state="*"
    # )
    # dp.register_message_handler(
    #     subscription_payment_handler,
    #     text="💰 Оплата подписки"
    # )

    dp.register_callback_query_handler(
        subscription_payment_handler,
        subscription_payment_clb.filter(
            a='s_p'
        ),
        state="*"
    )

    dp.register_callback_query_handler(
        subscription_payment_handler,
        subscription_payment_clb.filter(a='s_p_b'),
        state="*"
    )

    dp.register_callback_query_handler(
        subscription_payment_next_handler,
        subscription_payment_clb.filter(
            a='s_p_n',
        ),
        state=SubscriptionPaymentState
    )

    dp.register_callback_query_handler(
        subscription_payment_type_handler,
        subscription_payment_clb.filter(
            a=['c'],
        ),
        state="*"
    )

    dp.register_callback_query_handler(
        subscription_payment_channels_handler,
        subscription_payment_clb.filter(
            a=['ch_s'],
        ),
        state=SubscriptionPaymentState
    )

    dp.register_callback_query_handler(
        subscription_payment_channel_tap_handler,
        subscription_payment_channel_tap_clb.filter(),
        state=SubscriptionPaymentState
    )

    dp.register_callback_query_handler(
        subscription_payment_month_handler,
        subscription_payment_clb.filter(a='m'),
        state=SubscriptionPaymentState
    )

    dp.register_callback_query_handler(
        subscription_payment_month_pressed_handler,
        subscription_payment_month_tap_clb.filter(),
        state=SubscriptionPaymentState
    )

    dp.register_callback_query_handler(
        subscription_payment_check_free_subscription,
        subscription_payment_free_clb.filter(a='ch_s'),
        state=SubscriptionPaymentState
    )

    dp.register_callback_query_handler(
        subscription_payment_type_next_button_handler,
        subscription_payment_clb.filter(a='s_p_t_n'),
        state=SubscriptionPaymentState
    )

    dp.register_callback_query_handler(
        subscription_payment_choosen_service_handler,
        subscription_payment_clb.filter(a=['Cryptobot', 'Карта']),
        state=SubscriptionPaymentState
    )

    dp.register_callback_query_handler(
        subscription_payment_cryptobot_clb_handler,
        subscription_payment_clb.filter(a=["BTC", "LTC", "USDT", "TON", "v_m_m", "u_h"]),
        state=SubscriptionPaymentState
    )

    dp.register_callback_query_handler(
        subscription_payment_check_invoice_clb_handler,
        subscription_payment_check_invoice_clb.filter(),
        state=SubscriptionPaymentState
    )

    dp.register_callback_query_handler(
        subscription_payment_back_clb_handler,
        subscription_payment_back_clb.filter(),
        state="*"
    )

    dp.register_callback_query_handler(
        subscription_payment_change_mail_clb_handler,
        subscription_payment_clb.filter(a='c_m'),
        state=SubscriptionPaymentState
    )

    dp.register_message_handler(
        subscription_payment_change_mail_message_handler,
        state=SubscriptionPaymentState.Change_Email
    )

    dp.register_callback_query_handler(
        trial_connect_handler,
        subscription_payment_trial_clb.filter(a='c'),
        state=SubscriptionPaymentState
    )
