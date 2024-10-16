import asyncio
import copy
import json
import logging
import math
from calendar import monthrange, weekday
from datetime import timezone, datetime, timedelta

import pytz
from babel.dates import format_date

from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import aiohttp

from tg_bot import config, scheduler, subscription_api
from tg_bot.aiogram_bot.handlers.task.task import auto_delete_timer_job

from tg_bot.aiogram_bot.handlers.users.create.create_post import delete_messages
from tg_bot.aiogram_bot.keyboards.inline.content_inline.content import post_callback
from tg_bot.aiogram_bot.keyboards.inline.create_inline.calendar_create import further, calendar_clbk, choose_time, \
    hour_clbk, \
    minute_clbk, \
    sending_clbk, choose_seconds
from tg_bot.aiogram_bot.network.dto.response import Response
from tg_bot.aiogram_bot.network.dto.subscription import SubscriptionSchema
from tg_bot.aiogram_bot.utils.utils import count_characters


async def sending(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    post_id = int(callback_data.get("post_id"))
    await delete_messages(call, post_id)
    id_channel = int(callback_data.get("channel_id"))

    data = {"id": id_channel}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel/one/",
                                json=data) as response:
            respns = await response.json()
    title = respns.get("data").get("title")
    link = respns.get("data").get("link")
    url = f"<a href='{link}'>{title}</a>"

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }
        ) as response:
            respns = await response.json()

    text = _("💼 <b>НАСТРОЙКИ ОТПРАВКИ</b>\n\n"
             "Пост готов к публикации в канале {}\n\n"
             "Настройте его перед отправкой.").format(url)
    try:
        auto_del_timer = int(respns.get("data").get("auto_delete_timer"))

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

    markup = types.InlineKeyboardMarkup(row_width=2)
    delete_timer_btn_text = _("Таймер автоудаления: {}").format(exist_del_timer)
    delayed_text = _("🕔 Отложить")
    publish_btn_text = _("🚀 Опубликовать")
    back_btn_text = _("⬅️ Назад")
    markup.row(InlineKeyboardButton(text=delete_timer_btn_text,
                                    callback_data=sending_clbk.new(action="auto_delete", channel_id=id_channel,
                                                                   post_id=post_id)))
    markup.row(InlineKeyboardButton(text=delayed_text,
                                    callback_data=sending_clbk.new(action="postpone", channel_id=id_channel,
                                                                   post_id=post_id)),
               InlineKeyboardButton(text=publish_btn_text,
                                    callback_data=sending_clbk.new(action="publish", channel_id=id_channel,
                                                                   post_id=post_id)))
    markup.row(
        InlineKeyboardButton(text=back_btn_text,
                             callback_data=sending_clbk.new(action="back", channel_id=id_channel, post_id=post_id)))

    try:
        await call.bot.edit_message_text(text=text, chat_id=call.from_user.id, message_id=call.message.message_id,
                                         reply_markup=markup)
    except Exception as e:
        logging.error(f"sending {e}")
        await call.bot.send_message(call.from_user.id, text, reply_markup=markup)


async def main_calendar(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    post_id = int(callback_data.get("post_id"))
    await delete_messages(call, post_id)

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }
        ) as response:
            respns = await response.json()
    markup = types.InlineKeyboardMarkup(row_width=2)
    id_channel = int(respns.get("data").get("channel_id"))

    try:
        utc_time_iso = respns.get("data").get("date")
        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)
        date_hour = int(user_input_time.hour)
        date_minute = int(user_input_time.minute)

        text_day = _("🗓 Показать календарь")

        if date_hour == 0:
            text_hour = _("Выберите час ↘️")
        else:
            text_hour = _("Часы: {} ↘️").format(date_hour)
        if date_minute == 0:
            text_minute = _("Выберите минуту ↘️")
        else:
            text_minute = ("Минуты: {} ↘️").format(date_minute)
    except:
        text_day = _("🗓 Показать календарь")
        text_hour = _("Выберите час ↘️")
        text_minute = _("Выберите минуту ↘️")

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/{call.from_user.id}/") as response:
            respoonse = await response.json()
    try:
        utc_time_iso = respns.get("data").get("date")
        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)
        year = int(user_input_time.year)
        month = int(user_input_time.month)
        day = int(user_input_time.day)
        action = "hide_calendar"
        calendar = await generate_calendar(_, markup, post_id, action, year, month, day)
    except:
        markup.row(
            InlineKeyboardButton(text=text_day, callback_data=choose_time.new(action="show_calendar", post_id=post_id)))
        user_timezone = int(respoonse.get("data").get("time_zone"))
        current_date = datetime.utcnow() + timedelta(hours=user_timezone)
        today = datetime(current_date.year, current_date.month, current_date.day)
        buttons = []
        tomorrow1 = today + timedelta(days=1)
        tomorrow2 = today + timedelta(days=2)
        days = [today, tomorrow1, tomorrow2]
        for dayt in days:
            if dayt == today:
                button_text = f"✅ {format_date(today, format='EEE, dd MMM', locale='ru')}"
                buttons.append(InlineKeyboardButton(text=button_text,
                                                    callback_data=calendar_clbk.new(action="date", year=str(today.year),
                                                                                    month=str(today.month),
                                                                                    day=today.day,
                                                                                    post_id=post_id)))
            elif dayt == tomorrow1:
                button_text = f"{format_date(tomorrow1, format='EEE, dd MMM', locale='ru')}"
                buttons.append(InlineKeyboardButton(text=button_text,
                                                    callback_data=calendar_clbk.new(action="date",
                                                                                    year=str(tomorrow1.year),
                                                                                    month=str(tomorrow1.month),
                                                                                    day=tomorrow1.day,
                                                                                    post_id=post_id)))
            elif dayt == tomorrow2:
                button_text = f"{format_date(tomorrow2, format='EEE, dd MMM', locale='ru')} →"
                buttons.append(InlineKeyboardButton(text=button_text,
                                                    callback_data=calendar_clbk.new(action="date",
                                                                                    year=str(tomorrow2.year),
                                                                                    month=str(tomorrow2.month),
                                                                                    day=tomorrow2.day,
                                                                                    post_id=post_id)))
            else:
                pass
        markup.row(*buttons)

    Back = _("⬅️ Назад")
    markup.row(InlineKeyboardButton(text=text_hour, callback_data=choose_time.new(action="hour", post_id=post_id)))
    markup.row(InlineKeyboardButton(text=text_minute, callback_data=choose_time.new(action="minute", post_id=post_id)))
    markup.row(InlineKeyboardButton(text=Back, callback_data=further.new(channel_id=id_channel, post_id=post_id)))

    try:
        utc_time_iso = respns.get("data").get("date")
        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)
        dayz = int(user_input_time.day)

        if dayz != 0:
            Next = _("➡️ Далее")
            markup.insert(
                InlineKeyboardButton(text=Next, callback_data=choose_time.new(action="next", post_id=post_id)))
    except:
        pass

    text = _("⏳ ОТЛОЖИТЬ\n\nВыберете время в меню")
    try:
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
    except Exception as e:
        logging.error(f"main_calendar {e}")
        await call.bot.send_message(call.from_user.id, text, reply_markup=markup)


