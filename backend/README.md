# Putokaz backend (Faza 0–1)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# ubaci XAI_API_KEY iz api_keys.txt (SPACEX_API_KEY)
uvicorn app.main:app --reload --port 8000
```

SQLite podrazumevano (`putokaz.db`). Seed ulazi pri startu.

```bash
docker compose up --build
```

- `GET http://localhost:8000/health`
- `GET http://localhost:8000/health/llm`
- `GET http://localhost:8000/docs`
- Mock JSON: `examples/`
- FE: `NEXT_PUBLIC_API_URL=http://localhost:8000`

Matching i prilog uz case rade **bez naloga**. Nalog je novčanik (`/auth/*`, `/documents`, `GET /me`, `POST /me/claim`). Gostovi fajlovi imaju `user_id=null` i `purge_at` (~48h). Fajlovi su AES-GCM na disku; ne logujemo email ni ime fajla.

Seed JSON se **upsert-uje** pri startu — izmene u `backend/seed/*.json` ulaze bez brisanja `putokaz.db`.

Matching (Faza 2): demo keš samo za tačne rečenice na POST `/cases` (ne substring, ne `/retry`/`/clarify`). Inače xAI nad katalogom, jedan pokušaj ~15s u threadu, van DB transakcije. Ako Grok padne, keyword fallback. Kartice nemaju instituciju. Ako postoje izvučena polja sa skena, matching dobija `[skenovi]` JSON (tip/rok), ne sliku.

Faza 3: OpenAI Vision na jpg/png pri uploadu (case ili novčanik). `GET /cases/{id}/document-status` = complete / missing / expired / unreadable / mismatch. PDF i nečitko → unreadable. Nije pravna overa.

Faza 5: `POST /auth/register` i `PATCH /me` primaju `municipality` (`beograd` | `pirot` | `nis`). `POST /cases/{id}/select` koristi mesto sa naloga **samo** ako u tekstu nema grada. Tekst (Pirot→Beograd) uvek pobedi nalog. Gost i dalje dobija „Nedostaje mesto prebivališta“.

```bash
python tests/test_bug_regressions.py
python tests/test_phase3_documents.py
python scripts/smoke_phase1.py
python scripts/smoke_phase2.py
```

Demo POST `/cases`: `"istekla mi je lična"` i `"selim se iz Pirota u Beograd"`.
