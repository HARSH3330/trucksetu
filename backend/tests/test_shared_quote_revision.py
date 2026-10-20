import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api import quotes


@pytest.mark.asyncio
async def test_provider_quote_listing_scopes_the_database_query_to_current_user():
    user=SimpleNamespace(id=uuid.uuid4())
    async def scalars(query):
        assert user.id in query.compile().params.values()
        assert 'provider_profiles.user_id =' in str(query)
        assert query._limit_clause.value==100
        return []
    db=SimpleNamespace(scalars=scalars)
    assert await quotes.own_quotes(db,user)==[]


@pytest.mark.asyncio
async def test_accepted_shared_quote_revision_cannot_mutate_accepted_fields(monkeypatch):
    from app.schemas import QuoteUpdate
    from datetime import UTC,datetime,timedelta
    from fastapi import HTTPException
    user=SimpleNamespace(id=uuid.uuid4(),roles=[])
    quote=SimpleNamespace(id=uuid.uuid4(),provider=SimpleNamespace(user_id=user.id),service_mode='SHARED_CAPACITY',status='accepted',version=2,estimated_pickup=datetime.now(UTC)+timedelta(days=1),expires_at=datetime.now(UTC),price_breakdown=[{'label':'Original','amount':'750'}],inclusions='Original',exclusions='None')
    db=SimpleNamespace(scalar=AsyncMock(return_value=quote),flush=AsyncMock())
    payload=QuoteUpdate(final_price='800',vehicles_offered=1,expires_at=datetime.now(UTC)+timedelta(hours=1),price_breakdown=[{'label':'Revised','amount':'800'}],inclusions='Changed',exclusions='None')
    before=(quote.expires_at,quote.price_breakdown,quote.inclusions)
    with pytest.raises(HTTPException) as error:
        await quotes.edit_quote(quote.id,payload,db,user)
    assert error.value.status_code==409
    assert (quote.expires_at,quote.price_breakdown,quote.inclusions)==before
