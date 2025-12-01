from app.modules.community.models import Community
from core.repositories.BaseRepository import BaseRepository
from flask_mail import Message
from flask import current_app
from app.extensions import mail


class CommunityRepository(BaseRepository):
    def __init__(self):
        super().__init__(Community)

    def send_email(subject, recipients, body):
        msg = Message(
            subject=subject,
            recipients=recipients,
            body=body,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        mail.send(msg)
