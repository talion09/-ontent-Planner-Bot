import asyncio
import calendar
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import List

import aiohttp
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Chat, ReplyKeyboardMarkup, \
    KeyboardButton
from aiogram_media_group import media_group_handler
from babel.dates import format_date

from tg_bot import config, channel_api, subscription_api, user_api, user_channel_api, parsed_messages_api, \
    channel_for_parsing_association_api
from tg_bot.aiogram_bot.filters.is_admin import IsUserBot, IsMediaGroup
from tg_bot.aiogram_bot.handlers.users.content.content_plan import content_handler
from tg_bot.aiogram_bot.handlers.users.create.create_post import edit_post, user_channels
from tg_bot.aiogram_bot.handlers.users.settings import user_settings
from tg_bot.aiogram_bot.keyboards.default.main_menu import admin_menu, m_menu
from tg_bot.aiogram_bot.keyboards.inline.parsing import parsers_user_channel, parser_channel_delete, parser_channels, \
    add_channel_clb, parsed_post, parsed_post_media, see_parsed_post, see_parsed_post_by_date, back_to_posts, \
    back_to_parser_channels, see_parsed_post_new
from tg_bot.aiogram_bot.keyboards.inline.subscription_payment.inline_button import subscription_payment_clb
from tg_bot.aiogram_bot.network.dto.channel import ChannelSchema
from tg_bot.aiogram_bot.network.dto.channel_for_parsing_association import ChannelForParsingAssociationSchema
from tg_bot.aiogram_bot.network.dto.parsed_messages import ParsedMessagesSchema
from tg_bot.aiogram_bot.network.dto.response import Response
from tg_bot.aiogram_bot.network.dto.subscription import SubscriptionSchema
from tg_bot.aiogram_bot.network.dto.user_channel import UserChannelSchema
from tg_bot.aiogram_bot.states.users import Parsing
from tg_bot.aiogram_bot.utils.constants import PremiumSubscription
from tg_bot.aiogram_bot.utils.utils import is_telegram_channel_link, is_private_channel_link


def create_calendar(year, month, channel_for_parsing_association_id, start_date=None, end_date=None, language='ru'):
    inline_kb = InlineKeyboardMarkup(row_width=7)

    date = datetime(year, month, 1)
    month_name = format_date(date, 'LLLL YYYY', locale=language)
    # Header with month and year
    inline_kb.row(
        InlineKeyboardButton("◀️ Предыдущий", callback_data=f"prev-month_{year}_{month}_{language}"),
        InlineKeyboardButton(month_name, callback_data="current-month"),
        InlineKeyboardButton("Следующий ▶️", callback_data=f"next-month_{year}_{month}_{language}")
    )

    # Days of the week
    days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"] if language == 'en' else ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб",
                                                                                "Вс"] if language == 'ru' else ["Дш",
                                                                                                                "Сш",
                                                                                                                "Чш",
                                                                                                                "Пш",
                                                                                                                "Жм",
                                                                                                                "Шн",
                                                                                                                "Як"]
    inline_kb.row(*[InlineKeyboardButton(day, callback_data="none") for day in days])

    # Days in month
    month_calendar = calendar.monthcalendar(year, month)
    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="none"))
            else:
                day_date = datetime(year, month, day)
                button_text = f"{day}"
                if start_date and start_date.date() == day_date.date():
                    button_text = f"✅ {button_text}"
                if end_date and end_date.date() == day_date.date():
                    button_text = f"✅ {button_text}"
                row.append(InlineKeyboardButton(button_text, callback_data=f"day_{year}_{month}_{day}_{language}"))
        inline_kb.row(*row)

    # Back button
    inline_kb.row(InlineKeyboardButton("⬅️ Назад", callback_data=back_to_posts.new(
        channel_for_parsing_association_id=channel_for_parsing_association_id
    )))
    return inline_kb


def markup_parsed_not_media(channel_id):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.row(InlineKeyboardButton(
        text=f"❌ Удалить",
        callback_data=parsed_post.new(
            action="delete",
            channel_id=channel_id
        )
    ),
        InlineKeyboardButton(
            text=f"Редактировать ➡️",
            callback_data=parsed_post.new(
                action="continue",
                channel_id=channel_id
            )
        )
    )

    return markup


def markup_parsed_media(channel_id, post_id):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.row(InlineKeyboardButton(
        text=f"❌ Удалить",
        callback_data=parsed_post_media.new(
            action="delete",
            channel_id=channel_id,
            post_id=post_id
        )
    ),
        InlineKeyboardButton(
            text=f"Редактировать ➡️",
            callback_data=parsed_post_media.new(
                action="continue",
                channel_id=channel_id,
                post_id=post_id
            )
        )
    )

    return markup


async def parsed_post_continue(call: CallbackQuery, callback_data: dict, state: FSMContext):
    if call.message.photo:
        file_id = call.message.photo[-1].file_id
    elif call.message.video:
        file_id = call.message.video.file_id
    elif call.message.document:
        file_id = call.message.document.file_id
    elif call.message.audio:
        file_id = call.message.audio.file_id
    elif call.message.animation:
        file_id = call.message.animation.file_id
    elif call.message.video_note:
        file_id = call.message.video_note.file_id
    elif call.message.text:
        file_id = None

    media = []
    media_type = call.message.content_type

    if file_id:
        media_info = {
            'sequence_number': 1,
            'file_id': file_id,
            'media_type': media_type
        }

        media.append(media_info)

    entities = None
    if call.message.caption_entities:
        entities = json.dumps([entity.to_python() for entity in call.message.caption_entities])
    elif call.message.entities:
        entities = json.dumps([entity.to_python() for entity in call.message.entities])

    data = {
        "user_id": call.from_user.id,
        "description": call.message.caption if call.message.content_type != 'text' else call.message.text,
        "url_buttons": None,
        "media": media if media_type != "text" else None,
        "messages_id": None,
        "channel_id": int(callback_data['channel_id']),
        "date": None,
        "auto_delete_timer": None,
        "is_saved": True,
        "is_scheduled": False,
        "initial_post_id": None,
        "entities": entities
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                json=data) as response:
            respons = await response.json()

    await edit_post(call=call, callback_data={"post_id": respons['data']['id']}, state=state, delete=False)


