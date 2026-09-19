# NaŠalter

Vodič kroz državne procedure iz slobodnog teksta (ili glasa). Nije eUprava: ne podnosimo zahtev, ne zakazujemo i ne overavamo dokumenta.

## Pokretanje

U dva terminala, iz korena repo-a:

```bash
cd backend && python -m uvicorn app.main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

API: `http://localhost:8000` · UI: `http://localhost:3000`  
`frontend` čita `NEXT_PUBLIC_API_URL` (podrazumevano `http://localhost:8000`).  
U `backend/.env` ubacite `XAI_API_KEY` (iz `api_keys.txt` / SPACEX), plus `JWT_SECRET` i `MASTER_KEY` (ne `change-me`). Docker: `cd backend && docker compose up --build` (opciono Postgres + API).

## Render

App Router (nije `output: export`) → dva web servisa iz `render.yaml`:

1. **nasalter-api** — `rootDir: backend`, SQLite, `JWT_SECRET`/`MASTER_KEY` se generišu. U dashboard ubaciti `XAI_API_KEY` i `OPENAI_API_KEY`. `FRONTEND_ORIGIN` se veže na host FE servisa.
2. **nasalter-web** — `npm ci && npm run build`, `npx next start --hostname 0.0.0.0 --port $PORT`. **Build-time:** `NEXT_PUBLIC_API_URL=https://nasalter-api.onrender.com` (ako Render doda sufiks na ime, uskladi URL).

SQLite na Renderu se gubi posle restarta. Postgres iz compose-a samo ako treba persistencija.

## Demo rečenice i skenovi

1. `istekla mi je lična` — zamena lične karte. Prilog: `demo/istekla-licna-karta.png` → **Isteklo**. Isti tok + `demo/necitko-sken.pdf` → **Nečitko**. Isti tok + `demo/pasos.png` → **Ne odgovara**.
2. `selim se iz Pirota u Beograd` — prijava prebivališta, šalter Ljermontova 12a.

Uputstvo za žiri: `demo/README.md`. Matching radi i kao gost. Nalog je samo novčanik skenova.
