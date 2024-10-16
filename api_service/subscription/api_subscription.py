from fastapi import APIRouter
# from fastapi_cache.decorator import cache

from api_service.subscription.dao import SubscriptionDao
from api_service.subscription.schemas import SubscriptionSchema
from api_service.utils.schemas import Response

router_subscription = APIRouter(
    prefix="/subscription",
    tags=["Подпииски"],
)


@router_subscription.post("/", response_model=Response[SubscriptionSchema])
async def add(payload: SubscriptionSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await SubscriptionDao.add_commit(**payload_dict)
        data = SubscriptionSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_subscription.get("/one/key_value/", response_model=Response[SubscriptionSchema])
async def get_one_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = SubscriptionSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await SubscriptionDao.find_one_or_none(**query_params)
        data = SubscriptionSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_subscription.get("/all/key_value/", response_model=Response[list[SubscriptionSchema]])
async def get_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = SubscriptionSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await SubscriptionDao.find_all(**query_params)
        data = [SubscriptionSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_subscription.post("/one/", response_model=Response[SubscriptionSchema])
async def get(payload: SubscriptionSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await SubscriptionDao.find_one_or_none(**payload_dict)
        data = SubscriptionSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_subscription.post("/all/", response_model=Response[list[SubscriptionSchema]])
async def get_all(payload: SubscriptionSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await SubscriptionDao.find_all(**payload_dict)
        data = [SubscriptionSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_subscription.put("/", response_model=Response[SubscriptionSchema])
async def update(payload: SubscriptionSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await SubscriptionDao.update_commit(**payload_dict)
        data = SubscriptionSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_subscription.delete("/{id}/", response_model=Response[SubscriptionSchema])
async def delete(id: int):
    try:
        data_dict = {"id": id}
        result = await SubscriptionDao.delete_commit(**data_dict)
        data = SubscriptionSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_subscription.get("/count/key_value/", response_model=Response[int])
async def count(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = SubscriptionSchema(**temp_dict)
        value = getattr(temp_obj, key)
        query_params = {key: value}
        data = await SubscriptionDao.count(**query_params)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response
