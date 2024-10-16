import copy
import datetime
import json
import logging
from typing import Union

import aiohttp
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Chat

from tg_bot import channel_api, user_channel_settings_api, user_api, user_channel_api, config
from tg_bot.aiogram_bot.keyboards.inline.create_inline.calendar_create import further

from tg_bot.aiogram_bot.keyboards.inline.create_inline.create import creating_clb, choose_prompts, create_post_prompt, \
    add_descrip, url_buttons_clb, gpt_clb, custom_media, auto_sign_clb, cancel_create
from tg_bot.aiogram_bot.keyboards.inline.parsing import add_channel_clb
from tg_bot.aiogram_bot.network.dto.channel import ChannelSchema
from tg_bot.aiogram_bot.network.dto.response import Response
from tg_bot.aiogram_bot.network.dto.user import UserSchema
from tg_bot.aiogram_bot.network.dto.user_channel import UserChannelSchema
from tg_bot.aiogram_bot.network.dto.user_channel_settings import UserChannelSettingsSchema
from tg_bot.aiogram_bot.states.users import CreatePost, Create
from tg_bot.aiogram_bot.utils.utils import is_telegram_channel_link, extract_channel_username, count_characters


async def markup_media(markup, descrip_button, exist_auto_sign, id_channel, post_id, _):
    url_btn_text = _("URL-кнопки")
    adjust_media_btn_text = _("Настроить медиа")
    chat_gpt_btn_text = _("Chat GPT")
    auto_sign_btn_text = _("Автоподпись")
    cancel_btn_text = _("Отмена")
    next_btn_text = _("Далее")

    markup.row(InlineKeyboardButton(text=descrip_button, callback_data=add_descrip.new(post_id=post_id)))
    markup.row(InlineKeyboardButton(text=url_btn_text, callback_data=url_buttons_clb.new(post_id=post_id)),
               InlineKeyboardButton(text=adjust_media_btn_text,
                                    callback_data=custom_media.new(action="None", post_id=post_id)))
    markup.row(InlineKeyboardButton(text=chat_gpt_btn_text, callback_data=gpt_clb.new(post_id=post_id)),
               InlineKeyboardButton(text=f"{exist_auto_sign} {auto_sign_btn_text}",
                                    callback_data=auto_sign_clb.new(post_id=post_id)))
    markup.row(InlineKeyboardButton(text=f"❌ {cancel_btn_text}", callback_data=cancel_create.new(post_id=post_id)),
               InlineKeyboardButton(text=f"➡️ {next_btn_text}",
                                    callback_data=further.new(channel_id=id_channel, post_id=post_id)))
    return markup


async def user_channel_func(call_message: CallbackQuery | types.Message):
    _ = call_message.bot.get("lang")
    user_channel_response: Response[list[ChannelSchema]] = Response[list[ChannelSchema]].model_validate(
        await channel_api.get_user_channels_with_certain_subscriptions(data={
            "user_id": call_message.from_user.id,
            "disabled": False
        }))

    text = _("<b>У вас пока нет подключенных каналов.</b>\n\n" \
             "Чтобы подключить первый канал, сделайте @{} его администратором, дав следующие права:\n\n" \
             "✅ Отправка сообщений\n" \
             "✅ Удаление сообщений\n" \
             "✅ Редактирование сообщений\n\n" \
             "А затем перешлите любое сообщений канала в диалог с ботом либо отправьте публичную ссылку на ваш канал.").format(
        (await call_message.bot.get_me()).username)

    if len(user_channel_response.data) > 0:
        text = _("<b>📝 СОЗДАНИЕ ПОСТА</b>\n\n" \
                 "Выберите канал, в котором хотите создать публикацию")

        markup = InlineKeyboardMarkup(row_width=2)
        for user_channel in user_channel_response.data:
            markup.insert(InlineKeyboardButton(text=f"{user_channel.title}",
                                               callback_data=creating_clb.new(channel_id=user_channel.id)))
        new_channel_btn = _("➕ Добавить новый канал")
        markup.add(InlineKeyboardButton(text=new_channel_btn, callback_data=add_channel_clb.new()))
        await call_message.bot.send_message(call_message.from_user.id, text, reply_markup=markup)
    else:
        await call_message.answer(text)
        await CreatePost.Message_Is_Channel.set()


