from sqlalchemy import Integer, ForeignKey, Boolean, String, JSON
from sqlalchemy.orm import mapped_column, Mapped

from api_service.database.database import Base


class Subscription(Base):
    __tablename__ = "subscription"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_for_parsing_quantity: Mapped[int] = mapped_column(Integer, nullable=True)
    has_advert: Mapped[bool] = mapped_column(Boolean)
    open_ai_id: Mapped[int] = mapped_column(Integer, ForeignKey("open_ai.id"), nullable=True)
    subscribers_quantity: Mapped[int] = mapped_column(Integer)
    posts_per_day_quantity: Mapped[int] = mapped_column(Integer)
    channel_name: Mapped[str] = mapped_column(String, nullable=True)
    price: Mapped[dict] = mapped_column(JSON, nullable=True)
