from typing import Optional

from pydantic import BaseModel


class ParsingSourceSchema(BaseModel):
    id: Optional[int] = None
    type: Optional[str] = None
    posts_quantity: Optional[int] = None
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True