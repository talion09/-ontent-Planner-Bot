from fastapi import APIRouter

from api_service.parsed_messages.dao import ParsedMessagesDao
from api_service.parsed_messages.schemas import ParsedMessagesSchema
from api_service.utils.schemas import Response

router_parsed_messages = APIRouter(
    prefix="/parsed_messages",
    tags=["ParsedMessages"],
)


@router_parsed_messages.post("/", response_model=Response[ParsedMessagesSchema])
async def add(payload: ParsedMessagesSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ParsedMessagesDao.add_commit(**payload_dict)
        data = ParsedMessagesSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_parsed_messages.get("/one/key_value/",
                    response_model=Response[ParsedMessagesSchema])
async def get_one_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = ParsedMessagesSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await ParsedMessagesDao.find_one_or_none(**query_params)
        data = ParsedMessagesSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_parsed_messages.get("/all/key_value/",
                    response_model=Response[list[ParsedMessagesSchema]])
async def get_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = ParsedMessagesSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await ParsedMessagesDao.find_all(**query_params)
        data = [ParsedMessagesSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_parsed_messages.post("/one/", response_model=Response[ParsedMessagesSchema])
async def get(payload: ParsedMessagesSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ParsedMessagesDao.find_one_or_none(**payload_dict)
        data = ParsedMessagesSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_parsed_messages.post("/all/", response_model=Response[list[ParsedMessagesSchema]])
async def get_all(payload: ParsedMessagesSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ParsedMessagesDao.find_all(**payload_dict)
        data = [ParsedMessagesSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_parsed_messages.put("/", response_model=Response[ParsedMessagesSchema])
async def update(payload: ParsedMessagesSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await ParsedMessagesDao.update_commit(**payload_dict)
        data = ParsedMessagesSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_parsed_messages.delete("/{id}/", response_model=Response[ParsedMessagesSchema])
async def delete(id: int):
    try:
        data_dict = {"id": id}
        result = await ParsedMessagesDao.delete_commit(**data_dict)
        data = ParsedMessagesSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_parsed_messages.get("/count/key_value/", response_model=Response[int])
async def count(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = ParsedMessagesSchema(**temp_dict)
        value = getattr(temp_obj, key)
        query_params = {key: value}
        data = await ParsedMessagesDao.count(**query_params)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response