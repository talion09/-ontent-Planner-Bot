from datetime import datetime

from sqlalchemy import Integer, ForeignKey, DateTime, BigInteger, JSON, String, ARRAY, Boolean, Text
from sqlalchemy.orm import mapped_column, Mapped

from api_service.database.database import Base
from api_service.post.schemas import MediaItem


class Post(Base):
    __tablename__ = "post"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"))
    channel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("channel.id"), nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    url_buttons: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    media: Mapped[list[MediaItem]] = mapped_column(ARRAY(JSON), nullable=True)
    messages_id: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    auto_delete_timer: Mapped[int] = mapped_column(Integer, nullable=True)
    is_saved: Mapped[bool] = mapped_column(Boolean, nullable=True)
    is_scheduled: Mapped[bool] = mapped_column(Boolean, nullable=True)
    initial_post_id: Mapped[bool] = mapped_column(Integer, nullable=True)
    entities: Mapped[str] = mapped_column(Text, nullable=True)


sql = """
CREATE TABLE IF NOT EXISTS Harvester_posts (
id INT SERIAL PRIMARY KEY,
user_id INT REFERENCES Harvester_users(id), 
description VARCHAR(255) NULL,
url_buttons TEXT NULL, 
media TEXT NULL
);
"""
