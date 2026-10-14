"""Server validation of the widget's proof. Never trust browser success/JWT claims."""
import re
import httpx

from app.core.config import settings


class InvalidWidgetVerification(ValueError):
    pass


class WidgetVerificationUnavailable(RuntimeError):
    pass


def canonical_mobile(value:str)->str:
    if not isinstance(value,str) or not re.fullmatch(r'\+?[1-9][0-9]{7,14}',value):
        raise InvalidWidgetVerification('Invalid mobile identifier')
    digits=value.lstrip('+')
    if len(digits)==10 and not value.startswith('+'):
        digits='91'+digits
    return '+'+digits


class Msg91WidgetVerifier:
    def __init__(self,*,transport:httpx.AsyncBaseTransport|None=None)->None:
        self.transport=transport

    async def verify(self,token:str)->str:
        if not settings.MSG91_AUTH_KEY:
            raise WidgetVerificationUnavailable('Phone verification is not configured')
        try:
            async with httpx.AsyncClient(timeout=10,transport=self.transport,follow_redirects=False) as client:
                response=await client.post('https://api.msg91.com/api/v5/widget/verifyAccessToken',headers={'authkey':settings.MSG91_AUTH_KEY},json={'access-token':token})
            if response.status_code>=500 or response.status_code in {301,302,307,308,429}:
                raise WidgetVerificationUnavailable('Phone verification is unavailable')
            if response.status_code!=200:
                raise InvalidWidgetVerification('Invalid or expired phone verification')
            payload=response.json()
        except (httpx.HTTPError,ValueError) as exc:
            if isinstance(exc,InvalidWidgetVerification):raise
            raise WidgetVerificationUnavailable('Phone verification is unavailable') from exc
        if not isinstance(payload,dict) or payload.get('type')!='success':
            raise InvalidWidgetVerification('Invalid or expired phone verification')
        # MSG91's documented success message is the verified identifier, NOT
        # a human success phrase. Reject emails, missing or malformed identifiers.
        return canonical_mobile(payload.get('message'))
