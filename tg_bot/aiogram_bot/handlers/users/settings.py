import json
from datetime import datetime

import aiohttp
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from tg_bot import config, user_api, open_ai_api, user_channel_api, user_channel_settings_api, \
    channel_for_parsing_association_api
from tg_bot.aiogram_bot.keyboards.inline.create_inline.settings_create import settings_channel, settings_timezone, \
    settings_chatgpt, set_gpt_api_key, del_prompt_clb, change_prompt_clb, \
    snap_gpt4_next, snap_gpt4, untie_gpt_account, update_auto_sign_clb, update_auto_send_clb
from tg_bot.aiogram_bot.keyboards.inline.parsing import add_channel_clb
from tg_bot.aiogram_bot.keyboards.inline.subscription_payment.inline_button import subscription_payment_clb
from tg_bot.aiogram_bot.network.dto.channel_for_parsing_association import ChannelForParsingAssociationSchema
from tg_bot.aiogram_bot.network.dto.response import Response
from tg_bot.aiogram_bot.network.dto.user import UserSchema
from tg_bot.aiogram_bot.network.dto.user_channel import UserChannelSchema
from tg_bot.aiogram_bot.network.dto.user_channel_settings import UserChannelSettingsSchema
from tg_bot.aiogram_bot.states.users import Settings
from tg_bot.aiogram_bot.utils.constants import FreeSubscription

time_zones = {
    0: "Линия смены дат",
    1: "Париж, Франция",
    2: "Афины, Греция",
    3: "Москва, Россия",
    4: "Дубай, ОАЭ",
    5: "Ташкент, Узбекистан",
    6: "Алматы, Казахстан",
    7: "Бангкок, Таиланд",
    8: "Пекин, Китай",
    9: "Токио, Япония",
    10: "Сидней, Австралия",
    11: "Апиа, Самоа",
    12: "Сува, Фиджи",
}


async def user_settings(message: types.Message, state: FSMContext):
    await state.reset_state()
    _ = message.bot.get("lang")
    data = {"user_id": message.from_user.id, "disabled": False}
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel/get_user_channels_with_certain_subscriptions/",
                json=data) as response:
            response1 = await response.json()

    markup = InlineKeyboardMarkup(row_width=2)
    text = _("⚙️ <b>НАСТРОЙКИ</b>\n\nВ этом разделе вы можете настроить работу с ботом, с отдельным каналом," \
             " а также добавить новый канал B HarvestlyBot")
    pay_btn = _("💰 Оплата подписки")

    markup.add(InlineKeyboardButton(text=pay_btn,
                                    callback_data=subscription_payment_clb.new(
                                        a="s_p_b", p="settings", t="None")))

    for i in range(0, len(response1.get('data')), 2):
        buttons_row = [
            InlineKeyboardButton(
                text=f"{response1.get('data')[j]['title']}",
                callback_data=settings_channel.new(
                    ch_id=response1.get('data')[j]['id'],
                    act="update",
                    ex="None")
            )
            for j in range(i, min(i + 2, len(response1.get('data'))))
        ]
        markup.row(*buttons_row)

    new_channel_btn = _("➕ Добавить новый канал")
    markup.add(InlineKeyboardButton(text=new_channel_btn, callback_data=add_channel_clb.new()))

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/{message.from_user.id}/") as response:
            response3 = await response.json()
            time_zone = int(response3.get("data").get('time_zone'))
    country = time_zones.get(time_zone)
    timezone_btn = _("Часовой пояс: GMT + {} {}").format(time_zone, country)
    link_GPT = _("⛓ Личный аккаунт GPT")
    markup.add(InlineKeyboardButton(text=timezone_btn,
                                    callback_data=settings_timezone.new(timezone=time_zone, act="next")))
    markup.add(InlineKeyboardButton(text=link_GPT,
                                    callback_data=set_gpt_api_key.new(act="snap_gpt4")))
    await message.bot.send_message(message.from_user.id, text, reply_markup=markup)


