from sqlalchemy import select

from api_service.database.base import BaseDao
from api_service.database.database import async_session_maker
from api_service.telethon_user.models import TelethonUser, TelethonParserChannel, TelethonUserParserChannelAssociation


class TelethonUserDao(BaseDao):
    model = TelethonUser

    @classmethod
    async def get_next_row(cls, id: int):
        async with async_session_maker() as session:
            query = select(cls.model.__table__.columns).where(cls.model.id > id).order_by(cls.model.id).limit(1)
            result = await session.execute(query)
            return result.mappings().one_or_none()


class TelethonParserChannelDao(BaseDao):
    model = TelethonParserChannel


class TelethonUserParserChannelAssociationDao(BaseDao):
    model = TelethonUserParserChannelAssociation
