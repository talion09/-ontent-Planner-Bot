from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserOpenAISchema(BaseModel):
    id: Optional[int] = None
    user_id: Optional[int] = None
    open_ai_id: Optional[int] = None
    requested_count: Optional[int] = None
    requested_date: Optional[datetime] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
