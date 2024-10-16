from sqlalchemy import String, BigInteger
from sqlalchemy.orm import mapped_column, Mapped

from api_service.database.database import Base


class Channel(Base):
    __tablename__ = "channel"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    link: Mapped[str] = mapped_column(String, unique=True)
    title: Mapped[str] = mapped_column(String, nullable=True)
