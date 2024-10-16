import asyncio
import logging
from datetime import datetime
from typing import List

import aiohttp
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram_media_group import media_group_handler

from tg_bot import config
from tg_bot.aiogram_bot.filters.is_admin import IsMediaGroup
from tg_bot.aiogram_bot.handlers.users.content.content_plan import edit_scheduled_post_message, edit_scheduled_post
from tg_bot.aiogram_bot.handlers.users.create.create_post import edit_post
from tg_bot.aiogram_bot.keyboards.inline.content_inline.content import post_callback, custom_media_content
from tg_bot.aiogram_bot.keyboards.inline.create_inline.create import custom_media, replace_media, swap_media_clb
from tg_bot.aiogram_bot.states.users import Create, Content


async def update_message(call, post_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                               params={
                                   "key": "id",
                                   "value": post_id
                               }
                               ) as response:
            respons = await response.json()
            messages_id = respons.get("data").get("messages_id")
            media_data = respons.get("data").get("media")

    if messages_id:
        for msg_id in messages_id:
            await call.bot.delete_message(call.from_user.id, msg_id)

    data = {"id": post_id,
            "messages_id": []}
    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                               json=data) as response:
            respons = await response.json()

    return media_data


async def update_message_type_message(message: types.Message, post_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                               params={
                                   "key": "id",
                                   "value": post_id
                               }
                               ) as response:
            respons = await response.json()
            messages_id = respons.get("data").get("messages_id")
            media_data = respons.get("data").get("media")

    if messages_id:
        for msg_id in messages_id:
            await message.bot.delete_message(message.from_user.id, msg_id)

    data = {"id": post_id,
            "messages_id": []}
    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                               json=data) as response:
            respons = await response.json()

    return media_data


