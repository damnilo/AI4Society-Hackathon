"""Tekst vodiča za TTS — katalog + checklist, ne LLM sadržaj."""

from __future__ import annotations

from app.schemas import DocumentStatusItem, GuideOut, OfficeOut
from app.services.extraction import doc_label

SPEECH_DISCLAIMER = "Putokaz nije eUprava i ne overava dokumenta."
MAX_SPEECH_CHARS = 3500


def build_speech_script(
    *,
    title: str,
    steps: list[dict[str, object]],
    office: OfficeOut | None,
    items: list[DocumentStatusItem],
) -> str:
    parts: list[str] = [title]
    for index, step in enumerate(steps, start=1):
        heading = str(step.get("title") or "").strip()
        body = str(step.get("description") or "").strip()
        chunk = f"Korak {index}."
        if heading:
            chunk = f"{chunk} {heading}."
        if body:
            chunk = f"{chunk} {body}"
        parts.append(chunk)
    if office:
        parts.append(
            f"Šalter: {office.name}, {office.address}. Telefon {office.phone}."
        )
    missing = [doc_label(item.type) for item in items if item.status != "complete"]
    if missing:
        parts.append("Šta fali: " + ", ".join(missing) + ".")
    parts.append(SPEECH_DISCLAIMER)
    return " ".join(parts)[:MAX_SPEECH_CHARS]


def script_from_guide(guide: GuideOut, items: list[DocumentStatusItem]) -> str:
    return build_speech_script(
        title=guide.title,
        steps=guide.steps,
        office=guide.office,
        items=items,
    )
