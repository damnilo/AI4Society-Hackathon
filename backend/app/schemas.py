from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


DISCLAIMER = (
    "Putokaz nije eUprava i ne podnosi zahtev. "
    "Provera dokumenata nije pravna overa originala — samo polja sa skena "
    "(kompletnost i rok)."
)

GDPR_NOTE = (
    "Nalog je novčanik: dokumenta su šifrovana i vidi ih samo vlasnik. "
    "Prilog gosta uz zahtev se briše posle 48 sati ako se nalogom ne preuzme. "
    "Fajlovi se ne šalju u MUP i nisu pravna overa."
)


class CandidateOut(BaseModel):
    slug: str
    title: str
    plain_summary: str
    score: float
    rationale: str


class CaseCreate(BaseModel):
    text: str = Field(min_length=1)
    document_ids: list[UUID] = Field(default_factory=list)


class CaseOut(BaseModel):
    case_id: UUID
    candidates: list[CandidateOut]
    need_clarification: bool
    questions: list[str]
    from_place: Optional[str] = None
    to_place: Optional[str] = None
    text: str = ""
    extra_answers: dict[str, Any] = Field(default_factory=dict)


class RetryBody(BaseModel):
    text: str = Field(min_length=1)


class ClarifyBody(BaseModel):
    answers: dict[str, Any]


class SelectBody(BaseModel):
    slug: str


class OfficeOut(BaseModel):
    id: str
    name: str
    address: str
    phone: str
    lat: float
    lng: float
    source_url: str


class RelatedOut(BaseModel):
    slug: str
    title: str


class GuideOut(BaseModel):
    case_id: UUID
    selected_slug: str
    title: str
    plain_summary: str
    steps: list[dict[str, Any]]
    required_documents: list[dict[str, Any]]
    institution: str
    channel: str
    jurisdiction_rule: str
    fees_note: str
    related: list[RelatedOut]
    source_name: str
    source_url: str
    last_verified_at: str
    office: Optional[OfficeOut] = None
    office_missing: bool = False
    office_missing_reason: Optional[str] = None
    legal_excerpt: str = ""
    disclaimer: str = DISCLAIMER


class DocumentOut(BaseModel):
    id: UUID
    original_filename: str
    content_type: str
    case_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    extracted_type: Optional[str] = None
    extracted_expiry: Optional[str] = None
    status: Optional[str] = None
    purge_at: Optional[datetime] = None


class DocumentStatusItem(BaseModel):
    type: str
    status: str
    message: str
    how_to_obtain: str = ""
    document_id: Optional[UUID] = None
    extracted_expiry: Optional[str] = None


class DocumentStatusOut(BaseModel):
    case_id: UUID
    items: list[DocumentStatusItem]
    disclaimer: str = DISCLAIMER
    as_of: date


class AuthRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = ""
    municipality: Optional[str] = None


class AuthLogin(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    name: str


class RefreshBody(BaseModel):
    refresh_token: str


class ClaimBody(BaseModel):
    case_id: UUID


class MeOut(BaseModel):
    user_id: str
    email: str
    name: str
    municipality: Optional[str] = None
    retention_hours: int
    gdpr_note: str


class MePatch(BaseModel):
    municipality: Optional[str] = None


class DashboardOut(BaseModel):
    user_id: UUID
    email: str
    name: str
    documents: list[DocumentOut]
    cases: list[CaseOut]


class HealthOut(BaseModel):
    ok: bool
    db: str
    catalog: dict[str, int]


class LlmHealthOut(BaseModel):
    configured: bool
    ok: bool
    detail: str
    model: str
    openai_configured: bool = False
    openai_ok: bool = False
    openai_detail: str = ""
    openai_model: str = ""
