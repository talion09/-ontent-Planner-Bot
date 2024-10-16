import aiohttp

from tg_bot.aiogram_bot.network.api.base import BaseApi
from tg_bot.aiogram_bot.network.dto.response import Response


class MailApi(BaseApi[Response[str]]):
    def __init__(self,
                 # session: aiohttp.ClientSession
                 ):
        from tg_bot import config
        super().__init__(
            # session,
            base_url=f'http://{config.api.api_mail}:{config.api.api_mail_port}/'
        )

    async def send_mail(self, data):
        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"{self.base_url}send_mail/",
                                    json=data) as response:
                return await response.json()