async def show_calendar(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    post_id = int(callback_data.get("post_id"))
    await delete_messages(call, post_id)
    action = callback_data.get("action")
    markup = types.InlineKeyboardMarkup(row_width=7)

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }
        ) as response:
            respns = await response.json()
    id_channel = int(respns.get("data").get("channel_id"))
    try:
        utc_time_iso = respns.get("data").get("date")
        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)
        year = int(user_input_time.year)
        month = int(user_input_time.month)
        day = int(user_input_time.day)

        dayz = int(user_input_time.day)
    except:
        dayz = 0
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/{call.from_user.id}/") as response:
                respoonse = await response.json()
        user_timezone = int(respoonse.get("data").get("time_zone"))
        current_date = datetime.utcnow() + timedelta(hours=user_timezone)
        year, month, day = current_date.year, current_date.month, current_date.day
        user_input_time = (year, month, day, 00, 00, 00)
        utc_time = await convert_to_utc(call.from_user.id, *user_input_time)

        data = {"id": post_id,
                "date": utc_time.replace(tzinfo=None).isoformat()}
        async with aiohttp.ClientSession() as session:
            async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                   json=data) as response:
                respns = await response.json()

    calendar = await generate_calendar(_, markup, post_id, action, year, month, day)
    hour_keyboard = await generate_hour_keyboard(_, markup, post_id, action)
    minute_keyboard = await generate_minute_keyboard(_, markup, post_id, action)
    Back = _("⬅️ Назад")
    markup.row(InlineKeyboardButton(text=Back, callback_data=further.new(channel_id=id_channel, post_id=post_id)))

    if dayz != 0:
        Next = _("➡️ Далее")
        markup.insert(InlineKeyboardButton(text=Next, callback_data=choose_time.new(action="next", post_id=post_id)))
    else:
        pass

    text = _("⏳ ОТЛОЖИТЬ\n\nВыберете время в меню")
    try:
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
    except Exception as e:
        logging.error(f"show_calendar {e}")
        await call.bot.send_message(call.from_user.id, text, reply_markup=markup)


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


