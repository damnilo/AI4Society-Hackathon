"""Vision extraction and checklist status. Not legal verification."""

from __future__ import annotations

import json
import re
from datetime import date
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.llm import extract_document_openai_vision
from app.models import Case, Document
from app.schemas import DocumentStatusItem
from app.services import storage

KNOWN_TYPES = frozenset(
    {
        "licna_karta",
        "pasos",
        "vozacka_dozvola",
        "izvod_rodjeni",
        "uverenje_drzavljanstvo",
        "zdravstvena_isprava",
        "saobracajna_dozvola",
        "polisa_osiguranja",
        "tehnicki_pregled",
        "uplatnica_euprava",
        "dokaz_pravnog_osnova",
        "saglasnost_vlasnika",
        "saglasnost_roditelja",
        "lekarsko_vozac",
        "dokaz_ispit_voznje",
        "apr_obrazac",
    }
)
IDENTITY_TYPES = frozenset({"licna_karta", "pasos", "vozacka_dozvola"})
DOC_LABELS = {
    "licna_karta": "lična karta",
    "pasos": "pasoš",
    "vozacka_dozvola": "vozačka dozvola",
    "izvod_rodjeni": "izvod iz matične knjige rođenih",
    "uverenje_drzavljanstvo": "uverenje o državljanstvu",
    "zdravstvena_isprava": "zdravstvena isprava",
    "saobracajna_dozvola": "saobraćajna dozvola",
    "polisa_osiguranja": "polisa osiguranja",
    "tehnicki_pregled": "tehnički pregled",
    "uplatnica_euprava": "uplatnica sa eUprave",
    "dokaz_pravnog_osnova": "dokaz o stanu",
    "saglasnost_vlasnika": "saglasnost vlasnika",
    "saglasnost_roditelja": "saglasnost roditelja",
    "lekarsko_vozac": "lekarsko uverenje",
    "dokaz_ispit_voznje": "dokaz o položenom ispitu",
    "apr_obrazac": "APR obrazac",
}
UNREADABLE_MSG = "Sken nije čitljiv. Pošaljite fotografiju isprave (jpg ili png)."
SCAN_NEXT_MSG = "Provera skena je sledeći korak"
MISSING_MSG = "Nije priložen."
NOT_LEGAL = "Provera je samo rok i kompletnost sa skena, nije pravna overa."


class _DocView(Protocol):
    id: object
    extracted_type: str | None
    extracted_expiry: str | None
    status: str | None


def sniff_media(data: bytes, content_type: str | None = None) -> str:
    if data.startswith(b"%PDF"):
        return "application/pdf"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"RIFF") and b"WEBP" in data[:16]:
        return "image/webp"
    if data.startswith(b"GIF8"):
        return "image/gif"
    guessed = (content_type or "").split(";")[0].strip().lower()
    if guessed in {"image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf"}:
        return guessed
    return "application/octet-stream"


def is_image_mime(mime: str) -> bool:
    return mime in {"image/jpeg", "image/png", "image/webp", "image/gif"}


