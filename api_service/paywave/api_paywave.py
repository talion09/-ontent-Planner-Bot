from fastapi import APIRouter

from api_service.paywave.dao import PaywaveDao
from api_service.paywave.schemas import PaywaveSchema
# from fastapi_cache.decorator import cache

from api_service.utils.schemas import Response

router_paywave = APIRouter(
    prefix="/paywave",
    tags=["Paywave"],
)


@router_paywave.post("/", response_model=Response[PaywaveSchema])
async def add(payload: PaywaveSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await PaywaveDao.add_commit(**payload_dict)
        data = PaywaveSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_paywave.get("/one/key_value/", response_model=Response[PaywaveSchema])
async def get_one_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = PaywaveSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await PaywaveDao.find_one_or_none(**query_params)
        data = PaywaveSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_paywave.get("/all/key_value/", response_model=Response[list[PaywaveSchema]])
async def get_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = PaywaveSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await PaywaveDao.find_all(**query_params)
        data = [PaywaveSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_paywave.post("/one/", response_model=Response[PaywaveSchema])
async def get(payload: PaywaveSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await PaywaveDao.find_one_or_none(**payload_dict)
        data = PaywaveSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_paywave.post("/all/", response_model=Response[list[PaywaveSchema]])
async def get_all(payload: PaywaveSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await PaywaveDao.find_all(**payload_dict)
        data = [PaywaveSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_paywave.put("/", response_model=Response[PaywaveSchema])
async def update(payload: PaywaveSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await PaywaveDao.update_commit(**payload_dict)
        data = PaywaveSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_paywave.delete("/{id}/", response_model=Response[PaywaveSchema])
async def delete(id: int):
    try:
        data_dict = {"id": id}
        result = await PaywaveDao.delete_commit(**data_dict)
        data = PaywaveSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_paywave.get("/count/key_value/", response_model=Response[int])
async def count(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = PaywaveSchema(**temp_dict)
        value = getattr(temp_obj, key)
        query_params = {key: value}
        data = await PaywaveDao.count(**query_params)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_paywave.post("/count/with_more_filters/", response_model=Response[int])
async def count_with_more_filters(payload: PaywaveSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        data = await PaywaveDao.count(**payload_dict)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response
