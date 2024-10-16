import copy
import datetime
import json
import logging
from typing import List, Union

import aiohttp
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Chat
from aiogram_media_group import media_group_handler

from tg_bot import config
from tg_bot.aiogram_bot.filters.is_admin import IsMediaGroup, IsAdmin
from tg_bot.aiogram_bot.keyboards.inline.admin_inline import admin_buttons_clb, admin_cancel_create, admin_further, \
    admin_calendar_clb, admin_choose_time, admin_sending_clb
from tg_bot.aiogram_bot.keyboards.inline.create_inline.calendar_create import choose_time, sending_clbk
from tg_bot.aiogram_bot.keyboards.inline.create_inline.create import choose_prompts
from tg_bot.aiogram_bot.states.users import Admins
from tg_bot.aiogram_bot.utils.utils import count_characters


async def markup_media(markup, post_id):
    markup.row(InlineKeyboardButton(text="URL-кнопки", callback_data=admin_buttons_clb.new(post_id=post_id)))
    markup.row(InlineKeyboardButton(text="❌ Отмена", callback_data=admin_cancel_create.new(post_id=post_id)),
               InlineKeyboardButton(text="➡️ Далее", callback_data=admin_further.new(post_id=post_id)))
    return markup


async def delete_messages(call, post_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }
        ) as response:
            respns = await response.json()
    messages_id = respns.get("data").get("messages_id")
    media_data = respns.get("data").get("media")

    if messages_id is not None:
        for msg_id in messages_id:
            try:
                await call.bot.delete_message(call.from_user.id, msg_id)
            except Exception as e:
                logging.error(e)
        if media_data is not None:
            if len(media_data) > 1:
                try:
                    await call.bot.delete_message(call.from_user.id, call.message.message_id)
                except Exception as e:
                    logging.error(e)
    else:
        try:
            await call.bot.delete_message(call.from_user.id, call.message.message_id)
        except Exception as e:
            logging.error(e)

    data = {"id": post_id,
            "messages_id": []}
    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/", json=data) as response:
            respons = await response.json()
    return respons


async def cancel_post(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.reset_state()

    post_id = callback_data['post_id']
    async with aiohttp.ClientSession() as session:
        async with session.delete(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/{post_id}"
        ) as response:
            post_response = await response.json()

    messages_id = post_response.get("data").get("messages_id")
    if messages_id:
        for message_id in messages_id:
            await call.bot.delete_message(call.from_user.id, message_id)

    await call.bot.delete_message(call.from_user.id, call.message.message_id)
    await call.bot.send_message(chat_id=call.from_user.id, text="❌ Создание поста отменено")


async def new_post(message: types.Message, state: FSMContext):
    await state.reset_state()

    # id_channel = int(callback_data.get("channel_id"))  ????????????????
    id_channel = None

    data = {"user_id": message.from_user.id,
            "channel_id": id_channel,
            "is_scheduled": False}

    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/all/",
                                json=data) as response:
            respns = await response.json()

    if respns.get('data') is not None:
        for item in respns.get('data'):
            id = int(item["id"])
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                        url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/{id}/") as response:
                    respns = await response.json()

    data = {"user_id": message.from_user.id,
            "description": None,
            "url_buttons": None,
            "media": None,
            "messages_id": None,
            "channel_id": id_channel,
            "date": None,
            "auto_delete_timer": None,
            "is_saved": True,
            "is_scheduled": False,
            "initial_post_id": None}

    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                json=data) as response:
            respons = await response.json()
    post_id = int(respons.get("data").get("id"))
    text = f"Отправьте или перешлите боту то, что хотите разослать пользователям с бесплатной подпиской"
    msg = await message.bot.send_message(message.from_user.id, text)
    await Admins.Get_Message.set()
    await state.update_data(msg=msg.message_id)
    await state.update_data(post_id=post_id)