def parse_expiry(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none"}:
        return None
    match = re.search(r"(20\d{2}|19\d{2})[-./](\d{1,2})[-./](\d{1,2})", text)
    if match:
        year, month, day = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return None
    match = re.search(r"(\d{1,2})[-./](\d{1,2})[-./](20\d{2}|19\d{2})", text)
    if match:
        day, month, year = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return None
    return None


def expiry_is_past(expiry: str | None, as_of: date) -> bool:
    if not expiry:
        return False
    try:
        parsed = date.fromisoformat(expiry[:10])
    except ValueError:
        return False
    return parsed < as_of


def normalize_type(value: object) -> str | None:
    if value is None:
        return None
    from app.services.matching import normalize as fold_text

    raw = fold_text(str(value)).strip().replace(" ", "_").replace("-", "_")
    aliases = {
        "lk": "licna_karta",
        "licna": "licna_karta",
        "id_card": "licna_karta",
        "passport": "pasos",
        "passos": "pasos",
        "drivers_license": "vozacka_dozvola",
        "vozacka": "vozacka_dozvola",
    }
    mapped = aliases.get(raw, raw)
    if mapped in KNOWN_TYPES:
        return mapped
    return None


def parse_vision_payload(raw: str) -> dict[str, object]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            return {"readable": False}
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return {"readable": False}
    if not isinstance(data, dict):
        return {"readable": False}
    return data


def doc_label(doc_type: str) -> str:
    return DOC_LABELS.get(doc_type, doc_type.replace("_", " "))


def scan_note_for_docs(docs: list[Document]) -> str:
    compact: list[dict[str, str | None]] = []
    for doc in docs:
        if not doc.extracted_type and not doc.status:
            continue
        compact.append(
            {
                "type": doc.extracted_type,
                "expiry": doc.extracted_expiry,
                "status": doc.status,
            }
        )
    if not compact:
        return ""
    return "[skenovi] " + json.dumps(compact, ensure_ascii=False)


def documents_for_case(session: Session, row: Case) -> list[Document]:
    attached = session.scalars(select(Document).where(Document.case_id == row.id)).all()
    found: list[Document] = list(attached)
    seen = {doc.id for doc in found}
    for doc_id in row.document_ids or []:
        if doc_id in seen:
            continue
        doc = session.get(Document, str(doc_id))
        if doc and doc.id not in seen:
            found.append(doc)
            seen.add(doc.id)
    return found


def apply_vision_result(doc: Document, payload: dict[str, object], as_of: date) -> None:
    readable = payload.get("readable")
    if readable is False or str(readable).lower() == "false":
        doc.extracted_type = None
        doc.extracted_expiry = None
        doc.status = "unreadable"
        return
    doc_type = normalize_type(payload.get("type"))
    expiry = parse_expiry(payload.get("expiry"))
    name = payload.get("name")
    place = payload.get("issuing_place")
    address = payload.get("address")
    doc.extracted_type = doc_type
    doc.extracted_expiry = expiry
    doc.extracted_name = str(name).strip() if isinstance(name, str) and name.strip() else None
    doc.extracted_issuing_place = (
        str(place).strip() if isinstance(place, str) and place.strip() else None
    )
    doc.extracted_address = (
        str(address).strip() if isinstance(address, str) and address.strip() else None
    )
    if not doc_type:
        doc.status = "unreadable"
        return
    doc.status = "expired" if expiry_is_past(expiry, as_of) else "complete"


def run_extraction(document_id: str) -> None:
    with SessionLocal() as session:
        doc = session.get(Document, document_id)
        if not doc or not doc.storage_path:
            return
        try:
            plain = storage.load_plaintext(doc)
        except OSError:
            doc.status = "unreadable"
            session.add(doc)
            session.commit()
            return
        mime = sniff_media(plain, doc.content_type)
        if not is_image_mime(mime):
            doc.extracted_type = None
            doc.extracted_expiry = None
            doc.status = "unreadable"
            session.add(doc)
            session.commit()
            return
        if not settings.openai_api_key:
            session.commit()
            return
        try:
            raw_wrap = extract_document_openai_vision(plain, mime=mime)
            raw = str(raw_wrap.get("raw") or "")
            payload = parse_vision_payload(raw)
        except RuntimeError:
            doc.status = "unreadable"
            session.add(doc)
            session.commit()
            return
        apply_vision_result(doc, payload, date.today())
        session.add(doc)
        session.commit()


def checklist_item(
    *,
    doc_type: str,
    how_to_obtain: str,
    pool: list[_DocView],
    attached: list[_DocView],
    as_of: date,
) -> DocumentStatusItem:
    match = next((doc for doc in pool if doc.extracted_type == doc_type), None)
    if match is not None:
        if match.status == "unreadable":
            return DocumentStatusItem(
                type=doc_type,
                status="unreadable",
                message=UNREADABLE_MSG,
                how_to_obtain=how_to_obtain,
                document_id=match.id,  # type: ignore[arg-type]
                extracted_expiry=match.extracted_expiry,
            )
        if expiry_is_past(match.extracted_expiry, as_of):
            when = match.extracted_expiry or ""
            return DocumentStatusItem(
                type=doc_type,
                status="expired",
                message=f"Na skenu piše da važi do {when}. {NOT_LEGAL}",
                how_to_obtain=how_to_obtain,
                document_id=match.id,  # type: ignore[arg-type]
                extracted_expiry=match.extracted_expiry,
            )
        return DocumentStatusItem(
            type=doc_type,
            status="complete",
            message=f"Sken ovog tipa je priložen. {NOT_LEGAL}",
            how_to_obtain=how_to_obtain,
            document_id=match.id,  # type: ignore[arg-type]
            extracted_expiry=match.extracted_expiry,
        )

    untyped = [
        doc for doc in attached if not doc.extracted_type and doc.status != "unreadable"
    ]
    unread = [doc for doc in attached if doc.status == "unreadable"]
    typed_on_case = [doc for doc in attached if doc.extracted_type]
    if untyped:
        return DocumentStatusItem(
            type=doc_type,
            status="missing",
            message=SCAN_NEXT_MSG,
            how_to_obtain=how_to_obtain,
        )
    if unread and not typed_on_case:
        return DocumentStatusItem(
            type=doc_type,
            status="unreadable",
            message=UNREADABLE_MSG,
            how_to_obtain=how_to_obtain,
            document_id=unread[0].id,  # type: ignore[arg-type]
        )
    if doc_type in IDENTITY_TYPES:
        other = next(
            (
                doc
                for doc in pool
                if doc.extracted_type in IDENTITY_TYPES and doc.extracted_type != doc_type
            ),
            None,
        )
        if other is not None and other.extracted_type:
            return DocumentStatusItem(
                type=doc_type,
                status="mismatch",
                message=(
                    f"Na skenu je {doc_label(other.extracted_type)}, "
                    f"ne {doc_label(doc_type)}. {NOT_LEGAL}"
                ),
                how_to_obtain=how_to_obtain,
                document_id=other.id,  # type: ignore[arg-type]
                extracted_expiry=other.extracted_expiry,
            )
    return DocumentStatusItem(
        type=doc_type,
        status="missing",
        message=MISSING_MSG,
        how_to_obtain=how_to_obtain,
    )


def build_checklist(
    *,
    required_documents: list[dict[str, object]],
    pool: list[Document],
    attached: list[Document],
    as_of: date,
) -> list[DocumentStatusItem]:
    items: list[DocumentStatusItem] = []
    for req in required_documents:
        items.append(
            checklist_item(
                doc_type=str(req.get("type")),
                how_to_obtain=str(req.get("how_to_obtain") or ""),
                pool=pool,
                attached=attached,
                as_of=as_of,
            )
        )
    return items


def collect_pool(session: Session, row: Case) -> tuple[list[Document], list[Document]]:
    attached = session.scalars(select(Document).where(Document.case_id == row.id)).all()
    pool: list[Document] = list(attached)
    seen = {doc.id for doc in pool}
    if row.user_id:
        wallet = session.scalars(select(Document).where(Document.user_id == row.user_id)).all()
        for doc in wallet:
            if doc.id not in seen:
                pool.append(doc)
                seen.add(doc.id)
    return attached, pool
