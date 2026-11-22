"""Version-bound scan attestations. Only a worker IAM role may write result objects."""
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class ScanIdentity:
    bucket: str
    key: str
    version_id: str

    def __post_init__(self):
        if not self.bucket or not self.key.startswith('kyc/') or not self.version_id or self.version_id=='null':
            raise ValueError('An exact private KYC object version is required')
        if len(self.key)>1024 or len(self.version_id)>255:
            raise ValueError('Invalid object identity')

    def as_dict(self):
        return dict(bucket=self.bucket,key=self.key,version_id=self.version_id)

    @property
    def attempt_id(self):
        return hashlib.sha256(json.dumps(self.as_dict(),sort_keys=True,separators=(',',':')).encode()).hexdigest()


def result_key(identity):
    return 'scan-results/v1/'+identity.attempt_id+'.json'


def validate_result(value, identity, *, max_definition_age_hours=48):
    try:
        if value['identity']!=identity.as_dict() or value['attempt_id']!=identity.attempt_id or value['provider']!='clamav' or value['status']!='clean':
            raise ValueError('Scan does not approve this exact version')
        if not value['engine'] or not value['signature_version'] or not value['reason']:
            raise ValueError('Missing engine evidence')
        scanned=datetime.fromisoformat(value['scanned_at'])
        definitions=datetime.fromisoformat(value['definitions_at'])
        now=datetime.now(UTC)
        if scanned.tzinfo is None or definitions.tzinfo is None or scanned>now+timedelta(minutes=5) or definitions>scanned+timedelta(minutes=5) or scanned-definitions>timedelta(hours=max_definition_age_hours):
            raise ValueError('Invalid or stale signature evidence')
    except (KeyError,TypeError,OverflowError) as exc:
        raise ValueError('Invalid scan evidence') from exc
