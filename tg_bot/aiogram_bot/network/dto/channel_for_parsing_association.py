from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ChannelForParsingAssociationSchema(BaseModel):
    id: Optional[int] = None
    channel_id: Optional[int] = None
    channel_for_parsing_id: Optional[int] = None
    user_id: Optional[int] = None
    last_time_view_posts_tapped: Optional[datetime] = None
    quantity_of_parsed_message: Optional[int] = None
