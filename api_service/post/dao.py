from datetime import datetime, timedelta
from operator import and_

from sqlalchemy import select

from api_service.database.base import BaseDao
from api_service.database.database import async_session_maker
from api_service.post.models import Post


class PostDao(BaseDao):
    model = Post  # table name

    @classmethod
    async def get_filtered_posts(cls,
                                 user_id: int = None,
                                 channel_id: int = None,
                                 is_scheduled: bool = None,
                                 date: datetime = None):
        conditions = []  # Список условий для фильтрации

        if user_id is not None:
            conditions.append(cls.model.user_id == user_id)
        if channel_id is not None:
            conditions.append(cls.model.channel_id == channel_id)
        if is_scheduled is not None:
            conditions.append(cls.model.is_scheduled == is_scheduled)
        if date is not None:
            end_date = (date + timedelta(days=1))
            conditions.append(cls.model.date >= date)
            conditions.append(cls.model.date < end_date)

        async with async_session_maker() as session:
            query = select(cls.model.__table__.columns)
            if conditions:
                # Применение условий фильтрации
                for condition in conditions:
                    query = query.where(condition)
            result = await session.execute(query)
            return result.mappings().all()
