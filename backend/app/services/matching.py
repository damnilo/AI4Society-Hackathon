from __future__ import annotations

import unicodedata

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import Procedure
from app.schemas import CandidateOut


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


DEMO_EXPIRED = "istekla mi je licna"
DEMO_MOVE = "selim se iz pirota u beograd"


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


def match_procedures(session: Session, text: str) -> tuple[list[CandidateOut], bool, list[str]]:
    """Faza 0: demo keš + prost overlap primera. Faza 2 zamenjuje xAI."""
    by_slug = {row.slug: row for row in session.scalars(select(Procedure)).all()}

    if is_demo_expired(text):
        order = [
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
        ]
        return [_candidate(by_slug[slug], score, why) for slug, score, why in order], False, []

    if is_demo_move(text):
        order = [
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
        ]
        return [_candidate(by_slug[slug], score, why) for slug, score, why in order], False, []

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
            "Tekst se poklapa sa primerima namere iz kataloga (privremeni matching, bez xAI).",
        )
        for score, proc in top
    ]
    questions = ["Da li je ovo stalna selidba, isprava, ili nešto treće?"] if need else []
    return candidates, need, questions
