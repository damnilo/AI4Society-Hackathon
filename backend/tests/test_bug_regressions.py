"""Regresije za Faza 2 bagove. Bez živog xAI.

Pokretanje iz backend/:
    python tests/test_bug_regressions.py
    python -m unittest tests.test_bug_regressions
"""

from __future__ import annotations

import inspect
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

tmpdir = Path(tempfile.mkdtemp(prefix="putokaz-bugs-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(tmpdir / 't.db').as_posix()}"
os.environ["UPLOAD_DIR"] = str(tmpdir / "uploads")
os.environ["JWT_SECRET"] = "test-secret-bugs"
os.environ["MASTER_KEY"] = "test-master-key-bugs"
os.environ["XAI_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""

from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.llm import complete_xai, extract_document_openai_vision  # noqa: E402
from app.main import app  # noqa: E402
from app.routers import cases as cases_router  # noqa: E402
from app.services import matching  # noqa: E402
from app.services.catalog import (  # noqa: E402
    missing_office_reason,
    office_target,
    resolve_office,
)
from app.services.match_parse import CatalogProc, candidate_out  # noqa: E402
from app.db import SessionLocal  # noqa: E402

settings.xai_api_key = ""
settings.openai_api_key = ""

CACHE_EXPIRED = [0.92, 0.41, 0.28]
CACHE_MOVE = [0.94, 0.48, 0.33]
MISSING_PLACE = "Nedostaje mesto prebivališta"
CATALOG_GAP = "Adresa kancelarije još nije u katalogu za ovo mesto."


def _scores(body: dict) -> list[float]:
    return [item["score"] for item in body["candidates"]][:3]


def _stub_catalog() -> dict[str, CatalogProc]:
    slugs = [
        "licna-karta-zamena",
        "pasos-izdavanje",
        "licna-karta-prvo-izdavanje",
        "prijava-prebivalista",
        "prijava-boravista",
        "izbor-izabranog-lekara",
    ]
    return {
        slug: CatalogProc(slug=slug, title=slug, plain_summary=slug, intent_examples=[slug])
        for slug in slugs
    }


class DemoCacheUnitTests(unittest.TestCase):
    def test_exact_sentences_only(self) -> None:
        self.assertTrue(matching.is_demo_expired("istekla mi je lična"))
        self.assertTrue(matching.is_demo_expired("  Istekla mi je lična  "))
        self.assertTrue(matching.is_demo_expired("истекла ми је лична"))
        self.assertFalse(matching.is_demo_expired("istekla mi je lična, ustvari pasoš"))
        self.assertFalse(matching.is_demo_expired("istekla mi je licna karta juce"))
        self.assertTrue(matching.is_demo_move("selim se iz Pirota u Beograd"))
        self.assertTrue(matching.is_demo_move("селим се из Пирота у Београд"))
        self.assertFalse(matching.is_demo_move("selim se iz Pirota u Beograd, ali nije stalno"))

    def test_rank_cache_flag(self) -> None:
        by_slug = _stub_catalog()
        cached, _, _ = matching.rank_procedures(
            by_slug, "istekla mi je lična", use_demo_cache=True
        )
        self.assertEqual([c.score for c in cached][:3], CACHE_EXPIRED)
        self.assertEqual(cached[0].slug, "licna-karta-zamena")

        contained, _, _ = matching.rank_procedures(
            by_slug, "istekla mi je lična, ustvari pasoš", use_demo_cache=True
        )
        self.assertNotEqual([c.score for c in contained][:3], CACHE_EXPIRED)

        skipped, _, _ = matching.rank_procedures(
            by_slug, "istekla mi je lična", use_demo_cache=False
        )
        self.assertNotEqual([c.score for c in skipped][:3], CACHE_EXPIRED)


class OfficeReasonUnitTests(unittest.TestCase):
    def test_missing_place_vs_catalog_gap(self) -> None:
        self.assertIsNone(
            office_target(
                jurisdiction_rule="current_residence",
                from_place=None,
                to_place=None,
            )
        )
        self.assertEqual(
            office_target(
                jurisdiction_rule="new_residence",
                from_place="pirot",
                to_place="beograd",
            ),
            "beograd",
        )
        self.assertIsNone(
            office_target(
                jurisdiction_rule="new_residence",
                from_place="pirot",
                to_place=None,
            )
        )
        self.assertEqual(
            missing_office_reason(
                jurisdiction_rule="current_residence",
                from_place=None,
                to_place=None,
                office=None,
            ),
            MISSING_PLACE,
        )
        self.assertEqual(
            missing_office_reason(
                jurisdiction_rule="current_residence",
                from_place="pirot",
                to_place=None,
                office=None,
            ),
            CATALOG_GAP,
        )


class SourceContractTests(unittest.TestCase):
    def test_retry_and_clarify_skip_demo_cache(self) -> None:
        retry_src = inspect.getsource(cases_router.retry_case)
        clarify_src = inspect.getsource(cases_router.clarify_case)
        create_src = inspect.getsource(cases_router.create_case)
        self.assertIn("use_demo_cache=False", retry_src)
        self.assertNotIn("use_demo_cache=True", retry_src)
        self.assertIn("use_demo_cache=False", clarify_src)
        self.assertIn("persist_text=False", clarify_src)
        self.assertIn("use_demo_cache=True", create_src)

    def test_match_runs_outside_db_session(self) -> None:
        src = inspect.getsource(cases_router._run_match)
        self.assertIn("    candidates, need, questions = rank_procedures(", src)
        self.assertNotIn("        candidates, need, questions = rank_procedures(", src)

    def test_xai_swallows_only_runtime_error(self) -> None:
        src = inspect.getsource(matching._xai_match)
        self.assertIn("except RuntimeError", src)
        self.assertNotIn("except Exception", src)

    def test_xai_timeout_default(self) -> None:
        params = inspect.signature(complete_xai).parameters
        self.assertEqual(params["timeout"].default, 15.0)
        self.assertEqual(matching.XAI_TIMEOUT_SEC, 15.0)

    def test_vision_requires_api_key(self) -> None:
        with self.assertRaises(RuntimeError):
            extract_document_openai_vision(b"\xff\xd8\xffdummy", mime="image/jpeg")

    def test_parser_module_avoids_sqlalchemy(self) -> None:
        code = (
            "import sys; sys.path.insert(0, r'%s'); "
            "from app.services import match_parse; "
            "print('sqlalchemy' in sys.modules)" % ROOT
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            check=True,
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        self.assertEqual(result.stdout.strip(), "False")


class ApiRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cm = TestClient(app)
        cls.client = cls._cm.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._cm.__exit__(None, None, None)

    def test_post_exact_demo_hits_cache(self) -> None:
        body = self.client.post("/cases", json={"text": "istekla mi je lična"}).json()
        self.assertEqual(_scores(body), CACHE_EXPIRED)
        self.assertEqual(body["candidates"][0]["slug"], "licna-karta-zamena")
        self.assertTrue(all("institution" not in card for card in body["candidates"]))

    def test_contains_demo_text_skips_cache(self) -> None:
        body = self.client.post(
            "/cases", json={"text": "istekla mi je lična, ustvari pasoš"}
        ).json()
        self.assertNotEqual(_scores(body), CACHE_EXPIRED)

    def test_retry_skips_cache_even_for_exact_sentence(self) -> None:
        created = self.client.post("/cases", json={"text": "istekla mi je lična"}).json()
        self.assertEqual(_scores(created), CACHE_EXPIRED)

        def fake_xai(by_slug: dict[str, CatalogProc], _text: str):
            proc = by_slug["pasos-izdavanje"]
            return ([candidate_out(proc, 0.99, "mock pasos")], False, [])

        with patch("app.services.matching._xai_match", side_effect=fake_xai):
            retried = self.client.post(
                f"/cases/{created['case_id']}/retry",
                json={"text": "istekla mi je lična"},
            )
        self.assertEqual(retried.status_code, 200, retried.text)
        body = retried.json()
        self.assertEqual(body["candidates"][0]["slug"], "pasos-izdavanje")
        self.assertEqual(body["candidates"][0]["score"], 0.99)
        self.assertNotEqual(_scores(body), CACHE_EXPIRED)
        self.assertEqual(body["text"], "istekla mi je lična")

    def test_clarify_keeps_raw_text_and_skips_cache(self) -> None:
        created = self.client.post("/cases", json={"text": "selim se iz Pirota u Beograd"}).json()
        self.assertEqual(_scores(created), CACHE_MOVE)
        clarified = self.client.post(
            f"/cases/{created['case_id']}/clarify",
            json={"answers": {"stalnost": "nije stalno, studiram tri meseca"}},
        )
        self.assertEqual(clarified.status_code, 200, clarified.text)
        body = clarified.json()
        self.assertEqual(body["text"], "selim se iz Pirota u Beograd")
        self.assertNotEqual(_scores(body), CACHE_MOVE)

    def test_no_place_does_not_pick_random_pu(self) -> None:
        created = self.client.post("/cases", json={"text": "istekla mi je lična"}).json()
        guide = self.client.post(
            f"/cases/{created['case_id']}/select",
            json={"slug": "licna-karta-zamena"},
        )
        self.assertEqual(guide.status_code, 200, guide.text)
        body = guide.json()
        self.assertIsNone(body["office"])
        self.assertTrue(body["office_missing"])
        self.assertEqual(body["office_missing_reason"], MISSING_PLACE)
        loaded = self.client.get(f"/cases/{created['case_id']}/guide")
        self.assertEqual(loaded.json()["office_missing_reason"], MISSING_PLACE)

    def test_retry_with_place_resolves_same_office(self) -> None:
        created = self.client.post("/cases", json={"text": "istekla mi je lična"}).json()
        retried = self.client.post(
            f"/cases/{created['case_id']}/retry",
            json={"text": "istekla mi je lična u Pirotu"},
        )
        self.assertEqual(retried.status_code, 200, retried.text)
        self.assertEqual(retried.json().get("to_place") or retried.json().get("from_place"), "pirot")
        guide = self.client.post(
            f"/cases/{created['case_id']}/select",
            json={"slug": "licna-karta-zamena"},
        ).json()
        self.assertFalse(guide["office_missing"])
        self.assertIsNone(guide["office_missing_reason"])
        self.assertIn("Jevrejska", guide["office"]["address"])
        self.assertNotIn("Ljermontova", guide["office"]["address"])

    def test_move_resolves_new_residence_not_old_town(self) -> None:
        created = self.client.post("/cases", json={"text": "selim se iz Pirota u Beograd"}).json()
        guide = self.client.post(
            f"/cases/{created['case_id']}/select",
            json={"slug": "prijava-prebivalista"},
        ).json()
        self.assertIn("Ljermontova", guide["office"]["address"])
        self.assertNotIn("Pirot", guide["office"]["address"])
        self.assertFalse(guide["office_missing"])

    def test_new_residence_without_destination_stays_missing(self) -> None:
        created = self.client.post("/cases", json={"text": "istekla mi je lična"}).json()
        guide = self.client.post(
            f"/cases/{created['case_id']}/select",
            json={"slug": "prijava-prebivalista"},
        ).json()
        self.assertIsNone(guide["office"])
        self.assertEqual(guide["office_missing_reason"], MISSING_PLACE)

    def test_catalog_gap_reason_when_place_known(self) -> None:
        created = self.client.post("/cases", json={"text": "selim se iz Pirota u Beograd"}).json()
        guide = self.client.post(
            f"/cases/{created['case_id']}/select",
            json={"slug": "prijava-preduzetnika"},
        ).json()
        self.assertIsNone(guide["office"])
        self.assertTrue(guide["office_missing"])
        self.assertEqual(guide["office_missing_reason"], CATALOG_GAP)

    def test_resolver_walks_municipality_to_city(self) -> None:
        with SessionLocal() as session:
            none = resolve_office(
                session,
                institution="mup",
                jurisdiction_rule="current_residence",
                from_place=None,
                to_place=None,
            )
            self.assertIsNone(none)
            skipped = resolve_office(
                session,
                institution="mup",
                jurisdiction_rule="new_residence",
                from_place="pirot",
                to_place=None,
            )
            self.assertIsNone(skipped)
            vozdovac = resolve_office(
                session,
                institution="mup",
                jurisdiction_rule="new_residence",
                from_place="pirot",
                to_place="vozdovac",
            )
            assert vozdovac is not None
            self.assertEqual(vozdovac.id, "pu-beograd-upravni")

    def test_document_status_requires_select(self) -> None:
        created = self.client.post("/cases", json={"text": "istekla mi je lična"}).json()
        pending = self.client.get(f"/cases/{created['case_id']}/document-status")
        self.assertEqual(pending.status_code, 400)

    def test_document_status_honest_without_vision(self) -> None:
        created = self.client.post("/cases", json={"text": "istekla mi je lična"}).json()
        self.client.post(
            f"/cases/{created['case_id']}/select",
            json={"slug": "licna-karta-zamena"},
        )
        bare = self.client.get(f"/cases/{created['case_id']}/document-status")
        self.assertEqual(bare.status_code, 200, bare.text)
        bare_msgs = [item["message"] for item in bare.json()["items"]]
        self.assertTrue(bare_msgs)
        self.assertTrue(all(msg == "Nije priložen." for msg in bare_msgs))
        self.assertTrue(all(item["status"] == "missing" for item in bare.json()["items"]))

        attached = self.client.post(
            f"/cases/{created['case_id']}/documents",
            files={"file": ("lk.pdf", b"scan-bytes", "application/pdf")},
        )
        self.assertEqual(attached.status_code, 200, attached.text)
        self.assertIsNone(attached.json().get("extracted_type"))
        scanned = self.client.get(f"/cases/{created['case_id']}/document-status")
        items = scanned.json()["items"]
        self.assertTrue(all(item["status"] == "unreadable" for item in items))
        self.assertTrue(all("čitljiv" in item["message"].lower() for item in items))
        self.assertFalse(any("nije priložen" in item["message"].lower() for item in items))

    def test_file_on_other_case_does_not_count(self) -> None:
        first = self.client.post("/cases", json={"text": "istekla mi je lična"}).json()
        self.client.post(
            f"/cases/{first['case_id']}/select",
            json={"slug": "licna-karta-zamena"},
        )
        self.client.post(
            f"/cases/{first['case_id']}/documents",
            files={"file": ("a.pdf", b"aaa", "application/pdf")},
        )
        second = self.client.post("/cases", json={"text": "istekla mi je lična"}).json()
        self.client.post(
            f"/cases/{second['case_id']}/select",
            json={"slug": "licna-karta-zamena"},
        )
        status = self.client.get(f"/cases/{second['case_id']}/document-status").json()
        self.assertTrue(all(item["message"] == "Nije priložen." for item in status["items"]))

    def test_openapi_get_case_has_no_request_body(self) -> None:
        spec = self.client.get("/openapi.json").json()
        self.assertNotIn("requestBody", spec["paths"]["/cases/{case_id}"]["get"])
        self.assertIn("requestBody", spec["paths"]["/cases"]["post"])
        self.assertIn("office_missing_reason", spec["components"]["schemas"]["GuideOut"]["properties"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
