import copy
import json
import logging
import math
from calendar import monthrange, weekday
from datetime import datetime, timedelta

import aiohttp
import pytz
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, InputMediaVideo, \
    InputMediaDocument, InputMediaAudio, InputMediaAnimation
from babel.dates import format_date

from tg_bot import config, scheduler, channel_api, user_api
from tg_bot.aiogram_bot.handlers.task.task import auto_delete_timer_job
from tg_bot.aiogram_bot.handlers.users.create.calendar_handler import convert_to_user_time
from tg_bot.aiogram_bot.handlers.users.create.create_post import edit_post
from tg_bot.aiogram_bot.keyboards.inline.content_inline.calendar_content import calendar_content
from tg_bot.aiogram_bot.keyboards.inline.content_inline.content import content_clb, add_descrip_content, \
    custom_media_content, \
    cancel_content, url_buttons_clb_content, gpt_clb_content, auto_sign_clb_content, choose_prompts_content, \
    post_callback, redaction_clb, choose_seconds_content_plan, further_content_plan, sending_clbk_content_plan
from tg_bot.aiogram_bot.keyboards.inline.create_inline.calendar_create import sending_clbk
from tg_bot.aiogram_bot.keyboards.inline.parsing import add_channel_clb
from tg_bot.aiogram_bot.keyboards.inline.subscription_payment.inline_button import subscription_payment_clb, \
    subscription_payment_back_clb
from tg_bot.aiogram_bot.network.dto.channel import ChannelSchema
from tg_bot.aiogram_bot.network.dto.response import Response
from tg_bot.aiogram_bot.network.dto.user import UserSchema
from tg_bot.aiogram_bot.states.users import Content, CreatePost
from tg_bot.aiogram_bot.utils.utils import count_characters

month_names = {
    1: 'Январь',
    2: 'Февраль',
    3: 'Март',
    4: 'Апрель',
    5: 'Май',
    6: 'Июнь',
    7: 'Июль',
    8: 'Август',
    9: 'Сентябрь',
    10: 'Октябрь',
    11: 'Ноябрь',
    12: 'Декабрь'
}


async def markup_media_content_plan(markup, descrip_button, exist_auto_sign, post_id):
    markup.row(InlineKeyboardButton(text=descrip_button,
                                    callback_data=add_descrip_content.new(action="edit",
                                                                          post_id=post_id)))
    markup.row(InlineKeyboardButton(text="URL-кнопки",
                                    callback_data=url_buttons_clb_content.new(action="edit",
                                                                              post_id=post_id)),
               InlineKeyboardButton(text="Настроить медиа",
                                    callback_data=custom_media_content.new(action="None", post_id=post_id)))
    markup.row(InlineKeyboardButton(text="Chat GPT",
                                    callback_data=gpt_clb_content.new(action="edit", post_id=post_id)),
               InlineKeyboardButton(text=f"{exist_auto_sign}Автоподпись",
                                    callback_data=auto_sign_clb_content.new(action="edit",
                                                                            post_id=post_id)))
    markup.row(
        InlineKeyboardButton(text="💾 Сохранить", callback_data=post_callback.new(action="save", post_id=post_id)))
    markup.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=post_callback.new(action="back", post_id=post_id)))
    return markup


async def delete_messages(call, post_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }) as response:
            respns = await response.json()
    try:
        messages_id = respns.get("data").get("messages_id")
        if messages_id is not None:
            for msg_id in messages_id:
                try:
                    await call.bot.delete_message(call.from_user.id, msg_id)
                except:
                    pass
    except:
        pass

    data = {"id": post_id,
            "messages_id": []}
    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                               json=data) as response:
            respons = await response.json()
    return respons


async def content_handler(message: types.Message, state: FSMContext):
    await state.reset_state()
    _ = message.bot.get("lang")
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel/count/key_value/",
                params={
                    "key": "user_id",
                    "value": message.from_user.id
                }) as response:
            respns = await response.json()
            amount = int(respns.get('data'))

    if amount >= 1:
        text = _(f'🗓 <b>КОНТЕНТ-ПЛАН</b>\n\n' \
                 f'В этом разделе вы можете просматривать и редактировать запланированные публикации. ' \
                 f'Выберите канал, в котором хотите увидеть контент-план.')

        data = {"user_id": message.from_user.id,
                "disabled": False}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel/get_user_channels_with_certain_subscriptions/",
                    json=data) as response:
                response1 = await response.json()
        markup = InlineKeyboardMarkup(row_width=2)
        for user_channel in response1.get('data'):
            id_channel = user_channel.get("id")
            title = user_channel.get("title")
            markup.insert(InlineKeyboardButton(text=f"{title}",
                                               callback_data=content_clb.new(action="content", channel_id=id_channel)))

        markup.add(InlineKeyboardButton(text="➕ Добавить новый канал", callback_data=add_channel_clb.new()))
        await message.bot.send_message(message.from_user.id, text, reply_markup=markup)
    else:
        text = _('<b>У вас пока нет подключенных каналов.</b>\n\n' \
                 'Чтобы подключить первый канал, сделайте @{} его администратором, дав следующие права:\n\n' \
                 '✅ Отправка сообщений\n' \
                 '✅ Удаление сообщений\n' \
                 '✅ Редактирование сообщений\n\n' \
                 'А затем перешлите любое сообщений канала в диалог с ботом либо отправьте публичную ссылку на ваш канал.').format(
            (await message.bot.get_me()).username)
        await message.answer(text)
        await CreatePost.Message_Is_Channel.set()


async def back_to_content(call: CallbackQuery, state: FSMContext):
    await state.reset_state()
    _ = call.bot.get("lang")
    await call.answer()
    try:
        await call.bot.delete_message(call.from_user.id, call.message.message_id)
    except:
        pass

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel/count/key_value/",
                params={
                    "key": "user_id",
                    "value": call.from_user.id
                }
        ) as response:
            respns = await response.json()
            amount = int(respns.get('data'))
    if amount >= 1:
        text = _(f"🗓 <b>КОНТЕНТ-ПЛАН</b>\n\n" \
                 f"В этом разделе вы можете просматривать и редактировать запланированные публикации. " \
                 f"Выберите канал, в котором хотите увидеть контент-план.")

        data = {"user_id": call.from_user.id,
                "disabled": False}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel/get_user_channels_with_certain_subscriptions/",
                    json=data) as response:
                response1 = await response.json()

        markup = InlineKeyboardMarkup(row_width=2)
        for user_channel in response1.get('data'):
            id_channel = user_channel.get("id")
            title = user_channel.get("title")
            markup.insert(InlineKeyboardButton(text=f"{title}",
                                               callback_data=content_clb.new(action="content", channel_id=id_channel)))

        markup.add(InlineKeyboardButton(text="➕ Добавить новый канал", callback_data=add_channel_clb.new()))
        await call.bot.send_message(call.from_user.id, text, reply_markup=markup)
    else:
        text = _('<b>У вас пока нет подключенных каналов.</b>\n\n' \
                 'Чтобы подключить первый канал, сделайте @{} его администратором, дав следующие права:\n\n' \
                 '✅ Отправка сообщений\n' \
                 '✅ Удаление сообщений\n' \
                 '✅ Редактирование сообщений\n\n' \
                 'А затем перешлите любое сообщений канала в диалог с ботом либо отправьте публичную ссылку на ваш канал.').format(
            (await call.bot.get_me()).username)
        await call.answer(text)


async def generate_calendar_content(markup, action, year, month, day, id_channel):
    month_calendar = []
    days_in_month = monthrange(year, month)[1]
    current_date = datetime(year, month, 1)
    offset = current_date.weekday()
    days_count = 0

    first_day_of_month = weekday(year, month, 1)
    full_weeks = math.ceil((days_in_month - (6 - first_day_of_month)) / 7)
    remaining_days = (days_in_month - (6 - first_day_of_month)) % 7
    if 1 < remaining_days <= 7:
        full_weeks += 1

    if action == "show_calendar":
        month_name = month_names.get(month)
        markup.row(
            InlineKeyboardButton(text=f"🗓 Скрыть календарь",
                                 callback_data=calendar_content.new(action="hide_calendar", year=str(year),
                                                                    month=str(month),
                                                                    day=str(day), channel_id=id_channel)))
        markup.row(
            InlineKeyboardButton(text='◀️ Предыдущий',
                                 callback_data=calendar_content.new(action="previous", year=str(year), month=str(month),
                                                                    day=str(day), channel_id=id_channel)),
            InlineKeyboardButton(text=f'{month_name} {year}',
                                 callback_data=calendar_content.new(action="empty", year=0, month=0, day=0,
                                                                    channel_id=id_channel)),
            InlineKeyboardButton(text='Следующий ▶️',
                                 callback_data=calendar_content.new(action="next", year=str(year), month=str(month),
                                                                    day=str(day), channel_id=id_channel))
        )

        markup.row(*[types.InlineKeyboardButton(text=day,
                                                callback_data=calendar_content.new(action="empty",
                                                                                   year=0, month=0, day=0,
                                                                                   channel_id=id_channel)) for day in
                     ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]])

        for _ in range(int(full_weeks)):
            week = []
            for i in range(7):
                if days_count < offset or days_count >= days_in_month + offset:
                    week.append(InlineKeyboardButton(
                        text=" ",
                        callback_data=calendar_content.new(action="empty", year=0, month=0, day=0,
                                                           channel_id=id_channel)
                    ))
                else:
                    day_clb = days_count - offset + 1
                    if int(day) == int(day_clb):
                        day_txt = f"✅ {day_clb}"
                    else:
                        day_txt = day_clb
                    week.append(InlineKeyboardButton(
                        text=day_txt,
                        callback_data=calendar_content.new(action="date", year=str(year), month=str(month),
                                                           day=str(day_clb), channel_id=id_channel)
                    ))
                days_count += 1
            month_calendar.append(week)

        for week in month_calendar:
            markup.row(*week)
    else:
        markup.row(InlineKeyboardButton(text=f"🗓 Показать календарь",
                                        callback_data=calendar_content.new(action="show_calendar", year=str(year),
                                                                           month=str(month),
                                                                           day=str(day), channel_id=id_channel)))
        variable_day = datetime(year, month, day)
        buttons = []
        tomorrow1 = variable_day - timedelta(days=1)
        tomorrow2 = variable_day + timedelta(days=1)
        days = [tomorrow1, variable_day, tomorrow2]

        for dayt in days:
            if dayt == variable_day:
                button_text = f"✅ {format_date(variable_day, format='EEE, dd MMM', locale='ru')}"
                buttons.append(InlineKeyboardButton(text=button_text,
                                                    callback_data=calendar_content.new(action="date",
                                                                                       year=str(variable_day.year),
                                                                                       month=str(variable_day.month),
                                                                                       day=variable_day.day,
                                                                                       channel_id=id_channel)))
            elif dayt == tomorrow1:
                button_text = f"← {format_date(tomorrow1, format='EEE, dd MMM', locale='ru')}"
                buttons.append(InlineKeyboardButton(text=button_text,
                                                    callback_data=calendar_content.new(action="date",
                                                                                       year=str(tomorrow1.year),
                                                                                       month=str(tomorrow1.month),
                                                                                       day=tomorrow1.day,
                                                                                       channel_id=id_channel)))
            elif dayt == tomorrow2:
                button_text = f"{format_date(tomorrow2, format='EEE, dd MMM', locale='ru')} →"
                buttons.append(InlineKeyboardButton(text=button_text,
                                                    callback_data=calendar_content.new(action="date",
                                                                                       year=str(tomorrow2.year),
                                                                                       month=str(tomorrow2.month),
                                                                                       day=tomorrow2.day,
                                                                                       channel_id=id_channel)))
            else:
                pass
        markup.row(*buttons)
    return markup


