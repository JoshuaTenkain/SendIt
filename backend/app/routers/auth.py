from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import TokenOut, UserCreate, UserLogin, UserOut
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
logger = structlog.get_logger()


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, request: Request, db: Session = Depends(get_db)) -> User:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        logger.warning("signup_duplicate_email", email=payload.email, ip=request.client.host if request.client else "unknown")
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("signup_success", user_id=str(user.id), email=payload.email, ip=request.client.host if request.client else "unknown")
    return user


@router.post("/login", response_model=TokenOut)
def login(payload: UserLogin, request: Request, db: Session = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        logger.warning("login_failed", email=payload.email, ip=request.client.host if request.client else "unknown")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        logger.warning("login_inactive_user", user_id=str(user.id), email=payload.email, ip=request.client.host if request.client else "unknown")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

    token = create_access_token(subject=str(user.id))
    logger.info("login_success", user_id=str(user.id), email=payload.email, ip=request.client.host if request.client else "unknown")
    return TokenOut(access_token=token)
