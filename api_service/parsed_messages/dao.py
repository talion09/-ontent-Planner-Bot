from api_service.database.base import BaseDao
from api_service.parsed_messages.models import ParsedMessages


class ParsedMessagesDao(BaseDao):
    model = ParsedMessages  # table name