# Admins.Get_Message
@media_group_handler
async def get_photo_group(messages: List[types.Message], state: FSMContext):
    data = await state.get_data()
    msg = data.get("msg")
    post_id = int(data.get("post_id"))
    await messages[0].bot.delete_message(messages[0].from_user.id, msg)

    caption = None
    caption_entities = None

    if len(messages) <= 10:
        data = {"id": post_id,
                "media": []}
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
            elif m.animation:
                file_id = m.animation.file_id

            if m.caption:
                caption = m.caption

            if m.caption_entities:
                caption_entities = caption_entities

            media_info = {
                'sequence_number': sequence_number,
                'file_id': file_id,
                'media_type': m.content_type}

            data["media"].append(media_info)
            sequence_number += 1

        async with aiohttp.ClientSession() as session:
            async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                   json=data) as response:
                respns = await response.json()

        if caption:
            data = {
                "id": post_id,
                "description": caption,
                "entities": json.dumps([entity.to_python() for entity in caption_entities])
                if caption_entities else None
            }
            async with aiohttp.ClientSession() as session:
                async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                       json=data) as response:
                    respns = await response.json()

        await state.reset_state()
        await edit_post_message(messages[0], state, post_id)
    else:
        await state.reset_state()
        await messages[0].answer("Вы отправили слишком много медиа файлов")


# Admins.Get_Message
async def get_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg = data.get("msg")
    post_id = int(data.get("post_id"))
    await message.bot.delete_message(message.from_user.id, msg)

    data = {"id": post_id,
            "media": []}

    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.video:
        file_id = message.video.file_id
    elif message.document:
        file_id = message.document.file_id
    elif message.audio:
        file_id = message.audio.file_id
    elif message.animation:
        file_id = message.animation.file_id
    elif message.video_note:
        file_id = message.video_note.file_id

    media_type = message.content_type

    media_info = {
        'sequence_number': 1,
        'file_id': file_id,
        'media_type': media_type}

    data["media"].append(media_info)

    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/", json=data) as response:
            respns = await response.json()
    if message.caption:
        data = {
            "id": post_id,
            "description": message.caption,
            "entities": json.dumps([entity.to_python() for entity in message.caption_entities])
            if message.caption_entities else None
        }
        async with aiohttp.ClientSession() as session:
            async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                   json=data) as response:
                respns = await response.json()

    await state.reset_state()
    await edit_post_message(message, state, post_id)


# Admins.Get_Message
async def get_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg = data.get("msg")
    post_id = int(data.get("post_id"))
    await message.bot.delete_message(message.from_user.id, msg)
    data = {"id": post_id,
            "description": message.text,
            "entities": json.dumps([entity.to_python() for entity in message.entities])
            if message.entities else None}
    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/", json=data) as response:
            respns = await response.json()

    await state.reset_state()
    await edit_post_message(message, state, post_id)


