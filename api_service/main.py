from fastapi import FastAPI

from api_service.admin_statistics.api_admin_statistics import router_admin_statistics
# from fastapi_cache import FastAPICache
# from fastapi_cache.backends.redis import RedisBackend

from api_service.channel.api_channel import router_channel
from api_service.channel_for_parsing.api_channel_for_parsing import router_channel_for_parsing
from api_service.channel_for_parsing_association.api_channel_for_parsing_association import \
    router_channel_for_parsing_association
from api_service.message.api_message import router_message
from api_service.open_ai.api_open_ai import router_open_ai
from api_service.parsed_messages.api_parsed_messages import router_parsed_messages
from api_service.parsing_source.api_parsing_source import router_parsing_source
from api_service.payment.api_payment import router_payment
from api_service.paywave.api_paywave import router_paywave
from api_service.post.api_posts import router_post
from api_service.subscription.api_subscription import router_subscription
from api_service.telethon_user.api_telethon_user import router_telethon
from api_service.user_channel.api_user_channel import router_user_channel
from api_service.user_open_ai.api_user_open_ai import router_user_open_ai
from api_service.user.api_user import router_user
from api_service.user_channel_settings.api_channel_settings import router_user_channel_settings

# from redis import asyncio as aioredis

app = FastAPI(title="ApiService")
app.include_router(router_channel)
app.include_router(router_channel_for_parsing)
app.include_router(router_channel_for_parsing_association)
app.include_router(router_message)
app.include_router(router_open_ai)
app.include_router(router_post)
app.include_router(router_subscription)
app.include_router(router_telethon)
app.include_router(router_user_channel)
app.include_router(router_user_channel_settings)
app.include_router(router_user_open_ai)
app.include_router(router_user)
app.include_router(router_paywave)
app.include_router(router_parsed_messages)
app.include_router(router_parsing_source)
app.include_router(router_payment)
app.include_router(router_admin_statistics)

# @app.on_event("startup")
# async def startup_event():
#     redis = aioredis.from_url("redis://localhost", encoding="utf8", decode_responses=True)
#     FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
