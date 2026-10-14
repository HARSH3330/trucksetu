from app.services.storage import PrivateDocumentStorage
from app.services.communications import ChannelProvider, Msg91TripOtpProvider, SmtpEmailProvider
from app.core.config import settings
from fastapi import HTTPException
from app.services.msg91_widget import Msg91WidgetVerifier
from collections.abc import Callable


def get_private_document_storage() -> PrivateDocumentStorage:
    try:return PrivateDocumentStorage()
    except RuntimeError as exc:raise HTTPException(503,'Private document storage is not configured') from exc


def get_document_storage_factory()->Callable[[],PrivateDocumentStorage]:
    # Safety rejections/suspensions must not depend on S3 availability.
    return get_private_document_storage


def get_trip_otp_delivery() -> ChannelProvider:
    return Msg91TripOtpProvider()


def get_phone_verifier() -> Msg91WidgetVerifier:
    if not settings.MSG91_WIDGET_ENABLED or not settings.MSG91_AUTH_KEY:
        raise HTTPException(503,'Phone verification is not configured')
    return Msg91WidgetVerifier()


def get_account_email_delivery() -> ChannelProvider:
    # Configuration failure is identical for known and unknown accounts.
    if not settings.SMTP_HOST or not settings.EMAIL_FROM:
        raise HTTPException(503, 'Account email delivery is not configured')
    sender=SmtpEmailProvider()
    sender.subject='TransivoX account security'
    return sender
