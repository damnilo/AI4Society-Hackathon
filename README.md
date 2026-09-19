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
U `backend/.env` ubacite `XAI_API_KEY` (iz `api_keys.txt` / SPACEX). Docker: `cd backend && docker compose up --build` (Postgres + API).

## Demo rečenice i skenovi

1. `istekla mi je lična` — zamena lične karte. Prilog: `demo/istekla-licna-karta.png` → **Isteklo**. Isti tok + `demo/necitko-sken.pdf` → **Nečitko**. Isti tok + `demo/pasos.png` → **Ne odgovara**.
2. `selim se iz Pirota u Beograd` — prijava prebivališta, šalter Ljermontova 12a.

Uputstvo za žiri: `demo/README.md`. Matching radi i kao gost. Nalog je samo novčanik skenova.
