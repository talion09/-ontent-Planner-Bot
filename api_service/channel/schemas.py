from typing import Optional, Union

from pydantic import BaseModel


class ChannelSchema(BaseModel):
    id: Optional[int] = None
    link: Optional[str] = None
    title: Optional[str] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class ChannelRequestSchema(BaseModel):
    user_id: Optional[int] = None
    subscriptions: Optional[list[Union[int, None]]] = None
    disabled: Optional[bool] = None
