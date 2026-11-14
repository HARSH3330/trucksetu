"""Build jobs from an operator-reviewed recorded-version manifest; no cloud writes."""
import argparse,json
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('manifest');parser.add_argument('output');args=parser.parse_args()
rows=json.loads(Path(args.manifest).read_text(encoding='utf-8'));jobs=[];resubmit=[];seen=set()
for row in rows:
    bucket,key,version=row.get('bucket'),row.get('key'),row.get('version_id')
    if bucket!='transivox-kyc-harsh3330' or not isinstance(key,str) or not key.startswith('kyc/'):
        raise ValueError('Unexpected private object identity')
    if not version or version=='null':resubmit.append(row.get('document_id'));continue
    identity=(bucket,key,version)
    if identity in seen:continue
    seen.add(identity)
    jobs.append({'Records':[{'eventSource':'aws:s3','eventName':'ObjectCreated:Put','s3':{'bucket':{'name':bucket},'object':{'key':__import__('urllib.parse',fromlist=['quote_plus']).quote_plus(key),'versionId':version}}}]})
Path(args.output).write_text(json.dumps({'jobs':jobs,'resubmission_required':resubmit},indent=2),encoding='utf-8')
print(json.dumps({'prepared_jobs':len(jobs),'unversioned_resubmissions':len(resubmit),'sent':0}))
