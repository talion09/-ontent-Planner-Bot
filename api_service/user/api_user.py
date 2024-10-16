import asyncio

from fastapi import APIRouter
# from fastapi_cache.decorator import cache

from api_service.user.dao import UserDao
from api_service.user.schemas import UserSchema, GetUsersWithSpecificSubscription
from api_service.user_channel.schemas import UserChannelSchema
from api_service.utils.schemas import Response

router_user = APIRouter(
    prefix="/user",
    tags=["Пользователи"],
)


@router_user.post("/", response_model=Response[UserSchema])
async def add(payload: UserSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await UserDao.add_commit(**payload_dict)
        data = UserSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user.get("/one/key_value/", response_model=Response[UserSchema])
async def get_one_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = UserSchema(**temp_dict)
        value = getattr(temp_obj, key)
        query_params = {key: value}
        result = await UserDao.find_one_or_none(**query_params)
        data = UserSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user.get("/{id}/", response_model=Response[UserSchema])
async def get_one_by_id(id: int):
    try:
        result = await UserDao.find_one_or_none(id=id)
        data = UserSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user.get("/all/key_value/", response_model=Response[list[UserSchema]])
async def get_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = UserSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await UserDao.find_all(**query_params)
        data = [UserSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user.post("/one/", response_model=Response[UserSchema])
async def get(payload: UserSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await UserDao.find_one_or_none(**payload_dict)
        data = UserSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user.post("/all/", response_model=Response[list[UserSchema]])
async def get_all(payload: UserSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await UserDao.find_all(**payload_dict)
        data = [UserSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user.put("/", response_model=Response[UserSchema])
async def update(payload: UserSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await UserDao.update_commit(**payload_dict)
        data = UserSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user.delete("/{id}/", response_model=Response[UserSchema])
async def delete(id: int):
    try:
        data_dict = {"id": id}
        result = await UserDao.delete_commit(**data_dict)
        data = UserSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user.get("/count/key_value/", response_model=Response[int])
async def count(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = UserSchema(**temp_dict)
        value = getattr(temp_obj, key)
        query_params = {key: value}
        data = await UserDao.count(**query_params)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user.get("/count/all/", response_model=Response[int])
async def count_all():
    try:
        data = await UserDao.count_all()
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user.post("/get_users_with_specific_subscription/", response_model=Response[list[UserChannelSchema]])
async def get_users_with_specific_subscription(payload: GetUsersWithSpecificSubscription):
    try:
        result = await UserDao.get_users_with_specific_subscription(
            channel_for_parsing_id=payload.channel_for_parsing_id, subscription_id=payload.subscription_id)
        data = [UserChannelSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user.get("/get_unique_users_with_subscription/{subscription_id}", response_model=Response[list[int]])
async def get_unique_users_with_subscription(subscription_id: int):
    try:
        data = await UserDao.get_unique_users_with_subscription(subscription_id=subscription_id)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response
