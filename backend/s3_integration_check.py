"""Opt-in real S3 probe. No DB, tag writes, deletes, listing, or scan bypass.

Uses the production adapter's configured S3 client and scan/read methods.
Presigned PUT generation uses that client directly solely to constrain the
probe to kyc/test/, not the production provider-id key namespace.
"""
import argparse
import json
import os
import re
import uuid
from urllib.parse import urlsplit, urlunsplit

import boto3
import httpx
from botocore.exceptions import ClientError

BUCKET = 'transivox-kyc-harsh3330'
REGION = 'ap-south-1'


def validate_target(bucket, region):
    if bucket != BUCKET or region != REGION:
        raise ValueError('Expected test bucket/region configuration is missing or mismatched')


def harmless_pdf(label):
    # Same minimal PDF object/xref structure as e2e/fixtures/pdf.ts.
    # WinAnsi octal 227 renders an em dash; no identity data is included.
    stream = f'BT /F1 16 Tf 50 750 Td (TEST DOCUMENT \\227 NOT A REAL ID) Tj 0 -30 Td ({label}) Tj ET'.encode('ascii')
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>', b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>', b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>', b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream']
    content = b'%PDF-1.4\n'
    offsets = []
    for index, obj in enumerate(objects, 1):
        offsets.append(len(content))
        content += f'{index} 0 obj\n'.encode()+obj+b'\nendobj\n'
    xref = len(content)
    content += b'xref\n0 6\n0000000000 65535 f \n'+b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets)
    return content+f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode()


