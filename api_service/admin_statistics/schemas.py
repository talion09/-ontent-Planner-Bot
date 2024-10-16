from typing import Optional

from pydantic import BaseModel


class RFMClassification(BaseModel):
    constant_active: int
    leaving: int
    sleeping: int


class StatiscticSchema(BaseModel):
    users_quantity: int
    free_subscriptions_quantity: int
    free_subscription_rfm: RFMClassification
    active_user_quantity_free: int
    premium_subscriptions_quantity: int
    premium_subscription_rfm: RFMClassification
    active_user_quantity_premium: int
    telegram_parsed_posts: Optional[int] = None