async def message_is_channel_func(message: types.Message, state: FSMContext):
    add = False
    channel_username = None
    _ = message.bot.get("lang")

    print(message)

    if message.forward_from_chat and message.forward_from_chat.type == types.ChatType.CHANNEL:
        channel_username = message.forward_from_chat.id
        member = await message.bot.get_chat_member(channel_username, message.bot.id)
        is_admin = member.is_chat_admin()

        if is_admin:
            owner_admins: list[Union[
                types.ChatMemberOwner | types.ChatMemberAdministrator]] = await message.bot.get_chat_administrators(
                chat_id=channel_username)

            for user in owner_admins:
                if user.user.id == message.from_user.id:
                    add = True
                    break

            if not add:
                text = _("Вы не являетесь ни администратором, ни владельцем канала")
                await message.answer(text)
                return
        else:
            text = _("Сделайте бота администратором канала")
            await message.answer(text)
            return

    elif is_telegram_channel_link(message.text):
        channel_username = extract_channel_username(message.text)
        member = await message.bot.get_chat_member(channel_username, message.bot.id)
        is_admin = member.is_chat_admin()

        if is_admin:
            owner_admins: list[Union[
                types.ChatMemberOwner | types.ChatMemberAdministrator]] = await message.bot.get_chat_administrators(
                chat_id=channel_username)

            for user in owner_admins:
                if user.user.id == message.from_user.id:
                    add = True
                    break

            if not add:
                text = _("Вы не являетесь ни администратором, ни владельцем канала")
                await message.answer(text)
                return
        else:
            text = _("Сделайте бота администратором канала")
            await message.answer(text)
            return

    if add:
        show_payment = False
        channel_info: Chat = await message.bot.get_chat(channel_username)

        channel_response: Response[ChannelSchema] = Response[ChannelSchema].model_validate(
            await channel_api.get_one_by_key_value(
                params={"key": "id", "value": channel_info.id}
            ))

        if channel_response.data is None:
            channel_response: Response[ChannelSchema] = Response[ChannelSchema].model_validate(
                await channel_api.post_add(data={
                    "id": channel_info.id,
                    "title": channel_info.title,
                    "link": f"https://t.me/{channel_info.username if channel_info.username else channel_info.invite_link}"
                }))

            user_channel_settings_response: Response[UserChannelSettingsSchema] = Response[
                UserChannelSettingsSchema].model_validate(
                await user_channel_settings_api.post_add(data={}))

            owner_admins = await message.bot.get_chat_administrators(chat_id=channel_info.id)

            for user in owner_admins:
                if not user.user.is_bot:
                    data = {"id": user.user.id, "time_zone": 0}

                    if user.user.id != message.from_user.id:
                        user_response: Response[UserSchema] = Response[UserSchema].model_validate(
                            await user_api.post_add(data=data))

                    user_channel_response: Response[UserChannelSchema] = Response[UserChannelSchema].model_validate(
                        await user_channel_api.post_add(data={
                            "channel_id": channel_response.data.id,
                            "user_id": user.user.id,
                            "user_channel_settings_id": user_channel_settings_response.data.id
                        }))

            show_payment = True

            if channel_info.username is not None:
                link = channel_info.username
            elif channel_info.invite_link is not None:
                link = channel_info.invite_link
            else:
                link = ""

            text = _("✅ Канал <a href='https://t.me/{}'>{}</a> успешно привязан к Harvestly").format(link,
                                                                                                     channel_info.title)
            await message.answer(text)

        else:
            user_channel_response: Response[UserChannelSchema] = Response[UserChannelSchema].model_validate(
                await user_channel_api.post_one(data={
                    "user_id": message.from_user.id,
                    "channel_id": channel_response.data.id
                })
            )

            user_channel_settings: Response[UserChannelSettingsSchema] = Response[
                UserChannelSettingsSchema].model_validate(
                await user_channel_settings_api.get_one_by_key_value(
                    params={
                        "key": "id",
                        "value": user_channel_response.data.user_channel_settings_id
                    }
                )
            )

            if user_channel_settings.data.subscription_id is None or user_channel_settings.data.subscription_id == 1:
                show_payment = True

            if user_channel_settings.data.disabled:
                await user_channel_settings_api.put(
                    data={
                        "id": user_channel_settings.data.id,
                        "disabled": False
                    }
                )

            if channel_info.username is not None:
                link = channel_info.username
            elif channel_info.invite_link is not None:
                link = channel_info.invite_link
            else:
                link = ""

            text = _("✅ Канал <a href='https://t.me/{}'>{}</a> успешно привязан к Harvestly").format(link,
                                                                                                     channel_info.title)
            await message.answer(text)

        await state.reset_state()

        if show_payment:
            from tg_bot.aiogram_bot.handlers.users.create.create_post import to_payment
            await to_payment(message)


