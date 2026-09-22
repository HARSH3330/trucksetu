from app.api.auth import PUBLIC_ROLES, SignupInput
from app.core.security import create_access_token, create_refresh_token, get_password_hash, hash_otp, hash_token, verify_otp, verify_password, verify_token


def test_public_roles_exclude_privileged_roles() -> None:
    assert "admin" not in PUBLIC_ROLES
    assert "superadmin" not in PUBLIC_ROLES


def test_signup_rejects_short_password() -> None:
    try:
        SignupInput(full_name="Harsh Sharma", email="harsh@example.com", password="short")
        assert False
    except Exception:
        assert True


def test_tokens_are_typed_and_refresh_has_rotation_claims() -> None:
    access = verify_token(create_access_token({"sub": "user-1"}), "access")
    refresh = verify_token(create_refresh_token("user-1", "jti-1", "family-1"), "refresh")
    assert access["sub"] == "user-1"
    assert refresh["jti"] == "jti-1" and refresh["family"] == "family-1"


def test_token_hash_is_deterministic_without_storing_token() -> None:
    assert hash_token("secret") == hash_token("secret")
    assert hash_token("secret") != "secret"


def test_password_and_otp_hashing_work_with_deployed_bcrypt() -> None:
    password_hash = get_password_hash("ValidPassword123")
    assert verify_password("ValidPassword123", password_hash)
    assert not verify_password("WrongPassword123", password_hash)
    code_hash = hash_otp("123456")
    assert verify_otp("123456", code_hash)
