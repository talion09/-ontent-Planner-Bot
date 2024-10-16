import copy
import copy
import json
import math
from calendar import monthrange, weekday
from datetime import timezone, datetime, timedelta

import aiohttp
import pytz
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from babel.dates import format_date

from tg_bot import config, scheduler
from tg_bot.aiogram_bot.filters.is_admin import IsAdmin
from tg_bot.aiogram_bot.handlers.users.create.create_post import delete_messages
from tg_bot.aiogram_bot.keyboards.inline.admin_inline import admin_further, admin_sending_clb, admin_choose_time, \
    admin_calendar_clb, admin_hour_clb, admin_minute_clb


async def sending(call: CallbackQuery, callback_data: dict):
    await call.answer()
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

    text = f"💼 <b>НАСТРОЙКИ ОТПРАВКИ</b>\n\n" \
           f"Пост готов к рассылке\n\n" \
           f"Настройте его перед отправкой."
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
    markup.row(InlineKeyboardButton(text="🕔 Отложить",
                                    callback_data=admin_sending_clb.new(action="postpone", post_id=post_id)))
    markup.row(
        InlineKeyboardButton(text="⬅️ Назад",
                             callback_data=admin_sending_clb.new(action="back", post_id=post_id)))

    # await call.bot.delete_message(call.from_user.id, call.message.message_id)
    try:
        await call.bot.edit_message_text(text=text, chat_id=call.from_user.id, message_id=call.message.message_id,
                                         reply_markup=markup)
    except Exception as e:
        await call.bot.send_message(call.from_user.id, text, reply_markup=markup)


async def main_calendar(call: CallbackQuery, callback_data: dict):
    await call.answer()
    post_id = int(callback_data.get("post_id"))
    # await delete_messages(call, post_id)

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

    try:
        utc_time_iso = respns.get("data").get("date")
        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)
        date_hour = int(user_input_time.hour)
        date_minute = int(user_input_time.minute)

        text_day = f"🗓 Показать календарь"

        if date_hour == 0:
            text_hour = "Выберите час ↘️"
        else:
            text_hour = f"Часы: {date_hour} ↘️"

        if date_minute == 0:
            text_minute = "Выберите минуту ↘️"
        else:
            text_minute = f"Минуты: {date_minute} ↘️"
    except:
        text_day = f"🗓 Показать календарь"
        text_hour = "Выберите час ↘️"
        text_minute = "Выберите минуту ↘️"

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
        calendar = await generate_calendar(markup, post_id, action, year, month, day)
    except:
        markup.row(
            InlineKeyboardButton(text=text_day,
                                 callback_data=admin_choose_time.new(action="show_calendar", post_id=post_id)))
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
                                                    callback_data=admin_calendar_clb.new(action="date",
                                                                                         year=str(today.year),
                                                                                         month=str(today.month),
                                                                                         day=today.day,
                                                                                         post_id=post_id)))
            elif dayt == tomorrow1:
                button_text = f"{format_date(tomorrow1, format='EEE, dd MMM', locale='ru')}"
                buttons.append(InlineKeyboardButton(text=button_text,
                                                    callback_data=admin_calendar_clb.new(action="date",
                                                                                         year=str(tomorrow1.year),
                                                                                         month=str(tomorrow1.month),
                                                                                         day=tomorrow1.day,
                                                                                         post_id=post_id)))
            elif dayt == tomorrow2:
                button_text = f"{format_date(tomorrow2, format='EEE, dd MMM', locale='ru')} →"
                buttons.append(InlineKeyboardButton(text=button_text,
                                                    callback_data=admin_calendar_clb.new(action="date",
                                                                                         year=str(tomorrow2.year),
                                                                                         month=str(tomorrow2.month),
                                                                                         day=tomorrow2.day,
                                                                                         post_id=post_id)))
            else:
                pass
        markup.row(*buttons)

    markup.row(
        InlineKeyboardButton(text=text_hour, callback_data=admin_choose_time.new(action="hour", post_id=post_id)))
    markup.row(
        InlineKeyboardButton(text=text_minute, callback_data=admin_choose_time.new(action="minute", post_id=post_id)))
    markup.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=admin_further.new(post_id=post_id)))

    try:
        utc_time_iso = respns.get("data").get("date")
        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)
        dayz = int(user_input_time.day)

        if dayz != 0:
            markup.insert(
                InlineKeyboardButton(text="➡️ Далее",
                                     callback_data=admin_choose_time.new(action="next", post_id=post_id)))
        else:
            pass
    except:
        pass

    text = f"⏳ ОТЛОЖИТЬ\n\nВыберете время в меню"
    try:
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
    except Exception as e:
        await call.bot.send_message(call.from_user.id, text, reply_markup=markup)


