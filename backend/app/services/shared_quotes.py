"""Provider-authored final quote validation. No route-rate or tax formula."""
from copy import deepcopy
from decimal import Decimal

from fastapi import HTTPException


def validate_shared_quote(quote, shipment, expected_version, now):
    if quote.request_id != shipment.id or quote.available_route_id != shipment.available_route_id or not quote.available_route_id or quote.service_mode != 'SHARED_CAPACITY':
        raise HTTPException(409, 'Quotation does not identify this shared route and shipment')
    if quote.status != 'active' or quote.version != expected_version:
        raise HTTPException(409, 'Quotation changed or is no longer active; review the current revision')
    if not quote.expires_at or quote.expires_at <= now:
        raise HTTPException(409, 'Quotation expired; request a new quotation')
    charges = quote.price_breakdown or []
    if quote.currency != 'INR' or quote.vehicles_offered != 1 or not charges or sum(Decimal(item['amount']) for item in charges) != quote.final_price:
        raise HTTPException(422, 'Quotation financial breakdown is incomplete or inconsistent')
    return {'version':quote.version,'final_price':str(quote.final_price),'currency':quote.currency,'price_breakdown':deepcopy(charges), 'weight_tonnes':str(shipment.cargo.weight_tonnes),'volume_m3':str(shipment.cargo.volume_m3),'expires_at':quote.expires_at.isoformat(),'inclusions':getattr(quote,'inclusions',None),'exclusions':getattr(quote,'exclusions',None)}
