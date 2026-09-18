from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.models import Case, Document, User
from app.schemas import CaseOut, CandidateOut, DashboardOut, DocumentOut
from pathlib import Path

router = APIRouter(tags=["me"])


def get_current_user(
    session: Session = Depends(get_session),
    authorization: str | None = Header(default=None),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = UUID(str(payload["sub"]))
    except (JWTError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    user = session.get(User, str(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/me/dashboard", response_model=DashboardOut)
def dashboard(user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> DashboardOut:
    docs = session.scalars(select(Document).where(Document.user_id == user.id)).all()
    cases = session.scalars(select(Case).where(Case.user_id == user.id)).all()
    return DashboardOut(
        user_id=user.id,
        email=user.email,
        name=user.name,
        documents=[
            DocumentOut(
                id=doc.id,
                original_filename=doc.original_filename,
                content_type=doc.content_type,
                case_id=doc.case_id,
                extracted_type=doc.extracted_type,
                extracted_expiry=doc.extracted_expiry,
                status=doc.status,
            )
            for doc in docs
        ],
        cases=[
            CaseOut(
                case_id=row.id,
                candidates=[CandidateOut.model_validate(item) for item in row.candidates],
                need_clarification=row.need_clarification,
                questions=row.questions,
                from_place=row.from_place,
                to_place=row.to_place,
            )
            for row in cases
        ],
    )


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(
    user: User = Depends(get_current_user), session: Session = Depends(get_session)
) -> list[DocumentOut]:
    docs = session.scalars(select(Document).where(Document.user_id == user.id)).all()
    return [
        DocumentOut(
            id=doc.id,
            original_filename=doc.original_filename,
            content_type=doc.content_type,
            case_id=doc.case_id,
            extracted_type=doc.extracted_type,
            extracted_expiry=doc.extracted_expiry,
            status=doc.status,
        )
        for doc in docs
    ]


@router.post("/documents", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> DocumentOut:
    upload_root = Path(settings.upload_dir)
    upload_root.mkdir(parents=True, exist_ok=True)
    stored = Document(
        user_id=user.id,
        original_filename=file.filename or "upload.bin",
        storage_path="",
        content_type=file.content_type or "application/octet-stream",
    )
    session.add(stored)
    session.commit()
    session.refresh(stored)
    dest = upload_root / f"{stored.id}_{stored.original_filename}"
    dest.write_bytes(await file.read())
    stored.storage_path = str(dest)
    session.add(stored)
    session.commit()
    session.refresh(stored)
    return DocumentOut(
        id=stored.id,
        original_filename=stored.original_filename,
        content_type=stored.content_type,
        case_id=stored.case_id,
        extracted_type=stored.extracted_type,
        extracted_expiry=stored.extracted_expiry,
        status=stored.status,
    )


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    doc = session.get(Document, str(document_id))
    if not doc or doc.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    path = Path(doc.storage_path) if doc.storage_path else None
    if path and path.exists():
        path.unlink()
    session.delete(doc)
    session.commit()
    return {"status": "deleted"}