async def back_to_scheduled_channel_posts(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.reset_state()
    await call.answer()
    action = callback_data.get("action")
    post_id = int(action[5:])
    await delete_messages(call, post_id)
    await scheduled_channel_posts(call, callback_data, state)


async def scheduled_channel_posts(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.reset_state()
    _ = call.bot.get("lang")
    await call.answer()
    id_channel = callback_data.get("channel_id")
    action = callback_data.get("action")

    data = {"user_id": call.from_user.id,
            "channel_id": id_channel,
            "is_saved": False}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/all/",
                                json=data) as response:
            respns = await response.json()
    if respns.get('data') is not None:
        for item in respns.get('data'):
            id = int(item["id"])
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                        url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/{id}/"
                ) as response:
                    respns = await response.json()

    data = {"user_id": call.from_user.id,
            "channel_id": id_channel}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel/one/",
                                json=data) as response:
            response2 = await response.json()
    user_channel_settings_id = int(response2.get("data").get("user_channel_settings_id"))

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel_settings/one/key_value/",
                params={
                    "key": "id",
                    "value": user_channel_settings_id
                }) as response:
            response3 = await response.json()
    subscription_id = response3.get("data").get("subscription_id")

    if subscription_id is None:
        keyboard = InlineKeyboardMarkup(row_width=2)
        button_txt = _("🆓 Хочу пользоваться бесплатно")
        Back = _("⬅️ Назад")
        Next = _("➡️ Далее")
        subscription_payment_free_button = InlineKeyboardButton(text=button_txt,
                                                                callback_data=subscription_payment_clb.new(
                                                                    a="c",
                                                                    p='co_pl',
                                                                    t="f"
                                                                ))
        keyboard.add(subscription_payment_free_button)

        back = InlineKeyboardButton(text=Back,
                                    callback_data=subscription_payment_back_clb.new(
                                        a="s_p_b",
                                        p="co_pl",
                                        t="None"
                                    ))
        next = InlineKeyboardButton(text=Next,
                                    callback_data=subscription_payment_clb.new(
                                        a="s_p_n",
                                        p="co_pl",
                                        t="f"))
        keyboard.row(back, next)
        text = _("💰 ОПЛАТА ПОДПИСКИ\n\nЧтобы пользоваться Harvestly, необходима платная подписка. Чтобы подключить "
                 "подписку для ваших каналов, нажмите «Далее».\n\nИли попробуйте бесплатную версию:")
        await call.bot.send_message(
            chat_id=call.from_user.id,
            text=text,
            reply_markup=keyboard)
    else:
        data = {"user_id": call.from_user.id,
                "channel_id": id_channel,
                "is_scheduled": False}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/all/", json=data) as response:
                respns = await response.json()

        if respns.get('data') is not None:
            for item in respns.get('data'):
                id = int(item["id"])
                async with aiohttp.ClientSession() as session:
                    async with session.delete(
                            url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/{id}/"
                    ) as response:
                        respns = await response.json()

        if action is None:
            action = "hide_calendar"

        if action == "empty":
            pass
        else:
            markup = InlineKeyboardMarkup(row_width=1)
            current_date = await convert_to_user_time(call.from_user.id, datetime.utcnow().isoformat())
            try:
                year = int(callback_data.get("year"))
                month = int(callback_data.get("month"))
                day = int(callback_data.get("day"))
                if action == "previous":
                    action = "show_calendar"
                    if month == 1:
                        year -= 1
                        month = 12
                    else:
                        month -= 1
                elif action == "next":
                    action = "show_calendar"
                    if month == 12:
                        year += 1
                        month = 1
                    else:
                        month += 1
                else:
                    pass
            except:
                year, month, day = current_date.year, current_date.month, current_date.day

            await generate_calendar_content(markup, action, int(year), int(month), int(day), id_channel)
            date = datetime(int(year), int(month), int(day))

            data = {"id": id_channel}
            async with aiohttp.ClientSession() as session:
                async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel/one/",
                                        json=data) as response:
                    respns = await response.json()
            title = respns.get("data").get("title")
            link = respns.get("data").get("link")
            url = f"<a href='{link}'>{title}</a>"

            scheduled_posts = {}
            user_response: Response[UserSchema] = Response[UserSchema].model_validate(
                await user_api.get_one_by_key_value(params={
                    "key": "id",
                    "value": call.from_user.id
                })
            )

            data = {  # "user_id": call.from_user.id,
                "channel_id": id_channel,
                "date": (date - timedelta(hours=user_response.data.time_zone)).replace(tzinfo=None).isoformat(),
                "is_scheduled": True
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/get_filtered_posts/",
                        json=data) as response:
                    response1 = await response.json()
            posts = response1.get('data')

            for post in posts:
                id = int(post["id"])

                date_object = datetime.strptime(post["date"], "%Y-%m-%dT%H:%M:%S")
                new_date_object = date_object + timedelta(hours=user_response.data.time_zone)

                new_date_string = new_date_object.strftime("%Y-%m-%dT%H:%M:%S")

                scheduled_datetime = new_date_string
                description = post["description"]
                scheduled_posts[id] = f"{scheduled_datetime}>|<{description}"

            count = len(scheduled_posts)
            current_date_utc = datetime.utcnow()

            sorted_posts = sorted(scheduled_posts.items(),
                                  key=lambda item: datetime.strptime(item[1].split('>|<')[0], "%Y-%m-%dT%H:%M:%S"))

            for id, value in sorted_posts:
                all_value = value.split(">|<")
                time = all_value[0]
                description = all_value[1]
                date_parts = time.split("T")

                date_components = date_parts[1].split(":")
                hour = date_components[0]
                minute = date_components[1]

                date_components1 = date_parts[0].split("-")
                year = date_components1[0]
                month = date_components1[1]
                day = date_components1[2]

                utc_scheduled_time = datetime(int(year), int(month), int(day), int(hour), int(minute)) - timedelta(
                    hours=user_response.data.time_zone)
                if current_date_utc > utc_scheduled_time:
                    data = {"post_id": int(id)}
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/one/",
                                                json=data) as response:
                            respons = await response.json()
                    if respons.get("data") is None:
                        continue
                    messages_id = respons.get("data").get("message")
                    if messages_id is not None:
                        emoji = "✅ "
                    else:
                        emoji = "❌ "
                else:
                    emoji = "🕔 "
                if len(description) > 30:
                    description = f"{description[:30]}..."
                scheduled_time = f"{hour}:{minute}"
                markup.add(InlineKeyboardButton(text=f"{emoji}{scheduled_time} {description}",
                                                callback_data=post_callback.new(action="next", post_id=id)))

            formatted_date = format_date(date, format='EEEE, d MMMM y', locale='ru')
            text = _("🗓 <b>КОНТЕНТ-ПЛАН</b>\n\n" \
                     "На <b>{}</b> в канале {} запланированы посты ({} шт.). " \
                     "Чтобы посмотреть другие даты воспользуйтесь кнопками ниже").format(formatted_date, url, count)
            Back = _("⬅️ Назад")
            markup.add(InlineKeyboardButton(text=Back, callback_data=cancel_content.new()))
            await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def post_handler(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.reset_state()
    await call.answer()
    _ = call.bot.get("lang")
    await call.bot.delete_message(call.from_user.id, call.message.message_id)
    post_id = callback_data.get("post_id")
    await delete_messages(call, post_id)

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }) as response:
            response1 = await response.json()
    media_data = response1.get("data").get("media")
    buttons = response1.get("data").get("url_buttons")
    caption = response1.get("data").get("description")
    entities = response1.get("data").get("entities")
    entities = [types.MessageEntity(**entity) for entity in
                json.loads(entities)] if entities else None

    utc_time_iso = response1.get("data").get("date")
    scheduled_datetime_utc = datetime.fromisoformat(utc_time_iso)
    user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)

    scheduled_datetime = datetime(int(user_input_time.year), int(user_input_time.month), int(user_input_time.day),
                                  int(user_input_time.hour), int(user_input_time.minute))
    id_channel = response1.get('data').get("channel_id")

    markup = InlineKeyboardMarkup(row_width=2)
    if buttons is not None:
        inline_keyboard = []
        for row in buttons:
            elements = row.split(' | ')
            row_buttons = []
            for element in elements:
                title, url = element.split(' - ')
                row_buttons.append(InlineKeyboardButton(text=title, url=url))
            inline_keyboard.append(row_buttons)

        markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    data = {"user_id": call.from_user.id,
            "channel_id": id_channel}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel/one/",
                                json=data) as response:
            response2 = await response.json()
    user_channel_settings_id = int(response2.get("data").get("user_channel_settings_id"))

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel_settings/one/key_value/",
                params={
                    "key": "id",
                    "value": user_channel_settings_id
                }) as response:
            response3 = await response.json()
    auto_sign = response3.get("data").get("auto_sign")
    auto_sign_entities = response3.get('data').get('auto_sign_entities')
    auto_sign_entities = [types.MessageEntity(**entity) for entity in
                          json.loads(auto_sign_entities)] if auto_sign_entities else None

    combined_entities = copy.deepcopy(entities)

    if caption is not None:
        auto_sign_text = response3.get("data").get("auto_sign_text")
        if str(auto_sign) == "True":
            if auto_sign_text is not None:
                caption += f"\n\n{auto_sign_text}"

                text_length = count_characters(caption)
                auto_sign_len = count_characters(auto_sign_text)  # +2 для переноса строки между сообщениями

                updated_signature_entities = [
                    types.MessageEntity(
                        type=entity.type,
                        offset=text_length - auto_sign_len,
                        length=entity.length,
                        url=entity.url,
                        user=entity.user,
                        language=entity.language
                    ) for entity in auto_sign_entities
                ] if auto_sign_entities else None

                # Объединение стилей основного сообщения и автоподписи
                if entities is not None and updated_signature_entities is not None:
                    combined_entities += updated_signature_entities
                elif entities is None and updated_signature_entities:
                    combined_entities = updated_signature_entities
    else:
        auto_sign_text = response3.get("data").get("auto_sign_text")
        if str(auto_sign) == "True":
            if auto_sign_text is not None:
                caption = f"\n\n{auto_sign_text}"

                text_length = count_characters(caption)
                auto_sign_len = count_characters(auto_sign_text)  # +2 для переноса строки между сообщениями

                updated_signature_entities = [
                    types.MessageEntity(
                        type=entity.type,
                        offset=text_length - auto_sign_len,
                        length=entity.length,
                        url=entity.url,
                        user=entity.user,
                        language=entity.language
                    ) for entity in auto_sign_entities
                ] if auto_sign_entities else None

                # Объединение стилей основного сообщения и автоподписи
                if entities is not None and updated_signature_entities is not None:
                    combined_entities += updated_signature_entities
                elif entities is None and updated_signature_entities:
                    combined_entities = updated_signature_entities
        else:
            caption = None

    if media_data is not None:
        if len(media_data) > 1:
            media = types.MediaGroup()
            for index, media_id in enumerate(media_data):
                if media_id.get("media_type") == "photo":
                    media.attach(types.InputMediaPhoto(media_id.get("file_id"),
                                                       caption=caption if index == 0 and caption is not None and buttons is None else None))
                elif media_id.get("media_type") == "video":
                    media.attach(types.InputMediaVideo(media_id.get("file_id"),
                                                       caption=caption if index == 0 and caption is not None and buttons is None else None))
                elif media_id.get("media_type") == "document":
                    media.attach(types.InputMediaDocument(media_id.get("file_id"),
                                                          caption=caption if index == 0 and caption is not None and buttons is None else None))
                elif media_id.get("media_type") == "audio":
                    media.attach(types.InputMediaAudio(media_id.get("file_id"),
                                                       caption=caption if index == 0 and caption is not None and buttons is None else None))

            media.media[0].caption_entites = combined_entities
            messages = await call.bot.send_media_group(chat_id=call.from_user.id, media=media)

            data = {"id": post_id,
                    "messages_id": [message["message_id"] for message in messages]}

            async with aiohttp.ClientSession() as session:
                async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                       json=data) as response:
                    unused_response = await response.json()
        else:
            media_id = media_data[0]

            if media_id.get("media_type") == "photo":
                msg = await call.bot.send_photo(call.from_user.id, media_id.get("file_id"), caption,
                                                caption_entities=combined_entities,
                                                reply_markup=markup)

            elif media_id.get("media_type") == "video":
                msg = await call.bot.send_video(call.from_user.id,
                                                media_id.get("file_id"),
                                                caption=caption,
                                                caption_entities=combined_entities,
                                                reply_markup=markup)

            elif media_id.get("media_type") == "document":
                msg = await call.bot.send_document(call.from_user.id,
                                                   media_id.get("file_id"),
                                                   caption=caption,
                                                   caption_entities=combined_entities,
                                                   reply_markup=markup)

            elif media_id.get("media_type") == "audio":
                msg = await call.bot.send_audio(call.from_user.id,
                                                media_id.get("file_id"),
                                                caption=caption,
                                                caption_entities=combined_entities,
                                                reply_markup=markup)

            elif media_id.get("media_type") == "animation":
                msg = await call.bot.send_animation(call.from_user.id,
                                                    media_id.get("file_id"),
                                                    caption=caption,
                                                    caption_entities=combined_entities,
                                                    reply_markup=markup)

            elif media_id.get("media_type") == "video_note":
                msg = await call.bot.send_video_note(call.from_user.id,
                                                     media_id.get("file_id"),
                                                     reply_markup=markup)

            data = {"id": post_id,
                    "messages_id": [msg.message_id]}

            async with aiohttp.ClientSession() as session:
                async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                       json=data) as response:
                    unused_response = await response.json()
    else:
        data = {"id": post_id,
                "messages_id": []}
        msg = await call.bot.send_message(call.from_user.id, caption, entities=combined_entities, reply_markup=markup)
        data["messages_id"].append(msg.message_id)

        async with aiohttp.ClientSession() as session:
            async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                   json=data) as response:
                unused_response = await response.json()

    markup2 = InlineKeyboardMarkup(row_width=2)
    current_date_utc = datetime.utcnow()
    formatted_date = format_date(scheduled_datetime, format='EEEE, d MMMM y', locale='ru')
    username = (await call.bot.get_chat_member(chat_id=call.from_user.id, user_id=call.from_user.id)).user.username
    username = f"@{username}" if username is not None else "Отсутствует"

    try:
        auto_del_timer = int(response1.get("data").get("auto_delete_timer"))

        if auto_del_timer == 0:
            exist_del_timer = "нет"
        elif auto_del_timer < 3600:
            minutes = auto_del_timer // 60
            exist_del_timer = f"{minutes} мин"
        elif auto_del_timer < 86400:
            hours = auto_del_timer // 3600
            exist_del_timer = f"{hours}ч"
        else:
            days = auto_del_timer // 86400
            exist_del_timer = f"{days}д"
    except:
        exist_del_timer = "нет"

    if current_date_utc > scheduled_datetime_utc:

        data = {"post_id": int(post_id)}

        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/one/",
                                    json=data) as response:
                respons = await response.json()

        messages_id = respons.get("data").get("message")

        if messages_id is not None:
            channel_response: Response[ChannelSchema] = Response[ChannelSchema].model_validate(
                await channel_api.get_one_by_key_value(
                    params={"key": "id", "value": id_channel})
            )

            msg_id_in_channel = messages_id['message']
            if type(msg_id_in_channel) is list:
                msg_link = f"{channel_response.data.link}/{msg_id_in_channel[0]}"
            else:
                msg_link = f"{channel_response.data.link}/{msg_id_in_channel}"

            status = _("Опубликован")
            edit_btn = _("Изменить")
            delete_btn = _("Удалить")
            auto_delete_btn = _("Таймер автоудаления: {}").format(exist_del_timer)
            duplicate_btn = _("Дублировать")

            markup2.row(
                InlineKeyboardButton(text=edit_btn,
                                     callback_data=post_callback.new(action="edit", post_id=post_id)),
                InlineKeyboardButton(text=delete_btn,
                                     callback_data=post_callback.new(action="delete", post_id=post_id)
                                     )
            )
            markup2.add(InlineKeyboardButton(text=auto_delete_btn,
                                             callback_data=sending_clbk_content_plan.new(action="auto_delete",
                                                                                         channel_id=id_channel,
                                                                                         post_id=post_id)))

            markup2.add(InlineKeyboardButton(text=duplicate_btn,
                                             callback_data=post_callback.new(action="duplicate", post_id=post_id)))
            text = _("Статус: <b>{}</b>\nСсылка: {}\nДата: <b>{}</b>\nАвтор: {}").format(status, msg_link, formatted_date, username)
        else:
            status = _("Удален")
            delete_btn = _("❌ Удалить из контент плана")
            duplicate_btn = _("Дублировать")
            markup2.add(InlineKeyboardButton(text=delete_btn,
                                             callback_data=post_callback.new(action="delete_from_content",
                                                                             post_id=post_id)))
            markup2.add(InlineKeyboardButton(text=duplicate_btn,
                                             callback_data=post_callback.new(action="duplicate", post_id=post_id)))

            text = _("Статус: <b>{}</b>\nДата: <b>{}</b>\nАвтор: {}").format(status, formatted_date, username)

    else:
        text = _("Статус: <b>Ожидает публикации</b>\nДата: <b>{}</b>\nАвтор: {}").format(formatted_date, username)
        publish_btn = _("🚀 Опубликовать")
        edit_btn = _("Изменить")
        delete_btn = _("❌ Удалить из контент плана")
        auto_delete_btn = _("Таймер автоудаления: {}").format(exist_del_timer)
        edit_time_btn = _("🕔 Изменить дату и время")
        duplicate_btn = _("Дублировать")

        markup2.row(InlineKeyboardButton(text=publish_btn,
                                         callback_data=sending_clbk.new(action="publish", channel_id=id_channel,
                                                                        post_id=post_id)),
                    InlineKeyboardButton(text=edit_btn,
                                         callback_data=post_callback.new(action="edit_not_scheduled", post_id=post_id)))

        markup2.add(InlineKeyboardButton(text=auto_delete_btn,
                                         callback_data=sending_clbk_content_plan.new(action="auto_delete",
                                                                                     channel_id=id_channel,
                                                                                     post_id=post_id)))

        markup2.add(InlineKeyboardButton(text=duplicate_btn,
                                         callback_data=post_callback.new(action="duplicate", post_id=post_id)))

        markup2.row(InlineKeyboardButton(text=edit_time_btn,
                                         callback_data=post_callback.new(action="edit_time", post_id=post_id)))
        markup2.row(InlineKeyboardButton(text=delete_btn,
                                         callback_data=post_callback.new(action="delete", post_id=post_id)))

    Back = _("⬅️ Назад")
    markup2.row(InlineKeyboardButton(text=Back,
                                     callback_data=content_clb.new(action=f"back_{post_id}", channel_id=id_channel)))
    await call.bot.send_message(call.from_user.id, text, reply_markup=markup2, disable_web_page_preview=True)


