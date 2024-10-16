from sqlalchemy import BigInteger, ForeignKey, String, JSON, UniqueConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from api_service.database.database import Base


class TelethonUserParserChannelAssociation(Base):
    __tablename__ = "telethon_user_channel_association"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("telethon_user.user_id"))
    parser_channel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("telethon_parser_channel.id"))

    __table_args__ = (UniqueConstraint('user_id', 'parser_channel_id', name='_user_id_parser_channel_id_uc'),)


class TelethonUser(Base):
    __tablename__ = "telethon_user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    number: Mapped[str] = mapped_column(String)
    proxy: Mapped[dict] = mapped_column(JSON, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=True)


class TelethonParserChannel(Base):
    __tablename__ = "telethon_parser_channel"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    link: Mapped[str] = mapped_column(String)