async def back_to_user_settings(call: CallbackQuery, delete=False):
    await call.answer()
    _ = call.bot.get("lang")

    data = {"user_id": call.from_user.id, "disabled": False}
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel/get_user_channels_with_certain_subscriptions/",
                json=data) as response:
            response1 = await response.json()

    markup = InlineKeyboardMarkup(row_width=2)
    text = _(f"⚙️ <b>НАСТРОЙКИ</b>\n\nВ этом разделе вы можете настроить работу с ботом, с отдельным каналом," \
             f" а также добавить новый канал B HarvestlyBot")

    subs_payment = _("💰 Оплата подписки")
    markup.add(InlineKeyboardButton(text=subs_payment,
                                    callback_data=subscription_payment_clb.new(
                                        a="s_p_b", p="settings", t="None")))

    for i in range(0, len(response1.get('data')), 2):
        buttons_row = [
            InlineKeyboardButton(
                text=f"{response1.get('data')[j]['title']}",
                callback_data=settings_channel.new(
                    ch_id=response1.get('data')[j]['id'],
                    act="update",
                    ex="None")
            )
            for j in range(i, min(i + 2, len(response1.get('data'))))
        ]
        markup.row(*buttons_row)

    new_channel_btn = _("➕ Добавить новый канал")
    markup.add(InlineKeyboardButton(text=new_channel_btn, callback_data=add_channel_clb.new()))

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/{call.from_user.id}/") as response:
            response3 = await response.json()
            time_zone = int(response3.get("data").get('time_zone'))
    country = time_zones.get(time_zone)
    timezone_btn = _("Часовой пояс: GMT + {} {}").format(time_zone, country)
    link_GPT = _("⛓ Личный аккаунт GPT")
    markup.add(InlineKeyboardButton(text=timezone_btn,
                                    callback_data=settings_timezone.new(timezone=time_zone, act="next")))
    markup.add(InlineKeyboardButton(text=link_GPT,
                                    callback_data=set_gpt_api_key.new(act="snap_gpt4")))
    if delete:
        await call.bot.delete_message(call.from_user.id, call.message.message_id)
        await call.bot.send_message(call.from_user.id, text, reply_markup=markup)
    else:
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def channel_settings(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    id_channel = int(callback_data.get("ch_id"))

    data = {"id": id_channel}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel/one/",
                                json=data) as response:
            response1 = await response.json()
    id = response1['data']['id']
    title = response1.get("data").get("title")
    link = response1.get("data").get("link")
    url = f"<a href='{link}'>{title}</a>"
    # channel_username = link.split("/")[-1]

    admins = await call.bot.get_chat_administrators(id)
    members = await call.bot.get_chat_members_count(id)
    admins_txt = ""

    user_channel_response: Response[list[UserChannelSchema]] = Response[
        list[UserChannelSchema]].model_validate(
        await user_channel_api.post_all(data={
            "channel_id": id_channel
        }))

    user_ids = [obj.user_id for obj in user_channel_response.data]
    admin_ids = []

    for obj in admins:
        if obj.user.is_bot is False:
            admin_ids.append(obj.user.id)

    user_ids_set = set(user_ids)
    admin_ids_set = set(admin_ids)

    removed = user_ids_set - admin_ids_set
    added = admin_ids_set - user_ids_set

    for admin in admins:
        admins_txt += f"@{admin.user.username}\n" if admin.user.username is not None else ""

    for removed_user in removed:
        user_channel_response: Response[UserChannelSchema] = Response[UserChannelSchema].model_validate(
            await user_channel_api.post_one(data={
                "channel_id": id_channel,
                "user_id": removed_user
            })
        )

        await user_channel_api.delete(id=user_channel_response.data.id)

        channel_for_parsing_association_response: Response[list[ChannelForParsingAssociationSchema]] = Response[
            list[ChannelForParsingAssociationSchema]].model_validate(
            await channel_for_parsing_association_api.post_all(
                data={
                    "channel_id": id_channel,
                    "user_id": removed_user
                }
            )
        )

        for channel_for_parsing_association in channel_for_parsing_association_response.data:
            await channel_for_parsing_association_api.delete(id=channel_for_parsing_association.id)

    for added_user in added:
        data = {"id": added_user, "time_zone": 0}

        user_response: Response[UserSchema] = Response[UserSchema].model_validate(
            await user_api.post_add(data=data))

        # if user_response.status == "success":
        user_channel_response: Response[list[UserChannelSchema]] = Response[
            list[UserChannelSchema]].model_validate(
            await user_channel_api.post_all(data={
                "channel_id": id_channel
            })
        )

        user_channel_settings: Response[UserChannelSettingsSchema] = Response[
            UserChannelSettingsSchema].model_validate(
            await user_channel_settings_api.get_one_by_key_value(
                params={
                    "key": "id",
                    "value": user_channel_response.data[0].user_channel_settings_id
                }
            )
        )

        await user_channel_api.post_add(data={
            "channel_id": id_channel,
            "user_id": added_user,
            "user_channel_settings_id": user_channel_settings.data.id
        })

        channel_for_parsing_association_response: Response[list[ChannelForParsingAssociationSchema]] = Response[
            list[ChannelForParsingAssociationSchema]].model_validate(
            await channel_for_parsing_association_api.post_all(
                data={
                    "channel_id": id_channel
                }
            )
        )

        for channel_for_parsing_association in channel_for_parsing_association_response.data:
            await channel_for_parsing_association_api.post_add(
                data={
                    "user_id": added_user,
                    "channel_id": id_channel,
                    "channel_for_parsing_id": channel_for_parsing_association.channel_for_parsing_id
                }
            )

    markup = InlineKeyboardMarkup(row_width=1)
    text = _("{} \n" \
             "Подписчиков: {}\n\n" \
             "Имеют доступ:\n{}\n\n" \
             "Чтобы дать пользователю возможность работать с каналом, добавьте его в канал {} в качестве " \
             "администратора, дав права на: \n\n" \
             "✅ Отправку сообщений \n" \
             "✅ Удаление сообщений \n" \
             "✅ Редактирование сообщений \n\n" \
             "Затем нажмите «Обновить данные» ").format(url, members, admins_txt, url)

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
    auto_sign_text = response3.get("data").get("auto_sign_text")

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/{call.from_user.id}/") as response:
            response4 = await response.json()
    auto_send = response4.get("data").get("post_auto_send")
    updateData = _("🔄 Обновить данные")
    chatGPTPrompts = _("Промпты для Chat GPT")
    autoSignNo = _("Автоподпись: нет")
    autoSignYes = _("✅ Автоподпись: есть")
    sendPostsNo = _("Отправка спаршенных постов в чат: нет")
    sendPostsYes = _("✅ Отправка спаршенных постов в чат: да")
    unlinkFromBot = _("🗑 Отвязать от HarvestlyBot")
    Back = _("⬅️ Назад")
    markup.insert(InlineKeyboardButton(text=updateData,
                                       callback_data=settings_channel.new(ch_id=id_channel, act="update",
                                                                          ex="None")))

    markup.add(InlineKeyboardButton(text=chatGPTPrompts,
                                    callback_data=settings_chatgpt.new(ch_id=id_channel, act="gpt")))

    markup.add(InlineKeyboardButton(text=f"{autoSignNo if auto_sign_text is None else autoSignYes}",
                                    callback_data=update_auto_sign_clb.new(ch_id=id_channel,
                                                                           v=str(auto_sign_text))))

    markup.add(InlineKeyboardButton(
        text=sendPostsNo if auto_send == False else sendPostsYes,
        callback_data=update_auto_send_clb.new(ch_id=id_channel,
                                               v=auto_send)))

    markup.add(InlineKeyboardButton(text=unlinkFromBot,
                                    callback_data=settings_channel.new(ch_id=id_channel, act="untie",
                                                                       ex="None")))

    markup.insert(InlineKeyboardButton(text=Back,
                                       callback_data=settings_channel.new(ch_id=id_channel, act="back_1",
                                                                          ex="None")))

    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def channel_settings_without_callback(message: types.Message, channel_id):
    _ = message.bot.get("lang")
    data = {"id": channel_id}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel/one/",
                                json=data) as response:
            response1 = await response.json()

    id = response1['data']['id']
    title = response1.get("data").get("title")
    link = response1.get("data").get("link")
    url = f"<a href='{link}'>{title}</a>"
    # channel_username = link.split("/")[-1]
    admins = await message.bot.get_chat_administrators(id)
    members = await message.bot.get_chat_members_count(id)
    admins_txt = ""

    for admin in admins:
        admins_txt += f"@{admin.user.username}\n" if admin.user.username is not None else ""

    markup = InlineKeyboardMarkup(row_width=1)
    text = _("{} \n" \
             "Подписчиков: {}\n\n" \
             "Имеют доступ:\n{}\n\n" \
             "Чтобы дать пользователю возможность работать с каналом, добавьте его в канал {} в качестве " \
             "администратора, дав права на: \n\n" \
             "✅ Отправку сообщений \n" \
             "✅ Удаление сообщений \n" \
             "✅ Редактирование сообщений \n\n" \
             "Затем нажмите «Обновить данные» ").format(url, members, admins_txt, url)

    data = {"user_id": message.from_user.id,
            "channel_id": channel_id}
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
    auto_sign_text = response3.get("data").get("auto_sign_text")

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/{message.from_user.id}/") as response:
            response4 = await response.json()
    auto_send = response4.get("data").get("post_auto_send")

    updateData = _("🔄 Обновить данные")
    chatGPTPrompts = _("Промпты для Chat GPT")
    autoSignNo = _("Автоподпись: нет")
    autoSignYes = _("✅ Автоподпись: есть")
    sendPostsNo = _("Отправка спаршенных постов в чат: нет")
    sendPostsYes = _("✅ Отправка спаршенных постов в чат: да")
    unlinkFromBot = _("🗑 Отвязать от HarvestlyBot")
    Back = _("⬅️ Назад")
    markup.insert(InlineKeyboardButton(text=updateData,
                                       callback_data=settings_channel.new(ch_id=channel_id, act="update",
                                                                          ex="None")))

    markup.add(InlineKeyboardButton(text=chatGPTPrompts,
                                    callback_data=settings_chatgpt.new(ch_id=channel_id, act="gpt")))

    markup.add(InlineKeyboardButton(text=f"{autoSignNo if auto_sign_text is None else autoSignYes}",
                                    callback_data=update_auto_sign_clb.new(ch_id=channel_id,
                                                                           v=str(auto_sign_text))))

    markup.add(InlineKeyboardButton(
        text=sendPostsNo if auto_send == False else sendPostsYes,
        callback_data=update_auto_send_clb.new(ch_id=channel_id,
                                               v=auto_send)))

    markup.add(InlineKeyboardButton(text=unlinkFromBot,
                                    callback_data=settings_channel.new(ch_id=channel_id, act="untie",
                                                                       ex="None")))

    markup.insert(InlineKeyboardButton(text=Back,
                                       callback_data=settings_channel.new(ch_id=channel_id, act="back_1",
                                                                          ex="None")))
    await message.bot.send_message(chat_id=message.from_user.id, text=text, reply_markup=markup)


