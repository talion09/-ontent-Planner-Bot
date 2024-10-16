from datetime import datetime

from sqlalchemy import Integer, String, BigInteger, ForeignKey, DateTime, ARRAY
from sqlalchemy.orm import mapped_column, Mapped

from api_service.database.database import Base


class Payment(Base):
    __tablename__ = "payment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String, nullable=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"))
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow())
    duration: Mapped[int] = mapped_column(Integer)
    channels: Mapped[list[int]] = mapped_column(ARRAY(BigInteger))
