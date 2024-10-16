from api_service.channel_for_parsing.models import ChannelForParsing
from api_service.database.base import BaseDao


class ChannelForParsingDao(BaseDao):
    model = ChannelForParsing