async def timezone_settings(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    time_zone = int(callback_data.get("timezone"))

    country = time_zones.get(time_zone)
    text = _("Ваш часовой пояс: GMT + {} {}").format(time_zone, country)
    markup = InlineKeyboardMarkup(row_width=1)
    for timezone, country in time_zones.items():
        markup.add(InlineKeyboardButton(text=f"GMT + {timezone} {country}",
                                        callback_data=settings_timezone.new(timezone=timezone, act="update")))
    markup.insert(
        InlineKeyboardButton(text=f"⬅️ Назад", callback_data=settings_timezone.new(timezone="None", act="back_1")))
    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def timezone_update(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    time_zone = int(callback_data.get("timezone"))

    data = {"id": call.from_user.id,
            "time_zone": time_zone}
    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/", json=data) as response:
            response1 = await response.json()
    if response1.get('status') == "success":
        country = time_zones.get(time_zone)
        text = _("Вы изменили часовой пояс на \nGMT + {} {}").format(time_zone, country)
        await call.bot.send_message(call.from_user.id, text)
        await back_to_user_settings(call, delete=True)
    else:
        pass


async def update_auto_sign(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()
    _ = call.bot.get("lang")
    id_channel = int(callback_data.get("ch_id"))
    auto_sign_text = callback_data.get("v")

    if auto_sign_text == "None":
        auto_sign_text = None

    if auto_sign_text is None:

        markup = InlineKeyboardMarkup(row_width=1)
        text = _("✍️ АВТОПОДПИСЬ\n\n" \
                 "Вы можете настроить подпись, которая будет автоматически добавляться " \
                 "ко всем вашим публикациям.\n\n" \
                 "Отправьте текст для автоподписи.")
        Back = _("⬅️ Назад")
        markup.add(InlineKeyboardButton(text=Back,
                                        callback_data=settings_channel.new(ch_id=id_channel,
                                                                           act="update", ex="None")))
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id,
                                         reply_markup=markup)
        await Settings.Sign.set()
        await state.update_data(id_channel=id_channel)

    else:
        new_auto_sign = False
        data = {"user_id": call.from_user.id,
                "channel_id": id_channel}
        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel/one/",
                                    json=data) as response:
                response1 = await response.json()
        user_channel_settings_id = int(response1.get("data").get("user_channel_settings_id"))

        data = {"id": user_channel_settings_id,
                "auto_sign": new_auto_sign,
                "auto_sign_text": None}
        async with aiohttp.ClientSession() as session:
            async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel_settings/",
                                   json=data) as response:
                response2 = await response.json()
                if response2.get('status') == "success":
                    clb_data = {"ch_id": id_channel}
                    await channel_settings(call, clb_data)


