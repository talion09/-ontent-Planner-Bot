from datetime import datetime

from sqlalchemy import select, func, update

from api_service.database.database import async_session_maker
from api_service.user_channel.models import UserChannel
from api_service.user_channel_settings.models import UserChannelSettings
from api_service.database.base import BaseDao


class UserChannelSettingsDao(BaseDao):
    model = UserChannelSettings

    @classmethod
    async def check_trial_used_for_user(cls, user_id: int) -> bool:
        async with async_session_maker() as session:
            result = await session.execute(
                select(func.count())
                .select_from(UserChannel)
                .join(UserChannelSettings, UserChannel.user_channel_settings_id == UserChannelSettings.id)
                .where(UserChannel.user_id == user_id)
                .where(UserChannelSettings.trial_used.is_(True))
            )
            count_trial_used = result.scalar_one()
            return count_trial_used > 0

    @classmethod
    async def update_subscription_id_by_channel_ids(cls, channel_ids: list[int], new_subscription_id: int,
                                                    created: datetime = None,
                                                    finished: datetime = None):
        async with async_session_maker() as session:
            result = await session.execute(
                select(UserChannel.user_channel_settings_id)
                .filter(UserChannel.channel_id.in_(channel_ids))
                .distinct()
            )
            users_channel_settings_ids = result.scalars().all()

            if users_channel_settings_ids:
                await session.execute(
                    update(cls.model)
                    .where(cls.model.id.in_(users_channel_settings_ids))
                    .values(subscription_id=new_subscription_id, created=created, finished=finished)
                )
                await session.commit()