async def parsed_post_delete(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.bot.delete_message(chat_id=call.from_user.id,
                                  message_id=call.message.message_id)
    await call.bot.send_message(chat_id=call.from_user.id,
                                text="Пост удалён")


async def parsed_post_media_continue(call: CallbackQuery, callback_data: dict, state: FSMContext):
    try:
        parsed_messages_response: Response[ParsedMessagesSchema] = Response[ParsedMessagesSchema].model_validate(
            await parsed_messages_api.get_one_by_key_value(
                params={
                    "key": "post_id",
                    "value": int(callback_data['post_id'])
                }
            )
        )

    except Exception as e:
        logging.error(f"ERROR {e}")

    await edit_post(call=call, callback_data=callback_data, state=state, delete=False)


async def parsed_post_media_delete(call: CallbackQuery, callback_data: dict, state: FSMContext):
    async with aiohttp.ClientSession() as session:
        async with session.delete(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/{callback_data['post_id']}/"
        ) as response:
            respns = await response.json()

    parsed_messages_response: Response[ParsedMessagesSchema] = Response[ParsedMessagesSchema].model_validate(
        await parsed_messages_api.get_one_by_key_value(
            params={
                "key": "post_id",
                "value": int(callback_data['post_id'])
            }
        )
    )

    for message in parsed_messages_response.data.messages_id:
        await call.bot.delete_message(call.from_user.id, message)

    await call.bot.delete_message(chat_id=call.from_user.id,
                                  message_id=call.message.message_id)

    await call.bot.send_message(chat_id=call.from_user.id,
                                text="Пост удалён")


async def parsing_user_channels(message: types.Message, state: FSMContext):
    await state.reset_state()
    _ = message.bot.get("lang")

    text = _("📡 <b>ПАРСИНГ</b>\n\n" \
             "В этом разделе вы можете просматривать и редактировать каналы - парсинга. Выберите канал, в котором " \
             "хотите увидеть или подключить парсинг.")

    user_channel_response: Response[list[ChannelSchema]] = Response[list[ChannelSchema]].model_validate(
        await channel_api.get_user_channels_with_certain_subscriptions(data={
            "user_id": message.from_user.id,
            "disabled": False
        }))

    if len(user_channel_response.data) > 0:
        markup = InlineKeyboardMarkup(row_width=1)
        for channel in user_channel_response.data:
            id_channel = channel.id
            channel_title = channel.title
            markup.insert(InlineKeyboardButton(text=f"{channel_title}",
                                               callback_data=parsers_user_channel.new(channel_id=id_channel,
                                                                                      action="none")))
        await message.bot.send_message(message.from_user.id, text, reply_markup=markup)
    else:
        inline = InlineKeyboardMarkup(row_width=1)
        inline.insert(InlineKeyboardButton(text="➕ Добавить новый канал", callback_data=add_channel_clb.new()))
        await message.bot.send_message(message.from_user.id, text, reply_markup=inline)


async def back_to_parsing(call: CallbackQuery):
    await call.answer()
    _ = call.bot.get("lang")

    data = {"user_id": call.from_user.id,
            "disabled": False}
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel/get_user_channels_with_certain_subscriptions/",
                json=data) as response:
            response1 = await response.json()

    markup = InlineKeyboardMarkup(row_width=1)
    text = _("📡 <b>ПАРСИНГ</b>\n\n" \
             "В этом разделе вы можете просматривать и редактировать каналы - парсинга. Выберите канал, в котором " \
             "хотите увидеть или подключить парсинг.")

    for channel in response1.get('data'):
        id_channel = int(channel.get("id"))
        channel_title = channel.get("title")
        markup.insert(InlineKeyboardButton(text=f"{channel_title}",
                                           callback_data=parsers_user_channel.new(channel_id=id_channel,
                                                                                  action="none")))

    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def parsing_user_channel(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    id_channel = int(callback_data.get("channel_id"))
    markup = InlineKeyboardMarkup(row_width=2)

    channel_data = {"id": id_channel}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel/one/",
                                json=channel_data) as response:
            response1 = await response.json()
            channel_title = response1.get("data").get("title")

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

    if subscription_id is None or int(subscription_id) == 1:
        subscription_response: Response[SubscriptionSchema] = Response[SubscriptionSchema].model_validate(
            await subscription_api.get_one_by_key_value(
                params={"key": "id", "value": 2}
            ))

        month_price = subscription_response.data.price[str("1")]

        text = _("💰 ОПЛАТА ПОДПИСКИ\n\n" \
                 "Чтобы пользоваться парсингом в канале {} вам нужно перейти на платную подписку\n\nКонечная стоимость: {}₽<a href='{}'>&#8203;</a>").format(
            channel_title, month_price, PremiumSubscription)
        markup = InlineKeyboardMarkup(row_width=1)
        pay_btn = _("💰 Перейти к оплате")
        Back = _("⬅️ Назад")
        markup.add(InlineKeyboardButton(text=pay_btn,
                                        callback_data=subscription_payment_clb.new(
                                            a="c",
                                            p=f'{str(id_channel).replace("-100", "")}',
                                            t="g"
                                        )))
        markup.add(InlineKeyboardButton(text=Back,
                                        callback_data=parsers_user_channel.new(channel_id=id_channel, action="back_1")))
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
    else:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing_association/all/",
                    json=data) as response:
                response4 = await response.json()
                channels_for_parsing = response4.get("data")
                amount = len(channels_for_parsing)

        text = _("📡 <b>ПАРСИНГ</b>\n\n" \
                 "В канале {} парсеров ({} шт.). " \
                 "Чтобы посмотреть или удалить парсеры воспользуйтесь кнопками ниже.").format(channel_title, amount)
        for item in channels_for_parsing:
            channel_for_parsing_id = int(item['channel_for_parsing_id'])
            data = {"id": channel_for_parsing_id}
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing/one/",
                        json=data) as response:
                    response5 = await response.json()

            parser_title = response5.get("data").get("title")
            markup.insert(InlineKeyboardButton(text=f"{parser_title}",
                                               callback_data=parser_channels.new(id=channel_for_parsing_id,
                                                                                 channel_id=id_channel,
                                                                                 action="show_parser_channel")))
        add_btn = _("➕ Добавить парсер канал")
        Back = _("⬅️ Назад")
        markup.insert(InlineKeyboardButton(text=add_btn,
                                           callback_data=parsers_user_channel.new(channel_id=id_channel, action="add")))
        markup.add(InlineKeyboardButton(text=Back,
                                        callback_data=parsers_user_channel.new(channel_id=id_channel, action="back_1")))
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def parser_channel(call: CallbackQuery, callback_data: dict):
    _ = call.bot.get("lang")
    id_channel_for_parsing = int(callback_data.get("id"))
    id_channel = int(callback_data.get("channel_id"))

    await call.answer()

    markup = InlineKeyboardMarkup(row_width=1)

    data = {
        "channel_for_parsing_id": id_channel_for_parsing,
        "channel_id": id_channel,
        "user_id": call.from_user.id
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing_association/one/",
                json=data) as response:
            channel_for_parsing_association_response = await response.json()

    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing/one/",
                json={'id': id_channel_for_parsing}
        ) as response:
            channel_for_parsing_response = await response.json()

    parser_title = channel_for_parsing_response.get("data").get("title")

    text = _("📡 ПАРСЕР КАНАЛ\n\n" \
             "Спарсшеные посты с канала {}").format(parser_title)
    check_posts = _("Посмотреть посты")
    delete = _("❌ Удалить")
    Back = _("⬅️ Назад")

    markup.add(InlineKeyboardButton(text=check_posts,
                                    callback_data=see_parsed_post.new(channel_for_parsing_association_id=
                                                                      channel_for_parsing_association_response[
                                                                          'data']['id'])))
    markup.insert(InlineKeyboardButton(text=delete,
                                       callback_data=parser_channel_delete.new(id=id_channel_for_parsing,
                                                                               channel_id=id_channel,
                                                                               action="delete")))
    markup.add(InlineKeyboardButton(text=Back,
                                    callback_data=parsers_user_channel.new(channel_id=id_channel, action="back_2")))
    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def parsing_delete_confirm(call: CallbackQuery, callback_data: dict):
    _ = call.bot.get("lang")
    id_channel_for_parsing = int(callback_data.get("id"))
    id_channel = int(callback_data.get("channel_id"))

    await call.answer()
    markup = InlineKeyboardMarkup(row_width=1)

    text = _("Вы уверены, что хотите удалить выбранный парсер-канал?")
    delete = _("Да, удалить")
    Back = _("⬅️ Назад")
    markup.insert(InlineKeyboardButton(text=delete,
                                       callback_data=parser_channel_delete.new(id=id_channel_for_parsing,
                                                                               channel_id=id_channel,
                                                                               action="confirm_delete")))
    markup.insert(InlineKeyboardButton(text=Back, callback_data=parser_channels.new(id=id_channel_for_parsing,
                                                                                    channel_id=id_channel,
                                                                                    action="back_3")))

    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def parsing_deleted(call: CallbackQuery, callback_data: dict):
    _ = call.bot.get("lang")
    id_channel_for_parsing = int(callback_data.get("id"))
    id_channel = int(callback_data.get("channel_id"))

    # await call.answer()

    data = {"channel_id": id_channel,
            "channel_for_parsing_id": id_channel_for_parsing}

    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing_association/all/",
                json=data) as response:
            channel_for_parsing_association_response = await response.json()

    for obj in channel_for_parsing_association_response.get("data"):
        id = obj.get("id")
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing_association/{id}/") as response:
                response2 = await response.json()

    text = _("✅ Вы успешно удалили парсер-канал")
    await call.bot.answer_callback_query(call.id, text, show_alert=True)
    await back_to_parsing(call)


