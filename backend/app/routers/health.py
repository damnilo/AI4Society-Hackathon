from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.llm import ping_openai, ping_xai
from app.models import Office, Place, Procedure
from app.schemas import HealthOut, LlmHealthOut
from app.services import storage

router = APIRouter(tags=["health"])


def _count(session: Session, model) -> int:  # type: ignore[no-untyped-def]
    value = session.scalar(select(func.count()).select_from(model))
    return int(value or 0)


@router.get("/health", response_model=HealthOut)
def health(session: Session = Depends(get_session)) -> HealthOut:
    storage.purge_expired_documents(session)
    return HealthOut(
        ok=True,
        db="ok",
        catalog={
            "procedures": _count(session, Procedure),
            "offices": _count(session, Office),
            "places": _count(session, Place),
        },
    )


@router.get("/health/llm", response_model=LlmHealthOut)
def health_llm() -> LlmHealthOut:
    xai = ping_xai()
    openai = ping_openai()
    return LlmHealthOut(
        configured=bool(xai["configured"]),
        ok=bool(xai["ok"]),
        detail=str(xai["detail"]),
        model=str(xai["model"]),
        openai_configured=bool(openai["configured"]),
        openai_ok=bool(openai["ok"]),
        openai_detail=str(openai["detail"]),
        openai_model=str(openai["model"]),
    )