async def edit_post_message(message: types.Message, state: FSMContext, post_id: int):

    await state.reset_state()
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
    id_channel = response1.get("data").get("channel_id")
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

    combined_entities = copy.deepcopy(entities)

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
            markup = await markup_media(markup, post_id)

            data = {"id": post_id,
                    "messages_id": [message["message_id"] for message in messages]}

            async with aiohttp.ClientSession() as session:
                async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                       json=data) as response:
                    unused_response = await response.json()

            await message.bot.send_message(message.from_user.id, caption, reply_markup=markup)
        else:
            media_id = media_data[0]

            caption = "(Описание)" if caption is None else caption

            if media_id.get("media_type") == "photo":
                markup = await markup_media(markup, post_id)
                msg = await message.bot.send_photo(message.from_user.id, media_id.get("file_id"), caption,
                                                   caption_entities=combined_entities,
                                                   reply_markup=markup)

            elif media_id.get("media_type") == "video":
                markup = await markup_media(markup, post_id)
                msg = await message.bot.send_video(message.from_user.id, media_id.get("file_id"), caption=caption,
                                                   caption_entities=combined_entities,
                                                   reply_markup=markup)

            elif media_id.get("media_type") == "document":
                markup = await markup_media(markup, post_id)
                msg = await message.bot.send_document(message.from_user.id, media_id.get("file_id"),
                                                      caption_entities=combined_entities,
                                                      caption=caption, reply_markup=markup)

            elif media_id.get("media_type") == "audio":
                markup = await markup_media(markup, post_id)
                msg = await message.bot.send_audio(message.from_user.id, media_id.get("file_id"), caption=caption,
                                                   caption_entities=combined_entities,
                                                   reply_markup=markup)

            elif media_id.get("media_type") == "video_note":
                markup = await markup_media(markup, post_id)
                msg = await message.bot.send_video_note(message.from_user.id, media_id.get("file_id"),
                                                        reply_markup=markup)

            elif media_id.get("media_type") == "animation":
                markup = await markup_media(markup, post_id)
                msg = await message.bot.send_animation(message.from_user.id, media_id.get("file_id"),
                                                       caption=caption,
                                                       caption_entities=combined_entities,
                                                       reply_markup=markup)

            data = {"id": post_id,
                    "messages_id": [msg.message_id]}

            async with aiohttp.ClientSession() as session:
                async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                       json=data) as response:
                    unused_response = await response.json()

                # await message.bot.send_message(message.from_user.id, caption, reply_markup=markup)
    else:
        markup = await markup_media(markup, post_id)
        await message.bot.send_message(message.from_user.id, caption, reply_markup=markup, entities=combined_entities)


async def edit_post(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.reset_state()
    await call.answer()

    try:
        await call.bot.delete_message(call.from_user.id, call.message.message_id)
    except Exception as e:
        logging.error(e)

    post_id = int(callback_data.get("post_id"))

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
    id_channel = response1.get("data").get("channel_id")
    entities = response1.get("data").get("entities")
    entities = [types.MessageEntity(**entity) for entity in
                json.loads(entities)] if entities else None

    try:
        if messages_id is not None:
            for msg_id in messages_id:
                await call.bot.delete_message(call.from_user.id, msg_id)
    except Exception as e:
        logging.error(f"{e}")

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

            messages = await call.bot.send_media_group(chat_id=call.from_user.id, media=media)
            markup = await markup_media(markup, post_id)
            data = {"id": post_id,
                    "messages_id": [message["message_id"] for message in messages]}
            async with aiohttp.ClientSession() as session:
                async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                       json=data) as response:
                    unused_response = await response.json()

            await call.bot.send_message(call.from_user.id, caption, reply_markup=markup)
        else:
            media_id = media_data[0]
            caption = "(Описание)" if caption is None else caption

            if media_id.get("media_type") == "photo":
                markup = await markup_media(markup, post_id)
                msg = await call.bot.send_photo(call.from_user.id, media_id.get("file_id"), caption,
                                                caption_entities=combined_entities,
                                                reply_markup=markup)

            elif media_id.get("media_type") == "video":
                markup = await markup_media(markup, post_id)
                msg = await call.bot.send_video(call.from_user.id, media_id.get("file_id"), caption=caption,
                                                caption_entities=combined_entities,
                                                reply_markup=markup)

            elif media_id.get("media_type") == "document":
                markup = await markup_media(markup, post_id)
                msg = await call.bot.send_document(call.from_user.id, media_id.get("file_id"),
                                                   caption=caption,
                                                   caption_entities=combined_entities,
                                                   reply_markup=markup)

            elif media_id.get("media_type") == "audio":
                markup = await markup_media(markup, post_id)
                msg = await call.bot.send_audio(call.from_user.id, media_id.get("file_id"), caption=caption,
                                                caption_entities=combined_entities,
                                                reply_markup=markup)

            elif media_id.get("media_type") == "video_note":
                markup = await markup_media(markup, post_id)
                msg = await call.bot.send_video_note(call.from_user.id, media_id.get("file_id"),
                                                     reply_markup=markup)

            elif media_id.get("media_type") == "animation":
                markup = await markup_media(markup, post_id)
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
        markup = await markup_media(markup, post_id)
        await call.bot.send_message(call.from_user.id, caption, reply_markup=markup, entities=combined_entities)