async def generate_calendar(_, markup, post_id, action, year, month, day):
    hide_calendar_button = _("🗓 Скрыть календарь")
    previous_month_button = _("◀️ Предыдущий")
    next_month_button = _("Следующий ▶️")
    show_calendar_button = _("🗓 Показать календарь")


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

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }
        ) as response:
            respns = await response.json()
    user_id = int(respns.get("data").get("user_id"))
    try:
        utc_time_iso = respns.get("data").get("date")
        user_input_time = await convert_to_user_time(user_id, utc_time_iso)
        yearz = int(user_input_time.year)
        monthz = int(user_input_time.month)
        dayz = int(user_input_time.day)
    except:
        yearz, monthz, dayz = 0, 0, 0

    if action == "show_calendar":
        month_name = month_names.get(month)
        markup.row(
            InlineKeyboardButton(text=hide_calendar_button,
                                 callback_data=choose_time.new(action="hide_calendar", post_id=post_id)))
        markup.row(
            InlineKeyboardButton(text=previous_month_button,
                                 callback_data=calendar_clbk.new(action="previous", year=str(year), month=str(month),
                                                                 day="1", post_id=post_id)),
            InlineKeyboardButton(text=f'{month_name} {year}',
                                 callback_data=calendar_clbk.new(action="empty", year=0, month=0, day=0,
                                                                 post_id=post_id)),
            InlineKeyboardButton(text=next_month_button,
                                 callback_data=calendar_clbk.new(action="next", year=str(year), month=str(month),
                                                                 day="1", post_id=post_id))
        )

        markup.add(*[types.InlineKeyboardButton(text=day,
                                                callback_data=calendar_clbk.new(action="empty",
                                                                                year=0, month=0, day=0,
                                                                                post_id=post_id)) for day in
                     ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]])

        for _ in range(int(full_weeks)):
            week = []
            for i in range(7):
                if days_count < offset or days_count >= days_in_month + offset:
                    week.append(InlineKeyboardButton(
                        text=" ",
                        callback_data=calendar_clbk.new(action="empty", year=0, month=0, day=0, post_id=post_id)
                    ))
                else:
                    day_clb = days_count - offset + 1
                    if int(yearz) == int(year) and int(monthz) == int(month) and int(dayz) == int(day_clb):
                        day_txt = f"✅ {day_clb}"

                    else:
                        day_txt = day_clb
                    week.append(InlineKeyboardButton(
                        text=day_txt,
                        callback_data=calendar_clbk.new(action="date", year=str(year), month=str(month),
                                                        day=str(day_clb), post_id=post_id)
                    ))
                days_count += 1
            month_calendar.append(week)

        for week in month_calendar:
            markup.add(*week)
    else:
        markup.row(InlineKeyboardButton(text=show_calendar_button,
                                        callback_data=choose_time.new(action="show_calendar", post_id=post_id)))

        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/{user_id}/") as response:
                respoonse = await response.json()
        user_timezone = int(respoonse.get("data").get("time_zone"))
        current_date = datetime.utcnow() + timedelta(hours=user_timezone)
        today = datetime(current_date.year, current_date.month, current_date.day)

        variable_day = datetime(year, month, day)

        buttons = []
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        if variable_day == today or variable_day <= yesterday:
            tomorrow1 = today + timedelta(days=1)
            tomorrow2 = today + timedelta(days=2)
            days = [variable_day, tomorrow1, tomorrow2]
            for dayt in days:
                if dayt == variable_day:
                    button_text = f"✅ {format_date(today, format='EEE, dd MMM', locale='ru')}"
                    buttons.append(InlineKeyboardButton(text=button_text,
                                                        callback_data=calendar_clbk.new(action="date",
                                                                                        year=str(variable_day.year),
                                                                                        month=str(variable_day.month),
                                                                                        day=today.day,
                                                                                        post_id=post_id)))
                elif dayt == tomorrow1:
                    button_text = f"{format_date(tomorrow1, format='EEE, dd MMM', locale='ru')}"
                    buttons.append(InlineKeyboardButton(text=button_text,
                                                        callback_data=calendar_clbk.new(action="date",
                                                                                        year=str(tomorrow1.year),
                                                                                        month=str(tomorrow1.month),
                                                                                        day=tomorrow1.day,
                                                                                        post_id=post_id)))
                elif dayt == tomorrow2:
                    button_text = f"{format_date(tomorrow2, format='EEE, dd MMM', locale='ru')} →"
                    buttons.append(InlineKeyboardButton(text=button_text,
                                                        callback_data=calendar_clbk.new(action="date",
                                                                                        year=str(tomorrow2.year),
                                                                                        month=str(tomorrow2.month),
                                                                                        day=tomorrow2.day,
                                                                                        post_id=post_id)))
                else:
                    pass

        if variable_day >= tomorrow:
            tomorrow1 = variable_day - timedelta(days=1)
            tomorrow2 = variable_day + timedelta(days=1)
            days = [tomorrow1, variable_day, tomorrow2]

            for dayt in days:
                if dayt == variable_day:
                    button_text = f"✅ {format_date(variable_day, format='EEE, dd MMM', locale='ru')}"
                    buttons.append(InlineKeyboardButton(text=button_text,
                                                        callback_data=calendar_clbk.new(action="date",
                                                                                        year=str(variable_day.year),
                                                                                        month=str(variable_day.month),
                                                                                        day=variable_day.day,
                                                                                        post_id=post_id)))
                elif dayt == tomorrow1:
                    button_text = f"← {format_date(tomorrow1, format='EEE, dd MMM', locale='ru')}"
                    buttons.append(InlineKeyboardButton(text=button_text,
                                                        callback_data=calendar_clbk.new(action="date",
                                                                                        year=str(tomorrow1.year),
                                                                                        month=str(tomorrow1.month),
                                                                                        day=tomorrow1.day,
                                                                                        post_id=post_id)))
                elif dayt == tomorrow2:
                    button_text = f"{format_date(tomorrow2, format='EEE, dd MMM', locale='ru')} →"
                    buttons.append(InlineKeyboardButton(text=button_text,
                                                        callback_data=calendar_clbk.new(action="date",
                                                                                        year=str(tomorrow2.year),
                                                                                        month=str(tomorrow2.month),
                                                                                        day=tomorrow2.day,
                                                                                        post_id=post_id)))
                else:
                    pass
        markup.row(*buttons)
    return markup


async def previous_month(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    post_id = int(callback_data.get("post_id"))
    await delete_messages(call, post_id)
    year = int(callback_data["year"])
    month = int(callback_data["month"])
    day = int(callback_data["day"])

    action = "show_calendar"
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }
        ) as response:
            respns = await response.json()
    id_channel = int(respns.get("data").get("channel_id"))

    if month == 1:
        year -= 1
        month = 12
    else:
        month -= 1

    markup = types.InlineKeyboardMarkup(row_width=7)
    new_calendar = await generate_calendar(_, markup, post_id, action, year, month, day)
    hour_keyboard = await generate_hour_keyboard(_, markup, post_id, action)
    minute_keyboard = await generate_minute_keyboard(_, markup, post_id, action)
    markup.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=further.new(channel_id=id_channel, post_id=post_id)))

    try:
        utc_time_iso = respns.get("data").get("date")
        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)
        dayz = int(user_input_time.day)

        if dayz != 0:
            Next = _("➡️ Далее")
            markup.insert(
                InlineKeyboardButton(text=Next, callback_data=choose_time.new(action="next", post_id=post_id)))
        else:
            pass
    except:
        pass
    text = _("⏳ ОТЛОЖИТЬ\n\nВыберете время в меню")

    try:
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
    except Exception as e:
        logging.error(f"previous_month {e}")
        await call.bot.send_message(call.from_user.id, text, reply_markup=markup)


