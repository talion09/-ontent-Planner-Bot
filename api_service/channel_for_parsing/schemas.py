from typing import Optional

from pydantic import BaseModel


class ChannelForParsingSchema(BaseModel):
    id: Optional[int] = None
    link: Optional[str] = None
    title: Optional[str] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
