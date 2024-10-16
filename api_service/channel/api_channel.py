from fastapi import APIRouter
# from fastapi_cache.decorator import cache

from api_service.channel.dao import ChannelDao
from api_service.channel.schemas import ChannelSchema, ChannelRequestSchema
from api_service.utils.schemas import Response

router_channel = APIRouter(
    prefix="/channel",
    tags=["Каналы"],
)


@router_channel.post("/", response_model=Response[ChannelSchema])
async def add(payload: ChannelSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ChannelDao.add_commit(**payload_dict)
        data = ChannelSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel.get("/one/key_value/", response_model=Response[ChannelSchema])
async def get_one_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = ChannelSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await ChannelDao.find_one_or_none(**query_params)
        data = ChannelSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel.get("/all/key_value/", response_model=Response[list[ChannelSchema]])
async def get_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = ChannelSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await ChannelDao.find_all(**query_params)
        data = [ChannelSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel.post("/one/", response_model=Response[ChannelSchema])
async def get(payload: ChannelSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ChannelDao.find_one_or_none(**payload_dict)
        data = ChannelSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel.post("/all/", response_model=Response[list[ChannelSchema]])
async def get_all(payload: ChannelSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ChannelDao.find_all(**payload_dict)
        data = [ChannelSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel.put("/", response_model=Response[ChannelSchema])
async def update(payload: ChannelSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ChannelDao.update_commit(**payload_dict)
        data = ChannelSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel.delete("/{id}/", response_model=Response[ChannelSchema])
async def delete(id: int):
    try:
        data_dict = {"id": id}
        result = await ChannelDao.delete_commit(**data_dict)
        data = ChannelSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel.get("/count/key_value/", response_model=Response[int])
async def count(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = ChannelSchema(**temp_dict)
        value = getattr(temp_obj, key)
        query_params = {key: value}
        data = await ChannelDao.count(**query_params)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel.post("/get_user_channels_with_certain_subscriptions/", response_model=Response[list[ChannelSchema]])
async def get_user_channels_with_certain_subscriptions(payload: ChannelRequestSchema):
    try:
        payload_dict = payload.model_dump()
        result = await ChannelDao.get_user_channels_with_certain_subscriptions(**payload_dict)
        data = [ChannelSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response
