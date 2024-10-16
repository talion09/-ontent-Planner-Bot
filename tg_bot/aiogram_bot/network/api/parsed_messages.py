from tg_bot.aiogram_bot.network.api.base import BaseApi
from tg_bot.aiogram_bot.network.dto.parsed_messages import ParsedMessagesSchema
from tg_bot.aiogram_bot.network.dto.response import Response


class ParsedMessagesApi(BaseApi[Response[ParsedMessagesSchema]]):
    def __init__(self,
                 # session: aiohttp.ClientSession
                 ):
        from tg_bot import config
        super().__init__(
            # session,
            base_url=f'http://{config.api.api_db}:{config.api.api_db_port}/parsed_messages/'
        )
