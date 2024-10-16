import logging

from sqlalchemy import delete, insert, select, func, update, and_
from sqlalchemy.exc import SQLAlchemyError

from api_service.database.database import async_session_maker


class BaseDao:
    model = None

    @classmethod
    async def find_one_or_none(cls, **data):
        async with async_session_maker() as session:
            conditions = []

            for key, value in data.items():
                if isinstance(value, tuple) and len(value) == 2:
                    conditions.append(getattr(cls.model, key).between(value[0], value[1]))
                else:
                    conditions.append(getattr(cls.model, key) == value)

            query = select(cls.model.__table__.columns).filter(and_(*conditions))
            result = await session.execute(query)
            return result.mappings().one_or_none()

    @classmethod
    async def find_by_ids(cls, *data):
        async with async_session_maker() as session:
            query = select(cls.model.__table__.columns).where(cls.model.id.in_(data)).distinct()
            result = await session.execute(query)
            return result.mappings().all()

    @classmethod
    async def find_all(cls, **data):
        async with async_session_maker() as session:
            conditions = []

            for key, value in data.items():
                if isinstance(value, tuple) and len(value) == 2:
                    conditions.append(getattr(cls.model, key).between(value[0], value[1]))
                else:
                    conditions.append(getattr(cls.model, key) == value)

            query = select(cls.model.__table__.columns).filter(and_(*conditions))
            result = await session.execute(query)
            return result.mappings().all()

    @classmethod
    async def add_commit(cls, **data):
        try:
            query = insert(cls.model).values(**data).returning(cls.model.__table__.columns)
            async with async_session_maker() as session:
                result = await session.execute(query)
                await session.commit()
                return result.mappings().first()
        except (SQLAlchemyError, Exception) as e:
            msg = ""
            if isinstance(e, SQLAlchemyError):
                msg = "Database Exc: Cannot insert data into table"
            elif isinstance(e, Exception):
                msg = "Unknown Exc: Cannot insert data into table"

            logging.error(f'add_commit ERROR {e}\n{msg}')
            raise e

    @classmethod
    async def add_execute(cls, session, data:dict):
        try:
            query = insert(cls.model).values(**data).returning(cls.model.__table__.columns)
            result = await session.execute(query)
            return result.mappings().first()
        except (SQLAlchemyError, Exception) as e:
            msg = ""
            if isinstance(e, SQLAlchemyError):
                msg = "Database Exc: Cannot insert data into table"
            elif isinstance(e, Exception):
                msg = "Unknown Exc: Cannot insert data into table"

            logging.error(f'add_execute ERROR {e}\n{msg}')
            raise e

    @classmethod
    async def add_bulk_commit(cls, *data):
        try:
            query = insert(cls.model).values(data).returning(cls.model.__table__.columns)
            async with async_session_maker() as session:
                result = await session.execute(query)
                await session.commit()
                return result.mappings().all()
        except (SQLAlchemyError, Exception) as e:
            if isinstance(e, SQLAlchemyError):
                msg = "Database Exc"
            elif isinstance(e, Exception):
                msg = "Unknown Exc"
            msg += ": Cannot bulk insert data into table"

            logging.error(f'add_bulk_commit ERROR {e}\n{msg}')
            raise e

    @classmethod
    async def add_bulk_execute(cls, session, *data):
        try:
            query = insert(cls.model).values(data).returning(cls.model.__table__.columns)
            result = await session.execute(query)
            return result.mappings().all()
        except (SQLAlchemyError, Exception) as e:
            if isinstance(e, SQLAlchemyError):
                msg = "Database Exc"
            elif isinstance(e, Exception):
                msg = "Unknown Exc"
            msg += ": Cannot bulk insert data into table"

            logging.error(f'add_bulk_execute ERROR {e}\n{msg}')
            raise e

    @classmethod
    async def update_commit(cls, **data):
        try:
            id = data.pop("id")
            query = update(cls.model).where(cls.model.id == id).values(**data).returning(cls.model.__table__.columns)
            async with async_session_maker() as session:
                result = await session.execute(query)
                await session.commit()
                return result.mappings().first()
        except Exception as e:
            logging.error(f'update_commit ERROR {e}')
            raise e

    @classmethod
    async def update_execute(cls, session, **data):
        try:
            id = data.pop("id")
            query = update(cls.model).where(cls.model.id == id).values(**data).returning(cls.model.__table__.columns)
            result = await session.execute(query)

            return result.mappings().first()
        except Exception as e:
            logging.error(f'update_execute ERROR {e}')
            raise e

    @classmethod
    async def delete_commit(cls, **data):
        async with async_session_maker() as session:
            conditions = []

            for key, value in data.items():
                if isinstance(value, tuple) and len(value) == 2:
                    conditions.append(getattr(cls.model, key).between(value[0], value[1]))
                else:
                    conditions.append(getattr(cls.model, key) == value)

            query = delete(cls.model).filter(and_(*conditions)).returning(cls.model.__table__.columns)
            result = await session.execute(query)
            await session.commit()
            return result.mappings().first()

    @classmethod
    async def delete_execute(cls, session, **data):
        conditions = []

        for key, value in data.items():
            if isinstance(value, tuple) and len(value) == 2:
                conditions.append(getattr(cls.model, key).between(value[0], value[1]))
            else:
                conditions.append(getattr(cls.model, key) == value)

        query = delete(cls.model).filter(and_(*conditions)).returning(cls.model.__table__.columns)
        result = await session.execute(query)
        return result.mappings().first()

    @classmethod
    async def delete_bulk_commit(cls, *data):
        async with async_session_maker() as session:
            query = delete(cls.model).where(cls.model.id.in_(data)).returning(cls.model.__table__.columns)
            result = await session.execute(query)
            await session.commit()
            return result.mappings().all()

    @classmethod
    async def delete_bulk_execute(cls, session, *data):
        query = delete(cls.model).where(cls.model.id.in_(data)).returning(cls.model.__table__.columns)
        result = await session.execute(query)
        return result.mappings().all()

    @classmethod
    async def count(cls, **data):
        async with async_session_maker() as session:
            conditions = []

            for key, value in data.items():
                if isinstance(value, tuple) and len(value) == 2:
                    conditions.append(getattr(cls.model, key).between(value[0], value[1]))
                else:
                    conditions.append(getattr(cls.model, key) == value)

            stmt = select(func.count()).select_from(cls.model).filter(and_(*conditions))
            result = await session.execute(stmt)
            count = result.scalar_one()
            return count

    @classmethod
    async def count_all(cls):
        async with async_session_maker() as session:
            stmt = select(func.count('*')).select_from(cls.model)
            result = await session.execute(stmt)
            count = result.scalar_one()
            return count
