"""Account email text; tokens stay in the URL fragment, never the HTTP query."""
from urllib.parse import urlencode

from app.core.config import settings


def account_email_message(email: str, channel: str, code: str) -> str:
    purpose = 'email verification code' if channel == 'email' else 'password reset token'
    message = f'TransivoX {purpose}: {code}\nExpires in {settings.OTP_EXPIRE_MINUTES} minutes. Do not share this with anyone.'
    if settings.PUBLIC_FRONTEND_URL:
        route = 'account-verify' if channel == 'email' else 'account-reset'
        parameter = 'code' if channel == 'email' else 'token'
        query = urlencode({'email': email, parameter: code})
        message += f'\n{settings.PUBLIC_FRONTEND_URL}/#{route}?{query}'
    return message + '\nIf you did not request this, ignore this email.'