async def parsing_add(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()
    _ = call.bot.get("lang")
    id_channel = int(callback_data.get("channel_id"))

    data = {"user_id": call.from_user.id,
            "channel_id": id_channel}
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing_association/all/",
                json=data) as response:
            response1 = await response.json()
            channels_for_parsing = response1.get("data")
            amount = len(channels_for_parsing)

    markup = InlineKeyboardMarkup(row_width=1)
    Back = _("⬅️ Назад")
    if amount >= 3:
        text = _('<b>ПРЕВЫШЕНЫ ЛИМИТЫ</b>\n\n' \
                 'Кол-во парсер каналов: 3 шт.\n\n' \
                 'Удалите добавленные вами парсер каналы, чтобы добавить новый')
        markup.add(InlineKeyboardButton(text=Back,
                                        callback_data=parsers_user_channel.new(channel_id=id_channel,
                                                                               action="back_2")))
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
        return

    markup = InlineKeyboardMarkup(row_width=1)

    text = _("Чтобы добавить парсер-канал, отправьте ссылку на него в формате:\n\n" \
             "<b>https://t.me/link.com \n" \
             "https://t.me/channelname \n" \
             "@channelname</b>\n\n" \
             "Или перешлите любое сообщение из канала в диалог с ботом.")
    markup.add(InlineKeyboardButton(text=Back,
                                    callback_data=parsers_user_channel.new(channel_id=id_channel, action="back_2")))

    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
    await Parsing.Link.set()
    await state.update_data(id_channel=id_channel)


# Parsing.Link
async def parsing_add_link(message: types.Message, state: FSMContext):
    data = await state.get_data()
    _ = message.bot.get("lang")
    id_channel = int(data.get("id_channel"))
    add_parser = False
    create_txt = _("Создать пост")
    content_txt = _("Контент-план")
    parsing_txt = _("Парсинг")
    settings_txt = _("Настройки")

    if message.text == create_txt:
        await user_channels(message=message, state=state)
        return
    elif message.text == content_txt:
        await content_handler(message=message, state=state)
        return
    elif message.text == parsing_txt:
        await parsing_user_channels(message=message, state=state)
        return
    elif message.text == settings_txt:
        await user_settings(message=message, state=state)
        return

    if message.content_type == "text":
        text = message.text
    else:
        text = message.caption

    if is_telegram_channel_link(text):
        link = text
        add_parser = True

    elif text[0] == "@":
        link = text
        add_parser = True
        channel_info = await message.bot.get_chat(link)
        link = f"https://t.me/{channel_info.username}"

    elif is_private_channel_link(text):
        link = text
        add_parser = True

    elif message.forward_from_chat and message.forward_from_chat.type == types.ChatType.CHANNEL:
        channel_info = message.forward_from_chat
        if channel_info.username:
            link = f"https://t.me/{channel_info.username}"
            add_parser = True
        else:
            text = _("Введите ссылку на приглашение, так как это приватный канал\nПример: https://t.me/+4MqtJfmbfzowNzcy")
            await message.answer(text)
            return
    else:
        text = _("Вы отправили неверную ссылку")
        await message.answer(text)
        await state.reset_state()

    if add_parser is True:
        data = {"link": link}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing/one/",
                    json=data) as response:
                response2 = await response.json()
                status = response2.get("status")

        if status == "error":
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        url=f"http://{config.api.api_db}:{config.api.api_db_port}/telethon/telethon_users/") as response:
                    response3 = await response.json()

            if response3.get('data') is not None:
                user_bot_id = int(response3.get('data')[-1]["user_id"])

                data = {
                    "message": "Join to channel",
                    "user_bot_id": user_bot_id,
                    "channel_id": id_channel,
                    "user_id": message.from_user.id,
                    "parser_link": link
                }
                await message.bot.send_message(user_bot_id, json.dumps(data))
        else:
            parser_id = response2.get("data").get('id')
            parser_title = response2.get("data").get('title')
            parser_link = response2.get("data").get('link')

            user_channel_response: Response[list[UserChannelSchema]] = Response[
                list[UserChannelSchema]].model_validate(
                await user_channel_api.post_all(data={
                    "channel_id": id_channel
                }))

            for user_channel in user_channel_response.data:
                data = {"channel_id": user_channel.channel_id, "channel_for_parsing_id": parser_id,
                        "user_id": user_channel.user_id}
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                            url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing_association/",
                            json=data) as response:
                        response4 = await response.json()

                if user_channel.user_id == message.from_user.id:
                    if response4.get('status') == "success":
                        await message.bot.send_message(message.from_user.id,
                                                       f"✅ Вы успешно подключили парсер-канал <a href='{parser_link}'>{parser_title if parser_title is not None else 'название отсутствует'}</a> к HarvestlyBot")
                    else:
                        await message.bot.send_message(message.from_user.id,
                                                       f"У Вас уже подключен парсер-канал {parser_title if parser_title is not None else 'название отсутствует'} к HarvestlyBot")

        await state.reset_state()
    else:
        text = _("Вы отправили неверную ссылку")
        await message.answer(text)
        await state.reset_state()


