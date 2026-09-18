from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Office, Place, Procedure

ROOT = Path(__file__).resolve().parents[2]
SEED_DIR = ROOT / "seed"


def seed_catalog(session: Session) -> None:
    if session.scalar(select(Procedure.slug).limit(1)) is not None:
        return
    _seed_places(session)
    _seed_offices(session)
    _seed_procedures(session)
    session.commit()


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
            session.add(
                Place(
                    id=row["id"],
                    kind=row["kind"],
                    parent_id=row.get("parent_id"),
                    name_lat=row["name_lat"],
                    name_cyr=row["name_cyr"],
                    aliases=row.get("aliases") or [],
                )
            )
            session.flush()
        remaining = next_round
    if remaining:
        raise RuntimeError(f"Ne mogu da uvežem mesta: {[r['id'] for r in remaining]}")


def _seed_offices(session: Session) -> None:
    rows: list[dict] = json.loads((SEED_DIR / "offices.json").read_text(encoding="utf-8"))
    for row in rows:
        session.add(Office(**row))


def _seed_procedures(session: Session) -> None:
    rows: list[dict] = json.loads((SEED_DIR / "procedures.json").read_text(encoding="utf-8"))
    for row in rows:
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


def resolve_office(
    session: Session,
    *,
    institution: str,
    jurisdiction_rule: str,
    from_place: str | None,
    to_place: str | None,
) -> Office | None:
    target = to_place if jurisdiction_rule == "new_residence" else from_place or to_place
    if not target:
        return None
    chain = ancestors(session, target)
    offices = session.scalars(select(Office).where(Office.institution == institution)).all()
    for place_id in chain:
        for office in offices:
            if office.covers_place_id == place_id:
                return office
    return None
