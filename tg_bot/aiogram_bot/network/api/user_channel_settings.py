import aiohttp

from tg_bot.aiogram_bot.network.api.base import BaseApi
from tg_bot.aiogram_bot.network.dto.response import Response
from tg_bot.aiogram_bot.network.dto.user_channel_settings import UserChannelSettingsSchema


class UserChannelSettingsApi(BaseApi[Response[UserChannelSettingsSchema]]):
    def __init__(self,
                 # session: aiohttp.ClientSession
                 ):
        from tg_bot import config
        super().__init__(
            # session,
            base_url=f'http://{config.api.api_db}:{config.api.api_db_port}/user_channel_settings/'
        )

    async def trial_used(self, params=None):
        async with aiohttp.ClientSession() as session:
            async with session.get(url=f"{self.base_url}trial_used/",
                                   params=params) as response:
                return await response.json()

    async def update_subscription_id_by_channel_ids(self, data=None):
        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"{self.base_url}update_subscription_id_by_channel_ids/",
                                    json=data) as response:
                return await response.json()