@media_group_handler
async def parsing_add_link_media_group(messages: list[types.Message], state: FSMContext):
    data = await state.get_data()
    _ = messages[0].bot.get("lang")
    id_channel = int(data.get("id_channel"))
    add_parser = False

    if messages[0].forward_from_chat and messages[0].forward_from_chat.type == types.ChatType.CHANNEL:
        channel_info = messages[0].forward_from_chat

        if channel_info.username:
            link = f"https://t.me/{channel_info.username}"
            add_parser = True
        else:
            text = _("Введите ссылку на приглашение, так как это приватный канал\nПример: https://t.me/+4MqtJfmbfzowNzcy")
            await messages[0].answer(text)
            return
    else:
        text = _("Вы отправили неверную ссылку")
        await messages[0].answer(text)
        await state.reset_state()

    if add_parser is True:
        data = {"link": link}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing/one/",
                    json=data) as response:
                response2 = await response.json()
                status = response2.get("status")

        if status == "error":
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        url=f"http://{config.api.api_db}:{config.api.api_db_port}/telethon/telethon_users/") as response:
                    response3 = await response.json()

            if response3.get('data') is not None:
                user_bot_id = int(response3.get('data')[-1]["user_id"])

                data = {
                    "message": "Join to channel",
                    "user_bot_id": user_bot_id,
                    "channel_id": id_channel,
                    "user_id": messages[0].from_user.id,
                    "parser_link": link
                }
                await messages[0].bot.send_message(user_bot_id, json.dumps(data))
        else:
            parser_id = response2.get("data").get('id')
            parser_title = response2.get("data").get('title')
            parser_link = response2.get("data").get('link')

            user_channel_response: Response[list[UserChannelSchema]] = Response[
                list[UserChannelSchema]].model_validate(
                await user_channel_api.post_all(data={
                    "channel_id": id_channel
                }))

            for user_channel in user_channel_response.data:
                data = {"channel_id": user_channel.channel_id, "channel_for_parsing_id": parser_id,
                        "user_id": user_channel.user_id}
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                            url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing_association/",
                            json=data) as response:
                        response4 = await response.json()

                if user_channel.user_id == messages[0].from_user.id:
                    if response4.get('status') == "success":
                        await messages[0].bot.send_message(messages[0].from_user.id,
                                                           f"✅ Вы успешно подключили парсер-канал <a href='{parser_link}'>{parser_title if parser_title is not None else 'название отсутствует'}</a> к HarvestlyBot")
                    else:
                        await messages[0].bot.send_message(messages[0].from_user.id,
                                                           f"У Вас уже подключен парсер-канал {parser_title if parser_title is not None else 'название отсутствует'} к HarvestlyBot")

        await state.reset_state()
    else:
        text = _("Вы отправили неверную ссылку")
        await messages[0].answer(text)
        await state.reset_state()