async def edit_media_message(message: types.Message, state: FSMContext, post_id: int):
    await state.reset_state()
    _ = message.bot.get("lang")

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }
        ) as response:
            respns = await response.json()

    if not respns.get("data").get("is_saved"):
        post_id = int(respns.get("data").get("id"))
    else:
        data = {"user_id": message.from_user.id,
                "description": respns.get("data").get("description"),
                "url_buttons": respns.get("data").get("url_buttons"),
                "media": respns.get("data").get("media"),
                "messages_id": [],
                "channel_id": respns.get("data").get("channel_id"),
                "date": respns.get("data").get("date"),
                "auto_delete_timer": respns.get("data").get("auto_delete_timer"),
                "is_saved": False,
                "is_scheduled": respns.get("data").get("is_scheduled"),
                "initial_post_id": int(post_id)}

        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                    json=data) as response:
                responss = await response.json()

        post_id = int(responss.get("data").get("id"))

    text = _("🖼 <b>НАСТРОИТЬ МЕДИА</b>\n\n"
             "Для переключения между файлами используйте кнопки с цифрами:")

    markup = InlineKeyboardMarkup(row_width=2)
    add_media_btn_text = _("➕ Добавить медиа")
    save_btn_text = _("💾 Сохранить")
    back_btn_text = _("⬅️ Назад")
    markup.add(InlineKeyboardButton(text=add_media_btn_text,
                                    callback_data=custom_media.new(action="add_media", post_id=post_id)))
    markup.add(
        InlineKeyboardButton(text=save_btn_text, callback_data=custom_media.new(action="save", post_id=post_id)))
    markup.add(InlineKeyboardButton(text=back_btn_text, callback_data=custom_media.new(action="back", post_id=post_id)))

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }
        ) as response:
            respons = await response.json()
            media_data = respons.get("data").get("media")

    if media_data is not None:
        if len(media_data) > 1:
            media = types.MediaGroup()
            markup1 = InlineKeyboardMarkup(row_width=4)
            media_buttons = []
            id_photo = 1

            # try:
            for media_id in media_data:
                if len(media_buttons) >= 3:
                    markup1.row(*media_buttons)
                    media_buttons.clear()
                index = int(media_id.get("sequence_number"))
                if index == id_photo:
                    media_buttons.append(InlineKeyboardButton(text=f"*️⃣ {index}",
                                                              callback_data=replace_media.new(action="choise",
                                                                                              id_photo=index,
                                                                                              post_id=post_id)))
                else:
                    media_buttons.append(InlineKeyboardButton(text=f"{index}",
                                                              callback_data=replace_media.new(action="choise",
                                                                                              id_photo=index,
                                                                                              post_id=post_id)))

                if media_id.get("media_type") == "photo":
                    media.attach(types.InputMediaPhoto(media_id.get("file_id")))
                elif media_id.get("media_type") == "video":
                    media.attach(types.InputMediaVideo(media_id.get("file_id")))
                elif media_id.get("media_type") == "document":
                    media.attach(types.InputMediaDocument(media_id.get("file_id")))
                elif media_id.get("media_type") == "audio":
                    media.attach(types.InputMediaAudio(media_id.get("file_id")))

            messages = await message.bot.send_media_group(chat_id=message.from_user.id, media=media)

            # except Exception as e:
            #     msg = await message.bot.send_message(message.from_user.id,
            #                                          text="Отправляйте файлы одного формата")
            #     await Create.Add_Media.set()
            #     await state.update_data(msg=msg.message_id)
            #     await state.update_data(post_id=post_id)
            #     return

            data = {"id": post_id, "messages_id": [message["message_id"] for message in messages]}
            async with aiohttp.ClientSession() as session:
                async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                       json=data) as response:
                    respons = await response.json()
            markup1.row(*media_buttons, InlineKeyboardButton(text=f"🔄",
                                                             callback_data=swap_media_clb.new(action="swap_media",
                                                                                              id_1=id_photo,
                                                                                              id_2="None",
                                                                                              post_id=post_id)),
                        InlineKeyboardButton(text=f"➕",
                                             callback_data=custom_media.new(action="add_media", post_id=post_id)))
            delete_btn_text = _("Удалить медиа")
            replace_btn_text = _("Заменить медиа")
            markup1.row(InlineKeyboardButton(text=delete_btn_text,
                                             callback_data=replace_media.new(action="delete", id_photo=id_photo,
                                                                             post_id=post_id)),
                        InlineKeyboardButton(text=replace_btn_text,
                                             callback_data=replace_media.new(action="replace", id_photo=id_photo,
                                                                             post_id=post_id)))
            markup1.add(InlineKeyboardButton(text=save_btn_text,
                                             callback_data=custom_media.new(action="save", post_id=post_id)))
            markup1.add(
                InlineKeyboardButton(text=back_btn_text, callback_data=custom_media.new(action="back", post_id=post_id)))
            await message.bot.send_message(message.from_user.id, text, reply_markup=markup1)
        else:
            media_id = media_data[0]

            if media_id.get("media_type") == "photo":
                msg = await message.bot.send_photo(message.from_user.id, media_id.get("file_id"), caption=text,
                                                   reply_markup=markup)

            elif media_id.get("media_type") == "video":
                msg = await message.bot.send_video(message.from_user.id, media_id.get("file_id"), caption=text,
                                                   reply_markup=markup)
            elif media_id.get("media_type") == "document":
                msg = await message.bot.send_document(message.from_user.id, media_id.get("file_id"), caption=text,
                                                      reply_markup=markup)
            elif media_id.get("media_type") == "audio":
                msg = await message.bot.send_audio(message.from_user.id, media_id.get("file_id"), caption=text,
                                                   reply_markup=markup)
            elif media_id.get("media_type") == "video_note":
                msg = await message.bot.send_video_note(message.from_user.id, media_id.get("file_id"),
                                                        reply_markup=markup)
            elif media_id.get("media_type") == "animation":
                msg = await message.bot.send_animation(message.from_user.id, media_id.get("file_id"), caption=text,
                                                       reply_markup=markup)
    else:
        await message.bot.send_message(message.from_user.id, text, reply_markup=markup)