async def settings_add_sign(message: types.Message, state: FSMContext):
    data = await state.get_data()
    _ = message.bot.get("lang")
    id_channel = int(data.get("id_channel"))
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
        await user_settings(message, state)
    else:
        pass


async def update_auto_send(call: CallbackQuery, callback_data: dict):
    await call.answer()
    id_channel = int(callback_data.get("ch_id"))
    auto_send = callback_data.get("v")

    if str(auto_send) == "False":
        new_auto_send = True
        data = {"id": call.from_user.id,
                "post_auto_send": new_auto_send}

        async with aiohttp.ClientSession() as session:
            async with session.put(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/",
                    json=data) as response:
                user_response = await response.json()

        data = {
            "user_id": call.from_user.id,
            "channel_id": id_channel
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing_association/all/",
                    json=data) as response:
                channel_for_parsing_association_response = await response.json()

        for obj in channel_for_parsing_association_response.get("data"):
            channel_for_parsing_association_id = obj.get("id")

            data = {
                "id": channel_for_parsing_association_id,
                "last_time_view_posts_tapped": None
            }

            async with aiohttp.ClientSession() as session:
                async with session.put(
                        url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing_association/",
                        json=data) as response:
                    channel_for_parsing_association_response = await response.json()

    else:
        new_auto_send = False

        data = {"id": call.from_user.id,
                "post_auto_send": new_auto_send}

        async with aiohttp.ClientSession() as session:
            async with session.put(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/",
                    json=data) as response:
                user_response = await response.json()

        data = {
            "user_id": call.from_user.id,
            "channel_id": id_channel
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing_association/all/",
                    json=data) as response:
                channel_for_parsing_association_response = await response.json()

        for obj in channel_for_parsing_association_response.get("data"):
            channel_for_parsing_association_id = obj.get("id")

            data = {
                "id": channel_for_parsing_association_id,
                "last_time_view_posts_tapped": datetime.utcnow().isoformat()
            }

            async with aiohttp.ClientSession() as session:
                async with session.put(
                        url=f"http://{config.api.api_db}:{config.api.api_db_port}/channel_for_parsing_association/",
                        json=data) as response:
                    channel_for_parsing_association_response = await response.json()

    clb_data = {"ch_id": id_channel}
    await channel_settings(call, clb_data)


async def back_to_channel_settings(call: CallbackQuery, callback_data: dict, state: FSMContext):
    data = await state.get_data()
    id_channel = data.get("id_channel")
    await state.reset_state()
    await call.answer()
    clb_data = {"ch_id": id_channel}
    await channel_settings(call, clb_data)


async def untie_channel(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    id_channel = int(callback_data.get("ch_id"))

    markup = InlineKeyboardMarkup(row_width=1)
    text = _("Вы уверены, что хотите отвязать канал от HarvestlyBot?\n\n" \
             "Вы в любой момент можете заново привязать канал, сохранив все настройки и контент-план.")
    Back = _("⬅️ Назад")
    Unlink = _("Да, отвязать")
    markup.add(InlineKeyboardButton(text=Unlink,
                                    callback_data=settings_channel.new(ch_id=id_channel, act="untie_confirm",
                                                                       ex="None")))
    markup.add(InlineKeyboardButton(text=Back,
                                    callback_data=settings_channel.new(ch_id=id_channel, act="update",
                                                                       ex="None")))
    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def untie_channel_confirm(call: CallbackQuery, callback_data: dict):
    await call.answer()
    id_channel = int(callback_data.get("ch_id"))

    data = {"user_id": call.from_user.id,
            "channel_id": id_channel}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel/one/",
                                json=data) as response:
            response1 = await response.json()
    user_channel_settings_id = int(response1.get("data").get("user_channel_settings_id"))

    data = {"id": user_channel_settings_id, "disabled": True}
    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel_settings/",
                               json=data) as response:
            response2 = await response.json()
            if response2.get('status') == "success":
                await call.bot.send_message(call.from_user.id, "Вы успешно отвязали свой канал")
                await back_to_user_settings(call, delete=True)
            else:
                pass


