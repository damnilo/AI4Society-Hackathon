from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.models import User
from app.schemas import AuthLogin, AuthRegister, RefreshBody, TokenOut

router = APIRouter(tags=["auth"])


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _tokens(user: User) -> TokenOut:
    now = datetime.now(timezone.utc)
    access = jwt.encode(
        {"sub": str(user.id), "exp": now + timedelta(hours=8), "typ": "access"},
        settings.jwt_secret,
        algorithm="HS256",
    )
    refresh = jwt.encode(
        {"sub": str(user.id), "exp": now + timedelta(days=7), "typ": "refresh"},
        settings.jwt_secret,
        algorithm="HS256",
    )
    return TokenOut(
        access_token=access,
        refresh_token=refresh,
        user_id=str(user.id),
        email=user.email,
        name=user.name,
    )


@router.post("/auth/register", response_model=TokenOut)
def register(body: AuthRegister, session: Session = Depends(get_session)) -> TokenOut:
    existing = session.scalars(select(User).where(User.email == body.email.lower())).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=body.email.lower(),
        password_hash=_hash_password(body.password),
        name=body.name,
        municipality=body.municipality,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return _tokens(user)


@router.post("/auth/login", response_model=TokenOut)
def login(body: AuthLogin, session: Session = Depends(get_session)) -> TokenOut:
    user = session.scalars(select(User).where(User.email == body.email.lower())).first()
    if not user or not _verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return _tokens(user)


@router.post("/auth/refresh", response_model=TokenOut)
def refresh(body: RefreshBody, session: Session = Depends(get_session)) -> TokenOut:
    try:
        payload = jwt.decode(body.refresh_token, settings.jwt_secret, algorithms=["HS256"])
        if payload.get("typ") != "refresh":
            raise JWTError("wrong type")
        user = session.get(User, str(payload["sub"]))
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return _tokens(user)
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc
