import aiohttp

from tg_bot.aiogram_bot.network.api.base import BaseApi
from tg_bot.aiogram_bot.network.dto.response import Response
from tg_bot.aiogram_bot.network.dto.user import UserSchema


class UserApi(BaseApi[Response[UserSchema]]):
    def __init__(self,
                 # session: aiohttp.ClientSession
                 ):
        from tg_bot import config
        super().__init__(
            # session,
            base_url=f'http://{config.api.api_db}:{config.api.api_db_port}/user/'
        )

    async def get_users_with_specific_subscription(self, data=None):
        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"{self.base_url}get_users_with_specific_subscription/", json=data) as response:
                return await response.json()
