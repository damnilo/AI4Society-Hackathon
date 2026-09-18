from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.types import JSON


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Place(Base):
    __tablename__ = "places"

    id = mapped_column(String(64), primary_key=True)
    kind = mapped_column(String(32), nullable=False)
    parent_id = mapped_column(ForeignKey("places.id"), nullable=True)
    name_lat = mapped_column(String(128), nullable=False)
    name_cyr = mapped_column(String(128), nullable=False)
    aliases = mapped_column(JSON, nullable=False, default=list)


class Office(Base):
    __tablename__ = "offices"

    id = mapped_column(String(64), primary_key=True)
    institution = mapped_column(String(32), nullable=False)
    covers_place_id = mapped_column(ForeignKey("places.id"), nullable=False)
    covers_municipality = mapped_column(String(64), nullable=True)
    covers_district = mapped_column(String(64), nullable=True)
    name = mapped_column(String(256), nullable=False)
    address = mapped_column(String(256), nullable=False)
    phone = mapped_column(String(64), nullable=False)
    lat = mapped_column(Float, nullable=False)
    lng = mapped_column(Float, nullable=False)
    source_url = mapped_column(String(512), nullable=False)
    notes = mapped_column(Text, nullable=False, default="")


class Procedure(Base):
    __tablename__ = "procedures"

    slug = mapped_column(String(128), primary_key=True)
    title = mapped_column(String(256), nullable=False)
    plain_summary = mapped_column(Text, nullable=False)
    legal_excerpt = mapped_column(Text, nullable=False)
    intent_examples = mapped_column(JSON, nullable=False, default=list)
    steps = mapped_column(JSON, nullable=False, default=list)
    required_documents = mapped_column(JSON, nullable=False, default=list)
    institution = mapped_column(String(32), nullable=False)
    jurisdiction_rule = mapped_column(String(64), nullable=False)
    channel = mapped_column(String(32), nullable=False)
    related_slugs = mapped_column(JSON, nullable=False, default=list)
    fees_note = mapped_column(Text, nullable=False, default="")
    source_name = mapped_column(String(256), nullable=False)
    source_url = mapped_column(String(512), nullable=False)
    last_verified_at = mapped_column(String(32), nullable=False)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email"),)

    id = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email = mapped_column(String(256), nullable=False)
    password_hash = mapped_column(String(256), nullable=False)
    name = mapped_column(String(128), nullable=False, default="")
    municipality = mapped_column(String(64), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=utcnow)


class Case(Base):
    __tablename__ = "cases"

    id = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = mapped_column(ForeignKey("users.id"), nullable=True)
    raw_text = mapped_column(Text, nullable=False)
    extra_answers = mapped_column(JSON, nullable=False, default=dict)
    from_place = mapped_column(String(64), nullable=True)
    to_place = mapped_column(String(64), nullable=True)
    document_ids = mapped_column(JSON, nullable=False, default=list)
    candidates = mapped_column(JSON, nullable=False, default=list)
    need_clarification = mapped_column(Boolean, nullable=False, default=False)
    questions = mapped_column(JSON, nullable=False, default=list)
    selected_slug = mapped_column(ForeignKey("procedures.slug"), nullable=True)
    resolved_office_id = mapped_column(ForeignKey("offices.id"), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=utcnow)


class Document(Base):
    __tablename__ = "documents"

    id = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = mapped_column(ForeignKey("users.id"), nullable=True)
    case_id = mapped_column(ForeignKey("cases.id"), nullable=True)
    original_filename = mapped_column(String(256), nullable=False)
    storage_path = mapped_column(String(512), nullable=False)
    content_type = mapped_column(String(128), nullable=False, default="application/octet-stream")
    extracted_type = mapped_column(String(64), nullable=True)
    extracted_expiry = mapped_column(String(32), nullable=True)
    extracted_name = mapped_column(String(256), nullable=True)
    extracted_issuing_place = mapped_column(String(128), nullable=True)
    extracted_address = mapped_column(String(256), nullable=True)
    status = mapped_column(String(32), nullable=True)
    purge_at = mapped_column(DateTime(timezone=True), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=utcnow)