async def back_to_parsing_2(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.reset_state()
    await call.answer()
    await parsing_user_channel(call, callback_data)


async def add_parser_channel(message: types.Message):
    data = json.loads(message.text)
    _ = message.bot.get("lang")

    user_id = int(data['data']['user_id'])
    channel_id = int(data['data']['channel_id'])
    parser_link = data['data']['parser_link']
    parser_id = int(data['data']['parser_id'])
    title = data['data']['parser_title']
    details = data['details']

    if details == "user_bot subscribed to channel":
        send_text = _("✅ Вы успешно подключили парсер-канал <a href='https://t.me/{}'>{}</a> к HarvestlyBot").format(parser_link, title)
    elif details == "successfully requested to join channel":
        send_text = _("✅ Заявка на вступление была принята <a href='https://t.me/{}'>{}</a>.\nКак только вашу заявку одобрят, вам придет сообщение😀").format(parser_link, title)
        await message.bot.send_message(user_id, send_text, parse_mode="HTML")
        return
    else:
        send_text = f"{details}"
        await message.bot.send_message(user_id, send_text, parse_mode="HTML")
        return

    data = {
        "id": parser_id,
        "link": parser_link,
        "title": title
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing/",
                                json=data) as response:
            response1 = await response.json()

    user_channel_response: Response[list[UserChannelSchema]] = Response[list[UserChannelSchema]].model_validate(
        await user_channel_api.post_all(data={
            "channel_id": channel_id
        }))

    for user_channel in user_channel_response.data:
        data = {
            "channel_id": user_channel.channel_id,
            "channel_for_parsing_id": parser_id,
            "user_id": user_channel.user_id
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing_association/",
                    json=data) as response:
                response2 = await response.json()

        if user_channel.user_id == user_id:
            if response2.get('status') == "success":
                await message.bot.send_message(user_id, send_text, parse_mode="HTML")
            else:
                text = _("У Вас уже подключен парсер-канал {} к HarvestlyBot").format(title)
                await message.bot.send_message(user_id, text)


async def channel_doesnt_exist(message: types.Message):
    data = json.loads(message.text)
    _ = message.bot.get("lang")
    user_id = int(data['data']['user_id'])
    text = _("Такого канала не существует")
    await message.bot.send_message(user_id, text)


async def message_from_parser_channel(message: types.Message):
    if message.content_type == "text":
        data = json.loads(message.text.split("\n\n")[-1])
    else:
        data = json.loads(message.caption.split("\n\n")[-1])

    if 'parser_channel_id' in data:
        parser_channel_id = data['parser_channel_id']
    elif 'channel_for_parsing_association_id' in data:
        channel_for_parsing_association_response: Response[ChannelForParsingAssociationSchema] = Response[
            ChannelForParsingAssociationSchema].model_validate(
            await channel_for_parsing_association_api.post_one(data={"id": data['channel_for_parsing_association_id']})
        )
        parser_channel_id = channel_for_parsing_association_response.data.channel_for_parsing_id

    get_users_with_specific_subscription_response: Response[list[UserChannelSchema]] = Response[
        list[UserChannelSchema]].model_validate(
        await user_api.get_users_with_specific_subscription(data={
            "channel_for_parsing_id": parser_channel_id,
            "subscription_id": 2
        })
    )

    if 'parser_channel_id' in data:
        for response in get_users_with_specific_subscription_response.data:
            try:
                await send_parsed_post_not_media(message=message, response=response)
            except Exception as e:
                logging.error(f"{e}")
    elif 'channel_for_parsing_association_id' in data:
        user_channel_schema_response: Response[UserChannelSchema] = Response[UserChannelSchema].model_validate(
            await user_channel_api.post_one(data={
                "channel_id": channel_for_parsing_association_response.data.channel_id,
                "user_id": channel_for_parsing_association_response.data.user_id
            })
        )
        await send_parsed_post_not_media(message=message, response=user_channel_schema_response.data)


@media_group_handler
async def media_group_handler(messages: List[types.Message]):
    media_message = types.MediaGroup()
    caption = ""
    for message in messages:
        if message.caption is not None:
            caption = message.caption.split("\n\n")[-1]

        if message.content_type == "photo":
            media_message.attach(
                types.InputMediaPhoto(
                    message.photo[0].file_id,
                    caption=message.caption.replace(message.caption.split("\n\n")[-1],
                                                    "") if message.caption is not None else None,
                    caption_entities=message.caption_entities
                )
            )
        elif message.content_type == "video":
            media_message.attach_video(
                video=types.InputMediaVideo(message.video.file_id,
                                            caption=message.caption.replace(message.caption.split("\n\n")[-1],
                                                                            "") if message.caption is not None else None,
                                            caption_entities=message.caption_entities if message.caption_entities else None
                                            )
            )
        elif message.content_type == "audio":
            media_message.attach_audio(audio=types.InputMediaAudio(message.audio.file_id,
                                                                   caption=message.caption.replace(
                                                                       message.caption.split("\n\n")[-1],
                                                                       "") if message.caption is not None else None,
                                                                   caption_entities=message.caption_entities))
        elif message.content_type == "document":
            media_message.attach_document(document=types.InputMediaDocument(message.document.file_id,
                                                                            caption=message.caption.replace(
                                                                                message.caption.split("\n\n")[-1],
                                                                                "") if message.caption is not None else None,
                                                                            caption_entities=message.caption_entities))

        elif message.content_type == "animation":
            media_message.attach(media=types.InputMediaAnimation(message.animation.file_id,
                                                                 caption=message.caption.replace(
                                                                     message.caption.split("\n\n")[-1],
                                                                     "") if message.caption is not None else None,
                                                                 caption_entities=message.caption_entities))

    data = json.loads(caption)

    if 'channel_for_parsing_association_id' in data:
        channel_for_parsing_association_response: Response[ChannelForParsingAssociationSchema] = Response[
            ChannelForParsingAssociationSchema].model_validate(
            await channel_for_parsing_association_api.post_one(data={"id": data['channel_for_parsing_association_id']})
        )
        parser_channel_id = channel_for_parsing_association_response.data.channel_for_parsing_id
    elif 'parser_channel_id' in data:
        parser_channel_id = data['parser_channel_id']

    get_users_with_specific_subscription_response: Response[list[UserChannelSchema]] = Response[
        list[UserChannelSchema]].model_validate(
        await user_api.get_users_with_specific_subscription(data={
            "channel_for_parsing_id": parser_channel_id,
            "subscription_id": 2
        })
    )

    if 'parser_channel_id' in data:
        for response in get_users_with_specific_subscription_response.data:
            try:
                await send_parsed_post_media(messages=messages, response=response, media_message=media_message)
            except Exception as e:
                logging.error(f"{e}")
    elif 'channel_for_parsing_association_id' in data:
        user_channel_schema_response: Response[UserChannelSchema] = Response[UserChannelSchema].model_validate(
            await user_channel_api.post_one(data={
                "channel_id": channel_for_parsing_association_response.data.channel_id,
                "user_id": channel_for_parsing_association_response.data.user_id
            })
        )

        await send_parsed_post_media(messages=messages, response=user_channel_schema_response.data,
                                     media_message=media_message)


async def get_posts_length(message: types.Message):
    _ = message.bot.get("lang")
    data = json.loads(message.text)
    channel_for_parsing_association_id = int(data['data']['id'])

    data = {"id": channel_for_parsing_association_id}
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing_association/one/",
                json=data) as response:
            channel_for_parsing_association_response = await response.json()

    channel_for_parsing_id = channel_for_parsing_association_response.get('data').get('channel_for_parsing_id')
    channel_id = channel_for_parsing_association_response.get('data').get('channel_id')

    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing/one/",
                json={"id": channel_for_parsing_association_response.get('data').get(
                    'channel_for_parsing_id')}
        ) as response:
            channel_for_parsing_response = await response.json()

    markup = InlineKeyboardMarkup(row_width=1)
    post_quantity = channel_for_parsing_association_response['data']['quantity_of_parsed_message']
    parser_title = channel_for_parsing_response.get("data").get("title")

    text = ("📡 ПАРСЕР КАНАЛ\n\n" \
            "Кол-во спарсшеных постов с канала {}").format(parser_title)
    option_1 = _("Посмотреть новые посты ({} шт.)").format(post_quantity)
    option_2 = _("Посмотреть посты по дате")
    Back = _("⬅️ Назад")
    markup.add(InlineKeyboardButton(text=option_1,
                                    callback_data=see_parsed_post_new.new(channel_for_parsing_association_id=
                                                                          channel_for_parsing_association_response[
                                                                              'data']['id'])))

    markup.add(InlineKeyboardButton(text=option_2,
                                    callback_data=see_parsed_post_by_date.new(channel_for_parsing_association_id=
                                                                              channel_for_parsing_association_response[
                                                                                  'data']['id'])))

    markup.add(InlineKeyboardButton(text=Back, callback_data=back_to_parser_channels.new(
        id=channel_for_parsing_id,
        channel_id=channel_id
    )))

    await message.bot.send_message(chat_id=channel_for_parsing_association_response['data']['user_id'], text=text,
                                   reply_markup=markup)

    # text = f"📡 ПАРСЕР КАНАЛ\n\n" \
    #        f"Кол-во спарсшеных постов с канала {parser_title}: ({post_quantity} шт.)"
    #
    # markup.add(InlineKeyboardButton(text=f"Посмотреть посты ({post_quantity} шт.)",
    #                                 callback_data=see_parsed_post.new(
    #                                     channel_for_parsing_association_id=
    #                                     channel_for_parsing_association_response['data']['id'])
    #                                 ))
    # markup.insert(InlineKeyboardButton(text=f"❌ Удалить",
    #                                    callback_data=parser_channel_delete.new(
    #                                        id=channel_for_parsing_association_response['data'][
    #                                            'channel_for_parsing_id'],
    #                                        channel_id=channel_for_parsing_association_response['data']['channel_id'],
    #                                        action="delete")))
    # markup.add(InlineKeyboardButton(text=f"⬅️ Назад",
    #                                 callback_data=parsers_user_channel.new(
    #                                     channel_id=channel_for_parsing_association_response['data']['channel_id'],
    #                                     action="back_2")))
    # await message.bot.send_message(chat_id=channel_for_parsing_association_response['data']['user_id'], text=text,
    #                                reply_markup=markup)


