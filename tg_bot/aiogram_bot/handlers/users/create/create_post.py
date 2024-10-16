import json
import logging
from typing import List

import aiohttp
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram_media_group import media_group_handler

from tg_bot import config, subscription_api, channel_api
from tg_bot.aiogram_bot.filters.is_admin import IsMediaGroup
from tg_bot.aiogram_bot.handlers.users.create.functions import user_channel_func, message_is_channel_func, \
    edit_post_func, gpt_choice_func, get_message_func, prompt_choice_func, prompt_message_func
from tg_bot.aiogram_bot.handlers.users.subscription_payment.state import SubscriptionPaymentState
from tg_bot.aiogram_bot.keyboards.inline.content_inline.content import redaction_clb
from tg_bot.aiogram_bot.keyboards.inline.create_inline.calendar_create import sending_clbk, choose_time
from tg_bot.aiogram_bot.keyboards.inline.create_inline.create import creating_clb, add_descrip, cancel_create, \
    url_buttons_clb, gpt_clb, auto_sign_clb, choose_prompts, create_sign, create_post_prompt
from tg_bot.aiogram_bot.keyboards.inline.parsing import add_channel_clb
from tg_bot.aiogram_bot.keyboards.inline.subscription_payment.inline_button import subscription_payment_clb, \
    subscription_payment_back_clb
from tg_bot.aiogram_bot.network.dto.channel import ChannelSchema
from tg_bot.aiogram_bot.network.dto.response import Response
from tg_bot.aiogram_bot.network.dto.subscription import SubscriptionSchema
from tg_bot.aiogram_bot.states.users import Create, CreatePost


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


async def to_payment(message: types.Message):
    _ = message.bot.get("lang")
    subscription_response: Response[SubscriptionSchema] = Response[SubscriptionSchema].model_validate(
        await subscription_api.get_one_by_key_value(
            params={"key": "id", "value": 1}
        ))
    keyboard = InlineKeyboardMarkup(row_width=1)
    pay_btn = _("💰 Оплата подписки")
    user_info_button = InlineKeyboardButton(text=pay_btn,
                                            callback_data=subscription_payment_clb.new(
                                                a="s_p", p="None", t="None"))
    keyboard.add(user_info_button)
    text = _("Вы можете пользоваться ботом бесплатно, пока ваш канал не достигнет отметки в {} подписчиков. Чтобы "
             "сразу продлить доступ, нажмите на кнопку ниже.").format(subscription_response.data.subscribers_quantity)
    await message.answer(text, reply_markup=keyboard)


async def back_to_creating(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.reset_state()
    await call.bot.delete_message(call.from_user.id, call.message.message_id)

    if "post_id" in callback_data:
        post_id = callback_data['post_id']
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/{post_id}"
            ) as response:
                respns = await response.json()

    await user_channel_func(call_message=call)


async def cancel_post(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.reset_state()
    _ = call.bot.get("lang")

    post_id = callback_data['post_id']

    async with aiohttp.ClientSession() as session:
        async with session.delete(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/{post_id}"
        ) as response:
            post_response = await response.json()

    if post_response.get("status") == "error":
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/post/one",
                    json={"id": post_id}
            ) as response:
                post_response = await response.json()

    messages_id = post_response.get("data").get("messages_id")
    if messages_id:
        for message_id in messages_id:
            await call.bot.delete_message(call.from_user.id, message_id)

    await call.bot.delete_message(call.from_user.id, call.message.message_id)
    text = _("❌ Создание поста отменено")
    await call.bot.send_message(chat_id=call.from_user.id, text=text)


