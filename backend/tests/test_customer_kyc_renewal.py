from types import SimpleNamespace
from app.services.customer_kyc import may_restart_application


def test_verified_customer_can_renew_after_policy_rotation():
    old=SimpleNamespace(status='verified',policy_version='old-policy',required_documents=['pan'])
    assert may_restart_application(old,'new-policy',['pan'])
    assert may_restart_application(old,'old-policy',['aadhaar','pan'])
    assert not may_restart_application(old,'old-policy',['pan'])


def test_changed_consent_requires_fresh_review_even_at_same_policy_version():
    old=SimpleNamespace(status="verified",policy_version="same-policy",required_documents=["pan"])
    assert may_restart_application(old,"same-policy",["pan"],consent_matches=False)
