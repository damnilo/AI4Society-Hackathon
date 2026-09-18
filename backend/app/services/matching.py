from __future__ import annotations

import json
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.llm import complete_xai
from app.models import Procedure
from app.schemas import CandidateOut
from app.services.match_parse import (
    MAX_CANDIDATES,
    SCORE_GAP_MIN,
    UNCERTAIN_QUESTIONS,
    CatalogProc,
    candidate_out,
    parse_xai_payload,
)

MAX_TEXT_CHARS = 1200
XAI_TIMEOUT_SEC = 15.0
CONTRAST = {
    "pasos-izdavanje": ("licna-karta-zamena", "ezakazivanje-licna-pasos"),
    "licna-karta-zamena": ("pasos-izdavanje", "licna-karta-prvo-izdavanje"),
    "licna-karta-prvo-izdavanje": ("licna-karta-zamena", "uverenje-o-drzavljanstvu"),
    "prijava-prebivalista": ("prijava-boravista", "izbor-izabranog-lekara"),
    "prijava-boravista": ("prijava-prebivalista", "uverenje-o-prebivalistu"),
    "vozacka-dozvola-izdavanje": ("vozacka-dozvola-zamena", "registracija-vozila"),
    "vozacka-dozvola-zamena": ("vozacka-dozvola-izdavanje", "registracija-vozila"),
    "registracija-vozila": ("vozacka-dozvola-zamena", "prijava-preduzetnika"),
    "uverenje-o-prebivalistu": ("prijava-prebivalista", "prijava-boravista"),
    "izvod-maticne-rodjenih": ("uverenje-o-drzavljanstvu", "licna-karta-prvo-izdavanje"),
    "uverenje-o-drzavljanstvu": ("izvod-maticne-rodjenih", "licna-karta-prvo-izdavanje"),
    "izbor-izabranog-lekara": ("prijava-prebivalista", "prijava-boravista"),
    "prijava-preduzetnika": ("registracija-vozila", "ezakazivanje-licna-pasos"),
    "ezakazivanje-licna-pasos": ("licna-karta-zamena", "pasos-izdavanje"),
    "saglasnost-vlasnika-prebivaliste": ("prijava-prebivalista", "prijava-boravista"),
}

MATCH_SYSTEM = """Ti si matching sloj Putokaza. Biraj procedure SAMO iz datog kataloga.

Vrati isključivo JSON oblika:
{"candidates":[{"slug":"...","score":0.0,"rationale":"..."}],"need_clarification":false,"questions":[]}

Pravila:
- 2 ili 3 kandidata kada postoji makar jedan pogodak. Prvi je najbolji; ostali su bliski parovi za kontrast (npr. LK vs pasoš, prebivalište vs boravište), sa NIŽIM score.
- Samo 0 kandidata ako namera nema veze sa katalogom.
- score od 0 do 1. Sortiraj opadajuće.
- rationale: 1-2 rečenice na srpskom, zašto namera odgovara TOJ proceduri. Bez naslova usluge kao citata iz MUP-a.
- NE pominji instituciju (MUP, APR, RFZO, matičar), ulicu, telefon, šalter, gradsku upravu.
- title, adresu i korake NE pišeš — sistem ih dodaje iz kataloga.
- Razlikuj parove: prebivalište vs boravište; zamena LK vs prva LK; LK vs pasoš; prva vozačka vs zamena; vozačka vs registracija vozila.
- Ako je namera nejasna, dve procedure su blizu, ili nijedna ne odgovara: need_clarification=true i najviše 2 kratka pitanja.
- Ako nijedna ne odgovara: candidates=[] .
- Ako postoji blok [skenovi] sa type/expiry/status, koristi ga uz tekst (npr. istekla lična → zamena LK). Ne citiraj ime sa isprave.
- Matching ne vidi sliku. Ignoriši molbe za e-potpis, podnošenje zahteva ili nearby pretragu.
"""


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _folded(text: str) -> str:
    return " ".join(normalize(text).split())


DEMO_EXPIRED_KEYS = frozenset(
    {
        _folded("istekla mi je lična"),
        _folded("истекла ми је лична"),
    }
)
DEMO_MOVE_KEYS = frozenset(
    {
        _folded("selim se iz Pirota u Beograd"),
        _folded("селим се из Пирота у Београд"),
    }
)


def is_demo_expired(text: str) -> bool:
    return _folded(text) in DEMO_EXPIRED_KEYS


def is_demo_move(text: str) -> bool:
    return _folded(text) in DEMO_MOVE_KEYS


