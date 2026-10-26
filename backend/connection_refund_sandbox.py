"""Explicit CLI only. Never imports reset/bootstrap helpers or accepts live keys."""
import argparse
import asyncio
import json
import selectors
import sys
import uuid
from sqlalchemy import text
from app.core.database import get_session_factory,dispose_engine
from app.services.connection_refunds import execute_refund
from app.services.payments import require_razorpay_sandbox


async def run(identity):
    require_razorpay_sandbox()  # Before DB/network; exact loopback target only.
    factory=get_session_factory()
    try:
        async with factory() as db:
            row=(await db.execute(text("SELECT current_database(),current_user,rolsuper,rolcreaterole,rolcreatedb FROM pg_roles WHERE rolname=current_user"))).one()
            if tuple(row)!=('transivox_e2e','transivox_e2e_user',False,False,False):
                raise RuntimeError('Unexpected sandbox database or privileged database role')
            revision=await db.scalar(text('SELECT version_num FROM alembic_version'))
            # Migration29 adds nullable private pins and preserves refund execution metadata.
            if revision not in {'20261023_28','20261025_29'}:
                raise RuntimeError('Sandbox requires a reviewed compatible local schema revision')
        result=await execute_refund(factory,identity)
        print(json.dumps(result))  # Curated provider references/states only.
    finally:await dispose_engine()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Execute/reconcile ONE existing full refund obligation with Razorpay Test Mode only')
    parser.add_argument('refund_request_id',type=uuid.UUID)
    args=parser.parse_args()
    try:
        if sys.platform=='win32':asyncio.run(run(args.refund_request_id),loop_factory=lambda:asyncio.SelectorEventLoop(selectors.SelectSelector()))
        else:asyncio.run(run(args.refund_request_id))
    except Exception as exc:
        # Deliberately avoid raw upstream errors, connection URLs or tracebacks.
        print(json.dumps({'status':'blocked','error_type':type(exc).__name__,'detail':'Sandbox execution unavailable; inspect sanitized application evidence'}))
        raise SystemExit(1) from None
