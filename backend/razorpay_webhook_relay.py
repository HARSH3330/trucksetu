"""Expose ONLY the signed Razorpay connection webhook, never the full API."""
import asyncio
import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from app.services.payments import verify_razorpay_signature

PATH='/api/v1/connection-fees/webhook'
MAX_BODY=262144


def create_relay(transport=None):
    async def receive(request:Request):
        body=bytearray()
        try:
            async with asyncio.timeout(10):
                async for chunk in request.stream():
                    body.extend(chunk)
                    if len(body)>MAX_BODY:return JSONResponse({'detail':'Payload too large'},status_code=413)
        except TimeoutError:
            return JSONResponse({'detail':'Request timed out'},status_code=408)
        signature=request.headers.get('X-Razorpay-Signature','')
        if not verify_razorpay_signature(bytes(body),signature):
            return JSONResponse({'detail':'Invalid webhook signature'},status_code=401)
        event=request.headers.get('X-Razorpay-Event-Id','')
        if not 8<=len(event)<=200:return JSONResponse({'detail':'Invalid event reference'},status_code=400)
        try:
            async with httpx.AsyncClient(transport=transport,timeout=20,follow_redirects=False) as client:
                result=await client.post('http://127.0.0.1:18110'+PATH,content=bytes(body),
                    headers={'Content-Type':'application/json','X-Razorpay-Signature':signature,'X-Razorpay-Event-Id':event})
            if result.status_code==200:return JSONResponse({'received':True})
        except httpx.HTTPError:
            pass
        return JSONResponse({'detail':'Webhook processing unavailable; retry delivery'},status_code=503)
    return Starlette(debug=False,routes=[Route(PATH,receive,methods=['POST'])])


app=create_relay()
