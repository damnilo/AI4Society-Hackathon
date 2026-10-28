"""JSON matching helpers. No SQLAlchemy — parser smoke can import this alone."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field

from app.schemas import CandidateOut

CONFIDENCE_MIN = 0.42
SCORE_GAP_MIN = 0.08
MAX_CANDIDATES = 3
UNCERTAIN_QUESTIONS = [
    "Da li ti treba lični dokument (lična karta, pasoš, vozačka) ili promena adrese?",
    "Da li je selidba stalna ili privremena?",
]
VAGUE_TOKENS = frozenset(
    {
        "papir",
        "papira",
        "dokument",
        "dokumenta",
        "isprava",
        "ispravu",
        "isprave",
        "treba",
        "trebam",
        "trebalo",
        "molim",
        "pomoc",
        "pomozite",
        "nesto",
        "stvar",
        "zahtev",
        "obrazac",
        "upit",
        "informacija",
    }
)


@dataclass(frozen=True)
class CatalogProc:
    slug: str
    title: str
    plain_summary: str
    intent_examples: list[str] = field(default_factory=list)


def candidate_out(proc: CatalogProc, score: float, rationale: str) -> CandidateOut:
    return CandidateOut(
        slug=proc.slug,
        title=proc.title,
        plain_summary=proc.plain_summary,
        score=score,
        rationale=rationale,
    )


def _fold_match_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def is_vague_intent(text: str) -> bool:
    """Kratak/generički unos (npr. „treba mi papir“) nije pogodak u katalogu."""
    user = text.split("[skenovi]", 1)[0]
    folded = _fold_match_text(user)
    tokens = {tok for tok in re.split(r"\W+", folded) if len(tok) > 3}
    if len(tokens) <= 1:
        return True
    return not (tokens - VAGUE_TOKENS)


def finalize_match(
    candidates: list[CandidateOut],
    need: bool,
    questions: list[str],
) -> tuple[list[CandidateOut], bool, list[str]]:
    """Kartice samo uz jasan pobednik; nagađanje ide na pitanja, ne na 75% score."""
    if not candidates:
        return [], True, questions or list(UNCERTAIN_QUESTIONS)
    top = candidates[0].score
    gap = (candidates[0].score - candidates[1].score) if len(candidates) > 1 else 1.0
    if top < CONFIDENCE_MIN:
        qs = questions or list(UNCERTAIN_QUESTIONS)
        return [], True, qs[:2]
    if gap < SCORE_GAP_MIN:
        qs = questions or ["Koja od prve dve kartice je bliža onome što trebaš?"]
        return candidates[:2], True, qs[:2]
    return candidates, False, []


def parse_xai_payload(
    raw: str, by_slug: dict[str, CatalogProc]
) -> tuple[list[CandidateOut], bool, list[str]] | None:
    data = extract_json_object(raw)
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
        proc = by_slug.get(slug)
        if proc is None or slug in seen:
            continue
        seen.add(slug)
        try:
            score = max(0.0, min(1.0, float(item.get("score", 0))))
        except (TypeError, ValueError):
            score = 0.0
        why = clean_rationale(str(item.get("rationale") or item.get("why") or ""))
        if not why:
            why = "Tekst odgovara ovoj proceduri iz kataloga."
        candidates.append(candidate_out(proc, score, why))
        if len(candidates) == MAX_CANDIDATES:
            break

    candidates.sort(key=lambda row: row.score, reverse=True)

    questions: list[str] = []
    raw_questions = data.get("questions") or []
    if isinstance(raw_questions, list):
        for question in raw_questions:
            if isinstance(question, str) and question.strip():
                questions.append(clean_rationale(question.strip())[:180])
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


def extract_json_object(raw: str) -> dict[str, object] | None:
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


def clean_rationale(text: str) -> str:
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
