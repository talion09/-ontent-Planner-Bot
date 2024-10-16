from telethon_bot.config import API_SERVICE_HOST, API_SERVICE_PORT
from telethon_bot.remote_api.base import BaseApi
from telethon_bot.remote_api.response_dto import Response, UserSchema


class UserApi(BaseApi[Response[UserSchema]]):
    def __init__(self):
        super().__init__(
            base_url=f'http://{API_SERVICE_HOST}:{API_SERVICE_PORT}/user/'
        )