async def edit_post_func(call_message: CallbackQuery | types.Message, state: FSMContext, post_id: int,
                         delete: bool = True):
    await state.reset_state()

    try:
        if delete:
            if type(call_message) == CallbackQuery:
                await call_message.bot.delete_message(call_message.from_user.id, call_message.message.message_id)
            else:
                await call_message.bot.delete_message(call_message.from_user.id, call_message.message_id)
    except Exception as e:
        logging.error(f"edit_post_func {e}")

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
            await call_message.bot.delete_message(call_message.from_user.id, msg_id)

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

    data = {"user_id": call_message.from_user.id,
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
    exist_auto_sign = ""
    auto_sign_entities = response3.get('data').get('auto_sign_entities')
    auto_sign_entities = [types.MessageEntity(**entity) for entity in
                          json.loads(auto_sign_entities)] if auto_sign_entities else None

    combined_entities = copy.deepcopy(entities)
    _ = call_message.bot.get("lang")

    if caption is not None:
        auto_sign_text = response3.get("data").get("auto_sign_text")

        if str(auto_sign) == "True":
            if auto_sign_text is not None:
                caption += f"\n\n{auto_sign_text}"
                exist_auto_sign = "✅ "

                text_length = count_characters(caption)
                auto_sign_len = count_characters(auto_sign_text)

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

        descrip_button = _("Изменить описание")

    else:
        auto_sign_text = response3.get("data").get("auto_sign_text")
        if str(auto_sign) == "True":
            if auto_sign_text is not None:
                caption = f"\n\n{auto_sign_text}"
                descrip_button = _("Изменить описание")
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

            messages = await call_message.bot.send_media_group(chat_id=call_message.from_user.id, media=media)
            markup = await markup_media(markup, descrip_button, exist_auto_sign, id_channel, post_id, _)

            data = {"id": post_id,
                    "messages_id": [message["message_id"] for message in messages]}

            async with aiohttp.ClientSession() as session:
                async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                       json=data) as response:
                    unused_response = await response.json()

            await call_message.bot.send_message(call_message.from_user.id, caption, reply_markup=markup)

        else:
            media_id = media_data[0]

            caption = "(Описание)" if caption is None else caption

            if media_id.get("media_type") == "photo":
                markup = await markup_media(markup, descrip_button, exist_auto_sign, id_channel, post_id, _)
                msg = await call_message.bot.send_photo(call_message.from_user.id, media_id.get("file_id"), caption,
                                                        caption_entities=combined_entities,
                                                        reply_markup=markup)

            elif media_id.get("media_type") == "video":
                markup = await markup_media(markup, descrip_button, exist_auto_sign, id_channel, post_id, _)
                msg = await call_message.bot.send_video(call_message.from_user.id, media_id.get("file_id"),
                                                        caption=caption,
                                                        caption_entities=combined_entities,
                                                        reply_markup=markup)

            elif media_id.get("media_type") == "document":
                markup = await markup_media(markup, descrip_button, exist_auto_sign, id_channel, post_id, _)
                msg = await call_message.bot.send_document(call_message.from_user.id, media_id.get("file_id"),
                                                           caption_entities=combined_entities,
                                                           caption=caption, reply_markup=markup)

            elif media_id.get("media_type") == "audio":
                markup = await markup_media(markup, descrip_button, exist_auto_sign, id_channel, post_id, _)
                msg = await call_message.bot.send_audio(call_message.from_user.id, media_id.get("file_id"),
                                                        caption=caption,
                                                        caption_entities=combined_entities,
                                                        reply_markup=markup)

            elif media_id.get("media_type") == "video_note":
                markup = await markup_media(markup, descrip_button, exist_auto_sign, id_channel, post_id, _)
                msg = await call_message.bot.send_video_note(call_message.from_user.id, media_id.get("file_id"),
                                                             reply_markup=markup)

            elif media_id.get("media_type") == "animation":
                markup = await markup_media(markup, descrip_button, exist_auto_sign, id_channel, post_id, _)
                msg = await call_message.bot.send_animation(call_message.from_user.id, media_id.get("file_id"),
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
        markup = await markup_media(markup, descrip_button, exist_auto_sign, id_channel, post_id, _)
        await call_message.bot.send_message(call_message.from_user.id, caption, reply_markup=markup,
                                            entities=combined_entities)


async def gpt_choice_func(call_message: CallbackQuery | types.Message, callback_data: dict, state: FSMContext):
    await state.reset_state()
    _ = call_message.bot.get("lang")
    post_id = int(callback_data.get("post_id"))

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
            await call_message.answer(text=text, show_alert=True)
            return

    id_channel = int(response1.get("data").get("channel_id"))

    data = {"user_id": call_message.from_user.id,
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
            subscription_id = response2.get("data").get("subscription_id")

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/{call_message.from_user.id}/") as response:
            response1 = await response.json()
            gpt_api_key = response1.get("data").get("gpt_api_key")

    if gpt_api_key is None and (subscription_id == 1 or subscription_id is None):
        text = _("⚠️ Чтобы пользоваться промптаим в Harvestly вы должны привязать свой аккаунт Chat GPT или Оплатить "
                 "подписку")
        await call_message.answer(text=text)
        return

    if gpt_prompts:
        for prompt in gpt_prompts:
            for key in prompt.keys():
                markup.insert(InlineKeyboardButton(text=f"{key}", callback_data=choose_prompts.new(action="next",
                                                                                                   index=gpt_prompts.index(
                                                                                                       prompt),
                                                                                                   post_id=post_id)))
    add_btn = _("Добавить")
    generation_btn = _("Моментальная генерация")
    back_btn = _("⬅️ Назад")
    markup.add(InlineKeyboardButton(text=add_btn,
                                    callback_data=create_post_prompt.new(channel_id=id_channel,
                                                                         post_id=post_id,
                                                                         action="add_prompt")))

    markup.add(InlineKeyboardButton(text=generation_btn,
                                    callback_data=create_post_prompt.new(channel_id=id_channel,
                                                                         post_id=post_id,
                                                                         action="generate_prompt")))

    markup.add(InlineKeyboardButton(text=back_btn,
                                    callback_data=choose_prompts.new(action="back", index=999, post_id=post_id)))

    message_id = call_message.message.message_id if type(call_message) == CallbackQuery else call_message.message_id

    try:
        await call_message.bot.edit_message_text(text=text, chat_id=call_message.from_user.id,
                                                 message_id=message_id,
                                                 reply_markup=markup)
    except Exception as e:
        await call_message.bot.send_message(chat_id=call_message.from_user.id,
                                            text=text,
                                            reply_markup=markup)


async def get_message_func(type: str, message: types.Message | list[types.Message], state: FSMContext):
    data = await state.get_data()
    msg = data.get("msg")
    post_id = int(data.get("post_id"))

    caption = None
    caption_entities = None

    if type == "media_group":
        await message[0].bot.delete_message(message[0].from_user.id, msg)

        data = {"id": post_id,
                "media": []}
        sequence_number = 1

        for m in message:
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

    else:
        await message.bot.delete_message(message.from_user.id, msg)

        if type == "media":
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
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                               json=data) as response:
            respns = await response.json()

    if type == "media_group":
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

    elif type == "media":
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

    elif type == "text":
        data = {"id": post_id,
                "description": message.text,
                "entities": json.dumps([entity.to_python() for entity in message.entities])
                if message.entities else None}
        async with aiohttp.ClientSession() as session:
            async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                   json=data) as response:
                respns = await response.json()

    await state.reset_state()

    if type == "media_group":
        await edit_post_func(call_message=message[0], state=state, post_id=post_id)
    elif type == "media":
        await edit_post_func(call_message=message, state=state, post_id=post_id)
    elif type == "text":
        await edit_post_func(call_message=message, state=state, post_id=post_id)


