from fastapi import APIRouter
# from fastapi_cache.decorator import cache

from api_service.user_channel_settings.dao import UserChannelSettingsDao
from api_service.user_channel_settings.schemas import UserChannelSettingsSchema, UpdateSubscriptionIdByChannelIdsSchema
from api_service.utils.schemas import Response

router_user_channel_settings = APIRouter(
    prefix="/user_channel_settings",
    tags=["Настройки Каналов"],
)


@router_user_channel_settings.post("/", response_model=Response[UserChannelSettingsSchema])
async def add(payload: UserChannelSettingsSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await UserChannelSettingsDao.add_commit(**payload_dict)
        data = UserChannelSettingsSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user_channel_settings.get("/one/key_value/",
                                  response_model=Response[UserChannelSettingsSchema])
async def get_one_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = UserChannelSettingsSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await UserChannelSettingsDao.find_one_or_none(**query_params)
        data = UserChannelSettingsSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user_channel_settings.get("/all/key_value/",
                                  response_model=Response[list[UserChannelSettingsSchema]])
async def get_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = UserChannelSettingsSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await UserChannelSettingsDao.find_all(**query_params)
        data = [UserChannelSettingsSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user_channel_settings.post("/one/", response_model=Response[UserChannelSettingsSchema])
async def get(payload: UserChannelSettingsSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await UserChannelSettingsDao.find_one_or_none(**payload_dict)
        data = UserChannelSettingsSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user_channel_settings.post("/all/", response_model=Response[list[UserChannelSettingsSchema]])
async def get_all(payload: UserChannelSettingsSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await UserChannelSettingsDao.find_all(**payload_dict)
        data = [UserChannelSettingsSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user_channel_settings.put("/", response_model=Response[UserChannelSettingsSchema])
async def update(payload: UserChannelSettingsSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await UserChannelSettingsDao.update_commit(**payload_dict)
        data = UserChannelSettingsSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user_channel_settings.delete("/{id}/", response_model=Response[UserChannelSettingsSchema])
async def delete(id: int):
    try:
        data_dict = {"id": id}
        result = await UserChannelSettingsDao.delete_commit(**data_dict)
        data = UserChannelSettingsSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user_channel_settings.get("/count/key_value/", response_model=Response[int])
async def count(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = UserChannelSettingsSchema(**temp_dict)
        value = getattr(temp_obj, key)
        query_params = {key: value}
        data = await UserChannelSettingsDao.count(**query_params)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user_channel_settings.get("/trial_used/", response_model=Response[bool])
async def trial_used(user_id: int):
    try:
        data = await UserChannelSettingsDao.check_trial_used_for_user(user_id=user_id)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


# update_subscription_id_by_channel_ids
@router_user_channel_settings.post("/update_subscription_id_by_channel_ids/", response_model=Response[bool])
async def update_subscription_id_by_channel_ids(payload: UpdateSubscriptionIdByChannelIdsSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        await UserChannelSettingsDao.update_subscription_id_by_channel_ids(**payload_dict)
        response = Response(status="success", data=True, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response
