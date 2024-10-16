from typing import Optional

from sqlalchemy import select, or_, null

from api_service.channel.models import Channel
from api_service.database.base import BaseDao
from api_service.database.database import async_session_maker
from api_service.user_channel.models import UserChannel
from api_service.user_channel_settings.models import UserChannelSettings


class ChannelDao(BaseDao):
    model = Channel

    @classmethod
    async def get_user_channels_with_certain_subscriptions(cls, user_id: int, subscriptions: Optional[list], disabled: Optional[bool]):
        async with async_session_maker() as session:
            query = select(cls.model.__table__.columns). \
                join(UserChannel, UserChannel.channel_id == Channel.id). \
                join(UserChannelSettings, UserChannel.user_channel_settings_id == UserChannelSettings.id). \
                filter(UserChannel.user_id == user_id)

            if subscriptions is not None:
                if None in subscriptions:
                    # Удаляем None из списка, чтобы использовать оставшиеся идентификаторы в .in_()
                    subscriptions = [s for s in subscriptions if s is not None]
                    if subscriptions:
                        # Случай, когда есть и None, и конкретные идентификаторы
                        query = query.filter(or_(
                            UserChannelSettings.subscription_id.is_(null()),
                            UserChannelSettings.subscription_id.in_(subscriptions)
                        ))
                    else:
                        # Случай, когда в списке был только None
                        query = query.filter(UserChannelSettings.subscription_id.is_(null()))
                else:
                    # Случай, когда в списке нет None, только конкретные идентификаторы
                    query = query.filter(UserChannelSettings.subscription_id.in_(subscriptions))

            if disabled is not None:
                query = query.filter(UserChannelSettings.disabled == disabled)

            result = await session.execute(query)
            return result.mappings().all()
