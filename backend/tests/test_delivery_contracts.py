from unittest.mock import Mock

import pytest

from app.services.communications import SmtpEmailProvider
from app.core.config import settings


@pytest.mark.asyncio
async def test_email_refusal_is_not_reported_as_acceptance(monkeypatch):
    smtp=Mock()
    smtp.__enter__=Mock(return_value=smtp);smtp.__exit__=Mock(return_value=False)
    smtp.send_message.return_value={'fictional@example.com':(550,b'refused')}
    monkeypatch.setattr('app.services.communications.smtplib.SMTP',lambda *args,**kwargs:smtp)
    monkeypatch.setattr(settings,'SMTP_HOST','local.invalid')
    monkeypatch.setattr(settings,'EMAIL_FROM','test@example.com')
    with pytest.raises(RuntimeError):
        await SmtpEmailProvider().send('fictional@example.com','harmless test')
