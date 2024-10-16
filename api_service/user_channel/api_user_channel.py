from fastapi import APIRouter
# from fastapi_cache.decorator import cache

from api_service.user_channel.dao import UserChannelDao
from api_service.user_channel.schemas import UserChannelSchema, FindByChannelsIdSchma
from api_service.utils.schemas import Response

router_user_channel = APIRouter(
    prefix="/user_channel",
    tags=["Каналы Пользователей"],
)


@router_user_channel.post("/", response_model=Response[UserChannelSchema])
async def add(payload: UserChannelSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await UserChannelDao.add_commit(**payload_dict)
        data = UserChannelSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user_channel.get("/one/key_value/", response_model=Response[UserChannelSchema])
async def get_one_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = UserChannelSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await UserChannelDao.find_one_or_none(**query_params)
        data = UserChannelSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user_channel.get("/all/key_value/", response_model=Response[list[UserChannelSchema]])
async def get_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = UserChannelSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await UserChannelDao.find_all(**query_params)
        data = [UserChannelSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user_channel.post("/one/", response_model=Response[UserChannelSchema])
async def get(payload: UserChannelSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await UserChannelDao.find_one_or_none(**payload_dict)
        data = UserChannelSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user_channel.post("/all/", response_model=Response[list[UserChannelSchema]])
async def get_all(payload: UserChannelSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await UserChannelDao.find_all(**payload_dict)
        data = [UserChannelSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user_channel.put("/", response_model=Response[UserChannelSchema])
async def update(payload: UserChannelSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await UserChannelDao.update_commit(**payload_dict)
        data = UserChannelSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user_channel.delete("/{id}/", response_model=Response[UserChannelSchema])
async def delete(id: int):
    try:
        data_dict = {"id": id}
        result = await UserChannelDao.delete_commit(**data_dict)
        data = UserChannelSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user_channel.get("/count/key_value/", response_model=Response[int])
async def count(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = UserChannelSchema(**temp_dict)
        value = getattr(temp_obj, key)
        query_params = {key: value}
        data = await UserChannelDao.count(**query_params)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user_channel.post("/find_by_channels_id/", response_model=Response[list[UserChannelSchema]])
async def find_by_channels_id(payload: FindByChannelsIdSchma):
    try:
        result = await UserChannelDao.find_by_channels_id(*payload.ids)
        data = [UserChannelSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response

# count_unique_channels_by_subscription

@router_user_channel.get("/count_unique_channels_by_subscription/{subscription_id}", response_model=Response[int])
async def count_unique_channels_by_subscription(subscription_id: int):
    try:
        data = await UserChannelDao.count_unique_channels_by_subscription(subscription_id=subscription_id)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response
