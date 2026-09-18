from datetime import date
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.models import Case, Document, Office, Procedure
from app.schemas import (
    DISCLAIMER,
    CaseCreate,
    CaseOut,
    CandidateOut,
    ClarifyBody,
    DocumentOut,
    DocumentStatusItem,
    DocumentStatusOut,
    GuideOut,
    OfficeOut,
    RelatedOut,
    RetryBody,
    SelectBody,
)
from app.services.catalog import extract_from_to, resolve_office
from app.services.matching import match_procedures

router = APIRouter(tags=["cases"])


def _case_out(row: Case) -> CaseOut:
    return CaseOut(
        case_id=row.id,
        candidates=[CandidateOut.model_validate(item) for item in row.candidates],
        need_clarification=row.need_clarification,
        questions=row.questions,
        from_place=row.from_place,
        to_place=row.to_place,
    )


def _run_match(session: Session, row: Case, text: str) -> Case:
    from_place, to_place = extract_from_to(session, text)
    candidates, need, questions = match_procedures(session, text)
    row.raw_text = text
    row.from_place = from_place
    row.to_place = to_place
    row.candidates = [item.model_dump() for item in candidates]
    row.need_clarification = need
    row.questions = questions
    row.selected_slug = None
    row.resolved_office_id = None
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _guide(session: Session, row: Case, procedure: Procedure) -> GuideOut:
    office_row = session.get(Office, row.resolved_office_id) if row.resolved_office_id else None
    related: list[RelatedOut] = []
    for slug in procedure.related_slugs:
        rel = session.get(Procedure, slug)
        if rel:
            related.append(RelatedOut(slug=rel.slug, title=rel.title))
    office_out = None
    if office_row:
        office_out = OfficeOut(
            id=office_row.id,
            name=office_row.name,
            address=office_row.address,
            phone=office_row.phone,
            lat=office_row.lat,
            lng=office_row.lng,
            source_url=office_row.source_url,
        )
    return GuideOut(
        case_id=row.id,
        selected_slug=procedure.slug,
        title=procedure.title,
        plain_summary=procedure.plain_summary,
        steps=procedure.steps,
        required_documents=procedure.required_documents,
        institution=procedure.institution,
        channel=procedure.channel,
        jurisdiction_rule=procedure.jurisdiction_rule,
        fees_note=procedure.fees_note,
        related=related,
        source_name=procedure.source_name,
        source_url=procedure.source_url,
        last_verified_at=procedure.last_verified_at,
        office=office_out,
        office_missing=office_out is None,
        disclaimer=DISCLAIMER,
    )


@router.post("/cases", response_model=CaseOut)
def create_case(body: CaseCreate, session: Session = Depends(get_session)) -> CaseOut:
    ids = [str(item) for item in body.document_ids]
    row = Case(
        raw_text=body.text,
        document_ids=ids,
        extra_answers={},
        candidates=[],
        questions=[],
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return _case_out(_run_match(session, row, body.text))


@router.post("/cases/{case_id}/retry", response_model=CaseOut)
def retry_case(case_id: UUID, body: RetryBody, session: Session = Depends(get_session)) -> CaseOut:
    row = session.get(Case, str(case_id))
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    return _case_out(_run_match(session, row, body.text))


@router.post("/cases/{case_id}/clarify", response_model=CaseOut)
def clarify_case(case_id: UUID, body: ClarifyBody, session: Session = Depends(get_session)) -> CaseOut:
    row = session.get(Case, str(case_id))
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    row.extra_answers = {**row.extra_answers, **body.answers}
    extra = " ".join(str(value) for value in body.answers.values())
    combined = f"{row.raw_text}\n{extra}".strip()
    return _case_out(_run_match(session, row, combined))


@router.post("/cases/{case_id}/select", response_model=GuideOut)
def select_procedure(case_id: UUID, body: SelectBody, session: Session = Depends(get_session)) -> GuideOut:
    row = session.get(Case, str(case_id))
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    procedure = session.get(Procedure, body.slug)
    if not procedure:
        raise HTTPException(status_code=404, detail="Procedure not found")
    office = resolve_office(
        session,
        institution=procedure.institution,
        jurisdiction_rule=procedure.jurisdiction_rule,
        from_place=row.from_place,
        to_place=row.to_place,
    )
    row.selected_slug = procedure.slug
    row.resolved_office_id = office.id if office else None
    session.add(row)
    session.commit()
    session.refresh(row)
    return _guide(session, row, procedure)


@router.get("/cases/{case_id}/guide", response_model=GuideOut)
def get_guide(case_id: UUID, session: Session = Depends(get_session)) -> GuideOut:
    row = session.get(Case, str(case_id))
    if not row or not row.selected_slug:
        raise HTTPException(status_code=404, detail="Case or selection not found")
    procedure = session.get(Procedure, row.selected_slug)
    if not procedure:
        raise HTTPException(status_code=404, detail="Procedure not found")
    return _guide(session, row, procedure)


@router.post("/cases/{case_id}/documents", response_model=DocumentOut)
async def attach_document(
    case_id: UUID,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> DocumentOut:
    row = session.get(Case, str(case_id))
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    upload_root = Path(settings.upload_dir)
    upload_root.mkdir(parents=True, exist_ok=True)
    stored = Document(
        case_id=row.id,
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
    row.document_ids = [*row.document_ids, str(stored.id)]
    session.add(stored)
    session.add(row)
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


@router.get("/cases/{case_id}/document-status", response_model=DocumentStatusOut)
def document_status(case_id: UUID, session: Session = Depends(get_session)) -> DocumentStatusOut:
    row = session.get(Case, str(case_id))
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    if not row.selected_slug:
        raise HTTPException(status_code=400, detail="Select a procedure first")
    procedure = session.get(Procedure, row.selected_slug)
    if not procedure:
        raise HTTPException(status_code=404, detail="Procedure not found")
    attached = session.scalars(select(Document).where(Document.case_id == row.id)).all()
    items: list[DocumentStatusItem] = []
    for req in procedure.required_documents:
        doc_type = str(req.get("type"))
        match = next((doc for doc in attached if doc.extracted_type == doc_type), None)
        if match is None:
            items.append(
                DocumentStatusItem(
                    type=doc_type,
                    status="missing",
                    message="Nije priložen. Vision ekstrakcija je Faza 3 — ovo je checklist.",
                    how_to_obtain=str(req.get("how_to_obtain") or ""),
                )
            )
            continue
        items.append(
            DocumentStatusItem(
                type=doc_type,
                status=match.status or "unreadable",
                message="Priložen fajl; provera roka dolazi u Fazi 3.",
                how_to_obtain=str(req.get("how_to_obtain") or ""),
                document_id=match.id,
                extracted_expiry=match.extracted_expiry,
            )
        )
    return DocumentStatusOut(case_id=row.id, items=items, disclaimer=DISCLAIMER, as_of=date.today())
