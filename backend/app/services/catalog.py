from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Office, Place, Procedure

ROOT = Path(__file__).resolve().parents[2]
SEED_DIR = ROOT / "seed"


def _apply(row_obj: object, data: dict) -> None:
    for key, value in data.items():
        setattr(row_obj, key, value)


def seed_catalog(session: Session) -> None:
    """Upsert seed JSON so Phase 2 catalog tweaks apply without deleting the DB."""
    _seed_places(session)
    _seed_offices(session)
    _seed_procedures(session)
    session.commit()


def catalog_for_matching(session: Session) -> list[dict[str, object]]:
    """Compact catalog for xAI. No streets, offices, or legal excerpts."""
    rows = session.scalars(select(Procedure)).all()
    return [
        {
            "slug": row.slug,
            "title": row.title,
            "plain_summary": row.plain_summary,
            "intent_examples": row.intent_examples,
        }
        for row in rows
    ]


def _seed_places(session: Session) -> None:
    rows: list[dict] = json.loads((SEED_DIR / "municipalities.json").read_text(encoding="utf-8"))
    remaining = list(rows)
    safety = 0
    while remaining and safety < 50:
        safety += 1
        next_round: list[dict] = []
        for row in remaining:
            parent = row.get("parent_id")
            if parent and session.get(Place, parent) is None:
                next_round.append(row)
                continue
            existing = session.get(Place, row["id"])
            payload = {
                "id": row["id"],
                "kind": row["kind"],
                "parent_id": row.get("parent_id"),
                "name_lat": row["name_lat"],
                "name_cyr": row["name_cyr"],
                "aliases": row.get("aliases") or [],
            }
            if existing:
                _apply(existing, payload)
            else:
                session.add(Place(**payload))
            session.flush()
        remaining = next_round
    if remaining:
        raise RuntimeError(f"Ne mogu da uvežem mesta: {[r['id'] for r in remaining]}")


def _seed_offices(session: Session) -> None:
    rows: list[dict] = json.loads((SEED_DIR / "offices.json").read_text(encoding="utf-8"))
    for row in rows:
        existing = session.get(Office, row["id"])
        if existing:
            _apply(existing, row)
        else:
            session.add(Office(**row))


def _seed_procedures(session: Session) -> None:
    rows: list[dict] = json.loads((SEED_DIR / "procedures.json").read_text(encoding="utf-8"))
    for row in rows:
        existing = session.get(Procedure, row["slug"])
        if existing:
            _apply(existing, row)
        else:
            session.add(Procedure(**row))


def extract_from_to(session: Session, text: str) -> tuple[str | None, str | None]:
    from app.services.matching import normalize

    normalized = normalize(text)
    hits: list[tuple[int, Place]] = []
    for place in session.scalars(select(Place)).all():
        for name in [place.id, place.name_lat, place.name_cyr, *place.aliases]:
            token = normalize(name)
            if len(token) < 3:
                continue
            idx = normalized.find(token)
            if idx >= 0:
                hits.append((idx, place))
                break
    hits.sort(key=lambda item: item[0])
    unique: list[Place] = []
    seen: set[str] = set()
    for _, place in hits:
        if place.id in seen:
            continue
        seen.add(place.id)
        unique.append(place)
    if len(unique) >= 2:
        return unique[0].id, unique[-1].id
    if len(unique) == 1:
        return None, unique[0].id
    return None, None


def ancestors(session: Session, place_id: str) -> list[str]:
    chain: list[str] = []
    current = session.get(Place, place_id)
    safety = 0
    while current and safety < 10:
        chain.append(current.id)
        if not current.parent_id:
            break
        current = session.get(Place, current.parent_id)
        safety += 1
    return chain


def place_id_from_label(session: Session, label: str | None) -> str | None:
    """Map nalog/UI label (Beograd, pirot, Niš) to places.id."""
    if not label or not str(label).strip():
        return None
    from_place, to_place = extract_from_to(session, str(label).strip())
    return to_place or from_place


def apply_account_municipality(
    session: Session,
    *,
    jurisdiction_rule: str,
    from_place: str | None,
    to_place: str | None,
    municipality: str | None,
) -> tuple[str | None, str | None]:
    """Text places always win. Account city only if extract found none."""
    if from_place or to_place:
        return from_place, to_place
    place_id = place_id_from_label(session, municipality)
    if not place_id:
        return from_place, to_place
    if jurisdiction_rule == "new_residence":
        return from_place, place_id
    return place_id, to_place or place_id


def office_target(
    *,
    jurisdiction_rule: str,
    from_place: str | None,
    to_place: str | None,
) -> str | None:
    if jurisdiction_rule == "new_residence":
        return to_place
    return from_place or to_place


def missing_office_reason(
    *,
    jurisdiction_rule: str,
    from_place: str | None,
    to_place: str | None,
    office: Office | None,
) -> str | None:
    if office is not None:
        return None
    if not office_target(
        jurisdiction_rule=jurisdiction_rule,
        from_place=from_place,
        to_place=to_place,
    ):
        return "Nedostaje mesto prebivališta"
    return "Adresa kancelarije još nije u katalogu za ovo mesto."


def resolve_office(
    session: Session,
    *,
    institution: str,
    jurisdiction_rule: str,
    from_place: str | None,
    to_place: str | None,
) -> Office | None:
    target = office_target(
        jurisdiction_rule=jurisdiction_rule,
        from_place=from_place,
        to_place=to_place,
    )
    if not target:
        return None
    chain = ancestors(session, target)
    offices = session.scalars(select(Office).where(Office.institution == institution)).all()
    for place_id in chain:
        for office in offices:
            if office.covers_place_id == place_id:
                return office
    return None
