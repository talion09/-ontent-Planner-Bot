from datetime import datetime
from typing import Optional, TypeVar, Generic

from pydantic import BaseModel
from pydantic.generics import GenericModel

DataT = TypeVar('DataT')


class Response(GenericModel, Generic[DataT]):
    status: str
    data: Optional[DataT] = None
    details: Optional[str] = None


class TelethonUserDto(BaseModel):
    id: Optional[int] = None
    user_id: Optional[int] = None
    number: Optional[str] = None
    proxy: Optional[dict] = None
    active: Optional[bool] = None


class JoinToChannelDto(BaseModel):
    user_id: Optional[int] = None
    channel_id: Optional[int] = None
    parser_link: Optional[str] = None


class GetPostsDto(BaseModel):
    channel_for_parsing_association_id: Optional[int] = None
    parser_link: Optional[str] = None


class GetPostsByDateDto(BaseModel):
    channel_for_parsing_association_id: Optional[int] = None
    parser_link: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ChannelForParsingAssociationSchema(BaseModel):
    id: Optional[int] = None
    channel_id: Optional[int] = None
    channel_for_parsing_id: Optional[int] = None
    user_id: Optional[int] = None
    last_time_view_posts_tapped: Optional[datetime] = None
    quantity_of_parsed_message: Optional[int] = None


class ParsingSourceSchema(BaseModel):
    id: Optional[int] = None
    type: Optional[str] = None
    posts_quantity: Optional[int] = None


class UserSchema(BaseModel):
    id: Optional[int] = None
    time_zone: Optional[int] = None
    gpt_api_key: Optional[str] = None
    mail: Optional[str] = None
    post_auto_send: Optional[bool] = None
    created: Optional[datetime] = None
    parsing_stopped: Optional[bool] = None
    lang: Optional[str] = None