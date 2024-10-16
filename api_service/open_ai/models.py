from sqlalchemy import Integer
from sqlalchemy.orm import mapped_column, Mapped

from api_service.database.database import Base


class OpenAI(Base):
    __tablename__ = "open_ai"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requests_count_per_minute: Mapped[int] = mapped_column(Integer)