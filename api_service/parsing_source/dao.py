from api_service.database.base import BaseDao
from api_service.parsing_source.models import ParsingSource


class ParsingSourceDao(BaseDao):
    model = ParsingSource  # table name
