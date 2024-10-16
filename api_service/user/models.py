from datetime import datetime

from sqlalchemy import Integer, DateTime, BigInteger, String, Boolean
from sqlalchemy.orm import mapped_column, Mapped

from api_service.database.database import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    time_zone: Mapped[int] = mapped_column(Integer, nullable=True)
    gpt_api_key: Mapped[str] = mapped_column(String, nullable=True)
    mail: Mapped[str] = mapped_column(String, nullable=True)
    post_auto_send: Mapped[bool] = mapped_column(Boolean, default=True)
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow())
    parsing_stopped: Mapped[bool] = mapped_column(Boolean, nullable=True)
    lang: Mapped[str] = mapped_column(String, nullable=True)
