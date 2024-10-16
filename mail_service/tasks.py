import smtplib
from email.message import EmailMessage

from mail_service.config import SMTP_USER, SMTP_PASSWORD, SMTP_HOST, SMTP_PORT


def get_email_template_dashboard(username: str, to: str):
    email = EmailMessage()
    email['Subject'] = 'Верификация'
    email['From'] = SMTP_USER
    email['To'] = to

    email.set_content(
        '<div>'
        f'<h1">Здравствуйте, {username}, вы успешно привязали почту к боту</h1>'
        '</div>',
        subtype='html'
    )
    return email


def send_email_report_dashboard(username: str, to: str):
    email = get_email_template_dashboard(username, to)
    with smtplib.SMTP_SSL(SMTP_HOST, int(SMTP_PORT)) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(email)
