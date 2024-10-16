import aiohttp

from tg_bot.aiogram_bot.network.api.base import BaseApi
from tg_bot.aiogram_bot.network.dto.channel import ChannelSchema
from tg_bot.aiogram_bot.network.dto.response import Response


class ChannelApi(BaseApi[Response[ChannelSchema]]):
    def __init__(self,
                 # session: aiohttp.ClientSession
                 ):
        from tg_bot import config
        super().__init__(
            # session,
            base_url=f'http://{config.api.api_db}:{config.api.api_db_port}/channel/'
        )

    async def get_user_channels_with_certain_subscriptions(self, data):
        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"{self.base_url}get_user_channels_with_certain_subscriptions/",
                                    json=data) as response:
                return await response.json()
