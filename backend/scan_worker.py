"""Private SQS worker. No listener, public callback, document logging or AWS keys."""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import unquote_plus

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.services.scan_contract import ScanIdentity, result_key

MAX_BYTES=10*1024*1024


def engine_evidence():
    value=subprocess.run(['clamdscan','--config-file=/opt/scanner/clamd.conf','--version'],capture_output=True,text=True,timeout=15,check=True).stdout.strip()
    matched=re.fullmatch(r'ClamAV ([^/]+)/([^/]+)/(.+)',value)
    if not matched:
        raise RuntimeError('missing_signature_evidence')
    built=datetime.strptime(matched[3],'%a %b %d %H:%M:%S %Y').replace(tzinfo=UTC)
    if built>datetime.now(UTC)+timedelta(minutes=5) or datetime.now(UTC)-built>timedelta(hours=48):
        raise RuntimeError('stale_definitions')
    return dict(engine=matched[1],signature_version=matched[2],definitions_at=built.isoformat())


def scan_path(path):
    result=subprocess.run([sys.executable,__file__,'--scan-file',str(path)],capture_output=True,text=True,timeout=180,check=True)
    return tuple(json.loads(result.stdout))


def _scan_path(path):
    # Signature and complete-format validation prevent arbitrary bytes masquerading as documents.
    from PIL import Image
    from pypdf import PdfReader
    prefix=path.read_bytes()[:8]
    try:
        if prefix.startswith(b'%PDF-'):
            document=PdfReader(path,strict=True)
            if document.is_encrypted:
                return 'encrypted','encrypted_document'
            if len(document.pages)>200:
                return 'limits_exceeded','page_limit'
        elif prefix.startswith(b'\x89PNG\r\n\x1a\n') or prefix.startswith(b'\xff\xd8\xff'):
            Image.MAX_IMAGE_PIXELS=25_000_000
            with Image.open(path) as image:
                if image.width*image.height>25_000_000:
                    return 'limits_exceeded','image_pixel_limit'
                image.verify()
        else:
            # EICAR must be detected by the real engine even though it is not a document.
            return run_engine(path,unsupported=True)
    except Exception:
        return 'unsupported','invalid_document_structure'
    return run_engine(path)


def run_engine(path,unsupported=False):
    result=subprocess.run(['clamdscan','--config-file=/opt/scanner/clamd.conf','--fdpass','--no-summary','--stdout',str(path)],capture_output=True,timeout=120,text=True)
    if result.returncode==1:
        if 'Heuristics.Limits.Exceeded' in result.stdout:
            return 'limits_exceeded','engine_limit'
        if 'Heuristics.Encrypted' in result.stdout:
            return 'encrypted','encrypted_document'
        return 'infected','engine_detection'
    if result.returncode!=0:
        raise RuntimeError('engine_failure')
    return ('unsupported','unsupported_content') if unsupported else ('clean','clean')


def process(identity,s3,results_bucket):
    evidence=engine_evidence()
    with tempfile.TemporaryDirectory(prefix='kyc-scan-') as temporary:
        path=Path(temporary)/'object'
        response=s3.get_object(Bucket=identity.bucket,Key=identity.key,VersionId=identity.version_id)
        body=response['Body']
        total=0
        try:
            if response.get('VersionId')!=identity.version_id:
                raise RuntimeError('version_mismatch')
            with path.open('wb') as destination:
                deadline=time.monotonic()+90
                while chunk:=body.read(65536):
                    if time.monotonic()>deadline:
                        raise RuntimeError('download_deadline')
                    total+=len(chunk)
                    if total>MAX_BYTES:
                        break
                    destination.write(chunk)
        finally:
            body.close()
        if total>MAX_BYTES or total==0:
            status,reason='limits_exceeded','object_size'
        else:
            status,reason=scan_path(path)
    result=dict(identity=identity.as_dict(),attempt_id=identity.attempt_id,provider='clamav',status=status,reason=reason,scanned_at=datetime.now(UTC).isoformat(),**evidence)
    try:
        s3.put_object(Bucket=results_bucket,Key=result_key(identity),Body=json.dumps(result).encode(),ContentType='application/json',ServerSideEncryption='AES256',IfNoneMatch='*')
    except ClientError as exc:
        if exc.response['Error']['Code'] not in {'PreconditionFailed','412'}:
            raise
        # Existing immutable result wins. Never overwrite an old/parallel attempt.
    return status


