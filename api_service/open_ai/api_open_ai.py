from fastapi import APIRouter
# from fastapi_cache.decorator import cache

from api_service.open_ai.dao import OpenAIDao
from api_service.open_ai.schemas import OpenAISchema
from api_service.utils.schemas import Response

router_open_ai = APIRouter(
    prefix="/open_ai",
    tags=["OpenAI"],
)


@router_open_ai.post("/", response_model=Response[OpenAISchema])
async def add(payload: OpenAISchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await OpenAIDao.add_commit(**payload_dict)
        data = OpenAISchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_open_ai.get("/one/key_value/",
                    response_model=Response[OpenAISchema])
async def get_one_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = OpenAISchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await OpenAIDao.find_one_or_none(**query_params)
        data = OpenAISchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_open_ai.get("/all/key_value/",
                    response_model=Response[list[OpenAISchema]])
async def get_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = OpenAISchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await OpenAIDao.find_all(**query_params)
        data = [OpenAISchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_open_ai.post("/one/", response_model=Response[OpenAISchema])
async def get(payload: OpenAISchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await OpenAIDao.find_one_or_none(**payload_dict)
        data = OpenAISchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_open_ai.post("/all/", response_model=Response[list[OpenAISchema]])
async def get_all(payload: OpenAISchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await OpenAIDao.find_all(**payload_dict)
        data = [OpenAISchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_open_ai.put("/", response_model=Response[OpenAISchema])
async def update(payload: OpenAISchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await OpenAIDao.update_commit(**payload_dict)
        data = OpenAISchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_open_ai.delete("/{id}/", response_model=Response[OpenAISchema])
async def delete(id: int):
    try:
        data_dict = {"id": id}
        result = await OpenAIDao.delete_commit(**data_dict)
        data = OpenAISchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_open_ai.get("/count/key_value/", response_model=Response[int])
async def count(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = OpenAISchema(**temp_dict)
        value = getattr(temp_obj, key)
        query_params = {key: value}
        data = await OpenAIDao.count(**query_params)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response