async def next_month(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    post_id = int(callback_data.get("post_id"))
    await delete_messages(call, post_id)
    year = int(callback_data["year"])
    month = int(callback_data["month"])
    day = int(callback_data["day"])
    action = "show_calendar"
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }) as response:
            respns = await response.json()
    id_channel = int(respns.get("data").get("channel_id"))
    if month == 12:
        year += 1
        month = 1
    else:
        month += 1

    markup = types.InlineKeyboardMarkup(row_width=7)
    new_calendar = await generate_calendar(_, markup, post_id, action, year, month, day)
    hour_keyboard = await generate_hour_keyboard(_, markup, post_id, action)
    minute_keyboard = await generate_minute_keyboard(_, markup, post_id, action)
    Back = _("⬅️ Назад")
    markup.row(InlineKeyboardButton(text=Back, callback_data=further.new(channel_id=id_channel, post_id=post_id)))

    try:
        utc_time_iso = respns.get("data").get("date")
        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)
        dayz = int(user_input_time.day)

        if dayz != 0:
            Next = _("➡️ Далее")
            markup.insert(
                InlineKeyboardButton(text=Next, callback_data=choose_time.new(action="next", post_id=post_id)))
        else:
            pass
    except:
        pass
    text = _("⏳ ОТЛОЖИТЬ\n\nВыберете время в меню")

    try:
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
    except Exception as e:
        logging.error(f"next_month {e}")
        await call.bot.send_message(call.from_user.id, text, reply_markup=markup)


async def generate_hour_keyboard(_, markup, post_id, action):
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }) as response:
            respns = await response.json()
    user_id = int(respns.get("data").get("user_id"))
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/{user_id}/") as response:
            respoonse = await response.json()
    user_timezone = int(respoonse.get("data").get("time_zone"))
    now = datetime.utcnow() + timedelta(hours=user_timezone)
    try:
        utc_time_iso = respns.get("data").get("date")
        user_input_time = await convert_to_user_time(user_id, utc_time_iso)
        yearz = user_input_time.year
        monthz = user_input_time.month
        dayz = user_input_time.day

        date_hour = int(user_input_time.hour)

        if yearz == now.year and monthz == now.month and dayz == now.day:
            hours = [str(i) for i in range(now.hour, 24)]
        else:
            hours = [str(i) for i in range(24)]

        if date_hour == 0:
            text_hour = _("Выберите час")
        else:
            text_hour = _("Часы: {}").formaat(date_hour)
    except:
        date_hour = 999
        text_hour = _("Выберите час")
        hours = [str(i) for i in range(24)]

    if action == "hour":
        markup.row(InlineKeyboardButton(text=f"--- {text_hour} ---",
                                        callback_data=choose_time.new(action="hour", post_id=post_id)))
        markup.add(*[InlineKeyboardButton(text=(f"✅ {hour}" if str(date_hour) == str(hour) else hour),
                                          callback_data=hour_clbk.new(hour=hour, post_id=post_id)) for hour in hours])
    else:
        markup.row(
            InlineKeyboardButton(text=f"{text_hour} ↘️", callback_data=choose_time.new(action="hour", post_id=post_id)))
    return markup


async def generate_minute_keyboard(_, markup, post_id, action):
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }) as response:
            respns = await response.json()
    user_id = int(respns.get("data").get("user_id"))
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/{user_id}/") as response:
            respoonse = await response.json()
    user_timezone = int(respoonse.get("data").get("time_zone"))
    now = datetime.utcnow() + timedelta(hours=user_timezone)
    now_minute = now.minute

    try:
        utc_time_iso = respns.get("data").get("date")
        user_input_time = await convert_to_user_time(user_id, utc_time_iso)
        yearz = user_input_time.year
        monthz = user_input_time.month
        dayz = user_input_time.day
        date_hour = user_input_time.hour

        date_minute = int(user_input_time.minute)
        day = f"{yearz}-{monthz}-{dayz}"

        if yearz == now.year and monthz == now.month and dayz == now.day and date_hour == now.hour:
            number = ((now_minute + 4) // 5) * 5
            minutes = [str(i) for i in range(int(number), 60, 5)]
        else:
            minutes = [str(i) for i in range(0, 60, 5)]

        if date_minute == 0:
            text_minute = _("Выберите минуту")
        else:
            text_minute = _("Минута: {}").format(date_minute)
    except:
        minutes = []
        date_minute = 999
        text_minute = _("Выберите минуту")

    if action == "minute":
        markup.row(InlineKeyboardButton(text=f"--- {text_minute} ---",
                                        callback_data=choose_time.new(action="minute", post_id=post_id)))
        markup.add(*[InlineKeyboardButton(text=(f"✅ {minute}" if int(date_minute) == int(minute) else minute),
                                          callback_data=minute_clbk.new(minute=minute, post_id=post_id)) for minute in
                     minutes])
    else:
        markup.row(InlineKeyboardButton(text=f"{text_minute} ↘️",
                                        callback_data=choose_time.new(action="minute", post_id=post_id)))
    return markup


async def choose_day(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    post_id = int(callback_data.get("post_id"))
    year = int(callback_data["year"])
    month = int(callback_data["month"])
    day = int(callback_data["day"])
    action = callback_data["action"]
    if action == "empty":
        pass
    else:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/{call.from_user.id}/") as response:
                respoonse = await response.json()
        user_timezone = int(respoonse.get("data").get("time_zone"))
        current_date = datetime.utcnow() + timedelta(hours=user_timezone)
        today = datetime(current_date.year, current_date.month, current_date.day)
        variable_day = datetime(year, month, day)
        yesterday = today - timedelta(days=1)

        if variable_day <= yesterday:
            pass
        else:
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
                utc_time_iso = respns.get("data").get("date")
                user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)
                desired_date = datetime(year=year, month=month, day=day, hour=user_input_time.hour,
                                        minute=user_input_time.minute)
            except:
                desired_date = datetime(year=year, month=month, day=day, hour=0, minute=0)

            user_input_time = (
                desired_date.year, desired_date.month, desired_date.day, desired_date.hour, desired_date.minute,
                desired_date.second)
            utc_time = await convert_to_utc(call.from_user.id, *user_input_time)

            data = {"id": post_id,
                    "date": utc_time.replace(tzinfo=None).isoformat()}

            async with aiohttp.ClientSession() as session:
                async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                       json=data) as response:
                    respns = await response.json()

            id_channel = int(respns.get("data").get("channel_id"))

            markup = types.InlineKeyboardMarkup(row_width=7)
            new_calendar = await generate_calendar(_, markup, post_id, action, year, month, day)
            hour_keyboard = await generate_hour_keyboard(_, markup, post_id, action)
            minute_keyboard = await generate_minute_keyboard(_, markup, post_id, action)
            Next = _("➡️ Далее")
            Back = _("⬅️ Назад")
            markup.row(InlineKeyboardButton(text=Back,
                                            callback_data=further.new(channel_id=id_channel, post_id=post_id)))

            try:
                utc_time_iso = respns.get("data").get("date")
                user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)
                dayz = int(user_input_time.day)

                if dayz != 0:
                    markup.insert(InlineKeyboardButton(text=Next,
                                                       callback_data=choose_time.new(action="next", post_id=post_id)))
            except:
                pass
            text = _("⏳ ОТЛОЖИТЬ\n\nВыберете время в меню")

            try:
                await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
            except Exception as e:
                logging.error(f"choose_day {e}")
                await call.bot.send_message(call.from_user.id, text, reply_markup=markup)