async def show_calendar(call: CallbackQuery, callback_data: dict):
    await call.answer()
    post_id = int(callback_data.get("post_id"))
    # await delete_messages(call, post_id)
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

    calendar = await generate_calendar(markup, post_id, action, year, month, day)
    hour_keyboard = await generate_hour_keyboard(markup, post_id, action)
    minute_keyboard = await generate_minute_keyboard(markup, post_id, action)
    markup.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=admin_further.new(post_id=post_id)))

    if dayz != 0:
        markup.insert(
            InlineKeyboardButton(text="➡️ Далее", callback_data=admin_choose_time.new(action="next", post_id=post_id)))
    else:
        pass

    text = f"⏳ ОТЛОЖИТЬ\n\nВыберете время в меню"
    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


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


async def generate_calendar(markup, post_id, action, year, month, day):
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
            InlineKeyboardButton(text=f"🗓 Скрыть календарь",
                                 callback_data=admin_choose_time.new(action="hide_calendar", post_id=post_id)))
        markup.row(
            InlineKeyboardButton(text='◀️ Предыдущий',
                                 callback_data=admin_calendar_clb.new(action="previous", year=str(year),
                                                                      month=str(month),
                                                                      day="1", post_id=post_id)),
            InlineKeyboardButton(text=f'{month_name} {year}',
                                 callback_data=admin_calendar_clb.new(action="empty", year=0, month=0, day=0,
                                                                      post_id=post_id)),
            InlineKeyboardButton(text='Следующий ▶️',
                                 callback_data=admin_calendar_clb.new(action="next", year=str(year), month=str(month),
                                                                      day="1", post_id=post_id))
        )

        markup.add(*[types.InlineKeyboardButton(text=day,
                                                callback_data=admin_calendar_clb.new(action="empty",
                                                                                     year=0, month=0, day=0,
                                                                                     post_id=post_id)) for day in
                     ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]])

        for _ in range(int(full_weeks)):
            week = []
            for i in range(7):
                if days_count < offset or days_count >= days_in_month + offset:
                    week.append(InlineKeyboardButton(
                        text=" ",
                        callback_data=admin_calendar_clb.new(action="empty", year=0, month=0, day=0, post_id=post_id)
                    ))
                else:
                    day_clb = days_count - offset + 1
                    if int(yearz) == int(year) and int(monthz) == int(month) and int(dayz) == int(day_clb):
                        day_txt = f"✅ {day_clb}"

                    else:
                        day_txt = day_clb
                    week.append(InlineKeyboardButton(
                        text=day_txt,
                        callback_data=admin_calendar_clb.new(action="date", year=str(year), month=str(month),
                                                             day=str(day_clb), post_id=post_id)
                    ))
                days_count += 1
            month_calendar.append(week)

        for week in month_calendar:
            markup.add(*week)
    else:
        markup.row(InlineKeyboardButton(text=f"🗓 Показать календарь",
                                        callback_data=admin_choose_time.new(action="show_calendar", post_id=post_id)))

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
                                                        callback_data=admin_calendar_clb.new(action="date",
                                                                                             year=str(
                                                                                                 variable_day.year),
                                                                                             month=str(
                                                                                                 variable_day.month),
                                                                                             day=today.day,
                                                                                             post_id=post_id)))
                elif dayt == tomorrow1:
                    button_text = f"{format_date(tomorrow1, format='EEE, dd MMM', locale='ru')}"
                    buttons.append(InlineKeyboardButton(text=button_text,
                                                        callback_data=admin_calendar_clb.new(action="date",
                                                                                             year=str(tomorrow1.year),
                                                                                             month=str(tomorrow1.month),
                                                                                             day=tomorrow1.day,
                                                                                             post_id=post_id)))
                elif dayt == tomorrow2:
                    button_text = f"{format_date(tomorrow2, format='EEE, dd MMM', locale='ru')} →"
                    buttons.append(InlineKeyboardButton(text=button_text,
                                                        callback_data=admin_calendar_clb.new(action="date",
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
                                                        callback_data=admin_calendar_clb.new(action="date",
                                                                                             year=str(
                                                                                                 variable_day.year),
                                                                                             month=str(
                                                                                                 variable_day.month),
                                                                                             day=variable_day.day,
                                                                                             post_id=post_id)))
                elif dayt == tomorrow1:
                    button_text = f"← {format_date(tomorrow1, format='EEE, dd MMM', locale='ru')}"
                    buttons.append(InlineKeyboardButton(text=button_text,
                                                        callback_data=admin_calendar_clb.new(action="date",
                                                                                             year=str(tomorrow1.year),
                                                                                             month=str(tomorrow1.month),
                                                                                             day=tomorrow1.day,
                                                                                             post_id=post_id)))
                elif dayt == tomorrow2:
                    button_text = f"{format_date(tomorrow2, format='EEE, dd MMM', locale='ru')} →"
                    buttons.append(InlineKeyboardButton(text=button_text,
                                                        callback_data=admin_calendar_clb.new(action="date",
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
    post_id = int(callback_data.get("post_id"))
    # await delete_messages(call, post_id)
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

    if month == 1:
        year -= 1
        month = 12
    else:
        month -= 1

    markup = types.InlineKeyboardMarkup(row_width=7)
    new_calendar = await generate_calendar(markup, post_id, action, year, month, day)
    hour_keyboard = await generate_hour_keyboard(markup, post_id, action)
    minute_keyboard = await generate_minute_keyboard(markup, post_id, action)
    markup.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=admin_further.new(post_id=post_id)))

    try:
        utc_time_iso = respns.get("data").get("date")
        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)
        dayz = int(user_input_time.day)

        if dayz != 0:
            markup.insert(
                InlineKeyboardButton(text="➡️ Далее",
                                     callback_data=admin_choose_time.new(action="next", post_id=post_id)))
        else:
            pass
    except:
        pass
    text = f"⏳ ОТЛОЖИТЬ\n\nВыберете время в меню"

    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def next_month(call: CallbackQuery, callback_data: dict):
    await call.answer()
    post_id = int(callback_data.get("post_id"))
    # await delete_messages(call, post_id)
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
    if month == 12:
        year += 1
        month = 1
    else:
        month += 1

    markup = types.InlineKeyboardMarkup(row_width=7)
    new_calendar = await generate_calendar(markup, post_id, action, year, month, day)
    hour_keyboard = await generate_hour_keyboard(markup, post_id, action)
    minute_keyboard = await generate_minute_keyboard(markup, post_id, action)
    markup.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=admin_further.new(post_id=post_id)))

    try:
        utc_time_iso = respns.get("data").get("date")
        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)
        dayz = int(user_input_time.day)

        if dayz != 0:
            markup.insert(
                InlineKeyboardButton(text="➡️ Далее",
                                     callback_data=admin_choose_time.new(action="next", post_id=post_id)))
        else:
            pass
    except:
        pass
    text = f"⏳ ОТЛОЖИТЬ\n\nВыберете время в меню"

    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def generate_hour_keyboard(markup, post_id, action):
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
            text_hour = "Выберите час"
        else:
            text_hour = f"Часы: {date_hour}"
    except:
        date_hour = 999
        text_hour = "Выберите час"
        hours = [str(i) for i in range(24)]

    if action == "hour":
        markup.row(InlineKeyboardButton(text=f"--- {text_hour} ---",
                                        callback_data=admin_choose_time.new(action="hour", post_id=post_id)))
        markup.add(*[InlineKeyboardButton(text=(f"✅ {hour}" if str(date_hour) == str(hour) else hour),
                                          callback_data=admin_hour_clb.new(hour=hour, post_id=post_id)) for hour in
                     hours])
    else:
        markup.row(
            InlineKeyboardButton(text=f"{text_hour} ↘️",
                                 callback_data=admin_choose_time.new(action="hour", post_id=post_id)))
    return markup


