import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

from mail_service.tasks import send_email_report_dashboard

app = FastAPI(
    title="MailService"
)


class MailSchema(BaseModel):
    username: Optional[str] = None
    to: Optional[str] = None


@app.post("/send_mail/")
def get_dashboard_report(background_tasks: BackgroundTasks, payload: MailSchema):
    try:
        logging.info(f"send_mail {payload}")
        background_tasks.add_task(send_email_report_dashboard, payload.username, payload.to)
        send_email_report_dashboard(payload.username, payload.to)
        return {
            "status": "success",
            "data": "success",
            "details": None
        }
    except Exception as e:
        logging.info(f"send_mail error {e}")
        return {
            "status": "error",
            "data": None,
            "details": str(e)
        }
