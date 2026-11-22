"""Real engine, synthetic documents, in-memory versioned S3 adapter; network disabled."""
import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from botocore.exceptions import ClientError
from pypdf import PdfWriter
import scan_worker as worker
from app.services.scan_contract import ScanIdentity,validate_result,result_key


def pdf(encrypted=False):
    writer=PdfWriter();writer.add_blank_page(width=72,height=72)
    if encrypted:writer.encrypt('fictional-test-only')
    output=io.BytesIO();writer.write(output);return output.getvalue()


class Store:
    def __init__(self):self.objects={};self.results={};self.requested=[]
    def get_object(self,**kw):
        self.requested.append(kw)
        return {'Body':io.BytesIO(self.objects[kw['VersionId']]),'VersionId':kw['VersionId']}
    def put_object(self,**kw):
        if kw['Key'] in self.results:
            raise ClientError({'Error':{'Code':'PreconditionFailed'}},'PutObject')
        assert kw['IfNoneMatch']=='*'
        self.results[kw['Key']]=json.loads(kw['Body'])


def main():
    daemon=worker.start_daemon()
    results={}
    with tempfile.TemporaryDirectory() as d:
        path=Path(d)/'object'
        cases={'clean':pdf(),'encrypted':pdf(True),'unsupported':b'not a document','eicar':b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'}
        expected={'clean':'clean','encrypted':'encrypted','unsupported':'unsupported','eicar':'infected'}
        for label,content in cases.items():
            path.write_bytes(content);outcome,_=worker.scan_path(path)
            assert outcome==expected[label],(label,outcome)
            results[label]=outcome
    store=Store();store.objects={'old':pdf(),'new':pdf(True)}
    old=ScanIdentity('private-uploads','kyc/fictional/file','old');new=ScanIdentity('private-uploads','kyc/fictional/file','new')
    assert worker.process(new,store,'private-results')=='encrypted'
    assert worker.process(old,store,'private-results')=='clean'
    validate_result(store.results[result_key(old)],old)
    try:validate_result(store.results[result_key(old)],new)
    except ValueError:pass
    else:raise AssertionError('old version approved replacement')
    before=dict(store.results)
    worker.process(old,store,'private-results');assert before==store.results
    with patch.object(worker,'engine_evidence',side_effect=RuntimeError('outage')):
        try:worker.process(ScanIdentity('private-uploads','kyc/outage','old'),store,'private-results')
        except RuntimeError:pass
        else:raise AssertionError('outage accepted')
    assert len(store.results)==2
    assert worker.process(ScanIdentity('private-uploads','kyc/outage','old'),store,'private-results')=='clean'
    store.objects['oversize']=b'0'*(worker.MAX_BYTES+1)
    assert worker.process(ScanIdentity('private-uploads','kyc/oversize','oversize'),store,'private-results')=='limits_exceeded'
    assert all('VersionId' in r for r in store.requested)
    results.update(exact_version=True,duplicate_immutable=True,out_of_order=True,outage_retry=True,oversize_blocked=True,engine=worker.engine_evidence())
    daemon.terminate()
    print(json.dumps(results))


if __name__=='__main__':main()
