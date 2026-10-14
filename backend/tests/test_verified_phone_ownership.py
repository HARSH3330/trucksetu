import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock,Mock

import pytest

from app.api.auth import SignupInput
from app.api.account_recovery import MobileInput,update_mobile
from app.api.phone_verification import WidgetProof,verify_widget
from app.core.security import get_password_hash
from app.models import User


def test_signup_and_contact_normalize_equivalent_mobile_spellings():
    for spelling in ['9999999999','919999999999','+919999999999']:
        assert SignupInput(full_name='Fictional account',email='fictional@example.com',mobile=spelling,password='FictionalOnly123!').mobile=='+919999999999'
        assert MobileInput(mobile=spelling,password='FictionalOnly123!').mobile=='+919999999999'


@pytest.mark.asyncio
@pytest.mark.parametrize('other_verified,expected_status',[(False,200),(True,409)])
async def test_only_verified_claims_block_the_phone_owner(monkeypatch,other_verified,expected_status):
    from app.api import phone_verification
    from fastapi import HTTPException
    monkeypatch.setattr(phone_verification,'enforce_rate_limit',AsyncMock())
    monkeypatch.setattr(phone_verification,'acquire_idempotency_lock',AsyncMock())
    user=User(id=uuid.uuid4(),mobile='+919999999999',mobile_verified=False,status='active')
    other=User(id=uuid.uuid4(),mobile='+919999999999',mobile_verified=other_verified)
    async def scalar(query):
        description=query.column_descriptions[0]
        if description['entity'] is User:
            if description['name']!='id':return user
            # Characterize the actual emitted database predicate. An unverified
            # claim must not match a verified-only ownership query.
            verified_only='users.mobile_verified IS true' in str(query)
            return other.id if other.mobile_verified or not verified_only else None
        return None
    db=SimpleNamespace(scalar=scalar,add=Mock(),commit=AsyncMock())
    verifier=SimpleNamespace(verify=AsyncMock(return_value='+919999999999'))
    try:
        result=await verify_widget(WidgetProof(verification_token='fictional-phone-proof-never-for-real-use'),SimpleNamespace(state=SimpleNamespace()),user,db,verifier)
    except HTTPException as failure:
        assert expected_status==failure.status_code
        assert user.mobile_verified is False
        db.commit.assert_not_awaited()
        assert str(other.id) not in str(failure.detail)
    else:
        assert expected_status==200 and result=={'mobile_verified':True}
        assert user.mobile_verified is True and other.mobile_verified is False


@pytest.mark.asyncio
@pytest.mark.parametrize('new_mobile,expected_verified',[('9999999999',True),('8888888888',False)])
async def test_contact_change_releases_claim_but_same_phone_preserves_it(monkeypatch,new_mobile,expected_verified):
    from app.api import account_recovery
    monkeypatch.setattr(account_recovery,'enforce_rate_limit',AsyncMock())
    user=User(id=uuid.uuid4(),status='active',mobile='+919999999999',mobile_verified=True,password_hash=get_password_hash('FictionalOnly123!'))
    db=SimpleNamespace(scalar=AsyncMock(return_value=user),add=Mock(),commit=AsyncMock())
    result=await update_mobile(MobileInput(mobile=new_mobile,password='FictionalOnly123!'),SimpleNamespace(),user,db)
    assert result['mobile_verified']==expected_verified and user.mobile_verified==expected_verified
    assert user.mobile==('+919999999999' if expected_verified else '+918888888888')
