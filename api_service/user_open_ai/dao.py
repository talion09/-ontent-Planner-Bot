from api_service.database.base import BaseDao
from api_service.user_open_ai.models import UserOpenAI


class UserOpenAIDao(BaseDao):
    model = UserOpenAI
