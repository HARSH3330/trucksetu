from __future__ import annotations

import json
import logging
import time
import uuid
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from app.core.config import settings

logger=logging.getLogger("trucksetu.http")
_requests:dict[str,deque[float]]=defaultdict(deque)


class OperationsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self,request:Request,call_next:RequestResponseEndpoint)->Response:
        request_id=request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id=request_id
        now=time.monotonic();client=request.client.host if request.client else "unknown";bucket=_requests[client]
        while bucket and bucket[0] < now-60:bucket.popleft()
        if len(bucket)>=settings.RATE_LIMIT_PER_MINUTE:
            response=JSONResponse(status_code=429,content={"detail":"Too many requests. Please try again shortly.","request_id":request_id})
        else:
            bucket.append(now);started=time.perf_counter()
            try:response=await call_next(request)
            except Exception:
                logger.exception(json.dumps({"event":"request_error","request_id":request_id,"path":request.url.path}))
                raise
            duration=round((time.perf_counter()-started)*1000,2)
            logger.info(json.dumps({"event":"http_request","request_id":request_id,"method":request.method,"path":request.url.path,"status":response.status_code,"duration_ms":duration}))
        response.headers["X-Request-ID"]=request_id
        response.headers["X-Content-Type-Options"]="nosniff"
        response.headers["X-Frame-Options"]="DENY"
        response.headers["Referrer-Policy"]="strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]="camera=(), microphone=(), geolocation=(self)"
        response.headers["Content-Security-Policy"]="default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data:; frame-ancestors 'none'"
        return response
