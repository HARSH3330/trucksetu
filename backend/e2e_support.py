from __future__ import annotations

import os
import re
import uuid
import hashlib
import hmac
import time
from pathlib import Path, PurePath
from urllib.parse import quote, unquote

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.engine import make_url

from app.main import app as production_app
from app.services.dependencies import get_private_document_storage,get_document_storage_factory,get_trip_otp_delivery,get_account_email_delivery,get_phone_verifier
from app.services.msg91_widget import InvalidWidgetVerification
from app.services.storage import ALLOWED_CONTENT_TYPES
from app.core.config import settings
from e2e_database import safe_database_url


class LocalDocumentStorage:
    def __init__(self, root: Path, control_token: str, api_origin: str = 'http://127.0.0.1:8000') -> None:
        self.root = root
        self.control_token = control_token
        self.api_origin = api_origin.rstrip('/')
        self.objects: dict[str, tuple[bytes, str]] = {}
        self.scan_statuses: dict[str, str] = {}
        self.current_versions:dict[str,str]={}
        self.versions:dict[tuple[str,str],tuple[bytes,str]]={}
        self.version_scans:dict[tuple[str,str],str]={}

    def upload_url(self, provider_id: object, document_type: str, filename: str, content_type: str) -> tuple[str, str]:
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError('Only PDF, JPEG and PNG documents are accepted')
        suffix = PurePath(filename).suffix.lower()
        if suffix not in {'.pdf', '.jpg', '.jpeg', '.png'}:
            raise ValueError('Unsupported document filename')
        safe = re.sub(r'[^a-zA-Z0-9._-]', '_', PurePath(filename).name)
        key = f'kyc/{provider_id}/{document_type}/{uuid.uuid4()}-{safe}'
        return key, f'{self.api_origin}/__e2e__/uploads/{quote(key, safe="")}'

    def put(self, key: str, content: bytes, content_type: str) -> None:
        self.objects[key] = (content, content_type)
        self.scan_statuses[key] = 'PENDING'
        version=uuid.uuid4().hex
        self.current_versions[key]=version
        self.versions[key,version]=(content,content_type)
        self.version_scans[key,version]='PENDING'

    def confirm(self, key: str) -> dict[str, object]:
        if key not in self.objects:
            raise ValueError('Uploaded document was not found')
        content, content_type = self.objects[key]
        return {'ContentLength': len(content), 'ContentType': content_type,'VersionId':self.current_versions[key]}

    def detected_content_type(self, key: str,version_id:str|None=None) -> str | None:
        content = (self.versions[key,version_id] if version_id else self.objects[key])[0]
        if content.startswith(b'%PDF-'):
            return 'application/pdf'
        if content.startswith(b'\xff\xd8\xff'):
            return 'image/jpeg'
        if content.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'image/png'
        return None

    def require_clean_scan(self, key: str,version_id:str|None=None) -> None:
        status=self.version_scans.get((key,version_id)) if version_id else self.scan_statuses.get(key)
        if status != 'NO_THREATS_FOUND':
            raise ValueError('Document scan is pending or was not clean')

    def set_scan_status(self, key: str, status: str) -> None:
        if key not in self.objects:
            raise KeyError(key)
        self.scan_statuses[key] = status
        self.version_scans[key,self.current_versions[key]]=status

    def download_url(self, key: str,version_id:str|None=None) -> str:
        self.confirm(key)
        expires = int(time.time()) + 300
        signature = hmac.new(self.control_token.encode(), f'{key}:{expires}:{version_id or ""}'.encode(), hashlib.sha256).hexdigest()
        return f'{self.api_origin}/__e2e__/downloads/{quote(key, safe="")}?expires={expires}&signature={signature}'+(f'&version_id={version_id}' if version_id else '')

    def read_signed(self, key: str, expires: int, signature: str,version_id:str|None=None) -> tuple[bytes, str]:
        expected = hmac.new(self.control_token.encode(), f'{key}:{expires}:{version_id or ""}'.encode(), hashlib.sha256).hexdigest()
        if expires <= time.time() or not hmac.compare_digest(signature, expected):
            raise HTTPException(403, 'Invalid or expired test download signature')
        self.require_clean_scan(key,version_id)
        self.confirm(key)
        return self.versions[key,version_id] if version_id else self.objects[key]


class ScanControl(BaseModel):
    storage_key: str


def require_e2e_control(expected: str, provided: str | None) -> None:
    if provided != expected:
        raise HTTPException(403, 'E2E control authorization failed')


