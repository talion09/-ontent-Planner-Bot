from fastapi import APIRouter

from api_service.open_ai.dao import OpenAIDao
from api_service.user_open_ai.dao import UserOpenAIDao
from api_service.user_open_ai.schemas import UserOpenAISchema
from api_service.utils.schemas import Response

router_user_open_ai = APIRouter(
    prefix="/user_open_ai",
    tags=["UserOpenAI"],
)


@router_user_open_ai.post("/", response_model=Response[UserOpenAISchema])
async def add(payload: UserOpenAISchema):
    try:
        data = payload.model_dump(exclude_unset=True)
        result = await UserOpenAIDao.add_commit(**data)
        data = UserOpenAISchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user_open_ai.post("/one/", response_model=Response[UserOpenAISchema])
async def get(payload: UserOpenAISchema):
    """
    requested_date должен передавать в таком виде
    2024-01-31 16:00:00
    """
    try:
        data = payload.model_dump(exclude_unset=True)
        if 'requested_date' in data:
            requested_date_datetime_obj = data.pop('requested_date')
            result = await UserOpenAIDao.find_one_or_none(**data)

            if result is None:
                response = Response(status="error", data=None, details="Record doesnt exists")
                return response

            data = UserOpenAISchema.model_validate(result)

            if data.requested_date:
                difference = requested_date_datetime_obj - data.requested_date
                difference_in_minutes = difference.total_seconds() / 60

                if difference_in_minutes < 1:
                    requested_count = data.requested_count + 1

                    subscription_requests_count_per_minute = \
                        (await OpenAIDao.find_one_or_none(**{"id": data.open_ai_id}))['requests_count_per_minute']

                    if requested_count > subscription_requests_count_per_minute:
                        response = Response(status="error", data=None, details="Limit exceeded")
                        return response

                    else:
                        result = await UserOpenAIDao.update_commit(**{"id": data.id,
                                                                      "requested_count": requested_count,
                                                                      "requested_date": requested_date_datetime_obj})
                        data = UserOpenAISchema.model_validate(result)

                else:
                    result = await UserOpenAIDao.update_commit(**{"id": data.id,
                                                                  "requested_count": 1,
                                                                  "requested_date": requested_date_datetime_obj})

                    data = UserOpenAISchema.model_validate(result)

            else:
                result = await UserOpenAIDao.update_commit(**{"id": data.id,
                                                              "requested_count": 1,
                                                              "requested_date": requested_date_datetime_obj})

                data = UserOpenAISchema.model_validate(result)

        else:
            result = await UserOpenAIDao.find_one_or_none(**data)
            if result is not None:
                data = UserOpenAISchema.model_validate(result)
            else:
                response = Response(status="error", data=None, details="Record doesnt exists")
                return response

        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user_open_ai.put("/", response_model=Response[UserOpenAISchema])
async def update(payload: UserOpenAISchema):
    try:
        data = payload.model_dump(exclude_unset=True)
        result = await UserOpenAIDao.update_commit(**data)
        data = UserOpenAISchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_user_open_ai.delete("/{id}/", response_model=Response[UserOpenAISchema])
async def delete(id: int):
    try:
        data_dict = {"id": id}
        result = await UserOpenAIDao.delete_commit(**data_dict)
        data = UserOpenAISchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response
