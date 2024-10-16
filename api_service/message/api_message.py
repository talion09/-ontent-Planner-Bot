from fastapi import APIRouter
# from fastapi_cache.decorator import cache

from api_service.message.dao import MessageDao
from api_service.message.schemas import MessageSchema
from api_service.utils.schemas import Response

router_message = APIRouter(
    prefix="/message",
    tags=["Сообщения"],
)


@router_message.post("/", response_model=Response[MessageSchema])
async def add(payload: MessageSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await MessageDao.add_commit(**payload_dict)
        data = MessageSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_message.get("/one/key_value/",
                    response_model=Response[MessageSchema])
async def get_one_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = MessageSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await MessageDao.find_one_or_none(**query_params)
        data = MessageSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_message.get("/all/key_value/",
                    response_model=Response[list[MessageSchema]])
async def get_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = MessageSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await MessageDao.find_all(**query_params)
        data = [MessageSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_message.post("/one/", response_model=Response[MessageSchema])
async def get(payload: MessageSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await MessageDao.find_one_or_none(**payload_dict)
        data = MessageSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_message.post("/all/", response_model=Response[list[MessageSchema]])
async def get_all(payload: MessageSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await MessageDao.find_all(**payload_dict)
        data = [MessageSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_message.put("/", response_model=Response[MessageSchema])
async def update(payload: MessageSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await MessageDao.update_commit(**payload_dict)
        data = MessageSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_message.delete("/{id}/", response_model=Response[MessageSchema])
async def delete(id: int):
    try:
        data_dict = {"id": id}
        result = await MessageDao.delete_commit(**data_dict)
        data = MessageSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_message.get("/count/key_value/", response_model=Response[int])
async def count(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = MessageSchema(**temp_dict)
        value = getattr(temp_obj, key)
        query_params = {key: value}
        data = await MessageDao.count(**query_params)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response
