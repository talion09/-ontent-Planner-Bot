from typing import Optional

from pydantic import BaseModel


class UserChannelSchema(BaseModel):
    id: Optional[int] = None
    channel_id: Optional[int] = None
    user_id: Optional[int] = None
    user_channel_settings_id: Optional[int] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class FindByChannelsIdSchma(BaseModel):
    ids: Optional[list[int]] = None