async def new_post(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()
    _ = call.bot.get("lang")
    await call.bot.delete_message(call.from_user.id, call.message.message_id)
    id_channel = int(callback_data.get("channel_id"))

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
        back_btn_text = _("⬅️ Назад")
        next_btn_text = _("➡️ Далее")
        subscription_payment_free_button = InlineKeyboardButton(text=button_txt,
                                                                callback_data=subscription_payment_clb.new(
                                                                    a="c",
                                                                    p='creating',
                                                                    t="f"
                                                                ))
        keyboard.add(subscription_payment_free_button)

        back = InlineKeyboardButton(text=back_btn_text,
                                    callback_data=subscription_payment_back_clb.new(
                                        a="s_p_b",
                                        p="creating",
                                        t="None"
                                    ))
        next = InlineKeyboardButton(text=next_btn_text,
                                    callback_data=subscription_payment_clb.new(
                                        a="s_p_n",
                                        p="creating",
                                        t="f"))
        keyboard.row(back, next)
        text = _("💰 ОПЛАТА ПОДПИСКИ\n\nЧтобы пользоваться Harvestly, необходима платная подписка. Чтобы подключить "
                 "подписку для ваших каналов, нажмите «Далее».\n\nИли попробуйте бесплатную версию:")
        await call.bot.send_message(
            chat_id=call.from_user.id,
            text=text,
            reply_markup=keyboard)

        await state.reset_state()
        await SubscriptionPaymentState.Get_Message.set()
    else:
        data = {"user_id": call.from_user.id,
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

        data = {"user_id": call.from_user.id,
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

        data = {"id": id_channel}
        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel/one/",
                                    json=data) as response:
                respns = await response.json()

        title = respns.get("data").get("title")
        link = respns.get("data").get("link")
        url = f"<a href='{link}'>{title}</a>"
        text = _("Отправьте или перешлите боту то, что хотите опубликовать в канале {}").format(url)
        another_channel = _("⬅️ Выбрать другой канал")

        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton(text=another_channel, callback_data=cancel_create.new(post_id=post_id)))

        msg = await call.bot.send_message(call.from_user.id, text, reply_markup=markup)

        await Create.Get_Message.set()
        await state.update_data(msg=msg.message_id)
        await state.update_data(post_id=post_id)


async def description(call: CallbackQuery, callback_data: dict, state: FSMContext):
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
    await delete_messages(call, post_id)

    text = _("Отправьте новый текст для поста")
    markup = InlineKeyboardMarkup(row_width=1)
    back_btn_text = _("⬅️ Назад")
    markup.add(InlineKeyboardButton(text=back_btn_text,
                                    callback_data=choose_prompts.new(action="back", index=999, post_id=post_id)))
    msg = await call.bot.send_message(call.from_user.id, text, reply_markup=markup)
    await Create.Get_Description.set()
    await state.update_data(msg=msg.message_id)
    await state.update_data(post_id=post_id)


# Create.Get_Description
async def description_add(message: types.Message, state: FSMContext):
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


async def url_buttons(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get("lang")
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

    text = _("⛓ <b>URL-КНОПКИ</b>\n\n" \
             "Отправьте боту список URL-кнопок в следующем формате:\n\n" \
             "<code>Название кнопки 1 - <b>http://link.com</b></code>\n" \
             "<code>Название кнопки 2 - <b>http://link.com</b></code>\n\n" \
             "Используйте разделитель '|', чтобы добавить до 8 кнопок в один ряд (допустимо 15 рядов):\n\n" \
             "<code>Название кнопки 1 - <b>http://link.com</b> | Название кнопки 2 - <b>http://link.com</b></code>")

    markup = InlineKeyboardMarkup(row_width=1)
    back_btn_text = _("⬅️ Назад")
    markup.add(InlineKeyboardButton(text=back_btn_text,
                                    callback_data=choose_prompts.new(action="back", index=999, post_id=post_id)))
    msg = await call.bot.send_message(call.from_user.id, text, reply_markup=markup)

    await Create.Get_URL.set()
    await state.update_data(msg=msg.message_id)
    await state.update_data(post_id=post_id)


# Create.Get_URL
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
            await call.answer(text, show_alert=True)
            return

    respons = await delete_messages(call, post_id)
    await call.answer()

    id_channel = int(respons.get("data").get("channel_id"))
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
    auto_sign = response2.get("data").get("auto_sign")
    auto_sign_text = response2.get("data").get("auto_sign_text")

    if not auto_sign and auto_sign_text is None:
        markup = InlineKeyboardMarkup(row_width=1)
        text = _("✍️ АВТОПОДПИСЬ\n\n" \
                 "Вы можете настроить подпись, которая будет автоматически добавляться " \
                 "ко всем вашим публикациям.\n\n" \
                 "Отправьте текст для автоподписи.")
        back = _("⬅️ Назад")
        markup.add(InlineKeyboardButton(text=back,
                                        callback_data=create_sign.new(post_id=post_id)))
        await call.bot.send_message(call.from_user.id, text, reply_markup=markup)
        await Create.Sign.set()
        await state.update_data(id_channel=id_channel)
        await state.update_data(post_id=post_id)
        return
    elif not auto_sign:
        new_auto_sign = True
    elif auto_sign:
        new_auto_sign = False

    data = {"id": user_channel_settings_id,
            "auto_sign": new_auto_sign}
    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel_settings/",
                               json=data) as response:
            unused_response = await response.json()
    await edit_post(call, callback_data, state)


async def create_sign_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    _ = message.bot.get("lang")
    id_channel = int(data.get("id_channel"))
    post_id = int(data.get("post_id"))
    sign = message.text

    data = {"user_id": message.from_user.id,
            "channel_id": id_channel}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel/one/",
                                json=data) as response:
            response1 = await response.json()
    user_channel_settings_id = int(response1.get("data").get("user_channel_settings_id"))

    data = {"id": user_channel_settings_id,
            "auto_sign": True,
            "auto_sign_text": sign,
            "auto_sign_entities": json.dumps([entity.to_python() for entity in message.entities])
            if message.entities else None}

    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel_settings/",
                               json=data) as response:
            response2 = await response.json()
    await state.reset_state()
    if response2.get('status') == "success":
        text = _("Вы успешно добавили автоподпись.")
        await message.answer(text)
        await edit_post_message(message, state, post_id)


