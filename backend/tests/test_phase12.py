from app.api.kyc import DOCUMENT_TYPES, REQUIRED, ApplicationInput
from app.services.storage import ALLOWED_CONTENT_TYPES


def test_individual_provider_requires_identity_licence_and_bank() -> None:
    assert REQUIRED["individual"] == {"aadhaar", "pan", "driving_licence", "bank_proof"}


def test_company_verification_requires_gst() -> None:
    assert "gst_certificate" in REQUIRED["company"]


def test_sensitive_upload_types_are_allowlisted() -> None:
    assert "aadhaar" in DOCUMENT_TYPES and "arbitrary" not in DOCUMENT_TYPES
    assert ALLOWED_CONTENT_TYPES == {"application/pdf", "image/jpeg", "image/png"}


def test_gstin_validation() -> None:
    item = ApplicationInput(legal_name="Rathi Roadlines Pvt Ltd", provider_type="company", pan_last_four="123F", gstin="07ABCDE1234F1Z5")
    assert item.gstin == "07ABCDE1234F1Z5"