async def delete_post(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.reset_state()
    _ = call.bot.get("lang")
    await call.answer()
    await call.bot.delete_message(call.from_user.id, call.message.message_id)
    post_id = callback_data.get("post_id")
    await delete_messages(call, post_id)
    text = _("Вы уверены, что хотите удалить выбранный пост?")
    markup = InlineKeyboardMarkup(row_width=1)
    delete_btn = _("Да, удалить")
    Back = _("⬅️ Назад")
    markup.add(InlineKeyboardButton(text=delete_btn,
                                    callback_data=post_callback.new(action="delete_confirm", post_id=post_id)))
    markup.add(InlineKeyboardButton(text=Back, callback_data=post_callback.new(action="next", post_id=post_id)))
    await call.bot.send_message(call.from_user.id, text, reply_markup=markup)


async def delete_post_confirm(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.reset_state()
    _ = call.bot.get("lang")
    await call.answer()
    await call.bot.delete_message(call.from_user.id, call.message.message_id)
    post_id = callback_data.get("post_id")

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }) as response:
            respns = await response.json()
    id_channel = int(respns.get('data').get("channel_id"))
    chat_id = id_channel

    utc_time_iso = respns.get("data").get("date")
    scheduled_datetime_utc = datetime.fromisoformat(utc_time_iso)

    current_date_utc = datetime.utcnow()
    data = {"post_id": int(post_id)}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/one/",
                                json=data) as response:
            respons = await response.json()
    message_id = respons.get("data").get("id")
    if current_date_utc > scheduled_datetime_utc:
        try:
            messages_id = respons.get("data").get("message")
            messages_to_del = []
            if messages_id.get('message'):
                if type(messages_id.get('message')) is list:
                    messages_to_del = messages_id['message']
                else:
                    messages_to_del.append(int(messages_id['message']))

            for id in messages_to_del:
                await call.bot.delete_message(chat_id, int(id))
            text = _("Пост успешно удален из канала")

            data = {"id": message_id, "message": None}
            async with aiohttp.ClientSession() as session:
                async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/",
                                       json=data) as response:
                    responsee = await response.json()
        except:
            text = _("Пост уже удален из канала")

    else:
        text = _("Пост успешно удален из контент плана")

        async with aiohttp.ClientSession() as session:
            async with session.delete(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/{message_id}/"
            ) as response:
                respons = await response.json()
        job_id = respons.get("data").get("job_id")
        job = scheduler.remove_job(job_id)

        async with aiohttp.ClientSession() as session:
            async with session.delete(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/{post_id}/"
            ) as response:
                respons = await response.json()

    await call.bot.send_message(call.from_user.id, text)


