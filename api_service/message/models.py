from sqlalchemy import Integer, ForeignKey, BigInteger, JSON, String
from sqlalchemy.orm import mapped_column, Mapped

from api_service.database.database import Base


class Message(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message: Mapped[dict] = mapped_column(JSON, nullable=True)
    job_id: Mapped[str] = mapped_column(String, nullable=True)
    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('post.id'))
    auto_delete_timer_job_id: Mapped[str] = mapped_column(String, nullable=True)
