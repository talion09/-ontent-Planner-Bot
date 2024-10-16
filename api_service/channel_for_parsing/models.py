from sqlalchemy import BigInteger, String
from sqlalchemy.orm import mapped_column, Mapped

from api_service.database.database import Base


class ChannelForParsing(Base):
    __tablename__ = "channel_for_parsing"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    link: Mapped[str] = mapped_column(String, unique=True)
    title: Mapped[str] = mapped_column(String, nullable=True)
