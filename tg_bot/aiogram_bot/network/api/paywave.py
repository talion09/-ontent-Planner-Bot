from tg_bot.aiogram_bot.network.api.base import BaseApi
from tg_bot.aiogram_bot.network.dto.paywave import PaywaveSchema
from tg_bot.aiogram_bot.network.dto.response import Response


class PaywaveApi(BaseApi[Response[PaywaveSchema]]):
    def __init__(self,
                 # session: aiohttp.ClientSession
                 ):
        from tg_bot import config
        super().__init__(
            # session,
            base_url=f'http://{config.api.api_db}:{config.api.api_db_port}/paywave/'
        )