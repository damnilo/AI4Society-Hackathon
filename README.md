# NaŠalter

**Od pitanja do rešenja.**

Vodič kroz državne procedure u Srbiji. Građanin opiše nameru svojim rečima (ili glasom), opciono priloži sken, i dobije proceduru, šta da ponese i na koji šalter da ode.

Nije eUprava: **ne podnosimo zahtev, ne zakazujemo termin i ne overavamo dokumenta.**

## Šta radi

1. Unos namere (tekst ili „Reci naglas“).
2. 2–3 kartice procedura (bez institucije na kartici).
3. Vodič: koraci, checklist papira, adresa šaltera, mapa, glasovno čitanje, štampa.
4. Opcioni nalog = novčanik skenova + mesto (Pirot / Beograd / Niš). Gost sme matching i prilog uz zahtev.

Adresa šaltera dolazi **samo iz tabele `offices`**. LLM ne piše ulicu. Checklist je provera polja sa skena (ima / fali / isteklo / nečitko / ne odgovara), nije pravna overa originala.

Lokalne usluge Grada Pirota u katalogu se nude samo ako je Pirot u tekstu ili na nalogu.

## Pokretanje (lokalno)

Dva terminala, iz korena repo-a.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

U `backend/.env` ubaciti:

- `XAI_API_KEY` (xAI / Grok, matching)
- `OPENAI_API_KEY` (Vision + TTS)
- `JWT_SECRET` i `MASTER_KEY` — jedinstvene vrednosti, ne `change-me` / `dev-only`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

```bash
python -m uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

| | URL |
|--|--|
| UI | http://localhost:3000 |
| API | http://localhost:8000 |
| OpenAPI | http://localhost:8000/docs |
| Health | http://localhost:8000/health |
| LLM health | http://localhost:8000/health/llm |

Frontend čita `NEXT_PUBLIC_API_URL` (podrazumevano `http://localhost:8000`). Seed kataloga se upsert-uje pri startu API-ja. SQLite je default (`backend/nasalter.db`).

Opciono Postgres + API: `cd backend && docker compose up --build` (samo ako treba persistencija).

## Demo pred žirijem

Tačne rečenice na **prvi** `POST /cases` (ne substring, ne retry/clarify). Cheat-sheet: [`demo/README.md`](demo/README.md). Skenovi su **sintetika**, nisu prave isprave.

| Unos | Ishod |
|------|--------|
| `istekla mi je lična` | zamena lične karte |
| + `demo/istekla-licna-karta.png` | checklist **Isteklo** (važi do 2024-03-01) |
| + `demo/necitko-sken.pdf` | **Nečitko** (PDF, Vision se ne zove) |
| + `demo/pasos.png` | **Ne odgovara** |
| `selim se iz Pirota u Beograd` | prijava prebivališta, šalter **Ljermontova 12a** |

Kartice izlaze odmah (matching na tekst). Status skena se crta posle uploada. Ako piše „Čitam sken…“, sačekati par sekundi.

Prioritet mesta za šalter: tekst (Pirot→Beograd) **uvek** pobedi nalog. Inače `municipality` sa naloga. Inače pitanje „U kom mestu ste?“ na vodiču.

## Stek

| Sloj | Tehnologija |
|------|-------------|
| Frontend | Next.js 15 (App Router), React 19 |
| Backend | FastAPI, SQLAlchemy 2, SQLite (opciono Postgres) |
| Matching | demo keš → xAI Grok → keyword fallback |
| Skenovi | OpenAI Vision (`gpt-4o-mini`), PDF = nečitko |
| Glas vodiča | OpenAI TTS (`gpt-4o-mini-tts`); fallback `speechSynthesis` |
| Fajlovi | AES-GCM na disku; gost ~48h retention |

## Matching, šalter, Vision

- Demo keš samo za gornje dve rečenice na `POST /cases`.
- Kartice nemaju instituciju; institucija i adresa dolaze posle izbora.
- `GET /cases/{id}/document-status`: complete / missing / expired / unreadable / mismatch.
- `POST /cases/{id}/speech` → mp3. Tekst je sa vodiča/kataloga, ne iz LLM-a. Ako 503, UI čita glas pregledača.

## Testovi (backend)

```bash
cd backend
python tests/test_bug_regressions.py
python tests/test_config.py
python tests/test_phase3_documents.py
python tests/test_tts.py
python tests/test_demo_scans.py
python scripts/smoke_phase1.py
python scripts/smoke_phase2.py
```

## Render

App Router (nije `output: export`) → dva web servisa iz [`render.yaml`](render.yaml):

1. **nasalter-api** — `rootDir: backend`, SQLite, `JWT_SECRET` / `MASTER_KEY` se generišu. U dashboard ubaciti `XAI_API_KEY` i `OPENAI_API_KEY`. `FRONTEND_ORIGIN` se veže na host FE servisa. Localhost CORS ostaje; FE URL ide u `FRONTEND_ORIGIN` ili `CORS_ORIGINS`.
2. **nasalter-web** — `npm ci && npm run build`, zatim `npx next start --hostname 0.0.0.0 --port $PORT`. **Build-time:** `NEXT_PUBLIC_API_URL=https://nasalter-api.onrender.com` (ako Render doda sufiks na ime, uskladiti URL).

SQLite na Renderu se gubi posle restarta. Postgres samo ako treba persistencija. Slabi defaulti za `JWT_SECRET` / `MASTER_KEY` ruše start kada je `RENDER=true` ili `ENVIRONMENT=production`.

## Struktura

```
backend/     FastAPI, seed, testovi
frontend/    Next.js UI
demo/        sintetski skenovi i uputstvo za žiri
render.yaml  Render blueprint
```

Detalji API-ja: [`backend/README.md`](backend/README.md).