async def pre_edit_media(call: CallbackQuery, callback_data: dict, state: FSMContext):
    post_id = int(callback_data.get("post_id"))
    _ = call.bot.get("lang")
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }
        ) as response:
            respons = await response.json()
            messages_id = respons.get("data").get("messages_id")
            utc_time_iso = respons.get("data").get("date")
            media_data = respons.get("data").get("media")

    if media_data is not None:
        if len(media_data) == 1 and (
                media_data[0]['media_type'] == "animation" or media_data[0]['media_type'] == "video_note"):
            text = _("❌ Настройки медиа для данного поста не поддерживается")
            await call.answer(text=text, show_alert=True)
            return

    if utc_time_iso is not None:
        scheduled_datetime_utc = datetime.fromisoformat(utc_time_iso)

        current_date_utc = datetime.utcnow()
        if current_date_utc > scheduled_datetime_utc:

            if media_data is not None:
                if len(media_data) > 1 or len(media_data) == 0:
                    text = _("❌ Настройки медиа для данного поста не поддерживается")
                    await call.answer(text=text, show_alert=True)
                else:
                    media_id = media_data[0]
                    if media_id.get("media_type") in ['photo', 'video', 'document', 'audio', 'animation']:
                        markup = InlineKeyboardMarkup(row_width=1)
                        markup.row(InlineKeyboardButton(text="⬅️ Назад",
                                                        callback_data=post_callback.new(action="back_to_edit",
                                                                                        post_id=post_id)))

                    if media_id.get("media_type") == "photo":
                        caption = _("Чтобы изменить отправьте одно фото")
                        msg = await call.bot.send_photo(call.from_user.id, media_id.get("file_id"), caption,
                                                        reply_markup=markup)

                    elif media_id.get("media_type") == "video":
                        caption = _("Чтобы изменить отправьте одно видео")

                        msg = await call.bot.send_video(call.from_user.id, media_id.get("file_id"), caption=caption,
                                                        reply_markup=markup)

                    elif media_id.get("media_type") == "document":
                        caption = _("Чтобы изменить отправьте один документ")

                        msg = await call.bot.send_document(call.from_user.id, media_id.get("file_id"), caption=caption,
                                                           reply_markup=markup)

                    elif media_id.get("media_type") == "audio":
                        caption = _("Чтобы изменить отправьте одно аудио")
                        msg = await call.bot.send_audio(call.from_user.id, media_id.get("file_id"), caption=caption,
                                                        reply_markup=markup)

                    elif media_id.get("media_type") == "animation":
                        caption = _("Чтобы изменить отправьте одно видео")
                        msg = await call.bot.send_animation(call.from_user.id, media_id.get("file_id"), caption=caption,
                                                            reply_markup=markup)

                    else:
                        text = _("Редактирование этого поста не поддерживается")
                        await call.bot.answer_callback_query(call.id, text, show_alert=True)

                    if media_id.get("media_type") in ['photo', 'video', 'document', 'audio', 'animation']:
                        await call.bot.delete_message(call.from_user.id, call.message.message_id)
                        await Content.Edit_Media.set()
                        await state.update_data(msg=msg.message_id)
                        await state.update_data(post_id=post_id)
                        await state.update_data(action="edit")

            else:
                if messages_id:
                    for msg_id in messages_id:
                        await call.bot.delete_message(call.from_user.id, msg_id)

                data = {"id": post_id,
                        "messages_id": []}
                async with aiohttp.ClientSession() as session:
                    async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                           json=data) as response:
                        respons = await response.json()

                await edit_media(call, callback_data, state)

        else:
            if messages_id:
                for msg_id in messages_id:
                    await call.bot.delete_message(call.from_user.id, msg_id)

            data = {"id": post_id,
                    "messages_id": []}
            async with aiohttp.ClientSession() as session:
                async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                       json=data) as response:
                    respons = await response.json()

            await edit_media(call, callback_data, state)
    else:
        if messages_id:
            for msg_id in messages_id:
                await call.bot.delete_message(call.from_user.id, msg_id)

        data = {"id": post_id,
                "messages_id": []}

        async with aiohttp.ClientSession() as session:
            async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                   json=data) as response:
                respons = await response.json()

        await edit_media(call, callback_data, state)


