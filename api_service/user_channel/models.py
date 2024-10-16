from sqlalchemy import Integer, ForeignKey, BigInteger, UniqueConstraint
from sqlalchemy.orm import mapped_column, Mapped

from api_service.database.database import Base


class UserChannel(Base):
    __tablename__ = "user_channel"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("channel.id"))
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"))
    user_channel_settings_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_channel_settings.id"))

    __table_args__ = (UniqueConstraint('channel_id', 'user_id'),)


sql = """
CREATE TABLE IF NOT EXISTS Harvester_user_channel (
id SERIAL PRIMARY KEY,
user_id INT REFERENCES Harvester_users(user_id),
channel_id INT REFERENCES Harvester_channel(id),
disabled BOOLEAN NOT NULL
);
"""
