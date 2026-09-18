"""Store files encrypted at rest. Do not log filenames or emails."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Document

MAX_UPLOAD_BYTES = 8 * 1024 * 1024


def _key_for(owner: str) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"putokaz-docs-v1",
        info=owner.encode("utf-8"),
    ).derive(settings.master_key.encode("utf-8"))


def owner_label(*, user_id: str | None, case_id: str | None) -> str:
    if user_id:
        return f"user:{user_id}"
    if case_id:
        return f"guest:{case_id}"
    return "guest:unknown"


def encrypt_bytes(data: bytes, owner: str) -> bytes:
    nonce = os.urandom(12)
    return nonce + AESGCM(_key_for(owner)).encrypt(nonce, data, None)


def decrypt_bytes(blob: bytes, owner: str) -> bytes:
    nonce, ciphertext = blob[:12], blob[12:]
    return AESGCM(_key_for(owner)).decrypt(nonce, ciphertext, None)


def save_upload(data: bytes, *, user_id: str | None, case_id: str | None) -> str:
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("file_too_large")
    root = Path(settings.upload_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{uuid4().hex}.enc"
    owner = owner_label(user_id=user_id, case_id=case_id)
    path.write_bytes(encrypt_bytes(data, owner))
    return str(path)


def reencrypt_for_user(doc: Document, user_id: str) -> None:
    if not doc.storage_path:
        return
    path = Path(doc.storage_path)
    if not path.exists():
        return
    blob = path.read_bytes()
    old_owner = owner_label(user_id=doc.user_id, case_id=doc.case_id)
    try:
        plain = decrypt_bytes(blob, old_owner)
    except Exception:
        plain = blob
    new_owner = owner_label(user_id=user_id, case_id=doc.case_id)
    path.write_bytes(encrypt_bytes(plain, new_owner))


def delete_file(storage_path: str | None) -> None:
    if not storage_path:
        return
    path = Path(storage_path)
    if path.exists():
        path.unlink()


def guest_purge_at() -> datetime:
    hours = max(1, settings.document_retention_hours)
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def purge_expired_documents(session: Session) -> int:
    now = datetime.now(timezone.utc)
    rows = session.scalars(select(Document).where(Document.purge_at.is_not(None))).all()
    count = 0
    for doc in rows:
        if _as_utc(doc.purge_at) > now:  # type: ignore[arg-type]
            continue
        delete_file(doc.storage_path)
        session.delete(doc)
        count += 1
    if count:
        session.commit()
    return count


def allowed_document(doc: Document, *, user_id: str | None, case_id: str | None) -> bool:
    if user_id and doc.user_id == user_id:
        return True
    if case_id and doc.case_id == case_id and doc.user_id is None:
        return True
    return False