async def delete_from_content_plan(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.reset_state()
    await call.answer()
    _ = call.bot.get("lang")
    await call.bot.delete_message(call.from_user.id, call.message.message_id)
    post_id = callback_data.get("post_id")
    await delete_messages(call, post_id)
    text = _("Вы уверены, что хотите удалить выбранный пост из Контент-плана?")
    markup = InlineKeyboardMarkup(row_width=1)
    delete_btn = _("Да, удалить")
    Back = _("⬅️ Назад")
    markup.add(InlineKeyboardButton(text=delete_btn,
                                    callback_data=post_callback.new(action="delete_from_content_confirm",
                                                                    post_id=post_id)))
    markup.add(InlineKeyboardButton(text=Back, callback_data=post_callback.new(action="next", post_id=post_id)))
    await call.bot.send_message(call.from_user.id, text, reply_markup=markup)


async def delete_from_content_plan_confirm(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.reset_state()
    _ = call.bot.get("lang")
    await call.answer()
    await call.bot.delete_message(call.from_user.id, call.message.message_id)
    post_id = callback_data.get("post_id")

    data = {"post_id": int(post_id)}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/one/",
                                json=data) as response:
            respons = await response.json()
    message_id = respons.get("data").get("id")

    async with aiohttp.ClientSession() as session:
        async with session.delete(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/{message_id}/"
        ) as response:
            respons = await response.json()

    text = _("Пост успешно удален из контент плана")

    async with aiohttp.ClientSession() as session:
        async with session.delete(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/{post_id}/"
        ) as response:
            respons = await response.json()

    await call.bot.send_message(call.from_user.id, text)


async def duplicate(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.reset_state()
    await call.answer()
    post_id = int(callback_data.get("post_id"))
    await delete_messages(call, post_id)

    data = {"id": post_id}
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/",
                json=data
        ) as response:
            post_response = await response.json()

    data = post_response['data']
    data.pop("id")
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                json=data
        ) as response:
            post_duplicate_response = await response.json()

    update_callback_data = {"post_id": post_duplicate_response.get('data').get('id')}
    await edit_post(call, update_callback_data, state)


