import logging

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from tg_bot.aiogram_bot.config import load_config
from tg_bot.aiogram_bot.network.api.channel import ChannelApi
from tg_bot.aiogram_bot.network.api.channel_for_parsing_association import ChannelForParsingAssociationApi
from tg_bot.aiogram_bot.network.api.mail_api import MailApi
from tg_bot.aiogram_bot.network.api.open_ai_api import OpenAiApi
from tg_bot.aiogram_bot.network.api.parsed_messages import ParsedMessagesApi
from tg_bot.aiogram_bot.network.api.payment_api import PaymentApi
from tg_bot.aiogram_bot.network.api.payment_db_api import PaymentDbApi
from tg_bot.aiogram_bot.network.api.paywave import PaywaveApi
from tg_bot.aiogram_bot.network.api.subscription_api import SubscriptionApi
from tg_bot.aiogram_bot.network.api.user import UserApi
from tg_bot.aiogram_bot.network.api.user_channel import UserChannelApi
from tg_bot.aiogram_bot.network.api.user_channel_settings import UserChannelSettingsApi

logging.basicConfig(level=logging.INFO)

config = load_config()

jobstores = {
    'default': SQLAlchemyJobStore(
        url=f"postgresql://{config.db.db_user}:{config.db.db_pass}@{config.db.db_host}:{config.db.db_port}/{config.db.db_name}")
}
scheduler = AsyncIOScheduler(jobstores=jobstores)

user_api = UserApi()
user_channel_api = UserChannelApi()
channel_api = ChannelApi()
user_channel_settings_api = UserChannelSettingsApi()
subscription_api = SubscriptionApi()
payment_api = PaymentApi()
paywave_api = PaywaveApi()
mail_api = MailApi()
channel_for_parsing_association_api = ChannelForParsingAssociationApi()
open_ai_api = OpenAiApi()
parsed_messages_api = ParsedMessagesApi()
payment_db_api = PaymentDbApi()
