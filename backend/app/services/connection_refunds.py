"""Durable full-refund executor. External execution is explicit and Test Mode only."""
from datetime import UTC, datetime
from sqlalchemy import select
from app.models import ConnectionFeeRefundRequest
from app.services.demand_marketplace import selection_for, audit
from app.services.payments import SandboxRazorpayGateway, RefundGatewayError


def refund_view(refund):
    return {'refund_request_id':str(refund.id),'status':refund.status,'amount':str(refund.amount),
            'currency':refund.currency,'payment_id':refund.gateway_payment_id,
            'refund_id':refund.gateway_refund_id,'error_code':refund.last_error_code}


def matches_reference(refund, entity):
    notes=entity.get('notes')
    return (entity.get('id')==refund.gateway_refund_id if refund.gateway_refund_id else
            entity.get('receipt')==str(refund.id) or
            isinstance(notes,dict) and notes.get('connection_refund_request')==str(refund.id))


def refund_error(refund, item, entity):
    if not isinstance(entity,dict):return 'invalid_refund_entity'
    if not isinstance(entity.get('id'),str) or not entity['id'].startswith('rfnd_') or len(entity['id'])>100:return 'invalid_refund_id'
    if entity.get('payment_id')!=item.gateway_payment_id or entity.get('payment_id')!=refund.gateway_payment_id:return 'refund_payment_mismatch'
    if type(entity.get('amount')) is not int or entity['amount']!=int(refund.amount*100):return 'refund_amount_mismatch'
    if entity.get('currency')!=refund.currency:return 'refund_currency_mismatch'
    if entity.get('status') not in {'pending','processed','failed'}:return 'invalid_refund_status'
    if not matches_reference(refund,entity):return 'refund_obligation_mismatch'
    return None


def apply_refund_entity(db,item,refund,entity):
    error=refund_error(refund,item,entity)
    if error:
        refund.last_error_code=error
        if refund.status!='processed':refund.status='review_required'
        item.status='review_required'
        audit(db,None,'connection.refund_rejected','demand_selection',item.id,{'refund_request_id':str(refund.id),'reason':error})
        return error
    if refund.status=='processed':return 'duplicate_or_stale_refund'
    refund.gateway_refund_id=entity['id']
    refund.status=entity['status']
    refund.last_error_code=None
    refund.reconciled_at=datetime.now(UTC)
    item.status='cancelled' if refund.status=='processed' else 'refund_requested'
    if refund.status=='processed':item.payment_status='refunded'
    audit(db,None,'connection.refund_reconciled','demand_selection',item.id,
          {'refund_request_id':str(refund.id),'refund_id':refund.gateway_refund_id,'status':refund.status})
    return 'refund_'+refund.status


async def locked_refund(db,identity):
    located=await db.get(ConnectionFeeRefundRequest,identity)
    if not located:raise ValueError('Refund obligation not found')
    item,_=await selection_for(db,located.selection_id)
    refund=await db.scalar(select(ConnectionFeeRefundRequest).where(ConnectionFeeRefundRequest.id==identity).with_for_update().execution_options(populate_existing=True))
    return item,refund


async def execute_refund(factory,identity,gateway=None):
    # Injected gateways are test doubles. The real adapter independently enforces
    # Test Mode + exact local database for EVERY HTTP operation.
    gateway=gateway or SandboxRazorpayGateway()
    if isinstance(gateway,SandboxRazorpayGateway):
        from app.services.payments import require_razorpay_sandbox
        require_razorpay_sandbox()
    async with factory() as db:
        item,refund=await locked_refund(db,identity)
        if refund.status=='processed' and refund.gateway_refund_id:return refund_view(refund)
        if (not item.cancelled_at or item.contact_revealed_at or not item.gateway_payment_id or
            item.payment_status not in {'captured','refunded'} or refund.amount!=item.fee_amount or
            refund.currency!=item.currency or refund.amount<=0):
            raise ValueError('Refund obligation is not eligible for execution')
        payload={'amount':int(refund.amount*100),'speed':'normal','receipt':str(refund.id),
                 'notes':{'connection_refund_request':str(refund.id)}}
        if refund.request_payload and (refund.request_payload!=payload or refund.gateway_payment_id!=item.gateway_payment_id):
            raise ValueError('Immutable refund execution snapshot differs')
        refund.gateway_payment_id=item.gateway_payment_id
        refund.idempotency_key=refund.idempotency_key or 'connection-refund-'+refund.id.hex
        refund.request_payload=payload
        refund.attempt_count+=1;refund.last_attempt_at=datetime.now(UTC)
        payment_id,order_id=item.gateway_payment_id,item.gateway_order_id
        expected_amount,expected_currency=int(item.fee_amount*100),item.currency
        key,known_id=refund.idempotency_key,refund.gateway_refund_id
        prior_status=refund.status
        if prior_status not in {'processed','pending','failed','review_required'}:refund.status='submitting'
        audit(db,None,'connection.refund_execution_attempt','demand_selection',item.id,{'refund_request_id':str(identity),'attempt':refund.attempt_count})
        await db.commit()  # Durable key/body BEFORE any network call.
    try:
        payment=await gateway.fetch_payment(payment_id)
        if (payment.get('id')!=payment_id or payment.get('order_id')!=order_id or
            type(payment.get('amount')) is not int or payment['amount']!=expected_amount or
            payment.get('currency')!=expected_currency or payment.get('status') not in {'captured','refunded'}):
            raise ValueError('payment_snapshot_mismatch')
        if known_id:
            entity=await gateway.fetch_refund(payment_id,known_id)
        else:
            listing=await gateway.list_refunds(payment_id)
            entries=listing.get('items')
            if not isinstance(entries,list) or len(entries)>=100 or any(not isinstance(r,dict) for r in entries):
                raise ValueError('refund_listing_requires_review')
            matches=[r for r in entries if r.get('receipt')==str(identity) or isinstance(r.get('notes'),dict) and r['notes'].get('connection_refund_request')==str(identity)]
            if len(matches)>1 or any(r not in matches for r in entries):
                raise ValueError('unrelated_refunds_require_review')
            if matches:entity=await gateway.fetch_refund(payment_id,matches[0]['id'])
            elif prior_status in {'failed','pending','processed','review_required'}:
                raise ValueError('provider_refund_missing_requires_review')
            elif payment.get('status')!='captured' or payment.get('amount_refunded',0)!=0:
                raise ValueError('payment_already_refunded_requires_review')
            else:
                created=await gateway.create_refund(payment_id,payload,key)
                # Persist the returned ID even if the following GET times out.
                async with factory() as db:
                    item,refund=await locked_refund(db,identity)
                    error=refund_error(refund,item,created)
                    if error:raise ValueError(error)
                    refund.gateway_refund_id=created['id']
                    if refund.status!='processed':refund.status='pending'
                    await db.commit()
                entity=await gateway.fetch_refund(payment_id,created['id'])
        async with factory() as db:
            item,refund=await locked_refund(db,identity)
            apply_refund_entity(db,item,refund,entity)
            await db.commit()
            return refund_view(refund)
    except (RefundGatewayError,ValueError,KeyError,TypeError) as error:
        async with factory() as db:
            item,refund=await locked_refund(db,identity)
            if refund.status!='processed':
                ambiguous=isinstance(error,RefundGatewayError)
                if not ambiguous:
                    refund.status='review_required'
                elif refund.status not in {'failed','review_required'}:
                    refund.status='unknown' if not refund.gateway_refund_id else 'pending'
                refund.last_error_code='gateway_response_unknown' if ambiguous else 'provider_evidence_mismatch'
            await db.commit()
            return refund_view(refund)
