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

Matching (Faza 2): demo keš samo za tačne rečenice na POST `/cases` (ne substring, ne `/retry`/`/clarify`). Inače xAI nad katalogom, jedan pokušaj ~15s u threadu, van DB transakcije. Ako Grok padne, keyword fallback. Kartice nemaju instituciju.

Demo POST `/cases`: `"istekla mi je lična"` i `"selim se iz Pirota u Beograd"`.
