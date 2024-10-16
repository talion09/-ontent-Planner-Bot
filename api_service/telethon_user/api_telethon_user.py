import logging

from fastapi import APIRouter

from api_service.database.database import async_session_maker
from api_service.telethon_user.dao import TelethonUserDao, TelethonParserChannelDao, \
    TelethonUserParserChannelAssociationDao
from api_service.telethon_user.schemas import TelethonUserSchema, \
    TelethonParserChannelSchema, AddChannelSchema, TelethonUserWithChannelAssociationlSchema
from api_service.utils.schemas import Response

# from fastapi_cache.decorator import cache

router_telethon = APIRouter(
    prefix="/telethon",
    tags=["Telethon"],
)


@router_telethon.post("/user/", response_model=Response[TelethonUserSchema])
async def add_telethon_user(user_payload: TelethonUserSchema):
    try:
        user_data = user_payload.model_dump(exclude_unset=True)
        result = await TelethonUserDao.add_commit(**user_data)
        data = TelethonUserSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        logging.error(f"telethon_user {e}")
        response = Response(status="error", data=None, details=str(e))
    return response


@router_telethon.post("/user/find/", response_model=Response[TelethonUserSchema])
async def find_telethon_user(telethon_user_payload: TelethonUserSchema):
    try:
        telethon_user_data = telethon_user_payload.model_dump(exclude_unset=True)
        result = await TelethonUserDao.find_one_or_none(**telethon_user_data)
        data = TelethonUserSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        logging.error(f"find_telethon_user {e}")
        response = Response(status="error", data=None, details=str(e))
    return response


@router_telethon.post("/channel/", response_model=Response[TelethonUserWithChannelAssociationlSchema])
async def add_channel(channel_payload: AddChannelSchema):
    try:
        parser_channel = await TelethonParserChannelDao.find_one_or_none(id=channel_payload.parser_id)

        if parser_channel:
            exists = await TelethonUserParserChannelAssociationDao.find_one_or_none(user_id=channel_payload.user_id,
                                                                                    parser_channel_id=parser_channel[
                                                                                        'id'])
            if not exists:
                result = await TelethonUserParserChannelAssociationDao.add_commit(user_id=channel_payload.user_id,
                                                                                  parser_channel_id=parser_channel[
                                                                                      'id'])
                data = TelethonUserWithChannelAssociationlSchema.model_validate(result)
            else:
                data = exists
        else:
            async with async_session_maker() as session:
                result = await TelethonParserChannelDao.add_execute(session=session,
                                                                    data={"id": channel_payload.parser_id,
                                                                          "link": channel_payload.parser_link})
                data = TelethonParserChannelSchema.model_validate(result)
                result = await TelethonUserParserChannelAssociationDao.add_execute(session=session,
                                                                                   data={
                                                                                       "user_id": channel_payload.user_id,
                                                                                       "parser_channel_id": data.id})
                data = TelethonUserWithChannelAssociationlSchema.model_validate(result)

                await session.commit()

        response = Response(status="success", data=data, details=None)
    except Exception as e:
        logging.error(f"channel {e}")
        response = Response(status="error", data=None, details=str(e))
    return response


@router_telethon.get("/telethon_users/", response_model=Response[list[TelethonUserSchema]])
async def find_all_telethon_users():
    try:
        result = await TelethonUserDao.find_all()
        data = [TelethonUserSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        logging.error(f"telethon_users {e}")
        response = Response(status="error", data=None, details=str(e))
    return response


@router_telethon.get("/get_next_telethon_user/{id}/", response_model=Response[TelethonUserSchema])
async def get_next_telethon_user(id: int):
    try:
        result = await TelethonUserDao.get_next_row(id=id)
        data = TelethonUserSchema.model_validate(result)
        update_not_active = await TelethonUserDao.update_commit(**{"id": id, "active": False})
        update_active = await TelethonUserDao.update_commit(**{"id": data.id, "active": True})
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        logging.error(f"get_next_telethon_user {e}")
        response = Response(status="error", data=None, details=str(e))
    return response


@router_telethon.get("/count_parser_channels/{user_id}", response_model=Response[int])
async def count_parser_channels(user_id: int):
    try:
        data = await TelethonUserParserChannelAssociationDao.count(user_id=user_id)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        logging.error(f"count_parser_channels {e}")
        response = Response(status="error", data=None, details=str(e))
    return response


@router_telethon.get("/telethon_user_channel_association/{parser_channel_id}/",response_model=Response[TelethonUserWithChannelAssociationlSchema])
async def telethon_user_channel_association(parser_channel_id:int):
    try:
        data = await TelethonUserParserChannelAssociationDao.find_one_or_none(parser_channel_id=parser_channel_id)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        logging.error(f"count_parser_channels {e}")
        response = Response(status="error", data=None, details=str(e))
    return response
