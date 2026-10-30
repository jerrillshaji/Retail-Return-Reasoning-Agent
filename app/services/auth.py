"""Password and access-token helpers."""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from pwdlib import PasswordHash
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.roles import Role
from app.models.user import User

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def register_user(db: Session, email: str, password: str, password_confirmation: str) -> User:
    if password != password_confirmation:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    normalized_email = email.strip().lower()
    if db.scalar(select(User.user_id).where(User.email == normalized_email)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    role = db.scalar(select(Role).where(Role.role_name == "retail_manager"))
    if role is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Sign-up is temporarily unavailable")

    user = User(
        name=normalized_email.split("@", 1)[0][:100],
        email=normalized_email,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists") from exc
    db.refresh(user)
    return user


def create_access_token(email: str, role: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": email, "role": role, "exp": expires},
        settings.secret_key,
        algorithm="HS256",
    )


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError:
        return None
