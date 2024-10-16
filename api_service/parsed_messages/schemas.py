from typing import Optional

from pydantic import BaseModel


class ParsedMessagesSchema(BaseModel):
    id: Optional[int] = None
    post_id: Optional[int] = None
    messages_id: Optional[list[int]] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