async def parsed_posts_show(call: CallbackQuery, callback_data: dict):
    _ = call.bot.get("lang")
    channel_for_parsing_association_id = int(callback_data['channel_for_parsing_association_id'])
    markup = InlineKeyboardMarkup(row_width=1)

    data = {
        "id": channel_for_parsing_association_id
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing_association/one/",
                json=data) as response:
            channel_for_parsing_association_response = await response.json()

    channel_for_parsing_id = channel_for_parsing_association_response.get('data').get('channel_for_parsing_id')
    channel_id = channel_for_parsing_association_response.get('data').get('channel_id')

    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing/one/",
                json={
                    "id": channel_for_parsing_association_response.get('data').get('channel_for_parsing_id')
                }) as response:
            channel_for_parsing_response = await response.json()

    if channel_for_parsing_association_response.get("data").get("last_time_view_posts_tapped") is None:
        post_quantity = 0

        parser_title = channel_for_parsing_response.get("data").get("title")

        text = ("📡 ПАРСЕР КАНАЛ\n\n" \
                "Кол-во спарсшеных постов с канала {}").format(parser_title)
        option_1 = _("Посмотреть новые посты ({} шт.)").format(post_quantity)
        option_2 = _("Посмотреть посты по дате")
        Back = _("⬅️ Назад")

        markup.add(InlineKeyboardButton(text=option_1,
                                        callback_data=see_parsed_post_new.new(channel_for_parsing_association_id=
                                                                              channel_for_parsing_association_response[
                                                                                  'data']['id'])))

        markup.add(InlineKeyboardButton(text=option_2,
                                        callback_data=see_parsed_post_by_date.new(channel_for_parsing_association_id=
                                                                                  channel_for_parsing_association_response[
                                                                                      'data']['id'])))

        markup.add(InlineKeyboardButton(text=Back, callback_data=back_to_parser_channels.new(
            id=channel_for_parsing_id,
            channel_id=channel_id
        )))

        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)

    else:
        text = _("Пожалуйста подождите")
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id,
                                         reply_markup=markup)

        data = {
            "message": "Get posts length",
            "parser_link": channel_for_parsing_response['data']['link'],
            "channel_for_parsing_association_id": channel_for_parsing_association_id
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/telethon/user/find/",
                    json={"active": True}
            ) as response:
                telethon_user_response = await response.json()

        if telethon_user_response.get('data') is not None:
            user_bot_id = telethon_user_response.get("data").get("user_id")

        await call.bot.send_message(user_bot_id, json.dumps(data))


async def send_parsed_post_media(messages: list[types.Message], response: UserChannelSchema,
                                 media_message: types.MediaGroup | list):
    msg: list[types.Message] = await messages[0].bot.send_media_group(chat_id=response.user_id,
                                                                      media=media_message)
    await asyncio.sleep(0.1)
    await messages[0].bot.pin_chat_message(chat_id=response.user_id, message_id=msg[0].message_id)

    if len(messages) <= 10:
        media = []
        sequence_number = 1
        for m in messages:
            if m.photo:
                file_id = m.photo[0].file_id
            elif m.video:
                file_id = m.video.file_id
            elif m.document:
                file_id = m.document.file_id
            elif m.audio:
                file_id = m.audio.file_id

            media_info = {
                'sequence_number': sequence_number,
                'file_id': file_id,
                'media_type': m.content_type}

            media.append(media_info)
            sequence_number += 1

    data = {
        "user_id": messages[0].from_user.id,
        "description": messages[0].caption.replace("\n\n" + messages[0].caption.split("\n\n")[-1],
                                                   "") if messages[0].caption is not None else None,
        "url_buttons": None,
        "media": media,
        "messages_id": None,
        "channel_id": response.channel_id,
        "date": None,
        "auto_delete_timer": None,
        "is_saved": True,
        "is_scheduled": False,
        "initial_post_id": None,
        "entities": json.dumps([entity.to_python() for entity in messages[0].caption_entities])
        if messages[0].caption_entities else None
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                json=data) as response_post:
            respons = await response_post.json()

    await messages[0].bot.send_message(chat_id=response.user_id, text="Выберите дейтсвие",
                                       reply_markup=markup_parsed_media(channel_id=response.channel_id,
                                                                        post_id=respons['data']['id']))

    await parsed_messages_api.post_add(data={
        "post_id": respons['data']['id'],
        "messages_id": [obj.message_id for obj in msg]
    })

    await asyncio.sleep(0.1)