async def generate_minute_keyboard(markup, post_id, action):
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
            text_minute = "Выберите минуту"
        else:
            text_minute = f"Минута: {date_minute}"
    except:
        minutes = []
        date_minute = 999
        text_minute = "Выберите минуту"

    if action == "minute":
        markup.row(InlineKeyboardButton(text=f"--- {text_minute} ---",
                                        callback_data=admin_choose_time.new(action="minute", post_id=post_id)))
        markup.add(*[InlineKeyboardButton(text=(f"✅ {minute}" if int(date_minute) == int(minute) else minute),
                                          callback_data=admin_minute_clb.new(minute=minute, post_id=post_id)) for minute
                     in
                     minutes])
    else:
        markup.row(InlineKeyboardButton(text=f"{text_minute} ↘️",
                                        callback_data=admin_choose_time.new(action="minute", post_id=post_id)))
    return markup


async def choose_day(call: CallbackQuery, callback_data: dict):
    await call.answer()
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
            # await delete_messages(call, post_id)
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

            markup = types.InlineKeyboardMarkup(row_width=7)
            new_calendar = await generate_calendar(markup, post_id, action, year, month, day)
            hour_keyboard = await generate_hour_keyboard(markup, post_id, action)
            minute_keyboard = await generate_minute_keyboard(markup, post_id, action)
            markup.row(InlineKeyboardButton(text="⬅️ Назад",
                                            callback_data=admin_further.new(post_id=post_id)))

            try:
                utc_time_iso = respns.get("data").get("date")
                user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)
                dayz = int(user_input_time.day)

                if dayz != 0:
                    markup.insert(InlineKeyboardButton(text="➡️ Далее",
                                                       callback_data=admin_choose_time.new(action="next",
                                                                                           post_id=post_id)))
                else:
                    pass
            except:
                pass
            text = f"⏳ ОТЛОЖИТЬ\n\nВыберете время в меню"

            await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def choose_hour(call: CallbackQuery, callback_data: dict):
    await call.answer()
    hour = callback_data["hour"]
    post_id = int(callback_data.get("post_id"))
    # await delete_messages(call, post_id)
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
    new_calendar = await generate_calendar(markup, post_id, "hour", year, month, day)
    hour_keyboard = await generate_hour_keyboard(markup, post_id, "hour")
    minute_keyboard = await generate_minute_keyboard(markup, post_id, "hour")
    markup.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=admin_further.new(post_id=post_id)))
    try:
        utc_time_iso = respns.get("data").get("date")
        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)
        dayz = int(user_input_time.day)

        if dayz != 0:
            markup.insert(
                InlineKeyboardButton(text="➡️ Далее",
                                     callback_data=admin_choose_time.new(action="next", post_id=post_id)))
        else:
            pass
    except:
        pass
    text = f"⏳ ОТЛОЖИТЬ\n\nВыберете время в меню"

    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def choose_minute(call: CallbackQuery, callback_data: dict):
    await call.answer()
    post_id = int(callback_data.get("post_id"))
    minute = int(callback_data["minute"])
    # await delete_messages(call, post_id)
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
    new_calendar = await generate_calendar(markup, post_id, "minute", year, month, day)
    hour_keyboard = await generate_hour_keyboard(markup, post_id, "minute")
    minute_keyboard = await generate_minute_keyboard(markup, post_id, "minute")
    markup.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=admin_further.new(post_id=post_id)))

    try:
        utc_time_iso = respns.get("data").get("date")
        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)
        dayz = int(user_input_time.day)

        if dayz != 0:
            markup.insert(
                InlineKeyboardButton(text="➡️ Далее",
                                     callback_data=admin_choose_time.new(action="next", post_id=post_id)))
        else:
            pass
    except:
        pass
    text = f"⏳ ОТЛОЖИТЬ\n\nВыберете время в меню"

    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def schedule_post(call: CallbackQuery, callback_data: dict):
    await call.answer()
    post_id = int(callback_data.get("post_id"))
    # await delete_messages(call, post_id)
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
        utc_time_iso = respns.get("data").get("date")

        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)

        dt_naive = datetime(user_input_time.year, user_input_time.month, user_input_time.day, user_input_time.hour,
                            user_input_time.minute, 00)
        translated_date = format_date(dt_naive, locale='ru')

        markup = InlineKeyboardMarkup(row_width=1)
        markup.insert(InlineKeyboardButton(text="🕘 Да, отложить",
                                           callback_data=admin_choose_time.new(action="confirm", post_id=post_id)))
        markup.insert(InlineKeyboardButton(text="⬅️ Назад",
                                           callback_data=admin_choose_time.new(action="back_to_main_calendar",
                                                                               post_id=post_id)))
        text = f"Запланировать рассылку на {str(translated_date)} ?"
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
    except:
        text = f"Публикацию запланировать не получилось"
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id)


