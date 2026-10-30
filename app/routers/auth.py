"""Login and authenticated-user dependencies."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.roles import Role
from app.models.user import User
from app.schemas.auth import LoginRequest, PasswordChange, SignupRequest, TokenResponse, UserCreate, UserRead
from app.services.auth import create_access_token, decode_access_token, hash_password, register_user, verify_password

router = APIRouter(prefix="/auth", tags=["authentication"])
bearer_scheme = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    role_name = user.role.role_name
    return TokenResponse(access_token=create_access_token(user.email, role_name), role=role_name)


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = register_user(db, str(data.email), data.password, data.password_confirmation)
    role_name = user.role.role_name
    return TokenResponse(access_token=create_access_token(user.email, role_name), role=role_name)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(credentials.credentials)
    email = payload.get("sub") if payload else None
    user = db.scalar(select(User).where(User.email == email)) if email else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")
    return user


def require_roles(*roles: str):
    def check_role(user: User = Depends(get_current_user)) -> User:
        if user.role.role_name not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your role cannot perform this action")
        return user

    return check_role


@router.post("/change-password")
def change_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "Password updated"}


@router.post("/users", response_model=UserRead, status_code=201, dependencies=[Depends(require_roles("administrator"))])
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    role = db.scalar(select(Role).where(Role.role_name == data.role))
    if role is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Requested role is not configured")
    user = User(name=data.name, email=email, password_hash=hash_password(data.password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"user_id": user.user_id, "name": user.name, "email": user.email, "role": role.role_name}
