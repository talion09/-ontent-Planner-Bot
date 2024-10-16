from datetime import datetime
from typing import Dict

from sqlalchemy import Integer, ForeignKey, DateTime, BigInteger, JSON, String, ARRAY, Boolean
from sqlalchemy.orm import mapped_column, Mapped

from api_service.database.database import Base
from api_service.post.schemas import MediaItem


class Paywave(Base):
    __tablename__ = "paywave"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"))
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow())
