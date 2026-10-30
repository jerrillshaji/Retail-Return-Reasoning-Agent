import pytest
from fastapi import HTTPException

from app.models.roles import Role
from app.services.auth import register_user, verify_password


def test_signup_normalizes_email_hashes_password_and_uses_safe_role(db):
    db.add(Role(role_name="retail_manager"))
    db.commit()

    user = register_user(db, "New.User@Example.com", "long-password-123", "long-password-123")

    assert user.email == "new.user@example.com"
    assert user.role.role_name == "retail_manager"
    assert user.password_hash != "long-password-123"
    assert verify_password("long-password-123", user.password_hash)


def test_signup_rejects_mismatched_passwords(db):
    db.add(Role(role_name="retail_manager"))
    db.commit()

    with pytest.raises(HTTPException) as error:
        register_user(db, "new@example.com", "long-password-123", "different-password")

    assert error.value.status_code == 400


def test_signup_rejects_duplicate_email(db):
    db.add(Role(role_name="retail_manager"))
    db.commit()
    register_user(db, "new@example.com", "long-password-123", "long-password-123")

    with pytest.raises(HTTPException) as error:
        register_user(db, "NEW@example.com", "another-password-123", "another-password-123")

    assert error.value.status_code == 409
