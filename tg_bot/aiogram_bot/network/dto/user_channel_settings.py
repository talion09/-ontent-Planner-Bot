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