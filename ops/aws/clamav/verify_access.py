"""Read-only personal-account inspection. No credentials are printed or configured."""
import argparse
import hashlib
import json
import os
import boto3
from botocore.config import Config

parser=argparse.ArgumentParser();parser.add_argument('--expected-account',required=True);parser.add_argument('--application-role');args=parser.parse_args()
os.environ['AWS_EC2_METADATA_DISABLED']='true'
config=Config(connect_timeout=5,read_timeout=10,retries={'max_attempts':0})
session=boto3.Session(region_name='ap-south-1');identity=session.client('sts',config=config).get_caller_identity()
if identity['Account']!=args.expected_account:raise SystemExit('Account mismatch. No storage or IAM inspection performed.')
bucket='transivox-kyc-harsh3330';s3=session.client('s3',config=config)
s3.head_bucket(Bucket=bucket,ExpectedBucketOwner=args.expected_account)
report={'account':identity['Account'],'caller_arn':identity['Arn'],'bucket':bucket,'region_expected':'ap-south-1','application_credentials_verified':False}
for key,method in [('location','get_bucket_location'),('versioning','get_bucket_versioning'),('encryption','get_bucket_encryption'),('public_access_block','get_public_access_block'),('cors','get_bucket_cors'),('notifications','get_bucket_notification_configuration')]:
    try:
        value=getattr(s3,method)(Bucket=bucket,ExpectedBucketOwner=args.expected_account);value.pop('ResponseMetadata',None);report[key]=value
    except Exception as exc:report[key]={'unverified':type(exc).__name__}
if args.application_role:
    iam=session.client('iam',config=config)
    role=iam.get_role(RoleName=args.application_role)['Role']
    if role['Arn'].split(':')[4]!=args.expected_account:raise SystemExit('Application role account mismatch')
    report['application_role_arn']=role['Arn']
    report['attached_policy_metadata']=iam.list_attached_role_policies(RoleName=args.application_role)['AttachedPolicies']
    policies=[]
    for name in iam.list_role_policies(RoleName=args.application_role)['PolicyNames']:
        document=iam.get_role_policy(RoleName=args.application_role,PolicyName=name)['PolicyDocument']
        policies.append({'name':name,'sha256':hashlib.sha256(json.dumps(document,sort_keys=True).encode()).hexdigest(),'statements':document.get('Statement',[])})
    report['inline_policy_review']=policies
print(json.dumps(report,indent=2,default=str))