async def prompt_choice_func(post_id: int, index: int | None,
                             call_message: CallbackQuery | types.Message,
                             state: FSMContext):
    print("prompt_choice_func", index)
    _ = call_message.bot.get("lang")
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one/key_value/",
                params={
                    "key": "id",
                    "value": post_id
                }) as response:
            response1 = await response.json()
    caption = response1.get("data").get("description")
    id_channel = int(response1.get("data").get("channel_id"))

    data = {"user_id": call_message.from_user.id,
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

    datetime_utc = datetime.datetime.utcnow()
    requested_date = datetime_utc.replace(microsecond=0).isoformat()

    if subscription_id == 2:
        user_ai_data = {"user_id": call_message.from_user.id,
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
                    "user_id": call_message.from_user.id,
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
                await call_message.bot.send_message(call_message.from_user.id, text)
                await edit_post_func(call_message=call_message, state=state, post_id=post_id)
                return

    else:
        user_response: Response[UserSchema] = Response[UserSchema].model_validate(
            await user_api.get_one_by_key_value(params={
                "key": "id",
                "value": call_message.from_user.id
            })
        )

        if user_response.data.gpt_api_key is not None:
            api_key = user_response.data.gpt_api_key
        else:
            text = _("Привяжите аккаунт Chat GPT в настройках канала, либо оплатите подписку")
            await call_message.bot.send_message(call_message.from_user.id, text)
            await edit_post_func(call_message=call_message, state=state, post_id=post_id)
            return

    if index is not None:
        data = {"content": f"{list(gpt_prompts[index].values())[0]}\n\n{caption}", "api_key": api_key}
    else:
        data = {"content": f"{call_message.text}\n\n{caption}", "api_key": api_key}

    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_chat_gpt}:{config.api.api_chat_gpt_port}/prompt/",
                                json=data) as response:
            respns = await response.json()

    if respns.get("status") == "success":
        data = {
            "id": post_id,
            "description": respns.get("data"),
            "entities": None}
        async with aiohttp.ClientSession() as session:
            async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/",
                                   json=data) as response:
                respns = await response.json()
        await edit_post_func(call_message=call_message, state=state, post_id=post_id)
    else:
        text = _("Преобразование текста не выполнилось")
        await call_message.bot.send_message(call_message.from_user.id, text)
        await edit_post_func(call_message=call_message, state=state, post_id=post_id)