async def choose_hour(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    hour = callback_data["hour"]
    post_id = int(callback_data.get("post_id"))
    await delete_messages(call, post_id)
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }) as response:
            respns = await response.json()
    id_channel = int(respns.get("data").get("channel_id"))
    try:
        utc_time_iso = respns.get("data").get("date")
        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)
        desired_date = datetime(year=user_input_time.year, month=user_input_time.month, day=user_input_time.day,
                                hour=int(hour),
                                minute=user_input_time.minute)

        year, month, day = user_input_time.year, user_input_time.month, user_input_time.day
    except:
        desired_date = datetime(year=0, month=0, day=0, hour=int(hour), minute=0)
        year, month, day = 0, 0, 0

    user_input_time = (desired_date.year, desired_date.month, desired_date.day, desired_date.hour, desired_date.minute,
                       desired_date.second)
    utc_time = await convert_to_utc(call.from_user.id, *user_input_time)
    data = {"id": post_id,
            "date": utc_time.replace(tzinfo=None).isoformat()}
    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                               json=data) as response:
            respnss = await response.json()

    markup = types.InlineKeyboardMarkup(row_width=7)
    new_calendar = await generate_calendar(_, markup, post_id, "hour", year, month, day)
    hour_keyboard = await generate_hour_keyboard(_, markup, post_id, "hour")
    minute_keyboard = await generate_minute_keyboard(_, markup, post_id, "hour")
    Back = _("⬅️ Назад")
    Next = _("➡️ Далее")
    markup.row(InlineKeyboardButton(text=Back, callback_data=further.new(channel_id=id_channel, post_id=post_id)))
    try:
        utc_time_iso = respns.get("data").get("date")
        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)
        dayz = int(user_input_time.day)

        if dayz != 0:
            markup.insert(
                InlineKeyboardButton(text=Next, callback_data=choose_time.new(action="next", post_id=post_id)))
        else:
            pass
    except:
        pass
    text = _("⏳ ОТЛОЖИТЬ\n\nВыберете время в меню")

    try:
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
    except Exception as e:
        logging.error(f"choose_hour {e}")
        await call.bot.send_message(call.from_user.id, text, reply_markup=markup)


async def choose_minute(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    post_id = int(callback_data.get("post_id"))
    minute = int(callback_data["minute"])
    await delete_messages(call, post_id)
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }) as response:
            respns = await response.json()
    id_channel = int(respns.get("data").get("channel_id"))
    try:
        utc_time_iso = respns.get("data").get("date")
        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)
        desired_date = user_input_time
        desired_date = datetime(year=user_input_time.year, month=user_input_time.month, day=user_input_time.day,
                                hour=user_input_time.hour,
                                minute=minute)
        year, month, day = user_input_time.year, user_input_time.month, user_input_time.day
    except:
        desired_date = datetime(year=0, month=0, day=0, hour=0, minute=minute)
        year, month, day = 0, 0, 0

    user_input_time = (desired_date.year, desired_date.month, desired_date.day, desired_date.hour, desired_date.minute,
                       desired_date.second)
    utc_time = await convert_to_utc(call.from_user.id, *user_input_time)
    data = {"id": post_id,
            "date": utc_time.replace(tzinfo=None).isoformat()}
    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                               json=data) as response:
            respns = await response.json()

    markup = types.InlineKeyboardMarkup(row_width=7)
    Next = _("➡️ Далее")
    Back = _("⬅️ Назад")
    markup.row(InlineKeyboardButton(text=Back, callback_data=further.new(channel_id=id_channel, post_id=post_id)))

    try:
        utc_time_iso = respns.get("data").get("date")
        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)
        dayz = int(user_input_time.day)

        if dayz != 0:
            markup.insert(
                InlineKeyboardButton(text=Next, callback_data=choose_time.new(action="next", post_id=post_id)))
        else:
            pass
    except:
        pass
    text = _("⏳ ОТЛОЖИТЬ\n\nВыберете время в меню")

    try:
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
    except Exception as e:
        logging.error(f"choose_minute {e}")
        await call.bot.send_message(call.from_user.id, text, reply_markup=markup)