async def send_parsed_post_not_media(message: types.Message, response: UserChannelSchema):
    if message.content_type == "photo":
        msg = await message.bot.send_photo(
            chat_id=response.user_id,
            photo=message.photo[-1].file_id,
            caption=message.caption.replace("\n\n" + message.caption.split("\n\n")[-1], ""),
            reply_markup=markup_parsed_not_media(channel_id=response.channel_id),
            caption_entities=message.caption_entities
        )

    elif message.content_type == "video":
        msg = await message.bot.send_video(
            response.user_id,
            message.video.file_id,
            caption=message.caption.replace("\n\n" + message.caption.split("\n\n")[-1], ""),
            reply_markup=markup_parsed_not_media(channel_id=response.channel_id),
            caption_entities=message.caption_entities
        )

    elif message.content_type == "document":
        msg = await message.bot.send_document(
            response.user_id,
            message.document.file_id,
            caption=message.caption.replace("\n\n" + message.caption.split("\n\n")[-1], ""),
            reply_markup=markup_parsed_not_media(channel_id=response.channel_id),
            caption_entities=message.caption_entities
        )

    elif message.content_type == "audio":
        msg = await message.bot.send_audio(
            response.user_id,
            message.audio.file_id,
            caption=message.caption.replace("\n\n" + message.caption.split("\n\n")[-1], ""),
            reply_markup=markup_parsed_not_media(channel_id=response.channel_id),
            caption_entities=message.caption_entities
        )

    elif message.content_type == "animation":
        msg = await message.bot.send_animation(
            response.user_id,
            message.animation.file_id,
            caption=message.caption.replace("\n\n" + message.caption.split("\n\n")[-1], ""),
            reply_markup=markup_parsed_not_media(channel_id=response.channel_id),
            caption_entities=message.caption_entities
        )

    elif message.content_type == "video_note":
        msg = await message.bot.send_video_note(
            response.user_id,
            message.video_note.file_id,
            reply_markup=markup_parsed_not_media(channel_id=response.channel_id)
        )

    elif message.content_type == "text":
        msg = await message.bot.send_message(
            response.user_id,
            text=message.text.replace("\n\n" + message.text.split("\n\n")[-1], ""),
            reply_markup=markup_parsed_not_media(channel_id=response.channel_id),
            entities=message.entities
        )

    await asyncio.sleep(0.1)

    await message.bot.pin_chat_message(chat_id=response.user_id, message_id=msg.message_id)


async def see_parsed_post_by_date_func(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.finish()
    _ = call.bot.get("lang")
    await Parsing.DateRangePickerStart.set()

    channel_for_parsing_association_id = int(callback_data['channel_for_parsing_association_id'])
    await state.update_data(channel_for_parsing_association_id=channel_for_parsing_association_id)

    data = {
        "id": call.from_user.id
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/one/",
                json=data) as response:
            user_response = await response.json()

    now = datetime.utcnow() + timedelta(hours=user_response.get('data').get('time_zone'))
    text = _("Выберите дату начала:")
    await call.bot.edit_message_text(text=text,
                                     chat_id=call.from_user.id,
                                     message_id=call.message.message_id,
                                     reply_markup=create_calendar(now.year,
                                                                  now.month,
                                                                  channel_for_parsing_association_id))


async def choose_start_date(query: types.CallbackQuery, state: FSMContext):
    _ = query.bot.get("lang")
    _, year, month, day, language = query.data.split('_')
    start_date = datetime(int(year), int(month), int(day))

    user_data = await state.get_data()
    channel_for_parsing_association_id = user_data.get('channel_for_parsing_association_id')

    await state.update_data(start_date=start_date)
    await Parsing.DateRangePickerEnd.set()
    text = _("Выберите конечную дату:\n\nДата начала: {}").format(start_date)
    await query.bot.edit_message_text(text=text,
                                      chat_id=query.from_user.id,
                                      message_id=query.message.message_id,
                                      reply_markup=create_calendar(int(year),
                                                                   int(month),
                                                                   channel_for_parsing_association_id=channel_for_parsing_association_id,
                                                                   language=language,
                                                                   start_date=start_date))


async def choose_end_date(query: types.CallbackQuery, state: FSMContext):
    _, year, month, day, language = query.data.split('_')
    end_date = datetime(int(year), int(month), int(day))

    user_data = await state.get_data()
    start_date = user_data.get('start_date')
    channel_for_parsing_association_id = user_data.get('channel_for_parsing_association_id')

    text = _("Парсинг начался\nПожалуйста подождите\n\nНачальная дата: {start_date.date()}\nКонечная дата: {end_date.date()}").format(start_date.date(), end_date.date())
    await query.bot.edit_message_text(
        text=text,
        chat_id=query.from_user.id,
        message_id=query.message.message_id
    )
    await state.finish()

    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/one/",
                json={"id": query.from_user.id}
        ) as response:
            user_response = await response.json()

    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing_association/one/",
                json={"id": channel_for_parsing_association_id}
        ) as response:
            channel_for_parsing_association_response = await response.json()

    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing/one/",
                json={"id": channel_for_parsing_association_response.get('data').get('channel_for_parsing_id')}
        ) as response:
            channel_for_parsing_response = await response.json()

    data = {
        "message": "Get posts by date",
        "parser_link": channel_for_parsing_response['data']['link'],
        "channel_for_parsing_association_id": channel_for_parsing_association_id,
        "start_date": (start_date - timedelta(hours=user_response.get('data').get('time_zone'))).replace(
            tzinfo=timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
        "end_date": (end_date - timedelta(hours=user_response.get('data').get('time_zone'))).replace(
            tzinfo=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/telethon/user/find/",
                json={"active": True}
        ) as response:
            telethon_user_response = await response.json()

    if telethon_user_response.get('data') is not None:
        user_bot_id = telethon_user_response.get("data").get("user_id")

    await query.bot.send_message(user_bot_id, json.dumps(data))

    await asyncio.sleep(1)
    button_txt = _("Остановить парсинг")
    mark_up = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=button_txt)
            ]
        ],
        resize_keyboard=True)

    text = _("Нажмите на кнопку, чтобы остановить парсинг")
    await query.bot.send_message(chat_id=query.from_user.id,
                                 text=text,
                                 reply_markup=mark_up)


async def handle_month_callback(query: types.CallbackQuery, state: FSMContext):
    action, year, month, language = query.data.split('_')
    year, month = int(year), int(month)

    user_data = await state.get_data()
    channel_for_parsing_association_id = user_data.get('channel_for_parsing_association_id')

    if action == 'prev-month':
        new_month = (month - 1) % 12 or 12
        year = year - 1 if month == 1 else year
    else:
        new_month = (month + 1) % 12 or 12
        year = year + 1 if month == 12 else year

    await query.message.edit_reply_markup(
        create_calendar(year,
                        new_month,
                        channel_for_parsing_association_id=channel_for_parsing_association_id,
                        language=language))


