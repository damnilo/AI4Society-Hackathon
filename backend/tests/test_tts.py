"""OpenAI TTS vodiča. Mock mreže.

Pokretanje iz backend/: python tests/test_tts.py
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

tmpdir = Path(tempfile.mkdtemp(prefix="putokaz-tts-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(tmpdir / 't.db').as_posix()}"
os.environ["UPLOAD_DIR"] = str(tmpdir / "uploads")
os.environ["JWT_SECRET"] = "test-secret-tts"
os.environ["MASTER_KEY"] = "test-master-key-tts"
os.environ["XAI_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = "sk-test-tts"

from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.llm import synthesize_speech_openai  # noqa: E402
from app.main import app  # noqa: E402
from app.schemas import DocumentStatusItem  # noqa: E402
from app.services.speech import build_speech_script  # noqa: E402

settings.xai_api_key = ""
settings.openai_api_key = "sk-test-tts"


class SpeechScriptTests(unittest.TestCase):
    def test_includes_steps_office_and_missing(self) -> None:
        text = build_speech_script(
            title="Zamena lične karte",
            steps=[{"title": "Zakažite", "description": "Preko eUprave."}],
            office=SimpleNamespace(
                name="PU Beograd",
                address="Ljermontova 12a",
                phone="011",
            ),
            items=[
                DocumentStatusItem(
                    type="licna_karta",
                    status="expired",
                    message="isteklo",
                ),
                DocumentStatusItem(
                    type="uplatnica_euprava",
                    status="complete",
                    message="ok",
                ),
            ],
        )
        self.assertIn("Zamena lične karte", text)
        self.assertIn("Korak 1", text)
        self.assertIn("Ljermontova", text)
        self.assertIn("lična karta", text)
        self.assertNotIn("uplatnica", text.lower())
        self.assertIn("nije eUprava", text)


class TtsApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cm = TestClient(app)
        cls.client = cls._cm.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._cm.__exit__(None, None, None)

    def test_speech_without_key_is_503(self) -> None:
        created = self.client.post("/cases", json={"text": "istekla mi je lična"}).json()
        settings.openai_api_key = ""
        try:
            response = self.client.post(
                f"/cases/{created['case_id']}/speech",
                json={"slug": "licna-karta-zamena"},
            )
            self.assertEqual(response.status_code, 503, response.text)
        finally:
            settings.openai_api_key = "sk-test-tts"

    def test_speech_returns_mp3(self) -> None:
        created = self.client.post("/cases", json={"text": "istekla mi je lična"}).json()
        fake = MagicMock()
        fake.content = b"ID3fake-mp3"
        fake.raise_for_status = MagicMock()
        with patch("app.llm.httpx.post", return_value=fake) as post:
            response = self.client.post(
                f"/cases/{created['case_id']}/speech",
                json={"slug": "licna-karta-zamena"},
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers["content-type"], "audio/mpeg")
        self.assertEqual(response.content, b"ID3fake-mp3")
        sent = post.call_args.kwargs["json"]
        self.assertEqual(sent["model"], "gpt-4o-mini-tts")
        self.assertIn("ličn", sent["input"].lower())
        self.assertNotIn("sk-test", str(sent))

    def test_synthesize_requires_key(self) -> None:
        settings.openai_api_key = ""
        try:
            with self.assertRaises(RuntimeError):
                synthesize_speech_openai("Zdravo")
        finally:
            settings.openai_api_key = "sk-test-tts"


if __name__ == "__main__":
    unittest.main(verbosity=2)