# Create.AddPrompt
async def add_prompt(message: types.Message, state: FSMContext):
    text = message.text.split(" - ")
    _ = message.bot.get("lang")
    key = text[0]
    value = text[1]

    data = await state.get_data()
    id_channel = int(data.get("channel_id"))
    post_id = int(data.get("post_id"))

    data = {"user_id": message.from_user.id,
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

    if gpt_prompts is not None:
        json_obj = {key: value}
        gpt_prompts.append(json_obj)
    else:
        json_obj = {key: value}
        gpt_prompts = [json_obj]

    data = {"id": user_channel_settings_id,
            "prompts": gpt_prompts}
    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel_settings/",
                               json=data) as response:
            response3 = await response.json()

    if response3.get('status') == "success":
        await state.reset_state()
        text = _("✅ Вы успешно добавили промпт {} в HarvestlyBot.").format(key)
        await message.answer(text)
        await gpt_choice_message(message=message,
                                 callback_data={"channel_id": id_channel, "post_id": post_id},
                                 state=state)


async def user_channels(message: types.Message, state: FSMContext):
    await state.reset_state()
    await user_channel_func(call_message=message)


async def add_channel_func(call: CallbackQuery, callback_data: dict):
    await call.answer()
    await call.bot.delete_message(call.from_user.id, call.message.message_id)

    _ = call.bot.get("lang")

    user_channel_response: Response[list[ChannelSchema]] = Response[list[ChannelSchema]].model_validate(
        await channel_api.get_user_channels_with_certain_subscriptions(data={
            "user_id": call.from_user.id,
            "disabled": False
        }))

    if len(user_channel_response.data) > 0:
        text = _("Чтобы подключить канал, сделайте @{} его администратором, дав следующие права:\n\n"
                 "✅ Отправка сообщений\n"
                 "✅ Удаление сообщений\n"
                 "✅ Редактирование сообщений\n\n"
                 "А затем перешлите любое сообщений канала в диалог с ботом либо отправьте публичную ссылку на ваш канал.").format(
            (await call.bot.get_me()).username)
    else:
        text = _("<b>У вас пока нет подключенных каналов.</b>\n\n"
                 "Чтобы подключить первый канал, сделайте @{} его администратором, дав следующие права:\n\n"
                 "✅ Отправка сообщений\n"
                 "✅ Удаление сообщений\n"
                 "✅ Редактирование сообщений\n\n"
                 "А затем перешлите любое сообщений канала в диалог с ботом либо отправьте публичную ссылку на ваш канал.").format(
            (await call.bot.get_me()).username)

    await call.bot.send_message(chat_id=call.from_user.id, text=text)
    await CreatePost.Message_Is_Channel.set()


# CreatePost.Message_Is_Channel
async def message_is_channel(message: types.Message, state: FSMContext):
    await message_is_channel_func(message, state)


@media_group_handler
async def message_is_channel_group(message: List[types.Message], state: FSMContext):
    await message_is_channel_func(message[0], state)


# Create.Get_Message
@media_group_handler
async def get_photo_group(messages: List[types.Message], state: FSMContext):
    await get_message_func(type="media_group", message=messages, state=state)


# Create.Get_Message
async def get_photo(message: types.Message, state: FSMContext):
    await get_message_func(type="media", message=message, state=state)


# Create.Get_Message
async def get_text(message: types.Message, state: FSMContext):
    await get_message_func(type="text", message=message, state=state)


async def edit_post_message(message: types.Message, state: FSMContext, post_id: int):
    await edit_post_func(call_message=message, state=state, post_id=post_id)