async def edit_media(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()
    _ = call.bot.get("lang")

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
                }
        ) as response:
            respns = await response.json()

    if not respns.get("data").get("is_saved"):
        post_id = respns.get("data").get("id")
    else:
        data = {"user_id": call.from_user.id,
                "description": respns.get("data").get("description"),
                "url_buttons": respns.get("data").get("url_buttons"),
                "media": respns.get("data").get("media"),
                "messages_id": [],
                "channel_id": respns.get("data").get("channel_id"),
                "date": respns.get("data").get("date"),
                "auto_delete_timer": respns.get("data").get("auto_delete_timer"),
                "is_saved": False,
                "is_scheduled": respns.get("data").get("is_scheduled"),
                "initial_post_id": post_id}

        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                    json=data) as response:
                responss = await response.json()

        post_id = int(responss.get("data").get("id"))

    text = _("🖼 <b>НАСТРОИТЬ МЕДИА</b>\n\n"
             "Для переключения между файлами используйте кнопки с цифрами:")
    add_media_btn_text = _("➕ Добавить медиа")
    save_btn_text = _("💾 Сохранить")
    back_btn_text = _("⬅️ Назад")
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton(text=add_media_btn_text,
                                    callback_data=custom_media.new(action="add_media", post_id=post_id)))
    markup.add(
        InlineKeyboardButton(text=save_btn_text, callback_data=custom_media.new(action="save", post_id=post_id)))
    markup.add(InlineKeyboardButton(text=back_btn_text, callback_data=custom_media.new(action="back", post_id=post_id)))

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }
        ) as response:
            respons = await response.json()
            media_data = respons.get("data").get("media")

    if media_data is not None:
        if len(media_data) > 1:
            media = types.MediaGroup()
            markup1 = InlineKeyboardMarkup(row_width=4)
            media_buttons = []
            id_photo = 1
            # try:
            for media_id in media_data:
                if len(media_buttons) >= 3:
                    markup1.row(*media_buttons)
                    media_buttons.clear()
                index = int(media_id.get("sequence_number"))
                if index == id_photo:
                    media_buttons.append(InlineKeyboardButton(text=f"*️⃣ {index}",
                                                              callback_data=replace_media.new(action="choise",
                                                                                              id_photo=index,
                                                                                              post_id=post_id)))
                else:
                    media_buttons.append(InlineKeyboardButton(text=f"{index}",
                                                              callback_data=replace_media.new(action="choise",
                                                                                              id_photo=index,
                                                                                              post_id=post_id)))

                if media_id.get("media_type") == "photo":
                    media.attach(types.InputMediaPhoto(media_id.get("file_id")))
                elif media_id.get("media_type") == "video":
                    media.attach(types.InputMediaVideo(media_id.get("file_id")))
                elif media_id.get("media_type") == "document":
                    media.attach(types.InputMediaDocument(media_id.get("file_id")))
                elif media_id.get("media_type") == "audio":
                    media.attach(types.InputMediaAudio(media_id.get("file_id")))

            messages = await call.bot.send_media_group(chat_id=call.from_user.id, media=media)

            # except Exception as e:
            #     msg = await call.bot.send_message(call.from_user.id,
            #                                          text="Отправляйте файлы одного формата")
            #     await Create.Add_Media.set()
            #     await state.update_data(msg=msg.message_id)
            #     await state.update_data(post_id=post_id)
            #     return

            data = {"id": post_id,
                    "messages_id": [message["message_id"] for message in messages]}
            async with aiohttp.ClientSession() as session:
                async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                       json=data) as response:
                    respons = await response.json()
            markup1.row(*media_buttons, InlineKeyboardButton(text=f"🔄",
                                                             callback_data=swap_media_clb.new(action="swap_media",
                                                                                              id_1=id_photo,
                                                                                              id_2="None",
                                                                                              post_id=post_id)),
                        InlineKeyboardButton(text=f"➕",
                                             callback_data=custom_media.new(action="add_media", post_id=post_id)))

            delete_btn_text = _("Удалить медиа")
            replace_btn_text = _("Заменить медиа")

            markup1.row(InlineKeyboardButton(text=delete_btn_text,
                                             callback_data=replace_media.new(action="delete", id_photo=id_photo,
                                                                             post_id=post_id)),
                        InlineKeyboardButton(text=replace_btn_text,
                                             callback_data=replace_media.new(action="replace", id_photo=id_photo,
                                                                             post_id=post_id)))
            markup1.add(InlineKeyboardButton(text=save_btn_text,
                                             callback_data=custom_media.new(action="save", post_id=post_id)))
            markup1.add(
                InlineKeyboardButton(text=back_btn_text, callback_data=custom_media.new(action="back", post_id=post_id)))
            await call.bot.send_message(call.from_user.id, text, reply_markup=markup1)
        else:
            media_id = media_data[0]

            if media_id.get("media_type") == "photo":
                msg = await call.bot.send_photo(call.from_user.id, media_id.get("file_id"), caption=text,
                                                reply_markup=markup)

            elif media_id.get("media_type") == "video":
                msg = await call.bot.send_video(call.from_user.id, media_id.get("file_id"), caption=text,
                                                reply_markup=markup)

            elif media_id.get("media_type") == "document":
                msg = await call.bot.send_document(call.from_user.id, media_id.get("file_id"), caption=text,
                                                   reply_markup=markup)

            elif media_id.get("media_type") == "audio":
                msg = await call.bot.send_audio(call.from_user.id, media_id.get("file_id"), caption=text,
                                                reply_markup=markup)

            elif media_id.get("media_type") == "animation":
                msg = await call.bot.send_animation(call.from_user.id, media_id.get("file_id"), caption=text,
                                                    reply_markup=markup)

    else:
        await call.bot.send_message(call.from_user.id, text, reply_markup=markup)


