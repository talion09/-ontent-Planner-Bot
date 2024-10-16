from typing import Optional

from pydantic import BaseModel


class MessageSchema(BaseModel):
    id: Optional[int] = None
    message: Optional[dict] = None
    job_id: Optional[str] = None
    post_id: Optional[int] = None
    auto_delete_timer_job_id: Optional[str] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
