from typing import Optional

from pydantic import BaseModel


class OpenAISchema(BaseModel):
    id: Optional[int] = None
    requests_count_per_minute: Optional[int] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