async def chatgpt_settings(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")

    id_channel = int(callback_data.get("ch_id"))

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/{call.from_user.id}/") as response:
            response1 = await response.json()
            gpt_api_key = response1.get("data").get("gpt_api_key")

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

    if gpt_api_key is None and (subscription_id == 1 or subscription_id is None):
        text = _(
            "Чтобы пользоваться промптаим в Harvestly вы должны привязать свой аккаунт Chat GPT или Оплатить подписку<a href='{}'>&#8203;</a>").format(
            FreeSubscription)
        markup = InlineKeyboardMarkup(row_width=2)
        link_GPT = _("⛓ Личный аккаунт GPT")
        subs_payment = _("💰 Оплата подписки")
        Back = _("⬅️ Назад")
        markup.add(InlineKeyboardButton(text=link_GPT,
                                        callback_data=snap_gpt4.new(channel_id=id_channel)))
        markup.add(InlineKeyboardButton(text=subs_payment,
                                        callback_data=subscription_payment_clb.new(
                                            a="s_p",
                                            p=str(id_channel).replace("-100", ""),
                                            t="None")))

        markup.add(InlineKeyboardButton(text=Back,
                                        callback_data=settings_channel.new(ch_id=id_channel, act="update",
                                                                           ex="None")))
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
    else:
        markup = InlineKeyboardMarkup(row_width=2)
        text = _("<b>⛓ GPT ПРОМПТЫ</b>\n\n" \
                 "В этом разделе вы можете настроить работу Chat GPT, добавить и удалить промпты")
        add_btn = _("Добавить")
        modify = _("Изменить")
        Back = _("⬅️ Назад")
        markup.insert(InlineKeyboardButton(text=add_btn,
                                           callback_data=settings_chatgpt.new(ch_id=id_channel,
                                                                              act="add_prompt")))
        markup.insert(InlineKeyboardButton(text=modify,
                                           callback_data=settings_chatgpt.new(ch_id=id_channel,
                                                                              act="change_prompt")))
        markup.add(InlineKeyboardButton(text=Back,
                                        callback_data=settings_chatgpt.new(ch_id=id_channel, act="back")))
        await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def chatgpt_settings_message(message: types.Message, id_channel: int):
    _ = message.bot.get("lang")
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/{message.from_user.id}/") as response:
            response1 = await response.json()
            gpt_api_key = response1.get("data").get("gpt_api_key")

    data = {"user_id": message.from_user.id,
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

    if gpt_api_key is None and (subscription_id == 1 or subscription_id is None):
        text = _(
            "Чтобы пользоваться промптаим в Harvestly вы должны привязать свой аккаунт Chat GPT или Оплатить подписку<a href='{}'>&#8203;</a>").format(
            FreeSubscription)
        markup = InlineKeyboardMarkup(row_width=2)
        link_GPT = _("⛓ Личный аккаунт GPT")
        subs_payment = _("💰 Оплата подписки")
        Back = _("⬅️ Назад")
        markup.add(InlineKeyboardButton(text=link_GPT,
                                        callback_data=snap_gpt4.new(channel_id=id_channel)))
        markup.add(InlineKeyboardButton(text=subs_payment,
                                        callback_data=subscription_payment_clb.new(
                                            a="s_p",
                                            p=str(id_channel).replace("-100", ""),
                                            t="None")))

        markup.add(InlineKeyboardButton(text=Back,
                                        callback_data=settings_channel.new(ch_id=id_channel, act="update",
                                                                           ex="None")))
        try:
            await message.bot.edit_message_text(text, message.from_user.id, message.message_id, reply_markup=markup)
        except Exception as e:
            await message.bot.send_message(message.from_user.id, text, reply_markup=markup)
    else:
        markup = InlineKeyboardMarkup(row_width=2)
        text = _("<b>⛓ GPT ПРОМПТЫ</b>\n\n" \
                 "В этом разделе вы можете настроить работу Chat GPT, добавить и удалить промпты")
        add_btn = _("Добавить")
        modify = _("Изменить")
        Back = _("⬅️ Назад")
        markup.insert(InlineKeyboardButton(text=add_btn,
                                           callback_data=settings_chatgpt.new(ch_id=id_channel,
                                                                              act="add_prompt")))
        markup.insert(InlineKeyboardButton(text=modify,
                                           callback_data=settings_chatgpt.new(ch_id=id_channel,
                                                                              act="change_prompt")))
        markup.add(InlineKeyboardButton(text=Back,
                                        callback_data=settings_chatgpt.new(ch_id=id_channel, act="back")))
        try:
            await message.bot.edit_message_text(text, message.from_user.id, message.message_id, reply_markup=markup)
        except Exception as e:
            await message.bot.send_message(message.from_user.id, text, reply_markup=markup)


async def chatgpt_add(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()
    _ = call.bot.get("lang")
    id_channel = int(callback_data.get("ch_id"))

    markup = InlineKeyboardMarkup(row_width=1)
    text = _('<b>⛓ CHAT GPT</b>\n\nОтправьте боту промпт в следующем формате:\n\n' \
             'Название - <b>Текст промпта</b>\n\n' \
             'Пример:\n\n' \
             'Изменение текста - <b>Преобразуйте следующий текст, чтобы сделать его кратким и информативным, ' \
             'сохраняя при этом его основной смысл</b>')
    Back = _("⬅️ Назад")
    markup.add(InlineKeyboardButton(text=Back,
                                    callback_data=settings_chatgpt.new(ch_id=id_channel, act="back")))
    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
    await Settings.Add_prompt.set()
    await state.update_data(channel_id=id_channel)


# Settings.Add_prompt
async def add_prompt(message: types.Message, state: FSMContext):
    text = message.text.split(" - ")
    _ = message.bot.get("lang")
    key = text[0]
    value = text[1]
    data = await state.get_data()
    id_channel = int(data.get("channel_id"))

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
        await chatgpt_settings_message(message, id_channel)


async def chatgpt_change(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    id_channel = int(callback_data.get("ch_id"))
    markup = InlineKeyboardMarkup(row_width=1)

    text = "<b>⛓️ ПОСМОТРЕТЬ ПРОМПТЫ</b>\n\n" \
           "В этом разделе вы можете посмотреть промпты для Chat GPT"
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
    if gpt_prompts is not None:
        gpt_prompts = list(response2.get("data").get("prompts"))

        for prompt in gpt_prompts:
            for key in prompt.keys():
                markup.insert(InlineKeyboardButton(text=f"{key}",
                                                   callback_data=change_prompt_clb.new(ch_id=id_channel,
                                                                                       act="change_prompt_2",
                                                                                       index=gpt_prompts.index(
                                                                                           prompt))))
        Back = _("⬅️ Назад")
        markup.add(InlineKeyboardButton(text=Back,
                                        callback_data=settings_chatgpt.new(ch_id=id_channel,
                                                                           act="back_to_chatgpt_settings")))
        try:
            await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
        except Exception as e:
            await call.bot.send_message(call.from_user.id, text, reply_markup=markup)

    else:
        text = _("Вы еще не добавили промпты для Сhat GPT")
        await call.bot.send_message(call.from_user.id, text, reply_markup=markup)
        await back_to_user_settings(call, delete=True)


async def change_prompt(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()
    _ = call.bot.get("lang")
    await state.reset_state()
    index = int(callback_data.get("index"))
    id_channel = int(callback_data.get("ch_id"))

    markup = InlineKeyboardMarkup(row_width=2)
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
                }
        ) as response:
            response2 = await response.json()
            gpt_prompts = response2.get("data").get("prompts")
    chosen_prompt = gpt_prompts[index]
    headline = list(chosen_prompt.keys())[0]
    value = chosen_prompt[headline]

    text = f"<b>⛓️ {headline}</b>\n\n" \
           f"<b>{headline}</b> - {value}"
    editText = _("Изменить текст")
    delete = _("Удалить")
    Back = _("⬅️ Назад")
    markup.insert(InlineKeyboardButton(text=editText, callback_data=change_prompt_clb.new(
        ch_id=id_channel, act="change_prompt_text", index=index)))
    markup.insert(InlineKeyboardButton(text=delete, callback_data=del_prompt_clb.new(
        ch_id=id_channel, act="del_prompt", index=index)))
    markup.add(InlineKeyboardButton(text=Back, callback_data=settings_chatgpt.new(ch_id=id_channel,
                                                                                  act="back_to_chatgpt_change")))
    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def change_prompt_text(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()
    _ = call.bot.get("lang")
    index = int(callback_data.get("index"))
    id_channel = int(callback_data.get("ch_id"))

    text = _("<b>⛓ ИЗМЕНИТЬ ТЕКСТ ПРОМПТА</b>\n\n" \
             "Отправьте боту промпт в следующем формате:\n\n" \
             "Название - Текст промпта\n\n" \
             "Пример:\n\n" \
             "Изменение текста - <b>Преобразуйте следующий текст, чтобы сделать его кратким и информативным, " \
             "сохраняя при этом его основной смысл</b>")
    Back = _("⬅️ Назад")
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text=Back, callback_data=change_prompt_clb.new(ch_id=id_channel,
                                                                                          act="back_to_change_prompt",
                                                                                          index=index)))
    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
    await Settings.Change_prompt.set()
    await state.update_data(channel_id=id_channel)
    await state.update_data(index=index)


# Settings.Change_prompt
async def change_prompt_text_confirm(message: types.Message, state: FSMContext):
    text = message.text.split(" - ")
    _ = message.bot.get("lang")
    key = text[0]
    value = text[1]
    date = await state.get_data()
    id_channel = int(date.get("channel_id"))
    index = int(date.get("index"))

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
                }
        ) as response:
            response2 = await response.json()
            gpt_prompts = response2.get("data").get("prompts")
    gpt_prompts.pop(index)
    json_obj = {key: value}
    gpt_prompts.append(json_obj)

    data = {"id": user_channel_settings_id,
            "prompts": gpt_prompts}
    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel_settings/",
                               json=data) as response:
            response3 = await response.json()
    if response3.get('status') == "success":
        await state.reset_state()
        text = _("✅ Вы успешно изменили промпт {} в HarvestlyBot.").format(key)
        await message.answer(text)
        await chatgpt_settings_message(message, id_channel)
    else:
        pass


