from fastapi import APIRouter
# from fastapi_cache.decorator import cache

from api_service.channel_for_parsing.dao import ChannelForParsingDao
from api_service.channel_for_parsing.schemas import ChannelForParsingSchema
from api_service.utils.schemas import Response

router_channel_for_parsing = APIRouter(
    prefix="/channel_for_parsing",
    tags=["Каналы - Парсеры"],
)


@router_channel_for_parsing.post("/", response_model=Response[ChannelForParsingSchema])
async def add(payload: ChannelForParsingSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ChannelForParsingDao.add_commit(**payload_dict)
        data = ChannelForParsingSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel_for_parsing.get("/one/key_value/", response_model=Response[ChannelForParsingSchema])
async def get_one_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = ChannelForParsingSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await ChannelForParsingDao.find_one_or_none(**query_params)
        data = ChannelForParsingSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel_for_parsing.get("/all/key_value/", response_model=Response[list[ChannelForParsingSchema]])
async def get_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = ChannelForParsingSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await ChannelForParsingDao.find_all(**query_params)
        data = [ChannelForParsingSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel_for_parsing.post("/one/", response_model=Response[ChannelForParsingSchema])
async def get(payload: ChannelForParsingSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ChannelForParsingDao.find_one_or_none(**payload_dict)
        data = ChannelForParsingSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel_for_parsing.post("/all/", response_model=Response[list[ChannelForParsingSchema]])
async def get_all(payload: ChannelForParsingSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ChannelForParsingDao.find_all(**payload_dict)
        data = [ChannelForParsingSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel_for_parsing.put("/", response_model=Response[ChannelForParsingSchema])
async def update(payload: ChannelForParsingSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ChannelForParsingDao.update_commit(**payload_dict)
        data = ChannelForParsingSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel_for_parsing.delete("/{id}/", response_model=Response[ChannelForParsingSchema])
async def delete(id: int):
    try:
        data_dict = {"id": id}
        result = await ChannelForParsingDao.delete_commit(**data_dict)
        data = ChannelForParsingSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel_for_parsing.get("/count/key_value/", response_model=Response[int])
async def count(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = ChannelForParsingSchema(**temp_dict)
        value = getattr(temp_obj, key)
        query_params = {key: value}
        data = await ChannelForParsingDao.count(**query_params)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response
