import asyncio
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import SessionLocal, get_session
from app.deps import get_optional_user
from app.llm import synthesize_speech_openai
from app.models import Case, Document, Office, Procedure, User
from app.schemas import (
    DISCLAIMER,
    CaseCreate,
    CaseOut,
    CandidateOut,
    ClarifyBody,
    DocumentOut,
    DocumentStatusOut,
    GuideOut,
    OfficeOut,
    RelatedOut,
    RetryBody,
    SelectBody,
)
from app.services.catalog import (
    apply_account_municipality,
    extract_from_to,
    missing_office_reason,
    resolve_office,
)
from app.services.extraction import (
    build_checklist,
    collect_pool,
    documents_for_case,
    run_extraction,
    scan_note_for_docs,
)
from app.services.matching import load_catalog_procs, rank_procedures
from app.services.speech import script_from_guide
from app.services import storage

router = APIRouter(tags=["cases"])


def _case_out(row: Case) -> CaseOut:
    return CaseOut(
        case_id=row.id,
        candidates=[CandidateOut.model_validate(item) for item in row.candidates],
        need_clarification=row.need_clarification,
        questions=row.questions,
        from_place=row.from_place,
        to_place=row.to_place,
        text=row.raw_text,
    )


def _run_match(
    case_id: str,
    text: str,
    *,
    persist_text: bool,
    use_demo_cache: bool,
) -> Case:
    with SessionLocal() as session:
        row = session.get(Case, case_id)
        if not row:
            raise HTTPException(status_code=404, detail="Case not found")
        from_place, to_place = extract_from_to(session, text)
        by_slug = load_catalog_procs(session)
        scan_note = scan_note_for_docs(documents_for_case(session, row))
        session.commit()

    rank_text = f"{text}\n\n{scan_note}".strip() if scan_note else text
    candidates, need, questions = rank_procedures(
        by_slug,
        rank_text,
        use_demo_cache=use_demo_cache and not scan_note,
    )

    with SessionLocal() as session:
        row = session.get(Case, case_id)
        if not row:
            raise HTTPException(status_code=404, detail="Case not found")
        if persist_text:
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
        office_missing_reason=missing_office_reason(
            jurisdiction_rule=procedure.jurisdiction_rule,
            from_place=row.from_place,
            to_place=row.to_place,
            office=office_row,
        ),
        disclaimer=DISCLAIMER,
    )