async def choise_photo(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()
    _ = call.bot.get("lang")
    id_photo = int(callback_data.get("id_photo"))
    post_id = int(callback_data.get("post_id"))

    text = _("🖼 <b>НАСТРОИТЬ МЕДИА</b>\n\n" \
             "Для переключения между файлами используйте кнопки с цифрами:")
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }
        ) as response:
            respons = await response.json()
    media_data = respons.get("data").get("media")

    markup1 = InlineKeyboardMarkup(row_width=4)
    media_buttons = []
    media = types.MediaGroup()
    for media_id in media_data:
        if len(media_buttons) >= 3:
            markup1.row(*media_buttons)
            media_buttons.clear()
        index = int(media_id.get("sequence_number"))
        if index == id_photo:
            media_buttons.append(InlineKeyboardButton(text=f"*️⃣ {index}",
                                                      callback_data=replace_media.new(action="choise", id_photo=index,
                                                                                      post_id=post_id)))
        else:
            media_buttons.append(
                InlineKeyboardButton(text=f"{index}",
                                     callback_data=replace_media.new(action="choise", id_photo=index, post_id=post_id)))

        if media_id.get("media_type") == "photo":
            media.attach(types.InputMediaPhoto(media_id.get("file_id")))
        elif media_id.get("media_type") == "video":
            media.attach(types.InputMediaVideo(media_id.get("file_id")))
        elif media_id.get("media_type") == "document":
            media.attach(types.InputMediaDocument(media_id.get("file_id")))
        elif media_id.get("media_type") == "audio":
            media.attach(types.InputMediaAudio(media_id.get("file_id")))

    markup1.row(*media_buttons, InlineKeyboardButton(text=f"🔄", callback_data=swap_media_clb.new(action="swap_media",
                                                                                                 id_1=id_photo,
                                                                                                 id_2="None",
                                                                                                 post_id=post_id)),
                InlineKeyboardButton(text=f"➕", callback_data=custom_media.new(action="add_media", post_id=post_id)))

    delete_btn_text = _("Удалить медиа")
    replace_btn_text = _("Заменить медиа")
    save_btn_text = _("💾 Сохранить")
    back_btn_text = _("⬅️ Назад")

    markup1.row(InlineKeyboardButton(text=delete_btn_text,
                                     callback_data=replace_media.new(action="delete", id_photo=id_photo,
                                                                     post_id=post_id)),
                InlineKeyboardButton(text=replace_btn_text,
                                     callback_data=replace_media.new(action="replace", id_photo=id_photo,
                                                                     post_id=post_id)))
    markup1.add(
        InlineKeyboardButton(text=save_btn_text, callback_data=custom_media.new(action="save", post_id=post_id)))
    markup1.add(InlineKeyboardButton(text=back_btn_text, callback_data=custom_media.new(action="back", post_id=post_id)))
    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup1)


async def add_media(call: CallbackQuery, callback_data: dict, state: FSMContext):
    post_id = int(callback_data.get("post_id"))
    _ = call.bot.get("lang")
    text = _("➕ <b>ДОБАВИТЬ МЕДИА</b>\n\n")

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }
        ) as response:
            respons = await response.json()

    media_data = respons.get("data").get("media")
    url_buttons = respons.get('data').get('url_buttons')

    if media_data is not None:
        if len(media_data) == 1 and url_buttons is not None:
            text = _("❌ Нельзя добавлять несколько медиа к посту , где имеются URL кнопки")
            await call.bot.send_message(call.from_user.id, text=text)
            await edit_media(call, callback_data, state)
            return

    await call.bot.delete_message(call.from_user.id, call.message.message_id)
    await update_message(call, post_id)
    await call.answer()

    if media_data is None:
        after_text = _("Вы можете отправлять фотографии, видео, аудиозаписи и документы.\n\nОднако вы не можете " \
                       "комбинировать разные типы файлов в одном сообщении, за исключением фото и видео.")
    else:
        if media_data[0]['media_type'] == "photo" or media_data[0]['media_type'] == "video":
            after_text = _("Вы можете отправлять фотографии и видео")
        elif media_data[0]['media_type'] == "audio":
            after_text = _("Вы можете отправлять аудиозаписи")
        elif media_data[0]['media_type'] == "document":
            after_text = _("Вы можете отправлять документы")

    text += after_text

    msg = await call.bot.send_message(call.from_user.id, text)
    await Create.Add_Media.set()
    await state.update_data(msg=msg.message_id)
    await state.update_data(post_id=post_id)


