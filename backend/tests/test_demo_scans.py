"""Korak 1 — sintetski skenovi postoje i sniff radi.

Pokretanje iz backend/: python tests/test_demo_scans.py
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from app.services.extraction import is_image_mime, sniff_media  # noqa: E402

DEMO = REPO / "demo"


class DemoScanAssetsTests(unittest.TestCase):
    def test_files_exist(self) -> None:
        self.assertTrue((DEMO / "istekla-licna-karta.png").is_file())
        self.assertTrue((DEMO / "pasos.png").is_file())
        self.assertTrue((DEMO / "necitko-sken.pdf").is_file())
        self.assertTrue((DEMO / "README.md").is_file())

    def test_sniff_types(self) -> None:
        lk = (DEMO / "istekla-licna-karta.png").read_bytes()
        pasos = (DEMO / "pasos.png").read_bytes()
        pdf = (DEMO / "necitko-sken.pdf").read_bytes()
        self.assertEqual(sniff_media(lk), "image/png")
        self.assertEqual(sniff_media(pasos), "image/png")
        self.assertEqual(sniff_media(pdf), "application/pdf")
        self.assertGreater(len(lk), 8_000)
        self.assertGreater(len(pasos), 8_000)
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertFalse(is_image_mime("application/pdf"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