async def handle_back(query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await state.finish()
    channel_for_parsing_association_id = callback_data['channel_for_parsing_association_id']
    await parsed_posts_show(call=query, callback_data={
        'channel_for_parsing_association_id': channel_for_parsing_association_id
    })


async def see_parsed_post_new_handler(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get("lang")
    channel_for_parsing_association_id = int(callback_data['channel_for_parsing_association_id'])

    data = {
        "id": channel_for_parsing_association_id
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing_association/one/",
                json=data) as response:
            channel_for_parsing_association_response = await response.json()

    quantity_of_parsed_messages = channel_for_parsing_association_response.get('data').get(
        'channel_for_parsing_association_response')
    no_exist_posts = _("Новых постов нету")
    if quantity_of_parsed_messages is None:
        await call.bot.send_message(chat_id=call.from_user.id, text=no_exist_posts)
        return
    if quantity_of_parsed_messages == 0:
        await call.bot.send_message(chat_id=call.from_user.id, text=no_exist_posts)
        return

    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing/one/",
                json={"id": channel_for_parsing_association_response.get('data').get(
                    'channel_for_parsing_id')}
        ) as response:
            channel_for_parsing_response = await response.json()

    data = {
        "message": "Get posts",
        "parser_link": channel_for_parsing_response['data']['link'],
        "channel_for_parsing_association_id": channel_for_parsing_association_id
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/telethon/user/find/",
                json={"active": True}
        ) as response:
            telethon_user_response = await response.json()

    if telethon_user_response.get('data') is not None:
        user_bot_id = telethon_user_response.get("data").get("user_id")

    await call.bot.send_message(user_bot_id, json.dumps(data))

    await asyncio.sleep(1)
    button_txt = _("Остановить парсинг")

    mark_up = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=button_txt)
            ]
        ],
        resize_keyboard=True)

    text = _("Нажмите на кнопку, чтобы остановить парсинг")
    await call.bot.send_message(chat_id=call.from_user.id,
                                text=text,
                                reply_markup=mark_up)


async def stop_parsing(message: types.Message):
    _ = message.bot.get("lang")
    async with aiohttp.ClientSession() as session:
        async with session.put(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/",
                json={
                    "id": message.from_user.id,
                    "parsing_stopped": True
                }
        ) as response:
            user_response = await response.json()

    admins_list = [1574853044, 1696518783]
    user_id = message.from_user.id
    if user_id in admins_list:
        menu = admin_menu
    else:
        menu = m_menu

    text = _("Парсинг остановлен")
    await message.bot.send_message(chat_id=message.from_user.id, text=text, reply_markup=menu)


def register_parsing(dp: Dispatcher):
    dp.register_message_handler(parsing_user_channels, text="Парсинг", state="*")
    dp.register_message_handler(parsing_user_channels, text="Парсинг")

    dp.register_message_handler(stop_parsing, text="Остановить парсинг", state="*")

    dp.register_callback_query_handler(back_to_parsing, parsers_user_channel.filter(action="back_1"))

    dp.register_callback_query_handler(parsing_user_channel, parsers_user_channel.filter(action="none"))
    dp.register_callback_query_handler(parsing_user_channel, parsers_user_channel.filter(action="back_2"))

    dp.register_callback_query_handler(parser_channel, parser_channels.filter(action="show_parser_channel"))
    dp.register_callback_query_handler(parser_channel, parser_channels.filter(action="back_3"))

    dp.register_callback_query_handler(parsing_delete_confirm, parser_channel_delete.filter(action="delete"))
    dp.register_callback_query_handler(parsing_deleted, parser_channel_delete.filter(action="confirm_delete"))

    dp.register_callback_query_handler(parsing_add, parsers_user_channel.filter(action="add"))

    dp.register_callback_query_handler(parsed_posts_show, see_parsed_post.filter())

    dp.register_message_handler(parsing_add_link_media_group, IsMediaGroup(), state=Parsing.Link,
                                content_types=[types.ContentType.PHOTO,
                                               types.ContentType.VIDEO,
                                               types.ContentType.AUDIO,
                                               types.ContentType.ANIMATION,
                                               types.ContentType.DOCUMENT])

    dp.register_message_handler(parsing_add_link, state=Parsing.Link, content_types=[types.ContentType.PHOTO,
                                                                                     types.ContentType.VIDEO,
                                                                                     types.ContentType.AUDIO,
                                                                                     types.ContentType.ANIMATION,
                                                                                     types.ContentType.DOCUMENT,
                                                                                     types.ContentType.VIDEO_NOTE,
                                                                                     types.ContentType.TEXT])

    dp.register_callback_query_handler(back_to_parsing_2, parsers_user_channel.filter(action="back_2"),
                                       state=Parsing.Link)

    dp.register_message_handler(
        add_parser_channel,
        lambda
            message: 'user_bot subscribed to channel' in message.text or 'successfully requested to join channel' in message.text,
        IsUserBot(),
        state='*'
    )
    dp.register_message_handler(
        channel_doesnt_exist,
        lambda message: 'channel doesnt exist' in message.text,
        IsUserBot(),
        state='*'
    )
    dp.register_message_handler(
        get_posts_length,
        lambda message: 'Get posts length' in message.text,
        IsUserBot(),
        state='*'
    )

    dp.register_message_handler(
        media_group_handler,
        IsUserBot(),
        IsMediaGroup(),
        content_types=[
            types.ContentType.PHOTO,
            types.ContentType.VIDEO,
            types.ContentType.AUDIO,
            types.ContentType.ANIMATION,
            types.ContentType.DOCUMENT
        ],
        state='*'
    )

    dp.register_message_handler(
        message_from_parser_channel,
        IsUserBot(),
        content_types=[types.ContentType.PHOTO,
                       types.ContentType.VIDEO,
                       types.ContentType.AUDIO,
                       types.ContentType.ANIMATION,
                       types.ContentType.DOCUMENT,
                       types.ContentType.TEXT,
                       types.ContentType.VIDEO_NOTE],
        state='*'
    )

    dp.register_callback_query_handler(
        parsed_post_continue,
        parsed_post.filter(action="continue")
    )

    dp.register_callback_query_handler(
        parsed_post_delete,
        parsed_post.filter(action="delete")
    )

    dp.register_callback_query_handler(
        parsed_post_media_continue,
        parsed_post_media.filter(action="continue")
    )

    dp.register_callback_query_handler(
        parsed_post_media_delete,
        parsed_post_media.filter(action="delete")
    )

    dp.register_callback_query_handler(
        see_parsed_post_by_date_func,
        see_parsed_post_by_date.filter()
    )

    dp.register_callback_query_handler(
        choose_start_date,
        lambda c: c.data and c.data.startswith('day_'),
        state=Parsing.DateRangePickerStart
    )

    dp.register_callback_query_handler(
        choose_end_date,
        lambda c: c.data and c.data.startswith('day_'),
        state=Parsing.DateRangePickerEnd
    )

    dp.register_callback_query_handler(
        handle_month_callback,
        lambda c: c.data and c.data.startswith(('prev-month_', 'next-month_')),
        state=[Parsing.DateRangePickerStart, Parsing.DateRangePickerEnd]
    )

    dp.register_callback_query_handler(
        handle_back,
        back_to_posts.filter(),
        state=[Parsing.DateRangePickerStart, Parsing.DateRangePickerEnd]
    )

    dp.register_callback_query_handler(
        parser_channel,
        back_to_parser_channels.filter()
    )

    dp.register_callback_query_handler(
        see_parsed_post_new_handler,
        see_parsed_post_new.filter()
    )