# Create.Add_Media
@media_group_handler
async def add_photo_group(messages: List[types.Message], state: FSMContext):
    data = await state.get_data()
    _ = messages[0].bot.get("lang")
    msg = data.get("msg")
    post_id = int(data.get("post_id"))

    await messages[0].bot.delete_message(messages[0].from_user.id, msg)

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }
        ) as response:
            respons = await response.json()

    media_data = respons.get("data").get("media") if respons.get("data").get("media") else []
    url_buttons = respons.get('data').get('url_buttons')
    counter = len(media_data) if media_data is not None else 0
    amount = counter + len(messages)

    if url_buttons is not None and amount > 1:
        text = _("❌ Нельзя добавлять несколько медиа к посту , где имеются URL кнопки")
        await messages[0].bot.send_message(messages[0].from_user.id,
                                    text=text)
        await edit_media_message(messages[0], state,post_id)
        return

    if amount <= 10:
        data = {"id": post_id, "media": media_data}
        sequence_number = counter + 1
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
                file_id = m.audio.file_id

            media_info = {
                'sequence_number': sequence_number,
                'file_id': file_id,
                'media_type': m.content_type}
            data["media"].append(media_info)
            sequence_number += 1

        media_types = set(item['media_type'] for item in data['media'])
        file_txt = _("Отправляйте файлы одного формата")
        if 'audio' in media_types and len(media_types) > 1:
            await messages[0].bot.send_message(messages[0].from_user.id, text=file_txt)
            await edit_media_message(messages[0], state, post_id)
            return
        elif 'document' in media_types and len(media_types) > 1:
            await messages[0].bot.send_message(messages[0].from_user.id, text=file_txt)
            await edit_media_message(messages[0], state, post_id)
            return
        elif 'animation' in media_types and len(media_types) > 1:
            await messages[0].bot.send_message(messages[0].from_user.id, text=file_txt)
            await edit_media_message(messages[0], state, post_id)
            return

        async with aiohttp.ClientSession() as session:
            async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                   json=data) as response:
                respns = await response.json()
        await state.reset_state()
        await edit_media_message(messages[0], state, post_id)
    else:
        await state.reset_state()
        text = _("Вы отправили слишком много медиа файлов")
        await messages[0].answer(text)


# Create.Add_Media
async def add_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    _ = message.bot.get("lang")

    msg = data.get("msg")
    post_id = int(data.get("post_id"))
    try:
        await message.bot.delete_message(message.from_user.id, msg)
    except Exception as e:
        logging.error(f"add_photo {e}")

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }
        ) as response:
            respons = await response.json()

    media_data = respons.get("data").get("media")

    if media_data is not None:
        counter = len(media_data)
    else:
        media_data = []
        counter = 0

    amount = counter + 1

    if amount <= 10:
        data = {"id": post_id, "media": media_data}
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

        counter += 1

        media_info = {
            'sequence_number': counter,
            'file_id': file_id,
            'media_type': message.content_type}

        data["media"].append(media_info)

        media_types = set(item['media_type'] for item in data['media'])
        file_txt = _("Отправляйте файлы одного формата")

        if 'audio' in media_types and len(media_types) > 1:
            await message.bot.send_message(message.from_user.id, text=file_txt)
            await edit_media_message(message, state, post_id)
            return
        elif 'document' in media_types and len(media_types) > 1:
            await message.bot.send_message(message.from_user.id, text=file_txt)
            await edit_media_message(message, state, post_id)
            return
        elif 'animation' in media_types and len(media_types) > 1:
            await message.bot.send_message(message.from_user.id, text=file_txt)
            await edit_media_message(message, state, post_id)
            return

        async with aiohttp.ClientSession() as session:
            async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                   json=data) as response:
                respns = await response.json()

        await state.reset_state()
        await edit_media_message(message, state, post_id)
    else:
        await state.reset_state()
        text = _("Вы отправили слишком много медиа файлов")
        await message.answer(text)


