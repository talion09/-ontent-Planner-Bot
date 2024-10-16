from api_service.database.base import BaseDao
from api_service.open_ai.models import OpenAI


class OpenAIDao(BaseDao):
    model = OpenAI  # table name
