from datetime import datetime

from sqlalchemy import Integer, BigInteger, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from api_service.database.database import Base


class UserOpenAI(Base):
    __tablename__ = "user_open_ai"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"))
    open_ai_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("open_ai.id"))
    requested_count: Mapped[int] = mapped_column(Integer, nullable=True)
    requested_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