async def replace(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()
    _ = call.bot.get("lang")
    await call.bot.delete_message(call.from_user.id, call.message.message_id)
    id_photo = int(callback_data.get("id_photo"))
    post_id = int(callback_data.get("post_id"))
    media_data = await update_message(call, post_id)

    for item in media_data:
        if item["sequence_number"] == id_photo:
            file_id = item["file_id"]
            content_type = item['media_type']
            break

    text = _("🖼 <b>ЗАМЕНИТЬ МЕДИА</b>\n\n")

    if content_type == "photo" or content_type == "video":
        after_text = _("Вы можете отправлять фотографии и видео")
    elif content_type == "audio":
        after_text = _("Вы можете отправлять аудиозаписи")
    elif content_type == "document":
        after_text = _("Вы можете отправлять документы")

    text += after_text

    msg = await call.bot.send_photo(call.from_user.id, file_id, text)
    await Create.Replace_Media.set()
    await state.update_data(msg=msg.message_id)
    await state.update_data(id_photo=id_photo)
    await state.update_data(post_id=post_id)


# Create.Replace_Media
async def replace_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg = data.get("msg")
    id_photo = data.get("id_photo")
    post_id = int(data.get("post_id"))
    await message.bot.delete_message(message.from_user.id, msg)

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }
        ) as response:
            respons = await response.json()
    media_data = respons.get("data").get("media")
    for item in media_data:
        if item["sequence_number"] == id_photo:
            if message.photo:
                file_id = message.photo[-1].file_id
                item["file_id"] = file_id
                item["media_type"] = message.content_type
            elif message.video:
                file_id = message.video.file_id
                item["file_id"] = file_id
                item["media_type"] = message.content_type
            elif message.document:
                file_id = message.document.file_id
                item["file_id"] = file_id
                item["media_type"] = message.content_type
            elif message.audio:
                file_id = message.audio.file_id
                item["file_id"] = file_id
                item["media_type"] = message.content_type
            elif message.animation:
                file_id = message.animation.file_id
                item["file_id"] = file_id
                item["media_type"] = message.content_type
            break

    data = {"id": post_id, "media": media_data}
    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                               json=data) as response:
            respns = await response.json()

    await state.reset_state()
    await edit_media_message(message, state, post_id)


async def delete_photo(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()
    id_photo = int(callback_data.get("id_photo"))
    post_id = int(callback_data.get("post_id"))
    media_data = await update_message(call, post_id)

    media_data.pop((id_photo - 1))

    for item in media_data[(id_photo - 1):]:
        item["sequence_number"] -= 1
    data = {"id": post_id, "media": media_data}

    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                               json=data) as response:
            respns = await response.json()

    await edit_media(call, callback_data, state)


async def swap_media(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()
    _ = call.bot.get("lang")
    id_1 = int(callback_data.get("id_1"))
    post_id = int(callback_data.get("post_id"))

    text = _("🔄 <b>ПОМЕНЯТЬ МЕСТАМИ</b>\n\n" \
             "Выберите номер медиа которое хотите поменять местами:")
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }
        ) as response:
            respons = await response.json()
    media_data = respons.get("data").get("media")

    markup1 = InlineKeyboardMarkup(row_width=4)
    media_buttons = []
    for media_id in media_data:
        if len(media_buttons) >= 3:
            markup1.row(*media_buttons)
            media_buttons.clear()
        index = int(media_id.get("sequence_number"))
        media_buttons.append(InlineKeyboardButton(text=f"{index}",
                                                  callback_data=swap_media_clb.new(action="send_swapped", id_1=id_1,
                                                                                   id_2=index, post_id=post_id)))
    markup1.row(*media_buttons)
    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup1)


async def swapped_media(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()
    id_1 = int(callback_data.get("id_1"))
    id_2 = int(callback_data.get("id_2"))
    post_id = int(callback_data.get("post_id"))

    media_data = await update_message(call, post_id)

    id_1_file_id = None
    id_2_file_id = None
    id_1_media_type = None
    id_2_media_type = None

    for item in media_data:
        if item["sequence_number"] == id_1:
            id_1_file_id = item["file_id"]
            id_1_media_type = item["media_type"]
        elif item["sequence_number"] == id_2:
            id_2_file_id = item["file_id"]
            id_2_media_type = item["media_type"]

    for item in media_data:
        if item["sequence_number"] == id_1:
            item["file_id"] = id_2_file_id
            item["media_type"] = id_2_media_type

        elif item["sequence_number"] == id_2:
            item["file_id"] = id_1_file_id
            item["media_type"] = id_1_media_type

    data = {"id": post_id, "media": media_data}
    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                               json=data) as response:
            respns = await response.json()

    await edit_media(call, callback_data, state)


