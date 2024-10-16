from typing import Optional

from pydantic import BaseModel


class ChannelSchema(BaseModel):
    id: Optional[int] = None
    link: Optional[str] = None
    title: Optional[str] = None