"""Wire compatibility without importing a legacy JWT library."""
import base64,hashlib,hmac,json,time,uuid
import pytest
from app.core.config import settings
from app.core.security import verify_token,JWTError


def historical_token(**overrides):
    payload={'sub':str(uuid.uuid4()),'sv':0,'exp':int(time.time())+300,'iat':int(time.time()),'jti':uuid.uuid4().hex,'type':'access','iss':settings.JWT_ISSUER,'aud':settings.JWT_AUDIENCE,**overrides}
    def encode(value):return base64.urlsafe_b64encode(json.dumps(value,separators=(',',':')).encode()).rstrip(b'=')
    body=encode({'alg':'HS256','typ':'JWT'})+b'.'+encode(payload)
    signature=base64.urlsafe_b64encode(hmac.new(settings.SECRET_KEY.encode(),body,hashlib.sha256).digest()).rstrip(b'=')
    return (body+b'.'+signature).decode(),payload


def test_existing_hs256_token_keeps_issuer_audience_type_and_session_claims():
    token,payload=historical_token()
    assert verify_token(token)==payload


@pytest.mark.parametrize('overrides',[{'iss':'foreign-issuer'},{'aud':'foreign-audience'},{'type':'refresh'},{'exp':0}])
def test_wrong_issuer_audience_type_and_expiry_still_fail(overrides):
    token,_=historical_token(**overrides)
    with pytest.raises(JWTError):verify_token(token)
