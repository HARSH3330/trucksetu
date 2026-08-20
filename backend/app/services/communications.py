from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio
import smtplib
from email.message import EmailMessage

import httpx

from app.core.config import settings


class ChannelProvider(ABC):
    @abstractmethod
    async def send(self, recipient: str, message: str) -> str: ...


class Msg91SmsProvider(ChannelProvider):
    async def send(self, recipient: str, message: str) -> str:
        if not settings.MSG91_AUTH_KEY or not settings.MSG91_TEMPLATE_ID:
            raise RuntimeError("SMS provider is not configured")
        async with httpx.AsyncClient(timeout=15) as client:
            response=await client.post("https://control.msg91.com/api/v5/flow/",headers={"authkey":settings.MSG91_AUTH_KEY},json={"template_id":settings.MSG91_TEMPLATE_ID,"recipients":[{"mobiles":recipient,"message":message}]})
            response.raise_for_status();return str(response.json().get("request_id","sent"))


class WatiWhatsAppProvider(ChannelProvider):
    async def send(self, recipient: str, message: str) -> str:
        if not settings.WATI_API_KEY or not settings.WATI_BASE_URL:
            raise RuntimeError("WhatsApp provider is not configured")
        async with httpx.AsyncClient(timeout=15) as client:
            response=await client.post(f"{settings.WATI_BASE_URL.rstrip('/')}/api/v1/sendSessionMessage/{recipient}",headers={"Authorization":f"Bearer {settings.WATI_API_KEY}"},json={"messageText":message})
            response.raise_for_status();return str(response.json().get("id","sent"))


class SmtpEmailProvider(ChannelProvider):
    async def send(self, recipient: str, message: str) -> str:
        if not settings.SMTP_HOST or not settings.EMAIL_FROM:
            raise RuntimeError("Email provider is not configured")
        email=EmailMessage();email["From"]=settings.EMAIL_FROM;email["To"]=recipient;email["Subject"]="TruckSetu booking update";email.set_content(message)
        def deliver() -> None:
            with smtplib.SMTP(settings.SMTP_HOST,settings.SMTP_PORT,timeout=15) as client:
                client.starttls()
                if settings.SMTP_USERNAME:client.login(settings.SMTP_USERNAME,settings.SMTP_PASSWORD)
                client.send_message(email)
        await asyncio.to_thread(deliver)
        return "sent"


def provider_for(channel: str) -> ChannelProvider:
    if channel=="sms":return Msg91SmsProvider()
    if channel=="whatsapp":return WatiWhatsAppProvider()
    if channel=="email":return SmtpEmailProvider()
    raise ValueError(f"Unsupported external channel: {channel}")
