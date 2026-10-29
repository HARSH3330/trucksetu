import ssl
from unittest.mock import MagicMock

import pytest

from app.services import communications


@pytest.mark.asyncio
@pytest.mark.parametrize('refused',[False,True])
async def test_smtp_reports_acceptance_only_when_recipient_not_refused(monkeypatch,refused):
    settings=communications.settings
    monkeypatch.setattr(settings,'SMTP_HOST','fictional-smtp.invalid')
    monkeypatch.setattr(settings,'EMAIL_FROM','fictional-sender@example.com')
    monkeypatch.setattr(settings,'SMTP_USERNAME','')
    client=MagicMock()
    client.send_message.return_value={'fictional-recipient@example.com':(550,b'refused')} if refused else {}
    connection=MagicMock();connection.__enter__.return_value=client
    monkeypatch.setattr(communications.smtplib,'SMTP',lambda *args,**kwargs:connection)
    sender=communications.SmtpEmailProvider()
    if refused:
        with pytest.raises(RuntimeError,match='did not accept recipient'):
            await sender.send('fictional-recipient@example.com','Harmless simulated delivery')
    else:
        assert await sender.send('fictional-recipient@example.com','Harmless simulated delivery')=='accepted'
    # STARTTLS must precede transmitting even when no SMTP login is configured.
    assert [call[0] for call in client.mock_calls][:2]==['starttls','send_message']


@pytest.mark.asyncio
async def test_smtp_requires_verified_tls_before_sending(monkeypatch):
    monkeypatch.setattr(communications.settings, 'SMTP_HOST', 'fictional-smtp.invalid')
    monkeypatch.setattr(communications.settings, 'EMAIL_FROM', 'fictional-sender@example.com')
    monkeypatch.setattr(communications.settings, 'SMTP_USERNAME', '')
    client = MagicMock()
    client.send_message.return_value = {}
    connection = MagicMock()
    connection.__enter__.return_value = client
    monkeypatch.setattr(communications.smtplib, 'SMTP', lambda *args, **kwargs: connection)
    await communications.SmtpEmailProvider().send('fictional-recipient@example.com', 'Local mocked TLS check')
    context = client.starttls.call_args.kwargs.get('context')
    assert isinstance(context, ssl.SSLContext)
    assert context.check_hostname is True
    assert context.verify_mode == ssl.CERT_REQUIRED
