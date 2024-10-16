from sqlalchemy import Integer, ForeignKey, ARRAY, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from api_service.database.database import Base


class ParsedMessages(Base):
    __tablename__ = "parsed_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('post.id'))
    messages_id: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=True)
