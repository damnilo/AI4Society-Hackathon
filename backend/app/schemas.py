from datetime import date
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


DISCLAIMER = (
    "Putokaz nije eUprava i ne podnosi zahtev. "
    "Provera dokumenata nije pravna overa originala — samo polja sa skena "
    "(kompletnost i rok)."
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
    disclaimer: str = DISCLAIMER


class DocumentOut(BaseModel):
    id: UUID
    original_filename: str
    content_type: str
    case_id: Optional[UUID] = None
    extracted_type: Optional[str] = None
    extracted_expiry: Optional[str] = None
    status: Optional[str] = None


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


class RefreshBody(BaseModel):
    refresh_token: str


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