def run(execute=False):
    os.environ.setdefault('AWS_EC2_METADATA_DISABLED', 'true')
    from app.core.config import settings
    from app.services.storage import PrivateDocumentStorage
    report = {'environment':'local standalone probe; not Vercel', 'identity':'application adapter credentials; principal ARN not queried', 'checks':[], 'retained':[]}
    def record(name, status, detail):
        report['checks'].append({'check':name, 'status':status, 'detail':detail})
    try:
        validate_target(settings.AWS_S3_BUCKET, settings.AWS_REGION)
        credentials = bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)
        source = 'explicit API credentials (identifiers redacted)'
        if not credentials:
            resolved = boto3.Session().get_credentials()
            credentials = resolved is not None
            source = resolved.method if resolved else 'none'
        report['credential_source'] = source
        if not credentials:
            record('preflight', 'BLOCKED', 'NoCredentials: no local application credentials available')
            return report
        record('preflight', 'PASS', 'Expected target and credentials available; no credential values emitted')
        if not execute:
            record('real S3 operations', 'BLOCKED', 'Supply --run to authorize two harmless writes to one unique key')
            return report
        storage = PrivateDocumentStorage()
        key = f'kyc/test/{uuid.uuid4().hex}/TEST-NOT-A-REAL-ID.pdf'
        report['retained'].append({'bucket':BUCKET, 'key':key, 'versions':[]})
        signed = storage.client.generate_presigned_url('put_object', Params={'Bucket':BUCKET,'Key':key,'ContentType':'application/pdf','ServerSideEncryption':'AES256'}, ExpiresIn=600)
        original = harmless_pdf('ORIGINAL')
        replacement = harmless_pdf('REPLACEMENT')
        for label, content in [('original', original), ('replacement', replacement)]:
            response = httpx.put(signed, content=content, headers={'Content-Type':'application/pdf','x-amz-server-side-encryption':'AES256'}, timeout=30, follow_redirects=False)
            if response.status_code not in {200,201}:
                raise RuntimeError(f'Presigned PUT HTTP {response.status_code}; response body/URL suppressed')
            record(f'{label} signed upload', 'PASS', 'Harmless bytes uploaded with SSE-S3 request header')
            version = response.headers.get('x-amz-version-id')
            if not isinstance(version, str) or not version or version == 'null':
                raise RuntimeError('VersionId missing or null')
            report['retained'][0]['versions'].append({'label':label,'version_id':version})
            metadata = storage.confirm(key)
            if metadata.get('VersionId') != version:
                raise RuntimeError('Upload and metadata VersionId mismatch')
            if label == 'original':
                original_version = version
                head = storage.client.head_object(Bucket=BUCKET,Key=key,VersionId=version)
                if head.get('VersionId') != version or head.get('ServerSideEncryption') != 'AES256':
                    raise RuntimeError('Exact-version metadata/encryption mismatch')
                record('original version metadata/encryption', 'PASS', 'Non-null VersionId and exact-version AES256 confirmed')
                scan = storage.malware_scan_status(key, version)
                record('exact-version tag read', 'PASS', 'Tag read succeeded; clean result absent' if scan is None else 'Tag read succeeded; values not printed')
                if scan == 'NO_THREATS_FOUND':
                    raise RuntimeError('Unexpected clean tag on test object; missing-scan test cannot be claimed')
                try:
                    storage.require_clean_scan(key, version)
                except ValueError:
                    record('missing/nonclean scan storage gate', 'PASS', 'Actual adapter rejected the actual object scan result')
                else:
                    raise RuntimeError('Unsafe scan gate: nonclean object accepted')
                parts = urlsplit(signed)
                unsigned = urlunsplit((parts.scheme,parts.netloc,parts.path,'',''))
                denied = httpx.get(unsigned, timeout=30, follow_redirects=False)
                if denied.status_code != 403:
                    raise RuntimeError(f'Unsigned GET expected 403, received HTTP {denied.status_code}')
                record('unsigned download denied', 'PASS', 'HTTP 403; no Authorization or signed query')
            elif version == original_version:
                raise RuntimeError('Overwrite did not create a distinct version')
        body = storage.client.get_object(Bucket=BUCKET,Key=key,VersionId=original_version)['Body']
        try:
            if body.read(len(original)+1) != original:
                raise RuntimeError('Original version bytes changed after overwrite')
        finally:
            body.close()
        record('direct storage original-version read', 'PASS', 'Original bytes preserved after replacement; NOT application download authorization')
        record('adapter version-specific file signature', 'PASS' if storage.detected_content_type(key, original_version)=='application/pdf' else 'FAIL', 'Checked original stored version through the existing adapter')
    except Exception as error:
        # Deliberately do not print raw exceptions, URLs, response bodies, keys
        # or ARN/account identifiers from SDK errors. Test keys are above.
        if isinstance(error, ClientError):
            detail = f"AWS {error.response.get('Error',{}).get('Code','unknown')} HTTP {error.response.get('ResponseMetadata',{}).get('HTTPStatusCode','unknown')}; provider message redacted"
        elif str(error) in {'Expected test bucket/region configuration is missing or mismatched','VersionId missing or null','Upload and metadata VersionId mismatch','Exact-version metadata/encryption mismatch','Unexpected clean tag on test object; missing-scan test cannot be claimed','Unsafe scan gate: nonclean object accepted','Overwrite did not create a distinct version','Original version bytes changed after overwrite'}:
            detail = str(error)
        elif re.fullmatch(r'Presigned PUT HTTP \d{3}; response body/URL suppressed|Unsigned GET expected 403, received HTTP \d{3}', str(error)):
            detail = str(error)
        else:
            detail = f'{type(error).__name__}; details redacted'
        record('probe', 'BLOCKED' if not execute else 'FAIL', detail)
    record('real application registration/approval/download authorization', 'BLOCKED', 'Not exercised: no real API sessions/database records used. Storage-level gate is not route authorization proof.')
    record('successful malware scan/full KYC approval', 'BLOCKED', 'Scanner unavailable; no clean tags written or bypassed')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    result = run(parser.parse_args().run)
    print(json.dumps(result, indent=2))
    raise SystemExit(1 if any(item['status'] in {'FAIL','BLOCKED'} for item in result['checks']) else 0)
