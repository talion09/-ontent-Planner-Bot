from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PaywaveSchema(BaseModel):
    id: Optional[int] = None
    user_id: Optional[int] = None
    created: Optional[datetime] = None
