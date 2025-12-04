from flask_mailman import EmailMessage

from app.extensions import mail


def send_email(subject, recipients, body):
    with mail.get_connection() as connection:
        msg = EmailMessage(subject=subject, body=body, to=recipients, connection=connection)
        msg.send()
