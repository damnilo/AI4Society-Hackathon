"""CORS origins and production secret guards.

Pokretanje iz backend/:
    python tests/test_config.py
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from app.config import Settings  # noqa: E402


def make_settings(**env: str) -> Settings:
    payload = {
        "JWT_SECRET": "a" * 32,
        "MASTER_KEY": "b" * 32,
        "ENVIRONMENT": "development",
        "CORS_ORIGINS": "http://localhost:3000",
        "FRONTEND_ORIGIN": "",
        "DATABASE_URL": "sqlite:///./nasalter.db",
    }
    payload.update(env)
    with patch.dict(os.environ, payload, clear=False):
        return Settings(_env_file=None)


class ConfigTests(unittest.TestCase):
    def test_cors_keeps_localhost_and_adds_frontend_origin(self) -> None:
        settings = make_settings(FRONTEND_ORIGIN="nasalter-web.onrender.com")
        origins = settings.cors_origin_list
        self.assertIn("http://localhost:3000", origins)
        self.assertIn("http://127.0.0.1:3000", origins)
        self.assertIn("https://nasalter-web.onrender.com", origins)

    def test_cors_strips_slash_and_dedupes(self) -> None:
        settings = make_settings(
            CORS_ORIGINS="http://localhost:3000/,https://nasalter-web.onrender.com",
            FRONTEND_ORIGIN="https://nasalter-web.onrender.com/",
        )
        origins = settings.cors_origin_list
        self.assertEqual(origins.count("https://nasalter-web.onrender.com"), 1)
        self.assertNotIn("https://nasalter-web.onrender.com/", origins)

    def test_weak_secrets_rejected_when_deployed(self) -> None:
        settings = make_settings(
            ENVIRONMENT="production",
            JWT_SECRET="change-me-phase-1",
            MASTER_KEY="dev-only-not-for-prod",
        )
        with self.assertRaises(RuntimeError):
            settings.ensure_deploy_secrets()

    def test_strong_secrets_ok_when_deployed(self) -> None:
        settings = make_settings(ENVIRONMENT="production")
        settings.ensure_deploy_secrets()

    def test_weak_secrets_allowed_locally(self) -> None:
        settings = make_settings(
            JWT_SECRET="change-me-phase-1",
            MASTER_KEY="dev-only-not-for-prod",
        )
        settings.ensure_deploy_secrets()


if __name__ == "__main__":
    unittest.main()
