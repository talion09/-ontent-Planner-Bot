from fastapi import APIRouter

from api_service.parsing_source.dao import ParsingSourceDao
from api_service.parsing_source.schemas import ParsingSourceSchema
from api_service.utils.schemas import Response

router_parsing_source = APIRouter(
    prefix="/parsing_source",
    tags=["ParsingSource"],
)


@router_parsing_source.post("/", response_model=Response[ParsingSourceSchema])
async def add(payload: ParsingSourceSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ParsingSourceDao.add_commit(**payload_dict)
        data = ParsingSourceSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_parsing_source.get("/one/key_value/",
                           response_model=Response[ParsingSourceSchema])
async def get_one_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = ParsingSourceSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await ParsingSourceDao.find_one_or_none(**query_params)
        data = ParsingSourceSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_parsing_source.get("/all/key_value/",
                           response_model=Response[list[ParsingSourceSchema]])
async def get_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = ParsingSourceSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await ParsingSourceDao.find_all(**query_params)
        data = [ParsingSourceSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_parsing_source.post("/one/", response_model=Response[ParsingSourceSchema])
async def get(payload: ParsingSourceSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ParsingSourceDao.find_one_or_none(**payload_dict)
        data = ParsingSourceSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_parsing_source.post("/all/", response_model=Response[list[ParsingSourceSchema]])
async def get_all(payload: ParsingSourceSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ParsingSourceDao.find_all(**payload_dict)
        data = [ParsingSourceSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_parsing_source.put("/", response_model=Response[ParsingSourceSchema])
async def update(payload: ParsingSourceSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ParsingSourceDao.update_commit(**payload_dict)
        data = ParsingSourceSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_parsing_source.delete("/{id}/", response_model=Response[ParsingSourceSchema])
async def delete(id: int):
    try:
        data_dict = {"id": id}
        result = await ParsingSourceDao.delete_commit(**data_dict)
        data = ParsingSourceSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_parsing_source.get("/count/key_value/", response_model=Response[int])
async def count(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = ParsingSourceSchema(**temp_dict)
        value = getattr(temp_obj, key)
        query_params = {key: value}
        data = await ParsingSourceDao.count(**query_params)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response
