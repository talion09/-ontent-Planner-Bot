from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MediaItem(BaseModel):
    sequence_number: int
    file_id: str
    media_type: str

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class PostSchema(BaseModel):
    id: Optional[int] = None
    user_id: Optional[int] = None
    description: Optional[str] = None
    url_buttons: Optional[list[str]] = None
    media: Optional[list[MediaItem]] = None
    messages_id: Optional[list[int]] = None
    channel_id: Optional[int] = None
    date: Optional[datetime] = None
    auto_delete_timer: Optional[int] = None
    is_saved: Optional[bool] = None
    is_scheduled: Optional[bool] = None
    initial_post_id: Optional[int] = None
    entities: Optional[str] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class FilteredSchema(BaseModel):
    user_id: Optional[int] = None
    channel_id: Optional[int] = None
    date: Optional[datetime] = None
    is_scheduled: Optional[bool] = None
