from typing import Tuple, Any
from aiogram import types
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from tg_bot.aiogram_bot.network.dto.response import Response
from tg_bot.aiogram_bot.network.dto.user import UserSchema
from tg_bot import user_api

from tg_bot.aiogram_bot.config import I18N_DOMAIN, LOCALES_DIR


async def get_lang(user_id):
    try:
        params = {"key": "id",
                  "value": user_id}
        user_response: Response[UserSchema] = Response[UserSchema].model_validate(
            await user_api.get_one_by_key_value(params=params))
        status = user_response.status
        if status == "success":
            data = user_response.data
            lang = data.lang
            return lang
        else:
            return "ru"
    except:
        return "ru"


class ACLMidlleware(I18nMiddleware):
    async def get_user_locale(self, action: str, args: Tuple[Any]):
        user = types.User.get_current()
        return await get_lang(user.id)


def setup_middleware(dp):
    i18n = ACLMidlleware(I18N_DOMAIN, LOCALES_DIR)
    dp.middleware.setup(i18n)
    return i18n
