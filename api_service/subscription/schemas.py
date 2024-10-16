from typing import Optional

from pydantic import BaseModel


class SubscriptionSchema(BaseModel):
    id: Optional[int] = None
    channel_for_parsing_quantity: Optional[int] = None
    has_advert: Optional[bool] = None
    open_ai_id: Optional[int] = None
    subscribers_quantity: Optional[int] = None
    posts_per_day_quantity: Optional[int] = None
    channel_name: Optional[str] = None
    price: Optional[dict] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
