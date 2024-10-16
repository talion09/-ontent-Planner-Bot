from api_service.database.base import BaseDao
from api_service.paywave.models import Paywave


class PaywaveDao(BaseDao):
    model = Paywave  # table name
