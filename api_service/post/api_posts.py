from fastapi import APIRouter
# from fastapi_cache.decorator import cache

from api_service.post.dao import PostDao
from api_service.post.schemas import PostSchema, FilteredSchema
from api_service.utils.schemas import Response

router_post = APIRouter(
    prefix="/post",
    tags=["Посты"],
)


@router_post.post("/", response_model=Response[PostSchema])
async def add(payload: PostSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await PostDao.add_commit(**payload_dict)
        data = PostSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_post.get("/one/key_value/", response_model=Response[PostSchema])
async def get_one_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = PostSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await PostDao.find_one_or_none(**query_params)
        data = PostSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_post.get("/all/key_value/", response_model=Response[list[PostSchema]])
async def get_by_key_value(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = PostSchema(**temp_dict)
        value = getattr(temp_obj, key)

        query_params = {key: value}
        result = await PostDao.find_all(**query_params)
        data = [PostSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_post.post("/one/", response_model=Response[PostSchema])
async def get(payload: PostSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await PostDao.find_one_or_none(**payload_dict)
        data = PostSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_post.post("/all/", response_model=Response[list[PostSchema]])
async def get_all(payload: PostSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await PostDao.find_all(**payload_dict)
        data = [PostSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_post.put("/", response_model=Response[PostSchema])
async def update(payload: PostSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await PostDao.update_commit(**payload_dict)
        data = PostSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_post.delete("/{id}/", response_model=Response[PostSchema])
async def delete(id: int):
    try:
        data_dict = {"id": id}
        result = await PostDao.delete_commit(**data_dict)
        data = PostSchema.model_validate(result)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_post.get("/count/key_value/", response_model=Response[int])
async def count(key: str, value: str):
    try:
        temp_dict = {key: value}
        temp_obj = PostSchema(**temp_dict)
        value = getattr(temp_obj, key)
        query_params = {key: value}
        data = await PostDao.count(**query_params)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_post.post("/count/with_more_filters/", response_model=Response[int])
async def count_with_more_filters(payload: PostSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        data = await PostDao.count(**payload_dict)
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response


@router_post.post("/get_filtered_posts/", response_model=Response[list[PostSchema]])
async def get_filtered_posts(payload: FilteredSchema):
    try:
        payload_dict = payload.model_dump(exclude_unset=True)
        result = await PostDao.get_filtered_posts(**payload_dict)
        data = [PostSchema(**item) for item in result]
        response = Response(status="success", data=data, details=None)
    except Exception as e:
        response = Response(status="error", data=None, details=str(e))
    return response
