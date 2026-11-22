import pytest

from s3_integration_check import validate_target, harmless_pdf


def test_smoke_refuses_other_targets():
    with pytest.raises(ValueError):
        validate_target('another-bucket', 'ap-south-1')
    with pytest.raises(ValueError):
        validate_target('transivox-kyc-harsh3330', 'us-east-1')
    validate_target('transivox-kyc-harsh3330', 'ap-south-1')


def test_pdf_is_harmless_distinct_and_has_valid_xref():
    first, second = harmless_pdf('ORIGINAL'), harmless_pdf('REPLACEMENT')
    assert first != second and first.startswith(b'%PDF-1.4')
    assert b'TEST DOCUMENT' in first and b'NOT A REAL ID' in first
    offset = int(first.split(b'startxref\n')[1].splitlines()[0])
    assert first[offset:].startswith(b'xref\n')
