from fastapi import APIRouter

from api_service.payment.dao import PaymentDao
from api_service.payment.schemas import PaymentSchema
from api_service.utils.schemas import Response

router_payment = APIRouter(
    prefix="/payment",
    tags=["Payment"],
)


@router_payment.post("/", response_model=Response[PaymentSchema])
async def add(payload: PaymentSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await PaymentDao.add_commit(**payload_dict)
        data = PaymentSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_payment.get("/one/key_value/",
                           response_model=Response[PaymentSchema])
async def get_one_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = PaymentSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await PaymentDao.find_one_or_none(**query_params)
        data = PaymentSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_payment.get("/all/key_value/",
                           response_model=Response[list[PaymentSchema]])
async def get_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = PaymentSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await PaymentDao.find_all(**query_params)
        data = [PaymentSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_payment.post("/one/", response_model=Response[PaymentSchema])
async def get(payload: PaymentSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await PaymentDao.find_one_or_none(**payload_dict)
        data = PaymentSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_payment.post("/all/", response_model=Response[list[PaymentSchema]])
async def get_all(payload: PaymentSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await PaymentDao.find_all(**payload_dict)
        data = [PaymentSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_payment.put("/", response_model=Response[PaymentSchema])
async def update(payload: PaymentSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await PaymentDao.update_commit(**payload_dict)
        data = PaymentSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_payment.delete("/{id}/", response_model=Response[PaymentSchema])
async def delete(id: int):
    try:
        data_dict = {"id": id}
        result = await PaymentDao.delete_commit(**data_dict)
        data = PaymentSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_payment.get("/count/key_value/", response_model=Response[int])
async def count(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = PaymentSchema(**temp_dict)
        value = getattr(temp_obj, key)
        query_params = {key: value}
        data = await PaymentDao.count(**query_params)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response