def create_e2e_app() -> FastAPI:
    if os.getenv('APP_ENV', '').lower() != 'test' or os.getenv('TRANSIVOX_E2E', '').lower() != 'true':
        raise RuntimeError('E2E support API is available only in explicit local test mode')
    # Enforce this here too, not only in e2e_server: a direct ASGI import must
    # never enable simulated clean scans against an application/production DB.
    raw=safe_database_url()
    if os.getenv('E2E_REAL_AWS','').lower()!='false' or make_url(settings.DATABASE_URL).set(drivername='postgresql')!=make_url(raw).set(drivername='postgresql'):
        raise RuntimeError('Fake support API must be bound to the isolated E2E database with E2E_REAL_AWS=false')
    token = os.getenv('E2E_CONTROL_TOKEN', '')
    if len(token) < 16:
        raise RuntimeError('E2E_CONTROL_TOKEN must contain at least 16 characters')

    storage = LocalDocumentStorage(
        Path(os.getenv('E2E_STORAGE_DIR', '.e2e-storage')),
        token,
        os.getenv('E2E_API_ORIGIN', 'http://127.0.0.1:8000'),
    )
    app = FastAPI(title='TransivoX E2E support',exception_handlers=production_app.exception_handlers)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.getenv('E2E_WEB_URL', 'http://127.0.0.1:5173')],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    app.dependency_overrides[get_private_document_storage] = lambda: storage
    # Publication rechecks call this service boundary outside FastAPI Depends.
    # This override exists ONLY after exact local E2E guards above succeed.
    from app.services import customer_kyc
    customer_kyc.get_private_document_storage=lambda:storage
    app.dependency_overrides[get_document_storage_factory]=lambda:lambda:storage
    class LocalPhoneVerifier:
        async def verify(self,proof):
            # Explicit per-test proofs only; never contacts MSG91 or accepts an
            # arbitrary callback. Not exposed as an HTTP production control.
            if proof not in app.state.phone_proofs:raise InvalidWidgetVerification('Unknown local proof')
            return app.state.phone_proofs[proof]
    # This app is created only after the explicit local database safety guards.
    # No gateway call or browser callback can capture a real payment here.
    from app.api.demands import get_connection_gateway
    import uuid
    class LocalConnectionGateway:
        is_simulated = True
        async def create_order(self, amount, currency, receipt):
            return {'id':'order_local_'+uuid.uuid4().hex,'amount':int(amount*100),'currency':currency,'local_simulation':True}
    app.dependency_overrides[get_connection_gateway] = lambda:LocalConnectionGateway()
    app.state.phone_proofs={}
    app.dependency_overrides[get_phone_verifier]=lambda:LocalPhoneVerifier()
    outbox=[]
    app.state.delivery_outbox=outbox
    class LocalSender:
        def __init__(self,channel):self.channel=channel
        async def send(self,recipient,message):
            outbox.append({'channel':self.channel,'recipient':recipient,'message':message})
            return 'accepted'
    app.dependency_overrides[get_trip_otp_delivery]=lambda:LocalSender('sms')
    app.dependency_overrides[get_account_email_delivery]=lambda:LocalSender('email')

    def require_control(x_e2e_control_token: str | None = Header(default=None)) -> None:
        require_e2e_control(token, x_e2e_control_token)

    @app.get('/__e2e__/delivery/outbox',dependencies=[Depends(require_control)])
    async def read_local_outbox():
        return outbox

    @app.put('/__e2e__/uploads/{encoded_key:path}')
    async def upload(encoded_key: str, request: Request) -> dict[str, str]:
        key = unquote(encoded_key)
        storage.put(key, await request.body(), request.headers.get('content-type', ''))
        return {'status': 'uploaded'}

    @app.post('/__e2e__/scan/clean', dependencies=[Depends(require_control)])
    async def mark_clean(payload: ScanControl) -> dict[str, str]:
        try:
            storage.set_scan_status(payload.storage_key, 'NO_THREATS_FOUND')
        except KeyError as exc:
            raise HTTPException(404, 'E2E object not found') from exc
        return {'status': 'NO_THREATS_FOUND'}

    @app.get('/__e2e__/downloads/{encoded_key:path}')
    async def signed_download(encoded_key: str, expires: int = 0, signature: str = '',version_id:str|None=None) -> Response:
        try:
            content, content_type = storage.read_signed(unquote(encoded_key), expires, signature,version_id)
        except ValueError as exc:
            raise HTTPException(409, 'Test document is unavailable or not scan-clean') from exc
        return Response(content=content, media_type=content_type, headers={'Cache-Control':'private, no-store'})

    # Raw APIRoute objects retain the original application's dependency override
    # provider. Re-register routes so FastAPI binds them to this test-only app.
    app.include_router(production_app.router)
    return app


if os.getenv('APP_ENV', '').lower() == 'test' and os.getenv('TRANSIVOX_E2E', '').lower() == 'true':
    app = create_e2e_app()
else:
    app = FastAPI(title='Disabled TransivoX E2E support')