async def schedule_post(call: CallbackQuery, callback_data: dict):
    await call.answer()

    _ = call.bot.get("lang")
    post_id = int(callback_data.get("post_id"))

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
        post_id = int(respns.get("data").get("id"))
        id_channel = int(respns.get("data").get("channel_id"))
        utc_time_iso = respns.get("data").get("date")

        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)

        dt_naive = datetime(user_input_time.year, user_input_time.month, user_input_time.day, user_input_time.hour,
                            user_input_time.minute, 00)
        translated_date = format_date(dt_naive, locale='ru')

        data = {"id": id_channel}
        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel/one/",
                                    json=data) as response:
                respns = await response.json()

        title = respns.get("data").get("title")
        link = respns.get("data").get("link")
        url = f"<a href='{link}'>{title}</a>"

        markup = InlineKeyboardMarkup(row_width=1)
        schedule_btn = _("🕘 Да, отложить")
        back_btn_text = _("⬅️ Назад")
        schedule_post_txt = _("Запланировать пост в канал {} на {} ?").format(url, str(translated_date))

        markup.insert(InlineKeyboardButton(text=schedule_btn,
                                           callback_data=choose_time.new(action="confirm", post_id=post_id)))
        markup.insert(InlineKeyboardButton(text=back_btn_text,
                                           callback_data=choose_time.new(action="back_to_main_calendar",
                                                                         post_id=post_id)))

        try:
            await call.bot.edit_message_text(schedule_post_txt, call.from_user.id, call.message.message_id,
                                         reply_markup=markup)
        except Exception as e:
            logging.error(f"schedule_post {e}")
            await call.bot.send_message(call.from_user.id, schedule_post_txt, reply_markup=markup)

    except Exception as e:
        failed_scheduled = _("Публикацию запланировать не получилось")
        try:
            await call.bot.edit_message_text(failed_scheduled, call.from_user.id, call.message.message_id)
        except Exception as e:
            logging.error(f"failed_scheduled_post {e}")
            await call.bot.send_message(call.from_user.id, failed_scheduled)

async def schedule_post_confirm(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    post_id = int(callback_data.get("post_id"))
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
        post_id = int(respns.get("data").get("id"))
        id_channel = int(respns.get("data").get("channel_id"))

        data = {
            "channel_id": id_channel,
            "date": datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat(),
            "is_scheduled": True
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/get_filtered_posts/",
                    json=data) as response:
                response1 = await response.json()
        posts = response1.get('data')

        data = {"user_id": call.from_user.id,
                "channel_id": id_channel}

        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel/one/",
                                    json=data) as response:
                response2 = await response.json()
        user_channel_settings_id = response2.get("data").get("user_channel_settings_id")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel_settings/one/key_value/",
                    params={
                        "key": "id",
                        "value": user_channel_settings_id
                    }
            ) as response:
                response3 = await response.json()
        subscription_id = response3.get("data").get("subscription_id")

        subscription_response: Response[SubscriptionSchema] = Response[SubscriptionSchema].model_validate(
            await subscription_api.get_one_by_key_value(params={"key": "id", "value": 1})
        )

        if len(posts) > subscription_response.data.posts_per_day_quantity and subscription_id == 1:
            limits_exceeded = _("Превышены лимиты\n\nВы можете отправлять {} в день").format(
                subscription_response.data.posts_per_day_quantity)
            await call.bot.send_message(chat_id=call.from_user.id, text=limits_exceeded)
            return

        utc_time_iso = respns.get("data").get("date")
        utc_time = datetime.fromisoformat(utc_time_iso)
        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)

        dt_naive = datetime(user_input_time.year, user_input_time.month, user_input_time.day, user_input_time.hour,
                            user_input_time.minute, 00)
        translated_date = format_date(dt_naive, locale='ru')

        job = scheduler.add_job(scheduler_func, 'date', run_date=utc_time.replace(tzinfo=pytz.utc),
                                args=[id_channel, post_id])

        data = {"message": None,
                "job_id": job.id,
                "post_id": post_id}

        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/",
                                    json=data) as response:
                respons = await response.json()

        data = {"id": post_id,
                "is_scheduled": True}
        async with aiohttp.ClientSession() as session:
            async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                   json=data) as response:
                respns = await response.json()

        data = {"id": id_channel}
        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel/one/",
                                    json=data) as response:
                respns = await response.json()

        title = respns.get("data").get("title")
        link = respns.get("data").get("link")
        url = f"<a href='{link}'>{title}</a>"

        text = _("Пост запланирован в канал {} на {}").format(url, str(translated_date))

        try:
            await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id)
        except Exception as e:
            logging.error(f"schedule_post_confirm {e}")
            await call.bot.send_message(call.from_user.id, text)

    except Exception as e:
        text = _("Публикацию запланировать не получилось")
        try:
            await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id)
        except Exception as e:
            logging.error(f"schedule_post_confirm {e}")
            await call.bot.send_message(call.from_user.id, text)

