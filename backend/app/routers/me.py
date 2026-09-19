import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.deps import get_current_user
from app.models import Case, Document, User
from app.routers.cases import _case_out
from app.schemas import (
    GDPR_NOTE,
    CaseOut,
    ClaimBody,
    DashboardOut,
    DocumentOut,
    MeOut,
    MePatch,
)
from app.services.catalog import normalize_account_municipality
from app.services.extraction import run_extraction
from app.services import storage

router = APIRouter(tags=["me"])


def to_document_out(doc: Document) -> DocumentOut:
    return DocumentOut(
        id=doc.id,
        original_filename=doc.original_filename,
        content_type=doc.content_type,
        case_id=doc.case_id,
        user_id=doc.user_id,
        extracted_type=doc.extracted_type,
        extracted_expiry=doc.extracted_expiry,
        status=doc.status,
        purge_at=doc.purge_at,
    )


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user)) -> MeOut:
    return MeOut(
        user_id=str(user.id),
        email=user.email,
        name=user.name,
        municipality=user.municipality,
        retention_hours=settings.document_retention_hours,
        gdpr_note=GDPR_NOTE,
    )


@router.patch("/me", response_model=MeOut)
def patch_me(
    body: MePatch,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> MeOut:
    try:
        user.municipality = normalize_account_municipality(session, body.municipality)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session.add(user)
    session.commit()
    session.refresh(user)
    return MeOut(
        user_id=str(user.id),
        email=user.email,
        name=user.name,
        municipality=user.municipality,
        retention_hours=settings.document_retention_hours,
        gdpr_note=GDPR_NOTE,
    )


@router.get("/me/dashboard", response_model=DashboardOut)
def dashboard(user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> DashboardOut:
    storage.purge_expired_documents(session)
    docs = session.scalars(select(Document).where(Document.user_id == user.id)).all()
    cases = session.scalars(select(Case).where(Case.user_id == user.id)).all()
    return DashboardOut(
        user_id=user.id,
        email=user.email,
        name=user.name,
        documents=[to_document_out(doc) for doc in docs],
        cases=[_case_out(row) for row in cases],
    )


@router.post("/me/claim", response_model=CaseOut)
def claim_case(
    body: ClaimBody,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> CaseOut:
    row = session.get(Case, str(body.case_id))
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    if row.user_id and row.user_id != user.id:
        raise HTTPException(status_code=403, detail="Case belongs to another user")
    row.user_id = user.id
    docs = session.scalars(select(Document).where(Document.case_id == row.id)).all()
    for doc in docs:
        storage.reencrypt_for_user(doc, user.id)
        doc.user_id = user.id
        doc.purge_at = None
        session.add(doc)
    session.add(row)
    session.commit()
    session.refresh(row)
    return _case_out(row)


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(
    user: User = Depends(get_current_user), session: Session = Depends(get_session)
) -> list[DocumentOut]:
    storage.purge_expired_documents(session)
    docs = session.scalars(select(Document).where(Document.user_id == user.id)).all()
    return [to_document_out(doc) for doc in docs]


@router.post("/documents", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> DocumentOut:
    data = await file.read(storage.MAX_UPLOAD_BYTES + 1)
    try:
        path = storage.save_upload(data, user_id=user.id, case_id=None)
    except ValueError:
        raise HTTPException(status_code=413, detail="File too large (max 8 MB)")
    stored = Document(
        user_id=user.id,
        original_filename=file.filename or "upload.bin",
        storage_path=path,
        content_type=file.content_type or "application/octet-stream",
        purge_at=None,
    )
    session.add(stored)
    session.commit()
    session.refresh(stored)
    doc_id = str(stored.id)
    await asyncio.to_thread(run_extraction, doc_id)
    session.expire_all()
    stored = session.get(Document, doc_id)
    if not stored:
        raise HTTPException(status_code=404, detail="Document not found")
    return to_document_out(stored)


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    doc = session.get(Document, str(document_id))
    if not doc or doc.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    storage.delete_file(doc.storage_path)
    session.delete(doc)
    session.commit()
    return {"status": "deleted"}
