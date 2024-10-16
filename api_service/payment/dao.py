from api_service.database.base import BaseDao
from api_service.payment.models import Payment


class PaymentDao(BaseDao):
    model = Payment  # table name