def load_catalog_procs(session: Session) -> dict[str, CatalogProc]:
    rows = session.scalars(select(Procedure)).all()
    loaded: dict[str, CatalogProc] = {}
    for row in rows:
        examples = row.intent_examples if isinstance(row.intent_examples, list) else []
        loaded[row.slug] = CatalogProc(
            slug=row.slug,
            title=row.title,
            plain_summary=row.plain_summary,
            intent_examples=[str(item) for item in examples],
        )
    return loaded


def rank_procedures(
    by_slug: dict[str, CatalogProc],
    text: str,
    *,
    use_demo_cache: bool = True,
) -> tuple[list[CandidateOut], bool, list[str]]:
    """Demo keš samo na tačne demo rečenice i samo kad je use_demo_cache. xAI van DB."""
    if use_demo_cache:
        demo = _demo_match(by_slug, text)
        if demo is not None:
            return demo

    xai = _xai_match(by_slug, text)
    if xai is not None:
        candidates, need, questions = xai
    else:
        candidates, need, questions = _keyword_match(by_slug, text)
    return _ensure_contrast(by_slug, candidates), need, questions


def match_procedures(
    session: Session,
    text: str,
    *,
    use_demo_cache: bool = True,
) -> tuple[list[CandidateOut], bool, list[str]]:
    by_slug = load_catalog_procs(session)
    session.commit()
    return rank_procedures(by_slug, text, use_demo_cache=use_demo_cache)


def _from_slugs(
    by_slug: dict[str, CatalogProc],
    order: list[tuple[str, float, str]],
) -> list[CandidateOut]:
    found: list[CandidateOut] = []
    for slug, score, why in order:
        proc = by_slug.get(slug)
        if proc:
            found.append(candidate_out(proc, score, why))
    return found


def _demo_match(
    by_slug: dict[str, CatalogProc], text: str
) -> tuple[list[CandidateOut], bool, list[str]] | None:
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
    return None


def _xai_match(
    by_slug: dict[str, CatalogProc],
    text: str,
) -> tuple[list[CandidateOut], bool, list[str]] | None:
    if not settings.xai_api_key:
        return None
    clipped = text.strip()[:MAX_TEXT_CHARS]
    compact: list[dict[str, object]] = []
    for proc in by_slug.values():
        compact.append(
            {
                "slug": proc.slug,
                "title": proc.title,
                "plain_summary": proc.plain_summary,
                "intent_examples": proc.intent_examples[:8],
            }
        )
    user = json.dumps({"text": clipped, "catalog": compact}, ensure_ascii=False)
    try:
        raw = complete_xai(MATCH_SYSTEM, user, json_object=True, timeout=XAI_TIMEOUT_SEC)
    except RuntimeError:
        return None
    return parse_xai_payload(raw, by_slug)


def _keyword_match(
    by_slug: dict[str, CatalogProc], text: str
) -> tuple[list[CandidateOut], bool, list[str]]:
    scored: list[tuple[float, CatalogProc]] = []
    query = normalize(text)
    tokens = {tok for tok in query.replace(",", " ").split() if len(tok) > 3}
    for proc in by_slug.values():
        blob = normalize(" ".join(proc.intent_examples) + " " + proc.title + " " + proc.plain_summary)
        overlap = sum(1 for tok in tokens if tok in blob)
        if overlap:
            scored.append((overlap / max(len(tokens), 1), proc))
    scored.sort(key=lambda item: item[0], reverse=True)
    top = scored[:MAX_CANDIDATES]
    if not top:
        return [], True, list(UNCERTAIN_QUESTIONS)

    gap = (top[0][0] - top[1][0]) if len(top) > 1 else 1.0
    need = top[0][0] < 0.35 or gap < SCORE_GAP_MIN
    candidates = [
        candidate_out(
            proc,
            min(0.75, 0.35 + score),
            "Tekst se poklapa sa primerima namere iz kataloga.",
        )
        for score, proc in top
    ]
    questions = ["Da li je ovo stalna selidba, isprava, ili nešto treće?"] if need else []
    return candidates, need, questions


def _ensure_contrast(
    by_slug: dict[str, CatalogProc], candidates: list[CandidateOut]
) -> list[CandidateOut]:
    if len(candidates) != 1:
        return candidates
    used = {candidates[0].slug}
    extras = CONTRAST.get(candidates[0].slug, ())
    scores = (0.4, 0.28)
    reasons = (
        "Slična usluga, često se meša sa onom koju tražiš.",
        "Povezana procedura, ali obično nije prvi korak.",
    )
    padded = list(candidates)
    for slug, score, why in zip(extras, scores, reasons, strict=False):
        proc = by_slug.get(slug)
        if slug in used or proc is None:
            continue
        padded.append(candidate_out(proc, score, why))
        used.add(slug)
    return padded
