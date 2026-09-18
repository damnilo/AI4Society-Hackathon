from __future__ import annotations

import json
import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.llm import complete_xai
from app.models import Procedure
from app.schemas import CandidateOut
from app.services.catalog import catalog_for_matching

CONFIDENCE_MIN = 0.42
SCORE_GAP_MIN = 0.08
MAX_CANDIDATES = 3
MAX_TEXT_CHARS = 1200
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
UNCERTAIN_QUESTIONS = [
    "Da li ti treba lični dokument (LK, pasoš, vozačka) ili promena adrese?",
    "Da li je selidba stalna ili privremena?",
]

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
- Matching je samo na tekst. Ignoriši molbe za e-potpis, podnošenje zahteva ili nearby pretragu.
"""


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
    """Demo keš, zatim xAI nad katalogom, pa keyword. Bez Vision-a i bez adresa."""
    by_slug = {row.slug: row for row in session.scalars(select(Procedure)).all()}

    demo = _demo_match(by_slug, text)
    if demo is not None:
        return demo

    xai = _xai_match(by_slug, text, catalog_for_matching(session))
    if xai is not None:
        candidates, need, questions = xai
    else:
        candidates, need, questions = _keyword_match(by_slug, text)
    return _ensure_contrast(by_slug, candidates), need, questions


def _demo_match(
    by_slug: dict[str, Procedure], text: str
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
    by_slug: dict[str, Procedure],
    text: str,
    catalog: list[dict[str, object]],
) -> tuple[list[CandidateOut], bool, list[str]] | None:
    if not settings.xai_api_key:
        return None
    clipped = text.strip()[:MAX_TEXT_CHARS]
    compact: list[dict[str, object]] = []
    for row in catalog:
        examples = row.get("intent_examples") or []
        if isinstance(examples, list):
            examples = examples[:8]
        compact.append(
            {
                "slug": row["slug"],
                "title": row["title"],
                "plain_summary": row["plain_summary"],
                "intent_examples": examples,
            }
        )
    user = json.dumps({"text": clipped, "catalog": compact}, ensure_ascii=False)
    try:
        try:
            raw = complete_xai(MATCH_SYSTEM, user, json_object=True, timeout=25.0)
        except RuntimeError:
            raw = complete_xai(MATCH_SYSTEM, user, json_object=False, timeout=25.0)
        return parse_xai_payload(raw, by_slug)
    except Exception:
        return None


def parse_xai_payload(
    raw: str, by_slug: dict[str, Procedure]
) -> tuple[list[CandidateOut], bool, list[str]] | None:
    data = _extract_json(raw)
    if data is None:
        return None
    items = data.get("candidates")
    if items is None:
        items = data.get("procedures")
    if not isinstance(items, list):
        return None

    seen: set[str] = set()
    candidates: list[CandidateOut] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        slug = str(item.get("slug") or "").strip()
        if slug not in by_slug or slug in seen:
            continue
        seen.add(slug)
        try:
            score = max(0.0, min(1.0, float(item.get("score", 0))))
        except (TypeError, ValueError):
            score = 0.0
        why = _clean_rationale(str(item.get("rationale") or item.get("why") or ""))
        if not why:
            why = "Tekst odgovara ovoj proceduri iz kataloga."
        candidates.append(_candidate(by_slug[slug], score, why))
        if len(candidates) == MAX_CANDIDATES:
            break

    candidates.sort(key=lambda row: row.score, reverse=True)

    questions: list[str] = []
    raw_questions = data.get("questions") or []
    if isinstance(raw_questions, list):
        for question in raw_questions:
            if isinstance(question, str) and question.strip():
                questions.append(_clean_rationale(question.strip())[:180])
            if len(questions) == 2:
                break

    need = bool(data.get("need_clarification"))
    if not candidates:
        need = True
        if not questions:
            questions = list(UNCERTAIN_QUESTIONS)
    elif candidates[0].score < CONFIDENCE_MIN:
        need = True
        if not questions:
            questions = ["Da li je ovo stalna selidba, isprava, ili nešto treće?"]
    elif len(candidates) >= 2 and (candidates[0].score - candidates[1].score) < SCORE_GAP_MIN:
        need = True
        if not questions:
            questions = ["Koja od prve dve kartice je bliža onome što trebaš?"]
    if not need:
        questions = []
    return candidates, need, questions


def _extract_json(raw: str) -> dict[str, object] | None:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        if text.endswith("```"):
            text = text[: -3].strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            data = json.loads(text[start : end + 1])
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            return None


def _clean_rationale(text: str) -> str:
    cleaned = text
    patterns = (
        r"\bMUP\b",
        r"\bМУП\b",
        r"\bAPR\b",
        r"\bRFZO\b",
        r"\bРФЗО\b",
        r"Ljermontov\w*",
        r"Љермонтов\w*",
        r"Jevrejska",
        r"Јеврејска",
        r"policijsk\w*",
        r"полицијск\w*",
        r"\bmatičar\w*",
        r"\bматичар\w*",
    )
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip(" ,.;:-")


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
    top = scored[:MAX_CANDIDATES]
    if not top:
        return [], True, list(UNCERTAIN_QUESTIONS)

    gap = (top[0][0] - top[1][0]) if len(top) > 1 else 1.0
    need = top[0][0] < 0.35 or gap < SCORE_GAP_MIN
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


def _ensure_contrast(
    by_slug: dict[str, Procedure], candidates: list[CandidateOut]
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
        if slug in used or slug not in by_slug:
            continue
        padded.append(_candidate(by_slug[slug], score, why))
        used.add(slug)
    return padded