async def scheduler_func(id_channel, post_id):
    call = types.CallbackQuery.get_current()

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
    auto_delete_timer = response1.get("data").get("auto_delete_timer")
    channel_id = int(response1.get("data").get("channel_id"))
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
            response2 = await response.json()
    user_channel_settings_id = response2.get("data").get("user_channel_settings_id")

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

            send_message = await call.bot.send_media_group(chat_id=id_channel, media=media)
            # msg_id = send_message[0].message_id
            msg_id = [obj.message_id for obj in send_message]

        else:
            media_id = media_data[0]
            if media_id.get("media_type") == "photo":
                send_message = await call.bot.send_photo(id_channel, media_id.get("file_id"), caption,
                                                         caption_entities=combined_entities,
                                                         reply_markup=markup)

            elif media_id.get("media_type") == "video":
                send_message = await call.bot.send_video(id_channel,
                                                         media_id.get("file_id"),
                                                         caption=caption,
                                                         caption_entities=combined_entities,
                                                         reply_markup=markup)

            elif media_id.get("media_type") == "document":
                send_message = await call.bot.send_document(id_channel,
                                                            media_id.get("file_id"),
                                                            caption=caption,
                                                            caption_entities=combined_entities,
                                                            reply_markup=markup)

            elif media_id.get("media_type") == "audio":
                send_message = await call.bot.send_audio(id_channel,
                                                         media_id.get("file_id"),
                                                         caption=caption,
                                                         caption_entities=combined_entities,
                                                         reply_markup=markup)

            elif media_id.get("media_type") == "animation":
                send_message = await call.bot.send_animation(id_channel,
                                                             media_id.get("file_id"),
                                                             caption=caption,
                                                             caption_entities=combined_entities,
                                                             reply_markup=markup)

            elif media_id.get("media_type") == "video_note":
                send_message = await call.bot.send_video_note(id_channel,
                                                              media_id.get("file_id"),
                                                              reply_markup=markup)

            msg_id = send_message.message_id
    else:
        send_message = await call.bot.send_message(id_channel, caption, entities=combined_entities, reply_markup=markup)
        msg_id = send_message.message_id

    messages_id = {}
    if send_message:
        messages_id["message"] = msg_id

    data = {"post_id": post_id}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/one/",
                                json=data) as response:
            response4 = await response.json()

    message_id = response4.get("data").get("id")
    data = {"id": message_id,
            "message": messages_id}

    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/",
                               json=data) as response:
            message_response = await response.json()

    if auto_delete_timer and int(auto_delete_timer) != 0:
        utc_time_iso = response1.get("data").get("date")
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


async def convert_to_utc(user_id, year, month, day, hour, minute, second):
    async with aiohttp.ClientSession() as session:
        async with session.get(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/{user_id}/") as response:
            respoonse = await response.json()
    user_timezone = int(respoonse.get("data").get("time_zone"))
    user_time = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
    utc_time = user_time - timedelta(hours=user_timezone)
    return utc_time


async def convert_to_user_time(user_id, utc_time_iso):
    async with aiohttp.ClientSession() as session:
        async with session.get(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/{user_id}/") as response:
            respoonse = await response.json()
    user_timezone = int(respoonse.get("data").get("time_zone"))
    utc_datetime = datetime.fromisoformat(utc_time_iso)
    utc_time = datetime(utc_datetime.year, utc_datetime.month, utc_datetime.day, utc_datetime.hour, utc_datetime.minute,
                        utc_datetime.second, tzinfo=timezone.utc)
    user_time = utc_time + timedelta(hours=user_timezone)
    return user_time


async def auto_delete_timer(call: CallbackQuery, callback_data: dict):
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
        f"🗑 <b>ТАЙМЕР УДАЛЕНИЯ</b>\n\nВы можете установить через какое время после выхода поста, он будет удалён.\n\n" \
        f"Отправьте боту время, через которое нужно удалить пост либо выберите один из предложенных вариантов.")
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
                                                callback_data=choose_seconds.new(seconds=second,
                                                                                 channel_id=id_channel,
                                                                                 post_id=post_id)))
        elif second < 3600:
            minutes = second // 60
            buttons.append(InlineKeyboardButton(text=f"{exist_del_timer}{minutes} мин",
                                                callback_data=choose_seconds.new(seconds=second,
                                                                                 channel_id=id_channel,
                                                                                 post_id=post_id)))
        elif second < 86400:
            hours = second // 3600
            buttons.append(InlineKeyboardButton(text=f"{exist_del_timer}{hours}ч",
                                                callback_data=choose_seconds.new(seconds=second,
                                                                                 channel_id=id_channel,
                                                                                 post_id=post_id)))
        else:
            days = second // 86400
            buttons.append(InlineKeyboardButton(text=f"{exist_del_timer}{days}д",
                                                callback_data=choose_seconds.new(seconds=second,
                                                                                 channel_id=id_channel,
                                                                                 post_id=post_id)))

        if len(buttons) >= 4:
            markup.row(*buttons)
            buttons.clear()
    select_btn = _("Выбрать")
    markup.row(InlineKeyboardButton(text=select_btn, callback_data=further.new(channel_id=id_channel, post_id=post_id)))

    try:
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
    except Exception as e:
        logging.error(f"auto_delete_timer {e}")
        await call.bot.send_message(call.from_user.id, text, reply_markup=markup)


async def auto_delete_timer2(call: CallbackQuery, callback_data: dict):
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

    await auto_delete_timer(call, callback_data)


async def publish(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    post_id = int(callback_data.get("post_id"))
    await delete_messages(call, post_id)
    id_channel = int(callback_data.get("channel_id"))
    post_id = int(callback_data.get("post_id"))

    data = {"id": id_channel}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel/one/",
                                json=data) as response:
            respns = await response.json()
    title = respns.get("data").get("title")
    link = respns.get("data").get("link")
    url = f"<a href='{link}'>{title}</a>"

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }
        ) as response:
            respns = await response.json()

    text = _("Вы уверены, что хотите опубликовать пост в канале {} ?").format(url)
    publish_txt = _("🚀 Да, опубликовать")
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text=publish_txt,
                                    callback_data=sending_clbk.new(action="publish_connfirm", channel_id=id_channel,
                                                                   post_id=post_id)))
    is_scheduled = respns.get("data").get("is_scheduled")
    Back = _("⬅️ Назад")
    if is_scheduled is True:
        markup.add(
            InlineKeyboardButton(text=Back, callback_data=post_callback.new(action="next", post_id=post_id)))
    else:
        markup.add(
            InlineKeyboardButton(text=Back, callback_data=further.new(channel_id=id_channel, post_id=post_id)))
    try:
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
    except Exception as e:
        await call.bot.send_message(call.from_user.id, text, reply_markup=markup)


