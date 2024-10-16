from datetime import datetime

from aiogram.types import Message, CallbackQuery
from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
import aiohttp
from tg_bot import config


class IsAdmin(BoundFilter):
    async def check(self, message: Message):
        admins_list = [1574853044, 1696518783]
        return message.from_user.id in admins_list


# class IsForwardChat(BoundFilter):
#     async def check(self, message: Message):
#         if message.forward_from_chat and message.forward_from_chat.type == types.ChatType.CHANNEL:
#             return True
#         else:
#             return False


class IsMediaGroup(BoundFilter):
    async def check(self, message: Message):
        if message.media_group_id is not None:
            return True
        else:
            return False


class IsGroup(BoundFilter):
    async def check(self, message: types.Message) -> bool:
        return message.chat.type in (
            types.ChatType.GROUP,
            types.ChatType.SUPERGROUP,
        )


class IsUserBot(BoundFilter):
    async def check(self, message: Message):

        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url=f"http://{config.api.api_db}:{config.api.api_db_port}/telethon/telethon_users/") as response:
                respns = await response.json()
        botd_list = []
        if respns.get('data') is not None:
            for bot in respns.get('data'):
                user_id = int(bot["user_id"])
                botd_list.append(user_id)
        return message.from_user.id in botd_list


class IsSubscriptionValid(BoundFilter):
    async def check(self, message: Message = None, call: CallbackQuery = None):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/{call.from_user.id}/") as response:
                    respns = await response.json()
        except:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        url=f"http://{config.api.api_db}:{config.api.api_db_port}/user/{message.from_user.id}/") as response:
                    respns = await response.json()
        if respns.get("data").get("subscription_purchased") is not None:
            subscription_purchased = datetime.fromisoformat(respns.get("data").get("subscription_purchased"))
            subscription_finished = datetime.fromisoformat(respns.get("data").get("subscription_finished"))
            difference = subscription_finished - subscription_purchased

            if difference.days > 30:
                try:
                    await call.bot.send_message(call.from_user.id, "Срок подписки истек. сейчас вы находить на "
                                                                   "тарифе '🥉 Бесплатный'. Пожалуйста, "
                                                                   "продлите подписку.")
                except:
                    await message.bot.send_message(message.from_user.id, "Срок подписки истек. сейчас вы находить на "
                                                                         "тарифе '🥉 Бесплатный'. Пожалуйста, "
                                                                         "продлите подписку.")
                return True
            else:
                return True

        else:
            return True