async def previous_saved_media(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()
    post_id = int(callback_data.get("post_id"))
    await update_message(call, post_id)

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

    is_scheduled = respns.get("data").get("is_scheduled")
    if is_scheduled is True:
        await edit_scheduled_post(call, callback_data, state)
    else:
        await edit_post(call, callback_data, state)


async def save_media(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()
    post_id = int(callback_data.get("post_id"))

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }
        ) as response:
            respns = await response.json()
    initial_post_id = int(respns.get("data").get("initial_post_id"))

    is_scheduled = respns.get("data").get("is_scheduled")

    if is_scheduled is True:
        # data = {"post_id": int(initial_post_id)}
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/one/",
        #                             json=data) as response:
        #         respons = await response.json()
        # message_id = respons.get("data").get("id")
        #
        # data = {"id": message_id, "post_id": int(post_id)}
        # async with aiohttp.ClientSession() as session:
        #     async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/message/",
        #                            json=data) as response:
        #         responsee = await response.json()
        #
        # async with aiohttp.ClientSession() as session:
        #     async with session.delete(
        #             url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/{initial_post_id}/") as response:
        #         respns = await response.json()
        #
        # # data = {"id": post_id, "is_saved": True, "initial_post_id": None}
        data = {"id": post_id, "is_saved": True}

        async with aiohttp.ClientSession() as session:
            async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                   json=data) as response:
                respns = await response.json()

        await edit_scheduled_post(call, callback_data, state)
    else:
        # async with aiohttp.ClientSession() as session:
        #     async with session.delete(
        #             url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/{initial_post_id}/") as response:
        #         respns = await response.json()

        data = {"id": post_id, "is_saved": True}

        async with aiohttp.ClientSession() as session:
            async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                   json=data) as response:
                respns = await response.json()

        await edit_post(call, callback_data, state)


# Content.Edit_Media
async def edit_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg = data.get("msg")
    post_id = int(data.get("post_id"))
    action = data.get("action")

    await message.bot.delete_message(message.from_user.id, msg)

    file_id = message.photo[-1].file_id
    media_type = "photo"
    data = {"id": post_id,
            "media": []}
    media_info = {
        'sequence_number': 1,
        'file_id': file_id,
        'media_type': media_type}
    data["media"].append(media_info)

    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/", json=data) as response:
            respns = await response.json()
    await state.reset_state()
    await edit_scheduled_post_message(message, state, post_id, action)


def register_setting_media(dp: Dispatcher):
    dp.register_callback_query_handler(pre_edit_media, custom_media.filter(action="None"))
    dp.register_callback_query_handler(pre_edit_media, custom_media_content.filter(action="None"))

    dp.register_callback_query_handler(choise_photo, replace_media.filter(action="choise"))

    dp.register_callback_query_handler(add_media, custom_media.filter(action="add_media"))
    dp.register_message_handler(add_photo_group, IsMediaGroup(), state=Create.Add_Media,
                                content_types=[types.ContentType.PHOTO,
                                               types.ContentType.VIDEO,
                                               types.ContentType.DOCUMENT,
                                               types.ContentType.AUDIO,
                                               types.ContentType.ANIMATION,
                                               types.ContentType.VIDEO_NOTE])
    dp.register_message_handler(add_photo, state=Create.Add_Media,
                                content_types=[types.ContentType.PHOTO,
                                               types.ContentType.VIDEO,
                                               types.ContentType.DOCUMENT,
                                               types.ContentType.AUDIO,
                                               types.ContentType.ANIMATION,
                                               types.ContentType.VIDEO_NOTE])
    dp.register_callback_query_handler(replace, replace_media.filter(action="replace"))
    dp.register_message_handler(replace_photo, state=Create.Replace_Media,
                                content_types=[types.ContentType.PHOTO, types.ContentType.VIDEO])
    dp.register_callback_query_handler(delete_photo, replace_media.filter(action="delete"))

    dp.register_callback_query_handler(swap_media, swap_media_clb.filter(action="swap_media"))
    dp.register_callback_query_handler(swapped_media, swap_media_clb.filter(action="send_swapped"))

    dp.register_callback_query_handler(previous_saved_media, custom_media.filter(action="back"))
    dp.register_callback_query_handler(save_media, custom_media.filter(action="save"))

    dp.register_message_handler(edit_photo, state=Content.Edit_Media, content_types=types.ContentType.PHOTO)
