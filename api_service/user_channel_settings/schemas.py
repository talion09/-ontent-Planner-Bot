from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserChannelSettingsSchema(BaseModel):
    id: Optional[int] = None
    auto_sign: Optional[bool] = None
    auto_sign_text: Optional[str] = None
    prompts: Optional[list[dict]] = None
    disabled: Optional[bool] = None
    subscription_id: Optional[int] = None
    trial_used: Optional[bool] = None
    created: Optional[datetime] = None
    finished: Optional[datetime] = None
    posts_per_day: Optional[int] = None
    auto_sign_entities: Optional[str] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class UpdateSubscriptionIdByChannelIdsSchema(BaseModel):
    channel_ids: Optional[list[int]] = None
    new_subscription_id: Optional[int] = None
    created: Optional[datetime] = None
    finished: Optional[datetime] = None