async def edit_post(call: CallbackQuery, callback_data: dict, state: FSMContext, delete: bool = True):
    post_id = int(callback_data['post_id'])
    await edit_post_func(call_message=call, state=state, post_id=post_id, delete=delete)


async def gpt_choice_message(message: types.Message, callback_data: dict, state: FSMContext):
    await gpt_choice_func(call_message=message, callback_data=callback_data, state=state)


async def gpt_choice(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await gpt_choice_func(call_message=call, callback_data=callback_data, state=state)


async def create_sign_back_handler(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.reset_state()
    await call.answer()
    await edit_post(call, callback_data, state)


async def add_prompt_message(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await prompt_message_func(call=call, callback_data=callback_data, state=state, type="add_prompt")


async def generate_prompt_message(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await prompt_message_func(call=call, callback_data=callback_data, state=state, type="generate_prompt")


async def prompt_choice(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()
    index = int(callback_data.get("index"))
    post_id = int(callback_data.get("post_id"))
    await prompt_choice_func(post_id=post_id, index=index, call_message=call, state=state)


async def generate_prompt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    post_id = int(data.get("post_id"))

    await prompt_choice_func(post_id=post_id, index=None, call_message=message, state=state)


def register_create_post(dp: Dispatcher):
    dp.register_message_handler(user_channels, text="Создать пост", state="*")
    dp.register_message_handler(user_channels, text="Создать пост")

    dp.register_callback_query_handler(add_channel_func, add_channel_clb.filter())

    dp.register_message_handler(message_is_channel_group, IsMediaGroup(),
                                content_types=['text', 'photo', 'video', 'video_note'],
                                state=CreatePost.Message_Is_Channel)
    dp.register_message_handler(message_is_channel, content_types=['text', 'photo', 'video', 'video_note'],
                                state=CreatePost.Message_Is_Channel)

    dp.register_callback_query_handler(cancel_post, cancel_create.filter())
    dp.register_callback_query_handler(back_to_creating, cancel_create.filter(), state=Create)

    dp.register_callback_query_handler(edit_post, choose_prompts.filter(action="back"), state="*")
    dp.register_callback_query_handler(edit_post, choose_time.filter(action="back"))
    dp.register_callback_query_handler(edit_post, sending_clbk.filter(action="back"))

    dp.register_callback_query_handler(new_post, creating_clb.filter())
    dp.register_callback_query_handler(new_post, redaction_clb.filter(action="redaction"))

    dp.register_message_handler(get_photo_group,
                                IsMediaGroup(),
                                state=Create.Get_Message,
                                content_types=[types.ContentType.PHOTO,
                                               types.ContentType.VIDEO,
                                               types.ContentType.DOCUMENT,
                                               types.ContentType.AUDIO,
                                               types.ContentType.ANIMATION])

    dp.register_message_handler(get_photo,
                                state=Create.Get_Message,
                                content_types=[types.ContentType.PHOTO,
                                               types.ContentType.VIDEO,
                                               types.ContentType.DOCUMENT,
                                               types.ContentType.AUDIO,
                                               types.ContentType.ANIMATION,
                                               types.ContentType.VIDEO_NOTE])

    dp.register_message_handler(get_text,
                                state=Create.Get_Message,
                                content_types=types.ContentType.TEXT)

    dp.register_callback_query_handler(description, add_descrip.filter())
    dp.register_message_handler(description_add, state=Create.Get_Description)

    dp.register_callback_query_handler(url_buttons, url_buttons_clb.filter())
    dp.register_message_handler(url_buttons_add, state=Create.Get_URL)

    dp.register_callback_query_handler(auto_sign_change, auto_sign_clb.filter())

    dp.register_callback_query_handler(gpt_choice, gpt_clb.filter())
    dp.register_callback_query_handler(prompt_choice, choose_prompts.filter(action="next"))

    dp.register_callback_query_handler(create_sign_back_handler, create_sign.filter(), state=Create.Sign)
    dp.register_message_handler(create_sign_handler, state=Create.Sign)

    dp.register_callback_query_handler(add_prompt_message, create_post_prompt.filter(action="add_prompt"))
    dp.register_callback_query_handler(generate_prompt_message, create_post_prompt.filter(action="generate_prompt"))

    dp.register_message_handler(add_prompt, state=Create.AddPrompt)
    dp.register_message_handler(generate_prompt, state=Create.GeneratePrompt)

    dp.register_callback_query_handler(gpt_choice, create_post_prompt.filter(action="back_to_add"),
                                       state=[Create.AddPrompt, Create.GeneratePrompt])