@router.post("/cases", response_model=CaseOut)
async def create_case(
    body: CaseCreate,
    session: Session = Depends(get_session),
    user: User | None = Depends(get_optional_user),
) -> CaseOut:
    storage.purge_expired_documents(session)
    ids: list[str] = []
    for item in body.document_ids:
        doc = session.get(Document, str(item))
        if not doc or not storage.allowed_document(doc, user_id=user.id if user else None, case_id=None):
            raise HTTPException(status_code=404, detail="Document not found")
        ids.append(str(doc.id))
    row = Case(
        raw_text=body.text,
        document_ids=ids,
        extra_answers={},
        candidates=[],
        questions=[],
        user_id=user.id if user else None,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    if user:
        for doc_id in ids:
            doc = session.get(Document, doc_id)
            if doc:
                doc.case_id = row.id
                session.add(doc)
        session.commit()
    case_id = str(row.id)
    text = body.text
    session.close()
    matched = await asyncio.to_thread(
        _run_match,
        case_id,
        text,
        persist_text=True,
        use_demo_cache=True,
    )
    return _case_out(matched)


@router.get("/cases/{case_id}", response_model=CaseOut)
def get_case(case_id: UUID, session: Session = Depends(get_session)) -> CaseOut:
    row = session.get(Case, str(case_id))
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    return _case_out(row)


@router.post("/cases/{case_id}/retry", response_model=CaseOut)
async def retry_case(
    case_id: UUID, body: RetryBody, session: Session = Depends(get_session)
) -> CaseOut:
    row = session.get(Case, str(case_id))
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    row.extra_answers = {}
    session.add(row)
    session.commit()
    case_id = str(row.id)
    text = body.text
    session.close()
    matched = await asyncio.to_thread(
        _run_match,
        case_id,
        text,
        persist_text=True,
        use_demo_cache=False,
    )
    return _case_out(matched)


@router.post("/cases/{case_id}/clarify", response_model=CaseOut)
async def clarify_case(
    case_id: UUID, body: ClarifyBody, session: Session = Depends(get_session)
) -> CaseOut:
    row = session.get(Case, str(case_id))
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    row.extra_answers = {**(row.extra_answers or {}), **body.answers}
    extra = " ".join(str(value) for value in body.answers.values())
    combined = f"{row.raw_text}\n{extra}".strip()
    session.add(row)
    session.commit()
    case_id = str(row.id)
    session.close()
    matched = await asyncio.to_thread(
        _run_match,
        case_id,
        combined,
        persist_text=False,
        use_demo_cache=False,
    )
    return _case_out(matched)


@router.post("/cases/{case_id}/select", response_model=GuideOut)
def select_procedure(
    case_id: UUID,
    body: SelectBody,
    session: Session = Depends(get_session),
    user: User | None = Depends(get_optional_user),
) -> GuideOut:
    row = session.get(Case, str(case_id))
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    procedure = session.get(Procedure, body.slug)
    if not procedure:
        raise HTTPException(status_code=404, detail="Procedure not found")
    from_place, to_place = apply_account_municipality(
        session,
        jurisdiction_rule=procedure.jurisdiction_rule,
        from_place=row.from_place,
        to_place=row.to_place,
        municipality=user.municipality if user else None,
    )
    row.from_place = from_place
    row.to_place = to_place
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
    user: User | None = Depends(get_optional_user),
) -> DocumentOut:
    row = session.get(Case, str(case_id))
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    if row.user_id and (user is None or row.user_id != user.id):
        raise HTTPException(status_code=403, detail="Not allowed to attach to this case")
    data = await file.read(storage.MAX_UPLOAD_BYTES + 1)
    user_id = user.id if user else None
    try:
        path = storage.save_upload(data, user_id=user_id, case_id=row.id)
    except ValueError:
        raise HTTPException(status_code=413, detail="File too large (max 8 MB)")
    stored = Document(
        case_id=row.id,
        user_id=user_id,
        original_filename=file.filename or "upload.bin",
        storage_path=path,
        content_type=file.content_type or "application/octet-stream",
        purge_at=None if user else storage.guest_purge_at(),
    )
    session.add(stored)
    session.commit()
    session.refresh(stored)
    row.document_ids = [*row.document_ids, str(stored.id)]
    session.add(row)
    session.commit()
    session.refresh(stored)
    doc_id = str(stored.id)
    await asyncio.to_thread(run_extraction, doc_id)
    session.expire_all()
    stored = session.get(Document, doc_id)
    if not stored:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentOut(
        id=stored.id,
        original_filename=stored.original_filename,
        content_type=stored.content_type,
        case_id=stored.case_id,
        user_id=stored.user_id,
        extracted_type=stored.extracted_type,
        extracted_expiry=stored.extracted_expiry,
        status=stored.status,
        purge_at=stored.purge_at,
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
    attached, pool = collect_pool(session, row)
    items = build_checklist(
        required_documents=procedure.required_documents,
        pool=pool,
        attached=attached,
        as_of=date.today(),
    )
    return DocumentStatusOut(case_id=row.id, items=items, disclaimer=DISCLAIMER, as_of=date.today())


@router.post("/cases/{case_id}/speech")
async def speak_guide(
    case_id: UUID,
    body: SelectBody,
    session: Session = Depends(get_session),
    user: User | None = Depends(get_optional_user),
) -> Response:
    guide = select_procedure(case_id, body, session, user)
    row = session.get(Case, str(case_id))
    if not row or not row.selected_slug:
        raise HTTPException(status_code=404, detail="Case or selection not found")
    procedure = session.get(Procedure, row.selected_slug)
    if not procedure:
        raise HTTPException(status_code=404, detail="Procedure not found")
    attached, pool = collect_pool(session, row)
    items = build_checklist(
        required_documents=procedure.required_documents,
        pool=pool,
        attached=attached,
        as_of=date.today(),
    )
    script = script_from_guide(guide, items)
    try:
        audio = await asyncio.to_thread(synthesize_speech_openai, script)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Glas trenutno nije dostupan")
    return Response(content=audio, media_type="audio/mpeg")
