"""Truck owners, fleet owners and drivers must give a phone number when they sign up; customers need not."""
import pytest
from pydantic import ValidationError

from app.api.auth import GoogleSignInInput, SignupInput

BASE = {"full_name": "Fictional Person", "email": "fictional@example.com", "password": "FictionalOnly123"}
GOOGLE = {"credential": "x" * 40, "privacy_notice_version": "privacy-test"}


@pytest.mark.parametrize("role", ["provider", "fleet_owner", "driver", "Provider"])
def test_work_roles_need_a_phone_number(role):
    with pytest.raises(ValidationError, match="phone number is required"):
        SignupInput(**BASE, role=role)
    with pytest.raises(ValidationError, match="phone number is required"):
        GoogleSignInInput(**GOOGLE, role=role)
    assert SignupInput(**BASE, role=role, mobile="+919876543210").mobile
    assert GoogleSignInInput(**GOOGLE, role=role, mobile="9876543210").mobile


def test_customers_and_the_role_question_need_no_phone():
    assert SignupInput(**BASE).mobile is None
    assert GoogleSignInInput(**GOOGLE, role="customer").mobile is None
    assert GoogleSignInInput(credential="x" * 40).role is None  # first Google step asks for a role
