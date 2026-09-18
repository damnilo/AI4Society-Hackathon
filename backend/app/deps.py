from fastapi import Depends, Header, HTTPException
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.models import User


def get_optional_user(
    session: Session = Depends(get_session),
    authorization: str | None = Header(default=None),
) -> User | None:
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if payload.get("typ") not in (None, "access"):
            raise JWTError("wrong type")
        user_id = str(payload["sub"])
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