async def delete_prompt(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    id_channel = int(callback_data.get("ch_id"))
    index = int(callback_data.get("index"))

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
                }
        ) as response:
            response2 = await response.json()
            gpt_prompts = response2.get("data").get("prompts")
    chosen_prompt = gpt_prompts[index]
    headline = list(chosen_prompt.keys())[0]

    text = _("Вы уверены, что хотите удалить промпт '{}'?").format(headline)
    delete = _("Да, удалить")
    Back = _("⬅️ Назад")
    markup = InlineKeyboardMarkup(row_width=1)
    markup.insert(InlineKeyboardButton(text=delete, callback_data=del_prompt_clb.new(
        ch_id=id_channel, act="del_prompt_confirm", index=index)))
    markup.add(InlineKeyboardButton(text=Back, callback_data=change_prompt_clb.new(ch_id=id_channel,
                                                                                          act="back_to_change_prompt",
                                                                                          index=index)))
    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def delete_prompt_confirm(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    await call.bot.delete_message(call.from_user.id, call.message.message_id)
    index = int(callback_data.get("index"))
    id_channel = int(callback_data.get("ch_id"))

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
                }
        ) as response:
            response2 = await response.json()
            gpt_prompts = response2.get("data").get("prompts")
    chosen_prompt = gpt_prompts[index]
    headline = list(chosen_prompt.keys())[0]
    gpt_prompts.pop(index)

    data = {"id": user_channel_settings_id,
            "prompts": gpt_prompts}
    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user_channel_settings/",
                               json=data) as response:
            response3 = await response.json()
    if response3.get('status') == "success":
        text = _("Вы успешно удалили промпт {}").format(headline)
        await call.bot.send_message(call.from_user.id, text)
        callback_data = {"ch_id": id_channel}
        await chatgpt_change(call, callback_data)
    else:
        pass