async def prompt_message_func(call: CallbackQuery, callback_data: dict, state: FSMContext, type: str):
    await call.answer()
    _ = call.bot.get("lang")
    id_channel = int(callback_data.get("channel_id"))
    post_id = int(callback_data.get("post_id"))

    markup = InlineKeyboardMarkup(row_width=1)
    Back = _("⬅️ Назад")
    markup.add(InlineKeyboardButton(text=Back,
                                    callback_data=create_post_prompt.new(channel_id=id_channel, post_id=post_id,
                                                                         action="back_to_add")))
    if type == "generate_prompt":
        text = _("<b>⛓ CHAT GPT</b>\n\nОтправьте боту промпт в следующем формате:\n\n" \
                 "Пример:\n\n" \
                 "<b>Преобразуйте следующий текст, чтобы сделать его кратким и информативным, " \
                 "сохраняя при этом его основной смысл</b>")
        await Create.GeneratePrompt.set()

    elif type == "add_prompt":
        text = _("<b>⛓ CHAT GPT</b>\n\nОтправьте боту промпт в следующем формате:\n\n" \
                 "Название - Текст промпта\n\n" \
                 "Пример:\n\n" \
                 "Изменение текста - <b>Преобразуйте следующий текст, чтобы сделать его кратким и информативным, " \
                 "сохраняя при этом его основной смысл</b>")
        await Create.AddPrompt.set()

    await state.update_data(channel_id=id_channel)
    await state.update_data(post_id=post_id)

    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
