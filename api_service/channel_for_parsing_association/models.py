from datetime import datetime

from sqlalchemy import Integer, ForeignKey, BigInteger, UniqueConstraint, DateTime
from sqlalchemy.orm import mapped_column, Mapped

from api_service.database.database import Base


class ChannelForParsingAssociation(Base):
    __tablename__ = "channel_for_parsing_association"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("channel.id"))
    channel_for_parsing_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("channel_for_parsing.id"))
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"))
    last_time_view_posts_tapped: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    quantity_of_parsed_message: Mapped[int] = mapped_column(Integer, nullable=True)

    __table_args__ = (UniqueConstraint('channel_id', 'channel_for_parsing_id', 'user_id'),)