async def chatgpt_snap_main_menu(call: CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    await state.reset_state()

    markup = InlineKeyboardMarkup(row_width=1)
    text = _('<b>⛓ GPT ПРОМПТЫ</b>' \
             '\n\nПодключение вашего собственного GPT' \
             '\n\nВы можете подключить ваш собственный аккаунт GPT. Просто отправьте нам API токен вашего бота, и мы подключим его в нашу систему.' \
             '\n\nБлагодаря этому @{} будет работать быстрее и без ограничений на кол-во запросов.').format((await call.bot.get_me()).username)
    unlink = _("🗑 Отвязать аккаунт")
    link = _("⛓ Привязать аккаунт GPT")
    Back = _("⬅️ Назад")

    data = {"id": call.from_user.id}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/one/",
                                json=data) as response:
            user_response = await response.json()
    if user_response.get("data").get("gpt_api_key"):
        markup.add(InlineKeyboardButton(text=unlink,
                                        callback_data=untie_gpt_account.new(channel_id=0)))
    else:
        markup.add(InlineKeyboardButton(text=link,
                                        callback_data=snap_gpt4_next.new(channel_id=0)))
    markup.add(InlineKeyboardButton(text=Back, callback_data=settings_channel.new(ch_id=0,
                                                                                         act="back_1",
                                                                                         ex="None")))

    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def chatgpt_snap_channel_menu(call: CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    await state.reset_state()

    channel_id = callback_data['channel_id']

    markup = InlineKeyboardMarkup(row_width=1)
    text = _('<b>⛓ GPT ПРОМПТЫ</b>' \
             '\n\nПодключение вашего собственного GPT' \
             '\n\nВы можете подключить ваш собственный аккаунт GPT. Просто отправьте нам API токен вашего бота, и мы подключим его в нашу систему.' \
             '\n\nБлагодаря этому @{} будет работать быстрее и без ограничений на кол-во запросов.').format((await call.bot.get_me()).username)
    unlink = _("🗑 Отвязать аккаунт")
    link = _("⛓ Привязать аккаунт GPT")
    Back = _("⬅️ Назад")

    data = {"id": call.from_user.id}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/one/",
                                json=data) as response:
            user_response = await response.json()

    if user_response.get("data").get("gpt_api_key"):
        markup.add(InlineKeyboardButton(text=unlink,
                                        callback_data=untie_gpt_account.new(channel_id=0)))
    else:
        markup.add(InlineKeyboardButton(text=link,
                                        callback_data=snap_gpt4_next.new(channel_id=0)))

    markup.add(InlineKeyboardButton(text=Back, callback_data=settings_chatgpt.new(ch_id=channel_id,
                                                                                         act="back_to_chatgpt_settings")))

    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def chatgpt_snap_next(call: CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")
    await call.bot.delete_message(call.from_user.id, call.message.message_id)

    markup = InlineKeyboardMarkup(row_width=1)
    text = _('<b>Чтобы подключить Chat GPT отправьте ваш секретный API Token боту</b>\n\n' \
             'Пример:\n\n' \
             '<b>sk-\n' \
             'scsRpZt3T6xk72amwAATSBIDKFJOUECOMDNQEXLPBs29ROf</b>')
    Back = _("⬅️ Назад")

    channel_id = int(callback_data['channel_id'])
    markup.add(
        InlineKeyboardButton(text=Back,
                             callback_data=settings_channel.new(ch_id=channel_id, act="back_2",
                                                                ex="None")))
    await call.bot.send_message(call.from_user.id, text, reply_markup=markup)

    channel_id = callback_data['channel_id']

    await state.set_state(Settings.GPT4)
    await state.update_data(channel_id=channel_id)


# Settings.GPT4
async def gpt4_snap(message: types.Message, state: FSMContext):
    _ = message.bot.get("lang")
    open_ai_response: Response[str] = Response[str].model_validate(
        await open_ai_api.prompt(data={"content": "Привет", "api_key": message.text})
    )

    data = await state.get_data()
    channel_id = data['channel_id']

    if open_ai_response.status == "success":
        data = {"id": message.from_user.id,
                "gpt_api_key": message.text}

        async with aiohttp.ClientSession() as session:
            async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/",
                                   json=data) as response:
                response1 = await response.json()

        if response1.get('status') == "success":

            await state.reset_state()
            text =_("✅ Вы успешно привязали аккаунт Chat GPT 4 в HarvestlyBot.")
            await message.answer(text)

            if int(channel_id) == 0:
                await user_settings(message, state)
            else:
                await channel_settings_without_callback(message, channel_id)
        else:
            pass
    else:
        markup = InlineKeyboardMarkup(row_width=1)
        text = _('<b>Введенный API Token не действителен</b>\n\n' \
                 'Пример:\n\n' \
                 '<b>sk-\n' \
                 'scsRpZt3T6xk72amwAATSBIDKFJOUECOMDNQEXLPBs29ROf</b>')
        Back = _("⬅️ Назад")
        markup.add(
            InlineKeyboardButton(text=Back,
                                 callback_data=settings_channel.new(ch_id=channel_id, act="back_2",
                                                                    ex="None")))

        await message.bot.send_message(message.from_user.id, text, reply_markup=markup)
        await Settings.GPT4.set()


async def back_to_menu_after_gpt_key_input(call: CallbackQuery, state: FSMContext, callback_data: dict):
    channel_id = int(callback_data['channel_id'])
    if channel_id == 0:
        await chatgpt_snap_main_menu(call=call, state=state, callback_data=callback_data)
    else:
        await chatgpt_snap_channel_menu(call=call, state=state, callback_data=callback_data)


