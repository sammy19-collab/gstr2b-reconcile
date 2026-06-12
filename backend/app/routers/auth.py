from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from app.models.user import User, UserRole
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.core.audit import write_audit

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        role=UserRole.USER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    write_audit(db, action="REGISTER", user_id=user.id, resource_type="user", resource_id=user.id,
                ip_address=request.client.host if request.client else None)
    db.commit()

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email, User.is_active == True).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    write_audit(db, action="LOGIN", user_id=user.id, resource_type="user", resource_id=user.id,
                ip_address=request.client.host if request.client else None)
    db.commit()

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    payload = verify_token(body.refresh_token, token_type="refresh")
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)
    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)
