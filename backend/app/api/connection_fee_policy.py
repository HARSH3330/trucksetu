"""Audited local fee policy actions; no charge or refund adapter is called here."""
import uuid
from datetime import UTC,datetime
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from app.api.auth import require_roles
from app.core.database import get_db,acquire_idempotency_lock
from app.core.routing import AuthenticationFirstRoute
from app.models import ConnectionFeeCredit
from app.services.demand_marketplace import selection_for,selection_view,audit
from app.services.connection_fee_rules import cancel_connection
from app.services.demand_schemas import ReasonInput,CancelInput

router=APIRouter(prefix='/api/v1',tags=['connection fee policy'],route_class=AuthenticationFirstRoute)
customer=require_roles('customer')


class ApplyCredit(BaseModel):
    credit_id:uuid.UUID


def credit_view(item):
    return dict(id=str(item.id),status=item.status,label='Platform connection fee waived',source_selection_id=str(item.source_selection_id),reserved_selection_id=str(item.reserved_selection_id) if item.reserved_selection_id else None,redeemed_selection_id=str(item.redeemed_selection_id) if item.redeemed_selection_id else None,tax_treatment='pending_confirmation',expiry='unresolved',transferability='unresolved',invalid_contact_rules='unresolved')


@router.get('/connection-credits/mine')
async def credits(db=Depends(get_db),user=Depends(customer)):
    items=await db.scalars(select(ConnectionFeeCredit).where(ConnectionFeeCredit.customer_id==user.id).order_by(ConnectionFeeCredit.created_at))
    return [credit_view(i) for i in items]


@router.post('/demand-selections/{identity}/cancel')
async def cancel(identity:uuid.UUID,payload:CancelInput,db=Depends(get_db),user=Depends(customer)):
    item,demand=await selection_for(db,identity)
    if item.customer_id!=user.id:raise HTTPException(404,'Selection not found')
    if item.contact_revealed_at and not payload.confirm_after_reveal:
        raise HTTPException(409,'Contact was revealed. Ordinary cancellation has no refund; confirm this explicitly')
    result=await cancel_connection(db,item,demand,user.id,payload.reason)
    await db.commit()
    return result


@router.post('/admin/demand-selections/{identity}/provider-failure-credit',status_code=201)
async def confirm_failure(identity:uuid.UUID,payload:ReasonInput,db=Depends(get_db),user=Depends(require_roles('admin','superadmin'))):
    item,demand=await selection_for(db,identity)
    prior=await db.scalar(select(ConnectionFeeCredit).where(ConnectionFeeCredit.source_selection_id==item.id))
    if prior:return credit_view(prior)
    if item.status!='paid' or item.payment_status!='captured' or not item.contact_revealed_at:
        raise HTTPException(409,'Confirm provider failure only after a captured and revealed connection')
    if user.id==item.customer_id:raise HTTPException(403,'Independent administrator confirmation is required')
    credit=ConnectionFeeCredit(customer_id=item.customer_id,source_selection_id=item.id,issued_by=user.id,reason=payload.reason)
    db.add(credit);await db.flush()
    item.status='provider_failed'
    audit(db,user.id,'connection.provider_failure_confirmed','demand_selection',item.id,{'credit_id':str(credit.id),'reason':payload.reason,'refund':False,'scope':'platform_connection_fee_only'})
    await db.commit()
    return credit_view(credit)


@router.post('/demand-selections/{identity}/apply-credit')
async def apply_credit(identity:uuid.UUID,payload:ApplyCredit,db=Depends(get_db),user=Depends(customer)):
    item,demand=await selection_for(db,identity)
    if item.customer_id!=user.id:raise HTTPException(404,'Selection not found')
    if item.status!='pending' or item.order_state!='not_created' or item.gateway_order_id or item.credit_id not in {None,payload.credit_id}:
        raise HTTPException(409,'Apply a credit before creating any payment order')
    await acquire_idempotency_lock(db,'connection-credit:'+str(user.id))
    credit=await db.scalar(select(ConnectionFeeCredit).where(ConnectionFeeCredit.id==payload.credit_id).with_for_update())
    if not credit or credit.customer_id!=user.id:raise HTTPException(404,'Credit not found')
    if credit.source_selection_id==item.id or credit.status not in {'available','reserved'} or (credit.status=='reserved' and credit.reserved_selection_id!=item.id):
        raise HTTPException(409,'Credit is already reserved or redeemed')
    credit.status='reserved';credit.reserved_selection_id=item.id;item.credit_id=credit.id
    item.fee_snapshot={**item.fee_snapshot,'connection_fee_waived':True,'waiver_label':'Platform connection fee waived','waiver_tax_treatment':'pending_confirmation'}
    audit(db,user.id,'connection.credit_reserved','demand_selection',item.id,{'credit_id':str(credit.id)})
    await db.commit()
    return selection_view(item)


async def redeem_captured_credit(db,item):
    if not item.credit_id:return True
    credit=await db.scalar(select(ConnectionFeeCredit).where(ConnectionFeeCredit.id==item.credit_id).with_for_update())
    if not credit or credit.status!='reserved' or credit.reserved_selection_id!=item.id:return False
    credit.status='redeemed';credit.redeemed_selection_id=item.id;credit.redeemed_at=datetime.now(UTC)
    audit(db,item.customer_id,'connection.credit_redeemed','demand_selection',item.id,{'credit_id':str(credit.id)})
    return True
