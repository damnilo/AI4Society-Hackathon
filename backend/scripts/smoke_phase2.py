"""Phase 2 matching parser + optional live xAI. Run: python scripts/smoke_phase2.py"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

tmpdir = Path(tempfile.mkdtemp(prefix="putokaz-p2-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(tmpdir / 't.db').as_posix()}"
os.environ["UPLOAD_DIR"] = str(tmpdir / "uploads")

from app.services.matching import parse_xai_payload  # noqa: E402


def fail(msg: str) -> None:
    raise SystemExit(f"FAIL: {msg}")


def catalog() -> dict[str, SimpleNamespace]:
    def proc(slug: str, title: str) -> SimpleNamespace:
        return SimpleNamespace(slug=slug, title=title, plain_summary=f"Opis {title}")

    return {
        "pasos-izdavanje": proc("pasos-izdavanje", "Izdavanje / zamena pasoša"),
        "prijava-boravista": proc("prijava-boravista", "Prijava boravišta"),
        "licna-karta-zamena": proc("licna-karta-zamena", "Zamena lične karte"),
    }


def test_parser() -> None:
    by_slug = catalog()
    raw = """```json
    {"candidates":[
      {"slug":"pasos-izdavanje","score":0.91,"rationale":"Traži putnu ispravu, nije lična."},
      {"slug":"nema-ove","score":0.8,"rationale":"izmišljeno"},
      {"slug":"licna-karta-zamena","score":0.4,"rationale":"Idi u MUP na Ljermontova 12a."}
    ],"need_clarification":false,"questions":[]}
    ```"""
    parsed = parse_xai_payload(raw, by_slug)  # type: ignore[arg-type]
    if parsed is None:
        fail("parser returned None")
    candidates, need, questions = parsed
    if [c.slug for c in candidates] != ["pasos-izdavanje", "licna-karta-zamena"]:
        fail(f"slugs { [c.slug for c in candidates] }")
    if candidates[0].title != "Izdavanje / zamena pasoša":
        fail("title must come from catalog")
    if "MUP" in candidates[1].rationale or "Ljermontova" in candidates[1].rationale:
        fail(f"rationale leaked office: {candidates[1].rationale}")
    if need:
        fail("high-confidence match should not need clarification")
    if questions:
        fail("questions should be cleared when confident")

    empty = parse_xai_payload('{"candidates":[],"need_clarification":true,"questions":[]}', by_slug)  # type: ignore[arg-type]
    if empty is None or empty[1] is not True or not empty[2]:
        fail("empty candidates must clarify")


def test_live() -> None:
    from fastapi.testclient import TestClient

    from app.config import settings
    from app.main import app

    if not settings.xai_api_key:
        print("Phase 2 live xAI skipped (no key)")
        return
    with TestClient(app) as client:
        demo = client.post("/cases", json={"text": "istekla mi je lična"})
        if demo.status_code != 200:
            fail(f"demo {demo.status_code} {demo.text}")
        slugs = [c["slug"] for c in demo.json()["candidates"]]
        if slugs[:1] != ["licna-karta-zamena"]:
            fail(f"demo cache broken: {slugs}")

        live = client.post("/cases", json={"text": "treba mi pasoš za letovanje u Grčkoj"})
        if live.status_code != 200:
            fail(f"xAI case {live.status_code} {live.text}")
        body = live.json()
        live_slugs = [c["slug"] for c in body["candidates"]]
        if "pasos-izdavanje" not in live_slugs[:2]:
            fail(f"expected pasos near top, got {live_slugs} questions={body.get('questions')}")
        if len(live_slugs) < 2:
            fail(f"expected 2-3 cards, got {live_slugs}")
        for card in body["candidates"]:
            if "institution" in card:
                fail("card leaked institution field")
            blob = f"{card['title']} {card['rationale']}".lower()
            if "ljermontov" in blob or "jevrejska" in blob:
                fail(f"street in card: {card}")

        unclear = client.post("/cases", json={"text": "asdf qwer zxcv"})
        if unclear.status_code != 200:
            fail(f"unclear {unclear.status_code}")
        if not unclear.json().get("need_clarification"):
            fail("nonsense text should need clarification")


def main() -> None:
    test_parser()
    test_live()
    print("Phase 2 matching OK")


if __name__ == "__main__":
    main()