async def publish_connfirm(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    post_id = int(callback_data.get("post_id"))
    await delete_messages(call, post_id)
    id_channel = int(callback_data.get("channel_id"))

    # CHECK POST QUANTITY
    data = {
        "channel_id": id_channel,
        "date": datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat(),
        "is_scheduled": True
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/get_filtered_posts/",
                json=data) as response:
            response1 = await response.json()
    posts = response1.get('data')

    data = {"user_id": call.from_user.id,
            "channel_id": id_channel}

    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel/one/",
                                json=data) as response:
            response2 = await response.json()
    user_channel_settings_id = response2.get("data").get("user_channel_settings_id")

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel_settings/one/key_value/",
                params={
                    "key": "id",
                    "value": user_channel_settings_id
                }
        ) as response:
            response3 = await response.json()
    subscription_id = response3.get("data").get("subscription_id")

    subscription_response: Response[SubscriptionSchema] = Response[SubscriptionSchema].model_validate(
        await subscription_api.get_one_by_key_value(params={"key": "id", "value": 1})
    )

    if len(posts) > subscription_response.data.posts_per_day_quantity and subscription_id == 1:
        limits_exceeded = _("Превышены лимиты\n\nВы можете отправлять {} в день").format(
            subscription_response.data.posts_per_day_quantity)

        await call.bot.send_message(chat_id=call.from_user.id,
                                    text=limits_exceeded)
        return

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/{call.from_user.id}/") as response:
            respoonse = await response.json()

    user_timezone = int(respoonse.get("data").get("time_zone"))
    current_date = datetime.utcnow() + timedelta(hours=user_timezone)
    user_input_time = (current_date.year, current_date.month, current_date.day, current_date.hour,
                       current_date.minute, current_date.second)
    utc_time = await convert_to_utc(call.from_user.id, *user_input_time)

    data = {"id": post_id,
            "date": utc_time.replace(tzinfo=None).isoformat(),
            "is_scheduled": True}

    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                               json=data) as response:
            post_response = await response.json()

    data = {"post_id": post_id}

    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/one/",
                                json=data) as response:
            response4 = await response.json()

    # try:
    #     message_id = int(response4.get("data").get("id"))
    #
    #     data = {"id": message_id,
    #             "message": None,
    #             "job_id": None}
    #
    #     async with aiohttp.ClientSession() as session:
    #         async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/",
    #                                json=data) as response:
    #             unused_response = await response.json()
    #
    #     job_id = response4.get("data").get("job_id")
    #     scheduler.remove_job(job_id)
    # except:

    # message_id = response4.get("data").get("id") if response4.get("data") is not None else None
    data = {"message": None,  # message_id if message_id is not None else None,
            "job_id": None,
            "post_id": post_id}

    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/",
                                json=data) as response:
            unused_response = await response.json()

    data = {"id": id_channel}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel/one/",
                                json=data) as response:
            channel_response = await response.json()

    title = channel_response.get("data").get("title")
    link = channel_response.get("data").get("link")
    url = f"<a href='{link}'>{title}</a>"

    text = _("✅ Пост опубликован на канале {}").format(url)

    try:
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id)
    except Exception as e:
        await call.bot.send_message(call.from_user.id, text=text)

    await scheduler_func(id_channel, post_id)

    # TODO make in one request
    while True:
        initial_post_id = post_response.get("data").get("initial_post_id")
        if initial_post_id is None:
            break
        else:
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                        url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/{initial_post_id}") as response:
                    post_response = await response.json()

    data = {"id": post_id,
            "initial_post_id": None}

    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                               json=data) as response:
            respns = await response.json()


def register_calendar_handler(dp: Dispatcher):
    dp.register_callback_query_handler(sending, further.filter())

    dp.register_callback_query_handler(main_calendar, sending_clbk.filter(action="postpone"))
    dp.register_callback_query_handler(main_calendar, choose_time.filter(action="back_to_main_calendar"))

    dp.register_callback_query_handler(schedule_post, choose_time.filter(action="next"))
    dp.register_callback_query_handler(schedule_post_confirm, choose_time.filter(action="confirm"))
    dp.register_callback_query_handler(show_calendar, choose_time.filter())

    dp.register_callback_query_handler(previous_month, calendar_clbk.filter(action="previous"))
    dp.register_callback_query_handler(next_month, calendar_clbk.filter(action="next"))

    dp.register_callback_query_handler(choose_day, calendar_clbk.filter(action="date"))
    dp.register_callback_query_handler(choose_day, calendar_clbk.filter(action="empty"))
    dp.register_callback_query_handler(choose_hour, hour_clbk.filter())
    dp.register_callback_query_handler(choose_minute, minute_clbk.filter())

    dp.register_callback_query_handler(auto_delete_timer, sending_clbk.filter(action="auto_delete"))
    dp.register_callback_query_handler(auto_delete_timer2, choose_seconds.filter())

    dp.register_callback_query_handler(publish, sending_clbk.filter(action="publish"))
    dp.register_callback_query_handler(publish_connfirm, sending_clbk.filter(action="publish_connfirm"))