async def schedule_post_confirm(call: CallbackQuery, callback_data: dict):
    await call.answer()
    post_id = int(callback_data.get("post_id"))
    # await delete_messages(call, post_id)

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

        utc_time_iso = respns.get("data").get("date")
        utc_time = datetime.fromisoformat(utc_time_iso)
        user_input_time = await convert_to_user_time(call.from_user.id, utc_time_iso)

        dt_naive = datetime(user_input_time.year, user_input_time.month, user_input_time.day, user_input_time.hour,
                            user_input_time.minute, 00)
        translated_date = format_date(dt_naive, locale='ru')

        job = scheduler.add_job(scheduler_func, 'date', run_date=utc_time.replace(tzinfo=pytz.utc), args=[post_id])

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

        text = f"Рассылка запланирована на {str(translated_date)}"
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id)
    except:
        text = f"Публикацию запланировать не получилось"
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id)


async def scheduler_func(post_id):
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
    channel_id = response1.get("data").get("channel_id")
    entities = response1.get("data").get("entities")
    entities = [types.MessageEntity(**entity) for entity in
                json.loads(entities)] if entities else None

    subscription_id = 1
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/get_unique_users_with_subscription/{subscription_id}") as response:
            response2 = await response.json()
            users = response2.get("data")

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

    combined_entities = copy.deepcopy(entities)

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
            for user_id in users:
                try:
                    send_message = await call.bot.send_media_group(chat_id=user_id, media=media)
                except Exception as e:
                    ...

        else:
            media_id = media_data[0]
            if media_id.get("media_type") == "photo":
                for user_id in users:
                    try:
                        send_message = await call.bot.send_photo(user_id, media_id.get("file_id"), caption,
                                                                 caption_entities=combined_entities,
                                                                 reply_markup=markup)
                    except Exception as e:
                        ...
            elif media_id.get("media_type") == "video":
                for user_id in users:
                    try:
                        send_message = await call.bot.send_video(user_id,
                                                                 media_id.get("file_id"),
                                                                 caption=caption,
                                                                 caption_entities=combined_entities,
                                                                 reply_markup=markup)
                    except Exception as e:
                        ...
            elif media_id.get("media_type") == "document":
                for user_id in users:
                    try:
                        send_message = await call.bot.send_document(user_id,
                                                                    media_id.get("file_id"),
                                                                    caption=caption,
                                                                    caption_entities=combined_entities,
                                                                    reply_markup=markup)
                    except Exception as e:
                        ...
            elif media_id.get("media_type") == "audio":
                for user_id in users:
                    try:
                        send_message = await call.bot.send_audio(user_id,
                                                                 media_id.get("file_id"),
                                                                 caption=caption,
                                                                 caption_entities=combined_entities,
                                                                 reply_markup=markup)
                    except Exception as e:
                        ...

            elif media_id.get("media_type") == "animation":
                for user_id in users:
                    try:
                        send_message = await call.bot.send_animation(user_id,
                                                                     media_id.get("file_id"),
                                                                     caption=caption,
                                                                     caption_entities=combined_entities,
                                                                     reply_markup=markup)
                    except Exception as e:
                        ...

            elif media_id.get("media_type") == "video_note":
                for user_id in users:
                    try:
                        send_message = await call.bot.send_video_note(user_id,
                                                                      media_id.get("file_id"),
                                                                      reply_markup=markup)
                    except Exception as e:
                        ...

    else:
        for user_id in users:
            try:
                send_message = await call.bot.send_message(user_id, caption, entities=combined_entities,
                                                           reply_markup=markup)
            except Exception as e:
                ...


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