async def edit_scheduled_post(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.reset_state()
    await call.answer()
    await call.bot.delete_message(call.from_user.id, call.message.message_id)
    post_id = callback_data.get("post_id")
    action = callback_data.get("action")

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "initial_post_id",
                    "value": post_id
                }) as response:
            response1 = await response.json()

    if response1.get("status") == "error":
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                    params={
                        "key": "id",
                        "value": post_id
                    }) as response:
                response1 = await response.json()

    post_id = response1.get("data").get("id")
    await delete_messages(call, post_id)

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }) as response:
            response1 = await response.json()

    if action == "edit":
        if response1.get("data").get("is_saved"):
            data = {
                "user_id": call.from_user.id,
                "description": response1.get("data").get("description"),
                "url_buttons": response1.get("data").get("url_buttons"),
                "media": response1.get("data").get("media"),
                "messages_id": [],
                "channel_id": response1.get("data").get("channel_id"),
                "date": response1.get("data").get("date"),
                "auto_delete_timer": response1.get("data").get("auto_delete_timer"),
                "is_saved": False,
                "is_scheduled": response1.get("data").get("is_scheduled"),
                "initial_post_id": post_id,
                "entities": response1.get("data").get("entities")
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                        json=data) as response:
                    response2 = await response.json()
                    post_id = response2.get("data").get("id")

    media_data = response1.get("data").get("media")
    caption = response1.get("data").get("description")
    buttons = response1.get("data").get("url_buttons")
    messages_id = response1.get("data").get("messages_id")
    id_channel = int(response1.get("data").get("channel_id"))
    entities = response1.get("data").get("entities")
    entities = [types.MessageEntity(**entity) for entity in
                json.loads(entities)] if entities else None

    if messages_id is not None:
        for msg_id in messages_id:
            await call.bot.delete_message(call.from_user.id, msg_id)

    markup = InlineKeyboardMarkup(row_width=2)
    if buttons is not None:
        inline_keyboard = []
        for row in buttons:
            elements = row.split(' | ')
            row_buttons = []
            for element in elements:
                title, url = element.split(' - ')
                row_buttons.append(InlineKeyboardButton(text=title, url=url))
            inline_keyboard.append(row_buttons)

        markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    data = {"user_id": call.from_user.id,
            "channel_id": id_channel}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel/one/",
                                json=data) as response:
            response3 = await response.json()
    user_channel_settings_id = int(response3.get("data").get("user_channel_settings_id"))

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel_settings/one/key_value/",
                params={
                    "key": "id",
                    "value": user_channel_settings_id
                }
        ) as response:
            response4 = await response.json()
    auto_sign = response4.get("data").get("auto_sign")
    exist_auto_sign = ""
    auto_sign_entities = response4.get('data').get('auto_sign_entities')
    auto_sign_entities = [types.MessageEntity(**entity) for entity in
                          json.loads(auto_sign_entities)] if auto_sign_entities else None

    combined_entities = copy.deepcopy(entities)

    if caption is not None:
        auto_sign_text = response4.get("data").get("auto_sign_text")
        if str(auto_sign) == "True":
            if auto_sign_text is not None:
                caption += f"\n\n{auto_sign_text}"
                exist_auto_sign = "✅ "

                text_length = count_characters(caption)
                auto_sign_len = count_characters(auto_sign_text)  # +2 для переноса строки между сообщениями

                updated_signature_entities = [
                    types.MessageEntity(
                        type=entity.type,
                        offset=text_length - auto_sign_len,
                        length=entity.length,
                        url=entity.url,
                        user=entity.user,
                        language=entity.language
                    ) for entity in auto_sign_entities
                ] if auto_sign_entities else None

                # Объединение стилей основного сообщения и автоподписи
                if entities is not None and updated_signature_entities is not None:
                    combined_entities += updated_signature_entities
                elif entities is None and updated_signature_entities:
                    combined_entities = updated_signature_entities

        descrip_button = "Изменить описание"
    else:
        auto_sign_text = response4.get("data").get("auto_sign_text")
        if str(auto_sign) == "True":
            if auto_sign_text is not None:
                caption = f"\n\n{auto_sign_text}"
                descrip_button = "Изменить описание"
                exist_auto_sign = "✅ "

                text_length = count_characters(caption)
                auto_sign_len = count_characters(auto_sign_text)  # +2 для переноса строки между сообщениями

                updated_signature_entities = [
                    types.MessageEntity(
                        type=entity.type,
                        offset=text_length - auto_sign_len,
                        length=entity.length,
                        url=entity.url,
                        user=entity.user,
                        language=entity.language
                    ) for entity in auto_sign_entities
                ] if auto_sign_entities else None

                # Объединение стилей основного сообщения и автоподписи
                if entities is not None and updated_signature_entities is not None:
                    combined_entities += updated_signature_entities
                elif entities is None and updated_signature_entities:
                    combined_entities = updated_signature_entities
        else:
            caption = None
            descrip_button = "Добавить описание"

    if media_data is not None:
        if len(media_data) > 1:

            media = types.MediaGroup()
            for media_id in media_data:
                if media_id.get("media_type") == "photo":
                    media.attach(types.InputMediaPhoto(media_id.get("file_id")))
                elif media_id.get("media_type") == "video":
                    media.attach(types.InputMediaVideo(media_id.get("file_id")))
                elif media_id.get("media_type") == "document":
                    media.attach(types.InputMediaDocument(media_id.get("file_id")))
                elif media_id.get("media_type") == "audio":
                    media.attach(types.InputMediaAudio(media_id.get("file_id")))

            media.media[0].caption_entites = combined_entities
            messages = await call.bot.send_media_group(chat_id=call.from_user.id, media=media)
            markup = await markup_media_content_plan(markup, descrip_button, exist_auto_sign, post_id)

            data = {"id": post_id,
                    "messages_id": [message["message_id"] for message in messages]}

            async with aiohttp.ClientSession() as session:
                async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                       json=data) as response:
                    unused_response = await response.json()

            await call.bot.send_message(call.from_user.id, caption, reply_markup=markup)
        else:
            media_id = media_data[0]

            if media_id.get("media_type") == "photo":
                markup = await markup_media_content_plan(markup, descrip_button, exist_auto_sign, post_id)
                msg = await call.bot.send_photo(call.from_user.id, media_id.get("file_id"), caption,
                                                caption_entities=combined_entities,
                                                reply_markup=markup)

            elif media_id.get("media_type") == "video":
                markup = await markup_media_content_plan(markup, descrip_button, exist_auto_sign, post_id)
                msg = await call.bot.send_video(call.from_user.id, media_id.get("file_id"), caption=caption,
                                                caption_entities=combined_entities,
                                                reply_markup=markup)
            elif media_id.get("media_type") == "document":
                markup = await markup_media_content_plan(markup, descrip_button, exist_auto_sign, post_id)
                msg = await call.bot.send_document(call.from_user.id, media_id.get("file_id"),
                                                   caption=caption,
                                                   caption_entities=combined_entities,
                                                   reply_markup=markup)
            elif media_id.get("media_type") == "audio":
                markup = await markup_media_content_plan(markup, descrip_button, exist_auto_sign, post_id)
                msg = await call.bot.send_audio(call.from_user.id, media_id.get("file_id"), caption=caption,
                                                caption_entities=combined_entities,
                                                reply_markup=markup)
            elif media_id.get("media_type") == "video_note":
                markup = await markup_media_content_plan(markup, descrip_button, exist_auto_sign, post_id)
                msg = await call.bot.send_video_note(call.from_user.id, media_id.get("file_id"),
                                                     reply_markup=markup)
            elif media_id.get("media_type") == "animation":
                markup = await markup_media_content_plan(markup, descrip_button, exist_auto_sign, post_id)
                msg = await call.bot.send_animation(call.from_user.id, media_id.get("file_id"),
                                                    caption=caption,
                                                    caption_entities=combined_entities,
                                                    reply_markup=markup)

            data = {"id": post_id,
                    "messages_id": [msg.message_id]}

            async with aiohttp.ClientSession() as session:
                async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                       json=data) as response:
                    unused_response = await response.json()
    else:
        markup1 = await markup_media_content_plan(markup, descrip_button, exist_auto_sign, post_id)
        await call.bot.send_message(call.from_user.id, caption, entities=combined_entities, reply_markup=markup1)


async def edit_scheduled_post_message(message: types.Message, state: FSMContext, post_id: int, action: str):
    await state.reset_state()

    await delete_messages(message, post_id)

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }) as response:
            response1 = await response.json()

    media_data = response1.get("data").get("media")
    caption = response1.get("data").get("description")
    buttons = response1.get("data").get("url_buttons")
    messages_id = response1.get("data").get("messages_id")
    id_channel = int(response1.get("data").get("channel_id"))
    entities = response1.get("data").get("entities")
    entities = [types.MessageEntity(**entity) for entity in
                json.loads(entities)] if entities else None

    if messages_id is not None:
        for msg_id in messages_id:
            await message.bot.delete_message(message.from_user.id, msg_id)

    markup = InlineKeyboardMarkup(row_width=2)
    if buttons is not None:
        inline_keyboard = []
        for row in buttons:
            elements = row.split(' | ')
            row_buttons = []
            for element in elements:
                title, url = element.split(' - ')
                row_buttons.append(InlineKeyboardButton(text=title, url=url))
            inline_keyboard.append(row_buttons)

        markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    data = {"user_id": message.from_user.id,
            "channel_id": id_channel}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel/one/",
                                json=data) as response:
            response3 = await response.json()
    user_channel_settings_id = int(response3.get("data").get("user_channel_settings_id"))

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel_settings/one/key_value/",
                params={
                    "key": "id",
                    "value": user_channel_settings_id
                }
        ) as response:
            response4 = await response.json()

    auto_sign = response4.get("data").get("auto_sign")
    exist_auto_sign = ""
    auto_sign_entities = response4.get('data').get('auto_sign_entities')
    auto_sign_entities = [types.MessageEntity(**entity) for entity in
                          json.loads(auto_sign_entities)] if auto_sign_entities else None

    combined_entities = copy.deepcopy(entities)

    if caption is not None:
        auto_sign_text = response4.get("data").get("auto_sign_text")
        if str(auto_sign) == "True":
            if auto_sign_text is not None:
                caption += f"\n\n{auto_sign_text}"
                exist_auto_sign = "✅ "

                text_length = count_characters(caption)
                auto_sign_len = count_characters(auto_sign_text)  # +2 для переноса строки между сообщениями

                updated_signature_entities = [
                    types.MessageEntity(
                        type=entity.type,
                        offset=text_length - auto_sign_len,
                        length=entity.length,
                        url=entity.url,
                        user=entity.user,
                        language=entity.language
                    ) for entity in auto_sign_entities
                ] if auto_sign_entities else None

                # Объединение стилей основного сообщения и автоподписи
                if entities is not None and updated_signature_entities is not None:
                    combined_entities += updated_signature_entities
                elif entities is None and updated_signature_entities:
                    combined_entities = updated_signature_entities

        descrip_button = "Изменить описание"
    else:
        auto_sign_text = response4.get("data").get("auto_sign_text")
        if str(auto_sign) == "True":
            if auto_sign_text is not None:
                caption = f"\n\n{auto_sign_text}"
                descrip_button = "Изменить описание"
                exist_auto_sign = "✅ "

                text_length = count_characters(caption)
                auto_sign_len = count_characters(auto_sign_text)  # +2 для переноса строки между сообщениями

                updated_signature_entities = [
                    types.MessageEntity(
                        type=entity.type,
                        offset=text_length - auto_sign_len,
                        length=entity.length,
                        url=entity.url,
                        user=entity.user,
                        language=entity.language
                    ) for entity in auto_sign_entities
                ] if auto_sign_entities else None

                # Объединение стилей основного сообщения и автоподписи
                if entities is not None and updated_signature_entities is not None:
                    combined_entities += updated_signature_entities
                elif entities is None and updated_signature_entities:
                    combined_entities = updated_signature_entities
        else:
            caption = None
            descrip_button = "Добавить описание"

    if media_data is not None:
        if len(media_data) > 1:
            caption = "(Описание)" if caption is None else caption

            media = types.MediaGroup()
            for media_id in media_data:
                if media_id.get("media_type") == "photo":
                    media.attach(types.InputMediaPhoto(media_id.get("file_id")))
                elif media_id.get("media_type") == "video":
                    media.attach(types.InputMediaVideo(media_id.get("file_id")))
                elif media_id.get("media_type") == "document":
                    media.attach(types.InputMediaDocument(media_id.get("file_id")))
                elif media_id.get("media_type") == "audio":
                    media.attach(types.InputMediaAudio(media_id.get("file_id")))

            media.media[0].caption_entites = combined_entities

            messages = await message.bot.send_media_group(chat_id=message.from_user.id, media=media)
            markup = await markup_media_content_plan(markup, descrip_button, exist_auto_sign, post_id)

            data = {"id": post_id,
                    "messages_id": [message["message_id"] for message in messages]}

            async with aiohttp.ClientSession() as session:
                async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                       json=data) as response:
                    unused_response = await response.json()

            await message.bot.send_message(message.from_user.id, caption, reply_markup=markup)
        else:
            media_id = media_data[0]

            if media_id.get("media_type") == "photo":
                markup = await markup_media_content_plan(markup, descrip_button, exist_auto_sign, post_id)
                msg = await message.bot.send_photo(message.from_user.id, media_id.get("file_id"), caption,
                                                   caption_entities=combined_entities,
                                                   reply_markup=markup)

            elif media_id.get("media_type") == "video":
                markup = await markup_media_content_plan(markup, descrip_button, exist_auto_sign, post_id)
                msg = await message.bot.send_video(message.from_user.id,
                                                   media_id.get("file_id"),
                                                   caption=caption,
                                                   caption_entities=combined_entities,
                                                   reply_markup=markup)

            elif media_id.get("media_type") == "document":
                markup = await markup_media_content_plan(markup, descrip_button, exist_auto_sign, post_id)
                msg = await message.bot.send_document(message.from_user.id,
                                                      media_id.get("file_id"),
                                                      caption=caption,
                                                      caption_entities=combined_entities,
                                                      reply_markup=markup)

            elif media_id.get("media_type") == "audio":
                markup = await markup_media_content_plan(markup, descrip_button, exist_auto_sign, post_id)
                msg = await message.bot.send_audio(message.from_user.id,
                                                   media_id.get("file_id"),
                                                   caption=caption,
                                                   caption_entities=combined_entities,
                                                   reply_markup=markup)

            elif media_id.get("media_type") == "animation":
                markup = await markup_media_content_plan(markup, descrip_button, exist_auto_sign, post_id)
                msg = await message.bot.send_animation(message.from_user.id,
                                                       media_id.get("file_id"),
                                                       caption=caption,
                                                       caption_entities=combined_entities,
                                                       reply_markup=markup)

            elif media_id.get("media_type") == "video_note":
                markup = await markup_media_content_plan(markup, descrip_button, exist_auto_sign, post_id)
                msg = await message.bot.send_video_note(message.from_user.id,
                                                        media_id.get("file_id"),
                                                        reply_markup=markup)

            data = {"id": post_id,
                    "messages_id": [msg.message_id]}

            async with aiohttp.ClientSession() as session:
                async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                       json=data) as response:
                    unused_response = await response.json()
    else:
        markup1 = await markup_media_content_plan(markup, descrip_button, exist_auto_sign, post_id)
        await message.bot.send_message(message.from_user.id, caption, entities=combined_entities, reply_markup=markup1)


