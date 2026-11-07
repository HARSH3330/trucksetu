import json
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock
import pytest
from app.services.scan_contract import ScanIdentity, validate_result, result_key


def proof(identity, **changes):
    now=datetime.now(UTC)
    value=dict(identity=identity.as_dict(),attempt_id=identity.attempt_id,provider='clamav',status='clean',engine='ClamAV test',signature_version='test-signatures',definitions_at=(now-timedelta(hours=1)).isoformat(),scanned_at=now.isoformat(),reason='clean')
    value.update(changes)
    return value


def test_result_binds_bucket_key_version_and_attempt():
    a=ScanIdentity('private-bucket','kyc/fictional/file','version-1')
    b=ScanIdentity('private-bucket','kyc/fictional/file','version-2')
    assert result_key(a)!=result_key(b)
    validate_result(proof(a),a)
    with pytest.raises(ValueError):validate_result(proof(a),b)
    with pytest.raises(ValueError):validate_result(proof(a,attempt_id='forged'),a)


@pytest.mark.parametrize('status',['pending','infected','failed','unsupported','encrypted','limits_exceeded'])
def test_nonclean_never_approves(status):
    a=ScanIdentity('bucket','kyc/file','version')
    with pytest.raises(ValueError):validate_result(proof(a,status=status),a)


def test_stale_definitions_future_time_and_missing_engine_fail_closed():
    a=ScanIdentity('bucket','kyc/file','version')
    for change in [dict(definitions_at=(datetime.now(UTC)-timedelta(days=8)).isoformat()),dict(scanned_at=(datetime.now(UTC)+timedelta(days=1)).isoformat()),dict(engine='')]:
        with pytest.raises(ValueError):validate_result(proof(a,**change),a)


def test_provider_abstraction_does_not_trust_upload_tags(monkeypatch):
    from app.services.storage import PrivateDocumentStorage
    from app.core.config import settings
    monkeypatch.setattr(settings,'KYC_SCAN_PROVIDER','clamav')
    monkeypatch.setattr(settings,'KYC_SCAN_RESULTS_BUCKET','separate-private-results')
    storage=object.__new__(PrivateDocumentStorage);storage.bucket='uploads';storage.client=Mock()
    a=ScanIdentity('uploads','kyc/file','v1')
    storage.client.get_object.return_value={'Body':Mock(read=lambda n:json.dumps(proof(a)).encode())}
    storage.require_clean_scan('kyc/file','v1')
    storage.client.get_object_tagging.assert_not_called()
    with pytest.raises(ValueError):storage.require_clean_scan('kyc/file','v2')
    with pytest.raises(ValueError):storage.require_clean_scan('kyc/file',None)