def register_calendar_admin(dp: Dispatcher):
    dp.register_callback_query_handler(sending, admin_further.filter(), IsAdmin())

    dp.register_callback_query_handler(main_calendar, admin_sending_clb.filter(action="postpone"), IsAdmin())
    dp.register_callback_query_handler(main_calendar, admin_choose_time.filter(action="back_to_main_calendar"),
                                       IsAdmin())

    dp.register_callback_query_handler(schedule_post, admin_choose_time.filter(action="next"), IsAdmin())
    dp.register_callback_query_handler(schedule_post_confirm, admin_choose_time.filter(action="confirm"), IsAdmin())
    dp.register_callback_query_handler(show_calendar, admin_choose_time.filter(), IsAdmin())

    dp.register_callback_query_handler(previous_month, admin_calendar_clb.filter(action="previous"), IsAdmin())
    dp.register_callback_query_handler(next_month, admin_calendar_clb.filter(action="next"), IsAdmin())

    dp.register_callback_query_handler(choose_day, admin_calendar_clb.filter(action="date"), IsAdmin())
    dp.register_callback_query_handler(choose_day, admin_calendar_clb.filter(action="empty"), IsAdmin())
    dp.register_callback_query_handler(choose_hour, admin_hour_clb.filter(), IsAdmin())
    dp.register_callback_query_handler(choose_minute, admin_minute_clb.filter(), IsAdmin())