async def untie_chatgpt(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")

    channel_id = callback_data['channel_id']
    markup = InlineKeyboardMarkup(row_width=1)
    text = _("Вы уверены, что хотите отвязать свой аккаунт Chat GPT 4 от HarvestlyBot?\n\n" \
           "Вы в любой момент можете заново привязать свой аккаунт, сохранив все настройки и контент-план.")
    Back = _("⬅️ Назад")
    Unlink = _("Да, отвязать")
    markup.add(InlineKeyboardButton(text=Unlink,
                                    callback_data=set_gpt_api_key.new(act="untie_chatgpt")))
    markup.add(InlineKeyboardButton(text=Back,
                                    callback_data=settings_channel.new(ch_id=channel_id, act="back_2",
                                                                       ex="None")))
    await call.bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)


async def untie_chatgpt_confirm(call: CallbackQuery, callback_data: dict):
    await call.answer()
    _ = call.bot.get("lang")

    data = {"id": call.from_user.id,
            "gpt_api_key": None}

    async with aiohttp.ClientSession() as session:
        async with session.put(url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/",
                               json=data) as response:
            response1 = await response.json()
    if response1.get('status') == "success":
        text =_("✅ Вы успешно отвязали свой аккаунт Chat GPT 4 от HarvestlyBot")
        await call.bot.send_message(call.from_user.id, text)
        await back_to_user_settings(call, delete=True)
    else:
        pass


#  Settings.Add_prompt
async def back_to_chatgpt_settings(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    id_channel = int(data.get("channel_id"))
    await call.answer()
    await state.reset_state()
    callback_data = {"ch_id": id_channel}
    await chatgpt_settings(call, callback_data)


# Settings.GPT4
async def back_to_user_settings2(call: CallbackQuery, state: FSMContext):
    await state.reset_state()
    await call.answer()
    await back_to_user_settings(call)


def register_settings(dp: Dispatcher):
    dp.register_message_handler(user_settings, text="Настройки", state="*")
    dp.register_message_handler(user_settings, text="Настройки")
    dp.register_callback_query_handler(back_to_user_settings, settings_channel.filter(act="back_1"))
    dp.register_callback_query_handler(back_to_user_settings, settings_timezone.filter(act="back_1"))

    dp.register_callback_query_handler(channel_settings, settings_channel.filter(act="update"))
    dp.register_callback_query_handler(channel_settings, settings_chatgpt.filter(act="back"))
    dp.register_callback_query_handler(back_to_channel_settings, settings_channel.filter(act="update"),
                                       state=Settings.Sign)

    dp.register_callback_query_handler(update_auto_sign, update_auto_sign_clb.filter())
    dp.register_callback_query_handler(update_auto_send, update_auto_send_clb.filter())
    dp.register_message_handler(settings_add_sign, state=Settings.Sign)

    dp.register_callback_query_handler(timezone_settings, settings_timezone.filter(act="next"))
    dp.register_callback_query_handler(timezone_update, settings_timezone.filter(act="update"))

    dp.register_callback_query_handler(untie_channel, settings_channel.filter(act="untie"))
    dp.register_callback_query_handler(untie_channel_confirm, settings_channel.filter(act="untie_confirm"))

    dp.register_callback_query_handler(chatgpt_settings, settings_chatgpt.filter(act="gpt"))
    dp.register_callback_query_handler(chatgpt_settings, settings_chatgpt.filter(act="back_to_chatgpt_settings"))

    dp.register_callback_query_handler(chatgpt_add, settings_chatgpt.filter(act="add_prompt"))
    dp.register_message_handler(add_prompt, state=Settings.Add_prompt)

    dp.register_callback_query_handler(chatgpt_snap_main_menu, set_gpt_api_key.filter(act="snap_gpt4"))
    dp.register_callback_query_handler(chatgpt_snap_channel_menu, snap_gpt4.filter())

    dp.register_callback_query_handler(back_to_menu_after_gpt_key_input, settings_channel.filter(act="back_2"),
                                       state=Settings.GPT4)
    dp.register_callback_query_handler(back_to_menu_after_gpt_key_input, settings_channel.filter(act="back_2"))

    dp.register_callback_query_handler(chatgpt_snap_next, snap_gpt4_next.filter())
    dp.register_message_handler(gpt4_snap, state=Settings.GPT4)

    dp.register_callback_query_handler(untie_chatgpt, untie_gpt_account.filter())

    dp.register_callback_query_handler(untie_chatgpt_confirm, set_gpt_api_key.filter(act="untie_chatgpt"))

    dp.register_callback_query_handler(back_to_chatgpt_settings, settings_chatgpt.filter(act="back"),
                                       state=Settings.Add_prompt)
    dp.register_callback_query_handler(back_to_user_settings2, settings_channel.filter(act="back_1"),
                                       state=Settings.GPT4)

    dp.register_callback_query_handler(chatgpt_change, settings_chatgpt.filter(act="change_prompt"))
    dp.register_callback_query_handler(chatgpt_change, change_prompt_clb.filter(act="back_to_chatgpt_change"))
    dp.register_callback_query_handler(chatgpt_change, settings_chatgpt.filter(act="back_to_chatgpt_change"))

    dp.register_callback_query_handler(change_prompt, change_prompt_clb.filter(act="change_prompt_2"))
    dp.register_callback_query_handler(change_prompt, change_prompt_clb.filter(act="back_to_change_prompt"),
                                       state=Settings.Change_prompt)
    dp.register_callback_query_handler(change_prompt, change_prompt_clb.filter(act="back_to_change_prompt"))

    dp.register_callback_query_handler(change_prompt_text, change_prompt_clb.filter(act="change_prompt_text"))
    dp.register_message_handler(change_prompt_text_confirm, state=Settings.Change_prompt)

    dp.register_callback_query_handler(delete_prompt, del_prompt_clb.filter(act="del_prompt"))
    dp.register_callback_query_handler(delete_prompt_confirm, del_prompt_clb.filter(act="del_prompt_confirm"))
