from sqlalchemy import select, func

from api_service.database.base import BaseDao
from api_service.database.database import async_session_maker
from api_service.user_channel.models import UserChannel
from api_service.user_channel_settings.models import UserChannelSettings


class UserChannelDao(BaseDao):
    model = UserChannel  # table name

    @classmethod
    async def find_by_channels_id(cls, *data):
        async with async_session_maker() as session:
            subquery = (
                select(
                    cls.model.user_id,
                    func.max(cls.model.id).label('max_id')
                )
                .filter(cls.model.channel_id.in_(data))
                .group_by(cls.model.user_id)
                .subquery()
            )

            # Выполняем основной запрос с использованием JOIN
            query = (
                select(cls.model.__table__.columns)
                .join(subquery, cls.model.id == subquery.c.max_id)
            )

            result = await session.execute(query)
            return result.mappings().all()

    @classmethod
    async def count_unique_channels_by_subscription(cls, subscription_id:int):
        async with async_session_maker() as session:
            query = (
                select(func.count()).select_from(
                    select(UserChannel.channel_id)
                    .join(UserChannelSettings, UserChannel.user_channel_settings_id == UserChannelSettings.id)
                    .where(UserChannelSettings.subscription_id == subscription_id)
                    .distinct()
                )
            )
        result = await session.scalar(query)
        return result