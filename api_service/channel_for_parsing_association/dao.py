from api_service.channel_for_parsing_association.models import ChannelForParsingAssociation
from api_service.database.base import BaseDao


class ChannelForParsingAssociationDao(BaseDao):
    model = ChannelForParsingAssociation