async def url_buttons(call: CallbackQuery, callback_data: dict, state: FSMContext):
    post_id = int(callback_data.get("post_id"))
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
            await call.answer("❌ Url кнопки для данного поста не поддерживаются", show_alert=True)
            return

    await call.answer()

    await call.bot.delete_message(call.from_user.id, call.message.message_id)

    await delete_messages(call, post_id)

    text = f"⛓ <b>URL-КНОПКИ</b>\n\n" \
           f"Отправьте боту список URL-кнопок в следующем формате:\n\n" \
           f"<code>Название кнопки 1 - <b>http://link.com</b></code>\n" \
           f"<code>Название кнопки 2 - <b>http://link.com</b></code>\n\n" \
           f"Используйте разделитель '|', чтобы добавить до 8 кнопок в один ряд (допустимо 15 рядов):\n\n" \
           f"<code>Название кнопки 1 - <b>http://link.com</b> | Название кнопки 2 - <b>http://link.com</b></code>"
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text="⬅️ Назад",
                                    callback_data=choose_prompts.new(action="back", index=999, post_id=post_id)))
    msg = await call.bot.send_message(call.from_user.id, text, reply_markup=markup)
    await Admins.Get_URL.set()
    await state.update_data(msg=msg.message_id)
    await state.update_data(post_id=post_id)


# Admins.Get_URL
async def url_buttons_add(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg = data.get("msg")
    post_id = int(data.get("post_id"))
    await message.bot.delete_message(message.from_user.id, msg)

    data = {"id": post_id,
            "url_buttons": []}
    buttons_text = message.text.split('\n')

    for row in buttons_text:
        data["url_buttons"].append(row)

    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/", json=data) as response:
            respns = await response.json()
    await state.reset_state()
    await edit_post_message(message, state, post_id)


def register_admins_handler(dp: Dispatcher):
    dp.register_message_handler(new_post, IsAdmin(), text="Рекламный пост", state="*")
    dp.register_message_handler(new_post, IsAdmin(), text="Рекламный пост")

    dp.register_callback_query_handler(cancel_post, admin_cancel_create.filter(), IsAdmin())

    dp.register_callback_query_handler(edit_post, admin_choose_time.filter(action="back"), IsAdmin())
    dp.register_callback_query_handler(edit_post, admin_calendar_clb.filter(action="back"), IsAdmin())
    dp.register_callback_query_handler(edit_post, admin_sending_clb.filter(action="back"), IsAdmin())

    dp.register_message_handler(get_photo_group,
                                IsMediaGroup(),
                                state=Admins.Get_Message,
                                content_types=[types.ContentType.PHOTO,
                                               types.ContentType.VIDEO,
                                               types.ContentType.DOCUMENT,
                                               types.ContentType.AUDIO,
                                               types.ContentType.ANIMATION,
                                               types.ContentType.VIDEO_NOTE])

    dp.register_message_handler(get_photo,
                                state=Admins.Get_Message,
                                content_types=[types.ContentType.PHOTO,
                                               types.ContentType.VIDEO,
                                               types.ContentType.DOCUMENT,
                                               types.ContentType.AUDIO,
                                               types.ContentType.ANIMATION,
                                               types.ContentType.VIDEO_NOTE])

    dp.register_message_handler(get_text,
                                state=Admins.Get_Message,
                                content_types=types.ContentType.TEXT)

    dp.register_callback_query_handler(url_buttons, admin_buttons_clb.filter(), IsAdmin())
    dp.register_message_handler(url_buttons_add, state=Admins.Get_URL)
