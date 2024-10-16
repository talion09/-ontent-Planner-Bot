import json

from sqlalchemy import select, distinct

from api_service.channel_for_parsing_association.models import ChannelForParsingAssociation
from api_service.database.base import BaseDao
from api_service.database.database import async_session_maker
from api_service.user.models import User
from api_service.user_channel.models import UserChannel
from api_service.user_channel_settings.models import UserChannelSettings


class UserDao(BaseDao):
    model = User

    @classmethod
    async def get_unique_users_with_subscription(cls, subscription_id: int):
        async with async_session_maker() as session:
            result = await session.execute(
                select(distinct(UserChannel.user_id))
                .join(UserChannelSettings, UserChannel.user_channel_settings_id == UserChannelSettings.id)
                .where(UserChannelSettings.subscription_id == subscription_id)
            )
            user_ids = result.scalars().all()
            return user_ids

    @classmethod
    async def get_users_with_specific_subscription(cls, channel_for_parsing_id, subscription_id):
        async with async_session_maker() as session:
            stmt = (
                select(UserChannel.__table__.columns)
                .join(User, User.id == UserChannel.user_id)
                .join(UserChannelSettings, UserChannelSettings.id == UserChannel.user_channel_settings_id)
                .join(ChannelForParsingAssociation,
                      (ChannelForParsingAssociation.user_id == UserChannel.user_id) &
                      (ChannelForParsingAssociation.channel_id == UserChannel.channel_id))
                .where(
                    ChannelForParsingAssociation.channel_for_parsing_id == channel_for_parsing_id,
                    UserChannelSettings.subscription_id == subscription_id,
                    User.post_auto_send == True
                )
                .distinct()
            )
            result = await session.execute(stmt)
            data = result.mappings().all()
            return data