async def descripion(call: CallbackQuery, callback_data: dict, state: FSMContext):
    post_id = int(callback_data.get("post_id"))
    _ = call.bot.get("lang")

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }) as response:
            response1 = await response.json()

    media_data = response1.get("data").get("media")

    if media_data is not None:
        if len(media_data) == 1 and media_data[0]['media_type'] == "video_note":
            text = _("❌ Описание для данного поста не поддерживается")
            await call.answer(text=text, show_alert=True)
            return

    await call.answer()
    await call.bot.delete_message(call.from_user.id, call.message.message_id)
    action = callback_data.get("action")
    await delete_messages(call, post_id)

    text = _("Отправьте новый текст для поста")
    Back = _("⬅️ Назад")
    markup = InlineKeyboardMarkup(row_width=1)
    markup.row(InlineKeyboardButton(text=Back,
                                    callback_data=choose_prompts_content.new(action="back", index=999,
                                                                             post_id=post_id)))
    msg = await call.bot.send_message(call.from_user.id, text, reply_markup=markup)
    await Content.Get_Description.set()
    await state.update_data(msg=msg.message_id)
    await state.update_data(post_id=post_id)
    await state.update_data(action=action)


# Create.Get_Description
async def descripion_add(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg = data.get("msg")
    action = data.get("action")
    post_id = int(data.get("post_id"))
    await message.bot.delete_message(message.from_user.id, msg)

    data = {
        "id": post_id,
        "description": message.text,
        "entities": json.dumps([entity.to_python() for entity in message.caption_entities])
        if message.caption_entities else None
    }
    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                               json=data) as response:
            respns = await response.json()
    await state.reset_state()

    await edit_scheduled_post_message(message, state, post_id, action)


async def url_buttons(call: CallbackQuery, callback_data: dict, state: FSMContext):
    post_id = int(callback_data.get("post_id"))
    _ = call.bot.get("lang")
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }) as response:
            response1 = await response.json()

    media = response1.get("data").get("media")

    if media is not None:
        if len(media) > 1:
            text = _("❌ Url кнопки для данного поста не поддерживаются")
            await call.answer(text=text, show_alert=True)
            return

    await call.answer()
    await call.bot.delete_message(call.from_user.id, call.message.message_id)
    action = callback_data.get("action")
    await delete_messages(call, post_id)

    text = _('⛓ <b>URL-КНОПКИ</b>\n\n' \
             'Отправьте боту список URL-кнопок в следующем формате:\n\n' \
             '<code>Название кнопки 1 - <b>http://link.com</b></code>\n' \
             '<code>Название кнопки 2 - <b>http://link.com</b></code>\n\n' \
             'Используйте разделитель \'|\', чтобы добавить до 8 кнопок в один ряд (допустимо 15 рядов):\n\n' \
             '<code>Название кнопки 1 - <b>http://link.com</b> | Название кнопки 2 - <b>http://link.com</b></code>')
    Back = _("⬅️ Назад")
    markup = InlineKeyboardMarkup(row_width=1)
    markup.row(InlineKeyboardButton(text=Back, callback_data=choose_prompts_content.new(action="back", index=999,
                                                                                        post_id=post_id)))
    msg = await call.bot.send_message(call.from_user.id, text, reply_markup=markup)
    await Content.Get_URL.set()
    await state.update_data(msg=msg.message_id)
    await state.update_data(post_id=post_id)
    await state.update_data(action=action)


# Create.Get_URL
async def url_buttons_add(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg = data.get("msg")
    action = data.get("action")
    post_id = int(data.get("post_id"))
    await message.bot.delete_message(message.from_user.id, msg)

    data = {"id": post_id,
            "url_buttons": []}
    buttons_text = message.text.split('\n')

    for row in buttons_text:
        data["url_buttons"].append(row)

    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                               json=data) as response:
            respns = await response.json()
    await state.reset_state()
    await edit_scheduled_post_message(message, state, post_id, action)


async def auto_sign_change(call: CallbackQuery, callback_data: dict, state: FSMContext):
    post_id = int(callback_data.get("post_id"))
    _ = call.bot.get("lang")

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }) as response:
            response1 = await response.json()

    media = response1.get("data").get("media")

    if media is not None:
        if len(media) == 1 and media[0]["media_type"] == "video_note":
            text = _("❌ Автоподпись для данного поста не поддерживается")
            await call.answer(text=text, show_alert=True)
            return

    await call.answer()
    response1 = await delete_messages(call, post_id)

    id_channel = int(response1.get("data").get("channel_id"))
    data = {"user_id": call.from_user.id,
            "channel_id": id_channel}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel/one/",
                                json=data) as response:
            response2 = await response.json()
    user_channel_settings_id = int(response2.get("data").get("user_channel_settings_id"))

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel_settings/one/key_value/",
                params={
                    "key": "id",
                    "value": user_channel_settings_id
                }
        ) as response:
            response3 = await response.json()
    auto_sign = response3.get("data").get("auto_sign")

    if not auto_sign:
        new_auto_sign = True
    else:
        new_auto_sign = False

    data = {"id": user_channel_settings_id,
            "auto_sign": new_auto_sign}
    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel_settings/",
                               json=data) as response:
            unused_response = await response.json()

    await edit_scheduled_post(call, callback_data, state)


