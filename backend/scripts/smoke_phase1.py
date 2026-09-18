"""Phase 1 auth/wallet/guest smoke. Run from backend: python scripts/smoke_phase1.py"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

tmpdir = Path(tempfile.mkdtemp(prefix="putokaz-p1-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(tmpdir / 't.db').as_posix()}"
os.environ["UPLOAD_DIR"] = str(tmpdir / "uploads")
os.environ["JWT_SECRET"] = "test-secret-phase1"
os.environ["MASTER_KEY"] = "test-master-key-phase1"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def fail(msg: str) -> None:
    raise SystemExit(f"FAIL: {msg}")


def main() -> None:
    with TestClient(app) as client:
        health = client.get("/health")
        if health.status_code != 200 or health.json().get("catalog", {}).get("procedures", 0) < 1:
            fail(f"health {health.status_code} {health.text}")

        guest = client.post("/cases", json={"text": "selim se iz Pirota u Beograd"})
        if guest.status_code != 200:
            fail(f"guest case {guest.status_code} {guest.text}")
        case_id = guest.json()["case_id"]
        slugs = [c["slug"] for c in guest.json()["candidates"]]
        if "prijava-prebivalista" not in slugs:
            fail(f"expected move slug, got {slugs}")
        loaded = client.get(f"/cases/{case_id}")
        if loaded.status_code != 200 or not loaded.json().get("text"):
            fail(f"GET case {loaded.status_code} {loaded.text}")
        if any("institution" in c for c in loaded.json()["candidates"]):
            fail("candidate cards must not include institution")
        original_text = loaded.json()["text"]
        clarified = client.post(
            f"/cases/{case_id}/clarify",
            json={"answers": {"stalnost": "nije stalno, studiram tri meseca"}},
        )
        if clarified.status_code != 200:
            fail(f"clarify {clarified.status_code} {clarified.text}")
        if clarified.json().get("text") != original_text:
            fail(f"clarify overwrote raw_text: {clarified.json().get('text')}")
        if [c["score"] for c in clarified.json()["candidates"]][:3] == [0.94, 0.48, 0.33]:
            fail("demo cache must not win on clarify")
        picked = client.post(
            f"/cases/{case_id}/select",
            json={"slug": "prijava-prebivalista"},
        )
        if picked.status_code != 200:
            fail(f"select {picked.status_code} {picked.text}")
        office = picked.json().get("office") or {}
        if "Ljermontova" not in str(office.get("address")):
            fail(f"expected Ljermontova, got {office}")
        if "Pirot" in str(office.get("address")):
            fail(f"must not resolve to Pirot: {office}")

        secret = b"guest-scan-payload-do-not-store-plain"
        attach = client.post(
            f"/cases/{case_id}/documents",
            files={"file": ("lk.pdf", secret, "application/pdf")},
        )
        if attach.status_code != 200:
            fail(f"guest attach {attach.status_code} {attach.text}")
        body = attach.json()
        if body.get("user_id") is not None:
            fail(f"guest attach must have user_id null, got {body}")
        if not body.get("purge_at"):
            fail("guest attach missing purge_at")

        stored = list((tmpdir / "uploads").glob("*.enc"))
        if not stored:
            fail("encrypted file not written")
        blob = stored[0].read_bytes()
        if secret in blob:
            fail("plaintext leaked into encrypted blob")

        if client.get("/documents").status_code != 401:
            fail("wallet without auth must be 401")
        if client.get("/me").status_code != 401:
            fail("/me without auth must be 401")
        bad = client.post(
            "/cases",
            json={"text": "istekla mi je lična"},
            headers={"Authorization": "Bearer not-a-token"},
        )
        if bad.status_code != 401:
            fail(f"invalid bearer must 401, got {bad.status_code}")

        a = client.post(
            "/auth/register",
            json={
                "email": "ana@example.com",
                "password": "lozinka12",
                "name": "Ana",
            },
        )
        if a.status_code != 200:
            fail(f"register A {a.status_code} {a.text}")
        tok_a = a.json()
        for key in ("access_token", "refresh_token", "user_id", "email", "name"):
            if key not in tok_a:
                fail(f"TokenOut missing {key}")
        ha = {"Authorization": f"Bearer {tok_a['access_token']}"}

        me = client.get("/me", headers=ha)
        if me.status_code != 200 or "gdpr_note" not in me.json():
            fail(f"/me {me.status_code} {me.text}")

        wallet = client.post(
            "/documents",
            headers=ha,
            files={"file": ("pasos.pdf", b"wallet-bytes", "application/pdf")},
        )
        if wallet.status_code != 200:
            fail(f"wallet upload {wallet.status_code} {wallet.text}")
        wallet_id = wallet.json()["id"]
        if wallet.json().get("user_id") != tok_a["user_id"]:
            fail("wallet doc user_id mismatch")
        if wallet.json().get("purge_at") is not None:
            fail("wallet docs must not have purge_at")

        listed = client.get("/documents", headers=ha)
        if listed.status_code != 200 or len(listed.json()) != 1:
            fail(f"wallet list {listed.status_code} {listed.text}")

        linked = client.post(
            "/cases",
            json={"text": "istekla mi je lična", "document_ids": [wallet_id]},
            headers=ha,
        )
        if linked.status_code != 200:
            fail(f"case with wallet ids {linked.status_code} {linked.text}")

        claim = client.post("/me/claim", json={"case_id": case_id}, headers=ha)
        if claim.status_code != 200:
            fail(f"claim {claim.status_code} {claim.text}")
        after = client.get("/documents", headers=ha)
        claimed = [d for d in after.json() if d.get("case_id") == case_id]
        if not claimed or claimed[0].get("user_id") != tok_a["user_id"]:
            fail(f"claimed docs not in wallet: {after.json()}")
        if claimed[0].get("purge_at") is not None:
            fail("claimed doc still has purge_at")

        b = client.post(
            "/auth/register",
            json={"email": "bora@example.com", "password": "lozinka12", "name": "Bora"},
        )
        if b.status_code != 200:
            fail(f"register B {b.status_code} {b.text}")
        hb = {"Authorization": f"Bearer {b.json()['access_token']}"}
        steal = client.delete(f"/documents/{wallet_id}", headers=hb)
        if steal.status_code != 404:
            fail(f"other user delete must 404, got {steal.status_code} {steal.text}")
        steal_claim = client.post("/me/claim", json={"case_id": case_id}, headers=hb)
        if steal_claim.status_code != 403:
            fail(f"claim owned case must 403, got {steal_claim.status_code}")
        attach_b = client.post(
            f"/cases/{linked.json()['case_id']}/documents",
            headers=hb,
            files={"file": ("x.pdf", b"nope", "application/pdf")},
        )
        if attach_b.status_code != 403:
            fail(f"attach to others must 403, got {attach_b.status_code}")

        gone = client.delete(f"/documents/{wallet_id}", headers=ha)
        if gone.status_code != 200:
            fail(f"owner delete {gone.status_code} {gone.text}")

        login = client.post(
            "/auth/login",
            json={"email": "ana@example.com", "password": "lozinka12"},
        )
        if login.status_code != 200:
            fail(f"login {login.status_code} {login.text}")
        refreshed = client.post("/auth/refresh", json={"refresh_token": login.json()["refresh_token"]})
        if refreshed.status_code != 200:
            fail(f"refresh {refreshed.status_code} {refreshed.text}")

    print("Phase 1 smoke OK")


if __name__ == "__main__":
    main()