def identities(body,source_bucket):
    payload=json.loads(body)
    if payload.get('Event')=='s3:TestEvent':
        return []
    records=payload.get('Records')
    if not isinstance(records,list) or not 1<=len(records)<=10:
        raise ValueError('invalid_event')
    result=[]
    for record in records:
        if record.get('eventSource')!='aws:s3' or not record.get('eventName','').startswith('ObjectCreated:'):
            raise ValueError('invalid_event')
        obj=record['s3']['object']; bucket=record['s3']['bucket']['name']
        if bucket!=source_bucket:
            raise ValueError('wrong_bucket')
        result.append(ScanIdentity(bucket,unquote_plus(obj['key']),obj['versionId']))
    return result


def start_daemon():
    process=subprocess.Popen(['clamd','--foreground','--config-file=/opt/scanner/clamd.conf'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    deadline=time.monotonic()+240
    while time.monotonic()<deadline:
        if process.poll() is not None:
            raise RuntimeError('engine_startup_failed')
        try:
            result=subprocess.run(['clamdscan','--config-file=/opt/scanner/clamd.conf','--ping=1'],capture_output=True,timeout=5)
            if result.returncode==0:
                engine_evidence()
                return process
        except subprocess.TimeoutExpired:
            pass
        time.sleep(2)
    process.terminate()
    raise RuntimeError('engine_startup_timeout')


def main():
    region=os.environ.get('AWS_REGION','ap-south-1')
    source=os.environ['SCAN_SOURCE_BUCKET'];results=os.environ['SCAN_RESULTS_BUCKET'];queue=os.environ['SCAN_QUEUE_URL']
    if source==results:
        raise RuntimeError('separate_result_bucket_required')
    config=Config(connect_timeout=5,read_timeout=30,retries={'max_attempts':2})
    s3=boto3.client('s3',region_name=region,config=config);sqs=boto3.client('sqs',region_name=region,config=config)
    subprocess.run(['freshclam','--stdout'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,timeout=180)
    daemon=start_daemon()
    updated=time.monotonic()
    while True:
        try:
            if time.monotonic()-updated>12*3600 or updated==0:
                subprocess.run(['freshclam','--stdout'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,timeout=180)
                subprocess.run(['clamdscan','--config-file=/opt/scanner/clamd.conf','--reload'],capture_output=True,check=True,timeout=15)
                time.sleep(5)
                engine_evidence();updated=time.monotonic()
            if daemon.poll() is not None:
                raise RuntimeError('engine_stopped')
            engine_evidence()
            Path('/tmp/scanner-heartbeat').write_text(str(time.time()))
            messages=sqs.receive_message(QueueUrl=queue,MaxNumberOfMessages=1,WaitTimeSeconds=20,VisibilityTimeout=600).get('Messages',[])
            for message in messages:
                try:
                    jobs=identities(message['Body'],source)
                    outcomes=[process(i,s3,results) for i in jobs]
                    sqs.delete_message(QueueUrl=queue,ReceiptHandle=message['ReceiptHandle'])
                    print(json.dumps({'event':'scan_completed','outcomes':outcomes,'attempt_ids':[i.attempt_id for i in jobs]}),flush=True)
                except Exception as exc:
                    # No receipt deletion: SQS retries then DLQs per bounded redrive policy.
                    print(json.dumps({'event':'scan_attempt_failed','diagnostic':type(exc).__name__,'message_id':message.get('MessageId')}),flush=True)
        except Exception:
            print('{"event":"scanner_unavailable"}',flush=True)
            time.sleep(20)


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--scan-file':
        print(json.dumps(_scan_path(Path(sys.argv[2]))))
    else:
        main()
