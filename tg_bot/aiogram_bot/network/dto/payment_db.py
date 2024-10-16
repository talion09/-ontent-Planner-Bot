from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PaymentDbSchema(BaseModel):
    id: Optional[int] = None
    type: Optional[str] = None
    user_id: Optional[int] = None
    created: Optional[datetime] = None
    duration: Optional[int] = None
    channels: Optional[list[int]] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True