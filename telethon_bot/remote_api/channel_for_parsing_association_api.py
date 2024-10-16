from telethon_bot.config import API_SERVICE_PORT, API_SERVICE_HOST
from telethon_bot.remote_api.base import BaseApi
from telethon_bot.remote_api.response_dto import Response, ChannelForParsingAssociationSchema


class ChannelForParsingAssociationApi(BaseApi[Response[ChannelForParsingAssociationSchema]]):
    def __init__(self):
        super().__init__(
            base_url=f'http://{API_SERVICE_HOST}:{API_SERVICE_PORT}/channel_for_parsing_association/'
        )
