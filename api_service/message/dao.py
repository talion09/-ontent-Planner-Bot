from api_service.database.base import BaseDao
from api_service.message.models import Message


class MessageDao(BaseDao):
    model = Message
