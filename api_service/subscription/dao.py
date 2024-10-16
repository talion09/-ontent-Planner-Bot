from api_service.database.base import BaseDao
from api_service.subscription.models import Subscription


class SubscriptionDao(BaseDao):
    model = Subscription  # table name