async def gpt_choice(call: CallbackQuery, callback_data: dict, state: FSMContext):
    post_id = int(callback_data.get("post_id"))
    _ = call.bot.get("lang")

    markup = InlineKeyboardMarkup(row_width=1)
    text = _("<b>⛓ CHAT GPT</b>\n\n" \
             "Выберите промпт.")

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }) as response:
            response1 = await response.json()

    media_data = response1.get("data").get("media")

    if media_data is not None:
        if len(media_data) == 1 and media_data[0]['media_type'] == "video_note":
            text = _("❌ Chat GPT для данного поста не поддерживается")
            await call.answer(text=text, show_alert=True)
            return

    await call.answer()

    id_channel = int(response1.get("data").get("channel_id"))

    data = {"user_id": call.from_user.id,
            "channel_id": id_channel}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel/one/",
                                json=data) as response:
            response1 = await response.json()
    user_channel_settings_id = int(response1.get("data").get("user_channel_settings_id"))

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel_settings/one/key_value/",
                params={
                    "key": "id",
                    "value": user_channel_settings_id
                }) as response:
            response2 = await response.json()
            gpt_prompts = response2.get("data").get("prompts")

    for prompt in gpt_prompts:
        for key in prompt.keys():
            markup.insert(InlineKeyboardButton(text=f"{key}", callback_data=choose_prompts_content.new(action="edit",
                                                                                                       index=gpt_prompts.index(
                                                                                                           prompt),
                                                                                                       post_id=post_id)))
    # markup.add(InlineKeyboardButton(text=f"Добавить",
    #                                 callback_data=create_post_prompt.new(channel_id=id_channel,
    #                                                                      post_id=post_id,
    #                                                                      action="add_prompt")))
    Back = _("⬅️ Назад")
    markup.add(InlineKeyboardButton(text=Back,
                                    callback_data=choose_prompts_content.new(action="back", index=999,
                                                                             post_id=post_id)))

    await call.bot.edit_message_text(text=text, chat_id=call.from_user.id, message_id=call.message.message_id,
                                     reply_markup=markup)

    # if gpt_prompts is not None:
    #     await call.bot.delete_message(call.from_user.id, call.message.message_id)
    #     for prompt in gpt_prompts:
    #         for key in prompt.keys():
    #             markup.insert(
    #                 InlineKeyboardButton(text=f"{key}", callback_data=choose_prompts_content.new(action="edit",
    #                                                                                              index=gpt_prompts.index(
    #                                                                                                  prompt),
    #                                                                                              post_id=post_id)))
    #     markup.add(InlineKeyboardButton(text=f"⬅️ Назад",
    #                                     callback_data=choose_prompts_content.new(action="back", index=999,
    #                                                                              post_id=post_id)))
    #     await call.bot.send_message(call.from_user.id, text, reply_markup=markup)
    # else:
    #     text = "Вы еще не добавили промпты для Сhat GPT"
    #     await call.bot.send_message(call.from_user.id, text)
    #     await edit_scheduled_post(call, callback_data, state)


async def prompt_choice(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()
    _ = call.bot.get("lang")
    index = int(callback_data.get("index"))
    post_id = int(callback_data.get("post_id"))

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }
        ) as response:
            response1 = await response.json()
    caption = response1.get("data").get("description")
    id_channel = int(response1.get("data").get("channel_id"))

    data = {"user_id": call.from_user.id,
            "channel_id": id_channel}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel/one/",
                                json=data) as response:
            response2 = await response.json()
    user_channel_settings_id = int(response2.get("data").get("user_channel_settings_id"))

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel_settings/one/key_value/",
                params={
                    "key": "id",
                    "value": user_channel_settings_id
                }) as response:
            response3 = await response.json()
            gpt_prompts = response3.get("data").get("prompts")
            subscription_id = response3.get("data").get("subscription_id")

    datetime_utc = datetime.utcnow()
    requested_date = datetime_utc.isoformat()

    if subscription_id == 2:
        user_ai_data = {"user_id": call.from_user.id,
                        "requested_date": requested_date}
        api_key = None

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_open_ai/one/",
                    json=user_ai_data) as response:
                respons = await response.json()

        if respons['status'] == "error":
            if respons['details'] == "Record doesnt exists":
                add_data = {
                    "user_id": call.from_user.id,
                    "requested_date": requested_date,
                    "open_ai_id": 1,
                    "requested_count": 1
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                            url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_open_ai/",
                            json=add_data) as response:
                        add_response = await response.json()

            elif respons['details'] == "Limit exceeded":
                text = _("Превышен лимит запросов Сhat GPT в минуту, попробуйте немного позже")
                await call.bot.send_message(call.from_user.id, text)
                await edit_scheduled_post(call, callback_data, state)
                return

    else:
        user_response: Response[UserSchema] = Response[UserSchema].model_validate(
            await user_api.get_one_by_key_value(params={
                "key": "id",
                "value": call.from_user.id
            })
        )

        if user_response.data.gpt_api_key is not None:
            api_key = user_response.data.gpt_api_key
        else:
            text = _("Привяжите аккаунт Chat GPT в настройках канала, либо оплатите подписку")
            await call.bot.send_message(call.from_user.id, text)
            await edit_scheduled_post(call, callback_data, state)
            return

    data = {"content": f"{list(gpt_prompts[index].values())[0]}\n\n{caption}", "api_key": api_key}

    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_chat_gpt}:{config.api.api_chat_gpt_port}/prompt/",
                                json=data) as response:
            respns = await response.json()

    if respns.get("status") == "success":

        data = {
            "id": post_id,
            "description": respns.get("data")}
        async with aiohttp.ClientSession() as session:
            async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                   json=data) as response:
                respns = await response.json()
        await edit_scheduled_post(call, callback_data, state)
    else:
        text = _("Преобразование текста не выполнилось")
        await call.bot.send_message(call.from_user.id, text)
        await edit_scheduled_post(call, callback_data, state)


async def previous_saved(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()
    post_id = int(callback_data.get("post_id"))
    await delete_messages(call, post_id)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/{post_id}/") as response:
                respns = await response.json()
        initial_post_id = int(respns.get("data").get("initial_post_id"))
        del callback_data['post_id']

        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                    params={
                        "key": "id",
                        "value": initial_post_id
                    }
            ) as response:
                respns = await response.json()
        post_id = int(respns.get("data").get("id"))
        callback_data.update({'post_id': post_id})
    except:
        pass

    await post_handler(call, callback_data, state)


async def save(call: CallbackQuery, callback_data: dict, state: FSMContext):
    post_id = int(callback_data.get("post_id"))
    _ = call.bot.get("lang")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                    params={
                        "key": "id",
                        "value": post_id
                    }
            ) as response:
                response1 = await response.json()

        id_channel = response1.get("data").get("channel_id")
        initial_post_id = response1.get("data").get("initial_post_id")

        while initial_post_id is not None:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                        params={
                            "key": "id",
                            "value": initial_post_id
                        }
                ) as response:
                    response1 = await response.json()
            initial_post_id = response1.get("data").get("initial_post_id")
            post_id_to_delete = response1.get("data").get("id")

        data = {"post_id": post_id_to_delete}
        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/one/",
                                    json=data) as response:
                response2 = await response.json()
        message_id = response2.get("data").get("id")

        data = {"id": message_id, "post_id": post_id}
        async with aiohttp.ClientSession() as session:
            async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/",
                                   json=data) as response:
                response3 = await response.json()
        messages_id = response3.get("data").get("message")

        async with aiohttp.ClientSession() as session:
            async with session.delete(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/{post_id_to_delete}/") as response:
                unused_response = await response.json()

        data = {"id": post_id, "is_saved": True, "is_scheduled": True, "initial_post_id": None}
        async with aiohttp.ClientSession() as session:
            async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                   json=data) as response:
                response4 = await response.json()

        media_data = response4.get("data").get("media")
        buttons = response4.get("data").get("url_buttons")
        caption = response4.get("data").get("description")
        chat_id = response4.get("data").get("channel_id")
        entities = response1.get("data").get("entities")
        entities = [types.MessageEntity(**entity) for entity in
                    json.loads(entities)] if entities else None

        markup = InlineKeyboardMarkup(row_width=2)
        if buttons is not None:
            inline_keyboard = []
            for row in buttons:
                elements = row.split(' | ')
                row_buttons = []
                for element in elements:
                    title, url = element.split(' - ')
                    row_buttons.append(InlineKeyboardButton(text=title, url=url))
                inline_keyboard.append(row_buttons)

            markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

        data = {"user_id": call.from_user.id,
                "channel_id": id_channel}
        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel/one/",
                                    json=data) as response:
                response5 = await response.json()
        user_channel_settings_id = response5.get("data").get("user_channel_settings_id")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel_settings/one/key_value/",
                    params={
                        "key": "id",
                        "value": user_channel_settings_id
                    }
            ) as response:
                response6 = await response.json()
        auto_sign = response6.get("data").get("auto_sign")
        auto_sign_entities = response6.get('data').get('auto_sign_entities')
        auto_sign_entities = [types.MessageEntity(**entity) for entity in
                              json.loads(auto_sign_entities)] if auto_sign_entities else None

        combined_entities = copy.deepcopy(entities)

        if caption is not None:
            auto_sign_text = response6.get("data").get("auto_sign_text")
            if str(auto_sign) == "True":
                if auto_sign_text is not None:
                    caption += f"\n\n{auto_sign_text}"

                    text_length = count_characters(caption)
                    auto_sign_len = count_characters(auto_sign_text)  # +2 для переноса строки между сообщениями

                    updated_signature_entities = [
                        types.MessageEntity(
                            type=entity.type,
                            offset=text_length - auto_sign_len,
                            length=entity.length,
                            url=entity.url,
                            user=entity.user,
                            language=entity.language
                        ) for entity in auto_sign_entities
                    ] if auto_sign_entities else None

                    # Объединение стилей основного сообщения и автоподписи
                    if entities is not None and updated_signature_entities is not None:
                        combined_entities += updated_signature_entities
                    elif entities is None and updated_signature_entities:
                        combined_entities = updated_signature_entities
        else:
            auto_sign_text = response6.get("data").get("auto_sign_text")
            if str(auto_sign) == "True":
                if auto_sign_text is not None:
                    caption = f"\n\n{auto_sign_text}"

                text_length = count_characters(caption)
                auto_sign_len = count_characters(auto_sign_text)  # +2 для переноса строки между сообщениями
                updated_signature_entities = [
                    types.MessageEntity(
                        type=entity.type,
                        offset=text_length - auto_sign_len,
                        length=entity.length,
                        url=entity.url,
                        user=entity.user,
                        language=entity.language
                    ) for entity in auto_sign_entities
                ] if auto_sign_entities else None

                # Объединение стилей основного сообщения и автоподписи
                if entities is not None and updated_signature_entities is not None:
                    combined_entities += updated_signature_entities
                elif entities is None and updated_signature_entities:
                    combined_entities = updated_signature_entities
            else:
                caption = None

        # if messages_id.get("media"):
        #     await call.bot.edit_message_text(caption, chat_id, int(messages_id.get("message")), entities=combined_entities,
        #                                      reply_markup=markup)
        # else:
        if media_data is not None:
            if len(media_data) > 1:
                try:
                    await call.bot.edit_message_caption(chat_id=chat_id,
                                                        message_id=int(messages_id.get("message")[0]),
                                                        caption_entities=combined_entities,
                                                        caption=caption)
                except Exception as e:
                    logging.error(f"len(media_data) {e}")
            else:
                media_id = media_data[0]

                if media_id.get("media_type") == "photo":
                    media = InputMediaPhoto(media_id.get("file_id"), caption=caption,
                                            caption_entities=combined_entities)

                elif media_id.get("media_type") == "video":
                    media = InputMediaVideo(media_id.get("file_id"), caption=caption,
                                            caption_entities=combined_entities)

                elif media_id.get("media_type") == "document":
                    media = InputMediaDocument(media_id.get("file_id"), caption=caption,
                                               caption_entities=combined_entities)

                elif media_id.get("media_type") == "audio":
                    media = InputMediaAudio(media_id.get("file_id"), caption=caption,
                                            caption_entities=combined_entities)

                elif media_id.get("media_type") == "animation":
                    media = InputMediaAnimation(media_id.get("file_id"), caption=caption,
                                                caption_entities=combined_entities)

                try:
                    if media_id.get("media_type") in ["photo", "video", "document", "audio", "animation"]:
                        await call.bot.edit_message_media(media, chat_id, int(messages_id.get("message")),
                                                          reply_markup=markup)

                    elif media_id.get("media_type") == "video_note":
                        await call.bot.edit_message_reply_markup(chat_id=chat_id,
                                                                 message_id=int(messages_id.get("message")),
                                                                 reply_markup=markup)
                except Exception as e:
                    logging.error(f"media_id {e}")
        else:
            await call.bot.edit_message_text(caption, chat_id, int(messages_id.get("message")),
                                             entities=combined_entities,
                                             reply_markup=markup)

    except Exception as e:
        logging.error(str(e))
    text = _("✅ Пост изменен")
    await call.answer(text=text, show_alert=True)
    await post_handler(call, callback_data, state)


