"""Faza 3 — Vision checklist. Mock OpenAI; ne zove mrežu.

Pokretanje iz backend/: python tests/test_phase3_documents.py
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

tmpdir = Path(tempfile.mkdtemp(prefix="putokaz-p3-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(tmpdir / 't.db').as_posix()}"
os.environ["UPLOAD_DIR"] = str(tmpdir / "uploads")
os.environ["JWT_SECRET"] = "test-secret-phase3"
os.environ["MASTER_KEY"] = "test-master-key-phase3"
os.environ["XAI_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = "sk-test-phase3"

TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.services.extraction import (  # noqa: E402
    MISSING_MSG,
    SCAN_NEXT_MSG,
    UNREADABLE_MSG,
    apply_vision_result,
    checklist_item,
    expiry_is_past,
    normalize_type,
    parse_expiry,
    parse_vision_payload,
    sniff_media,
)

settings.xai_api_key = ""
settings.openai_api_key = "sk-test-phase3"


class _FakeDoc:
    def __init__(
        self,
        *,
        doc_id: str = "11111111-1111-4111-8111-111111111111",
        extracted_type: str | None = None,
        extracted_expiry: str | None = None,
        status: str | None = None,
    ) -> None:
        self.id = doc_id
        self.extracted_type = extracted_type
        self.extracted_expiry = extracted_expiry
        self.status = status


class ExtractionUnitTests(unittest.TestCase):
    def test_sniff_and_parse(self) -> None:
        self.assertEqual(sniff_media(TINY_PNG), "image/png")
        self.assertEqual(sniff_media(b"%PDF-1.4"), "application/pdf")
        self.assertEqual(parse_expiry("2024-03-01"), "2024-03-01")
        self.assertEqual(parse_expiry("01.03.2024"), "2024-03-01")
        self.assertTrue(expiry_is_past("2020-01-01", date(2026, 9, 18)))
        self.assertFalse(expiry_is_past("2030-01-01", date(2026, 9, 18)))
        self.assertEqual(normalize_type("lična karta"), "licna_karta")
        self.assertEqual(normalize_type("licna_karta"), "licna_karta")
        self.assertEqual(normalize_type("passport"), "pasos")
        payload = parse_vision_payload(
            '```json\n{"readable":true,"type":"licna_karta","expiry":"2024-01-15"}\n```'
        )
        self.assertEqual(payload.get("type"), "licna_karta")

    def test_apply_expired_and_unreadable(self) -> None:
        doc = _FakeDoc()
        apply_vision_result(
            doc,  # type: ignore[arg-type]
            {"readable": True, "type": "licna_karta", "expiry": "2020-06-01"},
            date(2026, 9, 18),
        )
        self.assertEqual(doc.extracted_type, "licna_karta")
        self.assertEqual(doc.status, "expired")
        apply_vision_result(doc, {"readable": False}, date(2026, 9, 18))  # type: ignore[arg-type]
        self.assertEqual(doc.status, "unreadable")
        self.assertIsNone(doc.extracted_type)

    def test_checklist_statuses(self) -> None:
        as_of = date(2026, 9, 18)
        expired = _FakeDoc(
            extracted_type="licna_karta",
            extracted_expiry="2020-01-01",
            status="expired",
        )
        item = checklist_item(
            doc_type="licna_karta",
            how_to_obtain="Ponesi LK.",
            pool=[expired],
            attached=[expired],
            as_of=as_of,
        )
        self.assertEqual(item.status, "expired")
        self.assertIn("2020-01-01", item.message)
        self.assertNotIn("originalan", item.message.lower())

        pasos = _FakeDoc(extracted_type="pasos", extracted_expiry="2030-01-01", status="complete")
        mismatch = checklist_item(
            doc_type="licna_karta",
            how_to_obtain="",
            pool=[pasos],
            attached=[pasos],
            as_of=as_of,
        )
        self.assertEqual(mismatch.status, "mismatch")
        self.assertIn("pasoš", mismatch.message)

        uplatnica = checklist_item(
            doc_type="uplatnica_euprava",
            how_to_obtain="eUprava",
            pool=[pasos],
            attached=[pasos],
            as_of=as_of,
        )
        self.assertEqual(uplatnica.status, "missing")
        self.assertEqual(uplatnica.message, MISSING_MSG)

        pending = _FakeDoc(status=None, extracted_type=None)
        waiting = checklist_item(
            doc_type="licna_karta",
            how_to_obtain="",
            pool=[pending],
            attached=[pending],
            as_of=as_of,
        )
        self.assertEqual(waiting.status, "missing")
        self.assertEqual(waiting.message, SCAN_NEXT_MSG)

        empty = checklist_item(
            doc_type="licna_karta",
            how_to_obtain="",
            pool=[],
            attached=[],
            as_of=as_of,
        )
        self.assertEqual(empty.message, MISSING_MSG)


def _vision(raw: str):
    def _fake(_image_bytes: bytes, *, mime: str = "image/jpeg", timeout: float = 20.0):
        return {"raw": raw}

    return _fake


class Phase3ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cm = TestClient(app)
        cls.client = cls._cm.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._cm.__exit__(None, None, None)

    def _select_lk(self) -> str:
        created = self.client.post("/cases", json={"text": "istekla mi je lična"}).json()
        picked = self.client.post(
            f"/cases/{created['case_id']}/select",
            json={"slug": "licna-karta-zamena"},
        )
        self.assertEqual(picked.status_code, 200, picked.text)
        return created["case_id"]

    def test_pdf_is_unreadable(self) -> None:
        case_id = self._select_lk()
        attached = self.client.post(
            f"/cases/{case_id}/documents",
            files={"file": ("lk.pdf", b"%PDF-1.4 junk", "application/pdf")},
        )
        self.assertEqual(attached.json().get("status"), "unreadable")
        status = self.client.get(f"/cases/{case_id}/document-status").json()
        lk = next(item for item in status["items"] if item["type"] == "licna_karta")
        self.assertEqual(lk["status"], "unreadable")
        self.assertEqual(lk["message"], UNREADABLE_MSG)
        self.assertNotIn("originalan", lk["message"].lower())

    def test_expired_id_scan(self) -> None:
        case_id = self._select_lk()
        raw = '{"readable":true,"type":"licna_karta","expiry":"2020-03-01"}'
        with patch("app.services.extraction.extract_document_openai_vision", side_effect=_vision(raw)):
            attached = self.client.post(
                f"/cases/{case_id}/documents",
                files={"file": ("lk.png", TINY_PNG, "image/png")},
            )
        self.assertEqual(attached.status_code, 200, attached.text)
        self.assertEqual(attached.json()["extracted_type"], "licna_karta")
        self.assertEqual(attached.json()["extracted_expiry"], "2020-03-01")
        self.assertEqual(attached.json()["status"], "expired")
        items = self.client.get(f"/cases/{case_id}/document-status").json()["items"]
        lk = next(item for item in items if item["type"] == "licna_karta")
        self.assertEqual(lk["status"], "expired")
        self.assertEqual(lk["extracted_expiry"], "2020-03-01")
        uplatnica = next(item for item in items if item["type"] == "uplatnica_euprava")
        self.assertEqual(uplatnica["status"], "missing")
        self.assertEqual(uplatnica["message"], MISSING_MSG)

    def test_mismatch_passport_vs_id(self) -> None:
        case_id = self._select_lk()
        raw = '{"readable":true,"type":"pasos","expiry":"2030-01-01"}'
        with patch("app.services.extraction.extract_document_openai_vision", side_effect=_vision(raw)):
            self.client.post(
                f"/cases/{case_id}/documents",
                files={"file": ("pasos.png", TINY_PNG, "image/png")},
            )
        items = self.client.get(f"/cases/{case_id}/document-status").json()["items"]
        lk = next(item for item in items if item["type"] == "licna_karta")
        self.assertEqual(lk["status"], "mismatch")
        self.assertIn("pasoš", lk["message"])

    def test_wallet_type_reused_on_new_case(self) -> None:
        raw = '{"readable":true,"type":"licna_karta","expiry":"2021-05-05"}'
        user = self.client.post(
            "/auth/register",
            json={"email": "vision@example.com", "password": "lozinka12", "name": "Vida"},
        )
        self.assertEqual(user.status_code, 200, user.text)
        headers = {"Authorization": f"Bearer {user.json()['access_token']}"}
        with patch("app.services.extraction.extract_document_openai_vision", side_effect=_vision(raw)):
            wallet = self.client.post(
                "/documents",
                headers=headers,
                files={"file": ("lk.png", TINY_PNG, "image/png")},
            )
        self.assertEqual(wallet.status_code, 200, wallet.text)
        wallet_id = wallet.json()["id"]
        created = self.client.post(
            "/cases",
            headers=headers,
            json={"text": "istekla mi je lična", "document_ids": [wallet_id]},
        )
        self.assertEqual(created.status_code, 200, created.text)
        case_id = created.json()["case_id"]
        self.client.post(
            f"/cases/{case_id}/select",
            headers=headers,
            json={"slug": "licna-karta-zamena"},
        )
        items = self.client.get(
            f"/cases/{case_id}/document-status",
            headers=headers,
        ).json()["items"]
        lk = next(item for item in items if item["type"] == "licna_karta")
        self.assertEqual(lk["status"], "expired")
        self.assertEqual(lk["document_id"], wallet_id)

    def test_image_without_key_waits_for_scan(self) -> None:
        settings.openai_api_key = ""
        try:
            case_id = self._select_lk()
            attached = self.client.post(
                f"/cases/{case_id}/documents",
                files={"file": ("lk.png", TINY_PNG, "image/png")},
            )
            self.assertIsNone(attached.json().get("extracted_type"))
            self.assertIsNone(attached.json().get("status"))
            items = self.client.get(f"/cases/{case_id}/document-status").json()["items"]
            self.assertTrue(all(item["status"] == "missing" for item in items))
            self.assertTrue(all(item["message"] == SCAN_NEXT_MSG for item in items))
        finally:
            settings.openai_api_key = "sk-test-phase3"


if __name__ == "__main__":
    unittest.main(verbosity=2)
