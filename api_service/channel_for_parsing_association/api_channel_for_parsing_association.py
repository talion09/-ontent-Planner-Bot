from fastapi import APIRouter
# from fastapi_cache.decorator import cache

from api_service.channel_for_parsing_association.dao import ChannelForParsingAssociationDao
from api_service.channel_for_parsing_association.schemas import ChannelForParsingAssociationSchema
from api_service.utils.schemas import Response

router_channel_for_parsing_association = APIRouter(
    prefix="/channel_for_parsing_association",
    tags=["Каналы - Парсеры - Ассоциации"],
)


@router_channel_for_parsing_association.post("/", response_model=Response[ChannelForParsingAssociationSchema])
async def add(payload: ChannelForParsingAssociationSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ChannelForParsingAssociationDao.add_commit(**payload_dict)
        data = ChannelForParsingAssociationSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel_for_parsing_association.get("/one/key_value/",
                                            response_model=Response[ChannelForParsingAssociationSchema])
async def get_one_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = ChannelForParsingAssociationSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await ChannelForParsingAssociationDao.find_one_or_none(**query_params)
        data = ChannelForParsingAssociationSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel_for_parsing_association.get("/all/key_value/",
                                            response_model=Response[list[ChannelForParsingAssociationSchema]])
async def get_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = ChannelForParsingAssociationSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await ChannelForParsingAssociationDao.find_all(**query_params)
        data = [ChannelForParsingAssociationSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel_for_parsing_association.post("/one/", response_model=Response[ChannelForParsingAssociationSchema])
async def get(payload: ChannelForParsingAssociationSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ChannelForParsingAssociationDao.find_one_or_none(**payload_dict)
        data = ChannelForParsingAssociationSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel_for_parsing_association.post("/all/", response_model=Response[list[ChannelForParsingAssociationSchema]])
async def get_all(payload: ChannelForParsingAssociationSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ChannelForParsingAssociationDao.find_all(**payload_dict)
        data = [ChannelForParsingAssociationSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel_for_parsing_association.put("/", response_model=Response[ChannelForParsingAssociationSchema])
async def update(payload: ChannelForParsingAssociationSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ChannelForParsingAssociationDao.update_commit(**payload_dict)
        data = ChannelForParsingAssociationSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel_for_parsing_association.delete("/{id}/", response_model=Response[ChannelForParsingAssociationSchema])
async def delete(id: int):
    try:
        data_dict = {"id": id}
        result = await ChannelForParsingAssociationDao.delete_commit(**data_dict)
        data = ChannelForParsingAssociationSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_channel_for_parsing_association.get("/count/key_value/", response_model=Response[int])
async def count(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = ChannelForParsingAssociationSchema(**temp_dict)
        value = getattr(temp_obj, key)
        query_params = {key: value}
        data = await ChannelForParsingAssociationDao.count(**query_params)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response
