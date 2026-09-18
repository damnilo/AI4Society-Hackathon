from __future__ import annotations

import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Procedure
from app.schemas import CandidateOut


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def is_demo_expired(text: str) -> bool:
    n = normalize(text)
    expired = "istekl" in n or "истекл" in n
    licna = "licn" in n or "личн" in n
    return expired and licna


def is_demo_move(text: str) -> bool:
    n = normalize(text)
    move = "sel" in n or "сели" in n or "presel" in n or "пресел" in n
    pirot = "pirot" in n or "пирот" in n
    beograd = "beograd" in n or "београд" in n
    return move and pirot and beograd


def _candidate(proc: Procedure, score: float, rationale: str) -> CandidateOut:
    return CandidateOut(
        slug=proc.slug,
        title=proc.title,
        plain_summary=proc.plain_summary,
        score=score,
        rationale=rationale,
    )


def _from_slugs(
    by_slug: dict[str, Procedure],
    order: list[tuple[str, float, str]],
) -> list[CandidateOut]:
    found: list[CandidateOut] = []
    for slug, score, why in order:
        proc = by_slug.get(slug)
        if proc:
            found.append(_candidate(proc, score, why))
    return found


def match_procedures(session: Session, text: str) -> tuple[list[CandidateOut], bool, list[str]]:
    """Demo keš ostaje ispred xAI (Faza 2). Vision nije potreban — samo tekst."""
    by_slug = {row.slug: row for row in session.scalars(select(Procedure)).all()}

    if is_demo_expired(text):
        candidates = _from_slugs(
            by_slug,
            [
                (
                    "licna-karta-zamena",
                    0.92,
                    "Pominješ da je lična istekla — to je zamena postojeće LK, ne prvo izdavanje.",
                ),
                (
                    "pasos-izdavanje",
                    0.41,
                    "Pasoš je drugi dokument; često se meša sa LK, ali tekst govori o ličnoj.",
                ),
                (
                    "licna-karta-prvo-izdavanje",
                    0.28,
                    "Prva LK je ako nikad nisi imao ličnu, ne ako je stara istekla.",
                ),
            ],
        )
        if candidates:
            return candidates, False, []

    if is_demo_move(text):
        candidates = _from_slugs(
            by_slug,
            [
                (
                    "prijava-prebivalista",
                    0.94,
                    "Selidba iz jednog grada u drugi obično znači stalno prebivalište na novoj adresi.",
                ),
                (
                    "prijava-boravista",
                    0.48,
                    "Ako selidba nije stalna (studije, sezona), to je boravište, ne prebivalište.",
                ),
                (
                    "izbor-izabranog-lekara",
                    0.33,
                    "Posle selidbe često treba novi lekar, ali prvo se rešava prijava adrese.",
                ),
            ],
        )
        if candidates:
            return candidates, False, []

    return _keyword_match(by_slug, text)


def _keyword_match(
    by_slug: dict[str, Procedure], text: str
) -> tuple[list[CandidateOut], bool, list[str]]:
    scored: list[tuple[float, Procedure]] = []
    query = normalize(text)
    tokens = {tok for tok in query.replace(",", " ").split() if len(tok) > 3}
    for proc in by_slug.values():
        blob = normalize(" ".join(proc.intent_examples) + " " + proc.title + " " + proc.plain_summary)
        overlap = sum(1 for tok in tokens if tok in blob)
        if overlap:
            scored.append((overlap / max(len(tokens), 1), proc))
    scored.sort(key=lambda item: item[0], reverse=True)
    top = scored[:3]
    if not top:
        questions = [
            "Da li ti treba lični dokument (LK, pasoš, vozačka) ili promena adrese?",
            "Da li je selidba stalna ili privremena?",
        ]
        return [], True, questions

    gap = (top[0][0] - top[1][0]) if len(top) > 1 else 1.0
    need = top[0][0] < 0.35 or gap < 0.08
    candidates = [
        _candidate(
            proc,
            min(0.75, 0.35 + score),
            "Tekst se poklapa sa primerima namere iz kataloga.",
        )
        for score, proc in top
    ]
    questions = ["Da li je ovo stalna selidba, isprava, ili nešto treće?"] if need else []
    return candidates, need, questions