async def auto_delete_timer_content_plan(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    post_id = int(callback_data.get("post_id"))
    id_channel = int(callback_data.get("channel_id"))
    await delete_messages(call, post_id)

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }) as response:
            respns = await response.json()

    try:
        auto_del_timer = int(respns.get("data").get("auto_delete_timer"))
    except:
        auto_del_timer = None

    text = _(
        "🗑 <b>ТАЙМЕР УДАЛЕНИЯ</b>\n\nВы можете установить через какое время после выхода поста, он будет удалён.\n\n" \
        "Отправьте боту время, через которое нужно удалить пост либо выберите один из предложенных вариантов.")
    list_seconds = [0, 300, 900, 1800, 3600, 7200, 14400, 28800, 43200, 64800, 86400, 172800, 259200, 432000, 604800,
                    864000]

    buttons = []
    markup = InlineKeyboardMarkup(row_width=4)

    for second in list_seconds:
        if auto_del_timer is not None and auto_del_timer == second:
            exist_del_timer = "✅ "
        else:
            exist_del_timer = ""

        if second == 0:
            buttons.append(InlineKeyboardButton(text=f"{exist_del_timer}Нет",
                                                callback_data=choose_seconds_content_plan.new(seconds=second,
                                                                                              channel_id=id_channel,
                                                                                              post_id=post_id)))
        elif second < 3600:
            minutes = second // 60
            buttons.append(InlineKeyboardButton(text=f"{exist_del_timer}{minutes} мин",
                                                callback_data=choose_seconds_content_plan.new(seconds=second,
                                                                                              channel_id=id_channel,
                                                                                              post_id=post_id)))
        elif second < 86400:
            hours = second // 3600
            buttons.append(InlineKeyboardButton(text=f"{exist_del_timer}{hours}ч",
                                                callback_data=choose_seconds_content_plan.new(seconds=second,
                                                                                              channel_id=id_channel,
                                                                                              post_id=post_id)))
        else:
            days = second // 86400
            buttons.append(InlineKeyboardButton(text=f"{exist_del_timer}{days}д",
                                                callback_data=choose_seconds_content_plan.new(seconds=second,
                                                                                              channel_id=id_channel,
                                                                                              post_id=post_id)))

        if len(buttons) >= 4:
            markup.row(*buttons)
            buttons.clear()
    choose_btn = _("Выбрать")
    markup.row(InlineKeyboardButton(text=choose_btn,
                                    callback_data=further_content_plan.new(channel_id=id_channel, post_id=post_id)))

    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def choose_seconds(call: CallbackQuery, callback_data: dict):
    await call.answer()
    post_id = int(callback_data.get("post_id"))
    await delete_messages(call, post_id)
    seconds_data = int(callback_data.get("seconds"))

    data = {"id": post_id,
            "auto_delete_timer": seconds_data}
    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                               json=data) as response:
            respns = await response.json()

    await auto_delete_timer_content_plan(call, callback_data)


async def further_content_plan_choose(call: CallbackQuery, callback_data: dict, state: FSMContext):
    post_id = int(callback_data['post_id'])
    channel_id = int(callback_data['channel_id'])

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }) as response:
            respns = await response.json()

    auto_delete_timer = respns.get("data").get("auto_delete_timer")

    data = {"post_id": post_id}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/one/",
                                json=data) as response:
            message_response = await response.json()

    message_id = message_response.get("data").get("id")

    if auto_delete_timer and int(auto_delete_timer) != 0:
        utc_time_iso = respns.get("data").get("date")
        utc_time = datetime.fromisoformat(utc_time_iso).replace(tzinfo=pytz.utc)
        new_run_time = utc_time + timedelta(seconds=auto_delete_timer)

        auto_delete_timer_job_id = message_response['data']['auto_delete_timer_job_id']
        if auto_delete_timer_job_id is not None:
            scheduler.remove_job(auto_delete_timer_job_id)

        job = scheduler.add_job(auto_delete_timer_job, 'date', run_date=new_run_time,
                                args=[message_id, channel_id])

        data = {"id": message_id, "auto_delete_timer_job_id": job.id}
        async with aiohttp.ClientSession() as session:
            async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/",
                                   json=data) as response:
                message_response = await response.json()

    await post_handler(call=call, callback_data=callback_data, state=state)


def register_content_plan(dp: Dispatcher):
    # dp.register_message_handler(content_handler, text="Контент-план", state=[CreatePost, Content, Create, Settings, Parsing])
    dp.register_message_handler(content_handler, text="Контент-план", state="*")
    dp.register_message_handler(content_handler, text="Контент-план")

    dp.register_callback_query_handler(back_to_content, cancel_content.filter())
    dp.register_callback_query_handler(back_to_content, cancel_content.filter(), state=Content)

    dp.register_callback_query_handler(scheduled_channel_posts, content_clb.filter(action="content"))
    dp.register_callback_query_handler(scheduled_channel_posts, calendar_content.filter())
    dp.register_callback_query_handler(back_to_scheduled_channel_posts, content_clb.filter())

    dp.register_callback_query_handler(post_handler, post_callback.filter(action="next"))
    dp.register_callback_query_handler(post_handler, post_callback.filter(action="back_not_scheduled"))
    dp.register_callback_query_handler(post_handler, redaction_clb.filter(action="edit"))
    dp.register_callback_query_handler(post_handler, post_callback.filter(action="back_to_post_handler"))

    dp.register_callback_query_handler(delete_post, post_callback.filter(action="delete"))
    dp.register_callback_query_handler(delete_post_confirm, post_callback.filter(action="delete_confirm"))
    dp.register_callback_query_handler(delete_from_content_plan, post_callback.filter(action="delete_from_content"))
    dp.register_callback_query_handler(delete_from_content_plan_confirm,
                                       post_callback.filter(action="delete_from_content_confirm"))

    dp.register_callback_query_handler(duplicate, post_callback.filter(action="duplicate"))

    dp.register_callback_query_handler(edit_scheduled_post, post_callback.filter(action="edit"))
    dp.register_callback_query_handler(edit_scheduled_post, post_callback.filter(action="edit_not_scheduled"))
    dp.register_callback_query_handler(edit_scheduled_post, post_callback.filter(action="back_to_edit"),
                                       state=Content.Edit_Media)

    dp.register_callback_query_handler(descripion, add_descrip_content.filter())
    dp.register_message_handler(descripion_add, state=Content.Get_Description)

    dp.register_callback_query_handler(url_buttons, url_buttons_clb_content.filter())
    dp.register_message_handler(url_buttons_add, state=Content.Get_URL)

    dp.register_callback_query_handler(auto_sign_change, auto_sign_clb_content.filter())

    dp.register_callback_query_handler(gpt_choice, gpt_clb_content.filter())
    dp.register_callback_query_handler(prompt_choice, choose_prompts_content.filter(action="edit"))

    dp.register_callback_query_handler(edit_scheduled_post, choose_prompts_content.filter(action="back"), state="*")

    dp.register_callback_query_handler(previous_saved, post_callback.filter(action="back"))
    dp.register_callback_query_handler(save, post_callback.filter(action="save"))

    dp.register_callback_query_handler(auto_delete_timer_content_plan,
                                       sending_clbk_content_plan.filter(action="auto_delete"))
    dp.register_callback_query_handler(choose_seconds, choose_seconds_content_plan.filter())
    dp.register_callback_query_handler(further_content_plan_choose, further_content_plan.filter())
