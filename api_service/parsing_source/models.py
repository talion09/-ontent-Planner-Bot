from sqlalchemy import Integer, ForeignKey, ARRAY, BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from api_service.database.database import Base


class ParsingSource(Base):
    __tablename__ = "parsing_source"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String, nullable=True)
    posts_quantity: Mapped[int] = mapped_column(Integer, nullable=True)
