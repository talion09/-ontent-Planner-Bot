from datetime import datetime
from sqlalchemy import Integer, ForeignKey, BigInteger, DateTime, Boolean, String, JSON, ARRAY, Text
from sqlalchemy.orm import mapped_column, Mapped

from api_service.database.database import Base


class UserChannelSettings(Base):
    __tablename__ = "user_channel_settings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    auto_sign: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_sign_text: Mapped[str] = mapped_column(String, nullable=True)
    auto_sign_entities: Mapped[str] = mapped_column(Text, nullable=True)
    prompts: Mapped[list[dict]] = mapped_column(ARRAY(JSON), nullable=True)
    disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    subscription_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscription.id"), nullable=True)
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    finished: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    posts_per_day: Mapped[int] = mapped_column(Integer, nullable=True)
