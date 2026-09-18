# Putokaz — FINALNI radni plan

**Ti = frontend (Next.js).** **Kolega = backend (FastAPI + Postgres).**  
Repo: `frontend/` (ti) + `backend/` (kolega). Ugovor: OpenAPI + mock JSON.

Analiza (ocena, mentori): Cursor `ocena_plana_putokaz_analiza_prethodna.plan.md`.

---

## Tok (oba gradite isti)

1. Prvi ekran: tekst ili glas, plus opciono dokumenta (nije obavezno).
2. Ako ima fajlova: Vision → JSON; u Grok samo JSON + tekst.
3. 2–3 kartice procedure: opis, score, zašto. **Bez institucije na kartici.**
4. Izbor ili “Nijedna nije to — dopuni opis”.
5. Posle izbora: institucija, checklist, nadležna adresa iz `offices` (Pirot→Beograd = Ljermontova 12a). LLM ne piše ulicu.
6. Status priloga: complete / missing / expired / unreadable / mismatch. Nije pravna overa.
7. Vodič, related, izvor. TTS „pročitaj vodič“. Mapa (pin na iste lat/lng) **nije zaključana** — odluka posle 5/6.
8. Nalog sme da čuva opštinu; ako u tekstu nema mesta, to je fallback za šalter (tekst > nalog > pitanje na vodiču).

Gost sme matching + prilog uz case. Nalog = novčanik + opciono mesto.

**Ne radimo u 48h:** e-potpis, podnošenje, zakazivanje, crawl, nearby MUP, Pirot-only katalog, četbot.

**Must-have:** Faza 2 + Faza 4. Faza 3 (Vision/checklist) je u toku.  
**Zaključano posle 3 (biće vremena):** TTS, mesto na nalogu, synthetic skenovi. Print checklist i mapa — razmisli, nije obaveza.

---

## Faza 0 — temelj (~3–4h)

Cilj: repo, ugovor, mock, prazni ekrani. FE ne čeka pravi LLM.

**Zajedno (30–45 min):** spisak 12–18 procedura (gusti intent_examples, oba pisma) + 3 kancelarije (PU Pirot, PU Beograd Ljermontova 12a, PU Niš) sa adresom, telefonom, lat/lng, source_url.

**Kolega (BE):**
- `backend/`: FastAPI, Postgres, docker-compose, Alembic, CORS, `GET /health`
- `openapi.yaml` + `examples/` mock za sve rute ispod
- `.env.example` (`XAI_API_KEY`, `OPENAI_API_KEY`)
- `llm.py`: ping na xAI
- seed skripta (može prazan JSON dok ne završite listu)

**Ti (FE):**
- `frontend/`: Next.js App Router, srpski layout
- API klijent koji čita mock / OpenAPI
- Prazni ekrani: unos, kartice, retry, vodič, login, dashboard dokumenata
- Env: `NEXT_PUBLIC_API_URL`

**Izlaz:** `docker-compose up` diže API+DB; ti lokalno vidiš mock tok.

---

## Faza 1 — nalog i novčanik (~5–7h)

Cilj: login čuva dokumente. **Matching i prilog na unosu rade i bez naloga.**

**Kolega (BE):**
- `POST /auth/register`, `login`, `refresh`
- `GET/POST/DELETE /documents` (samo vlasnik)
- Gost: prilog vezan za `case_id`, `user_id` null
- Retention/purge ako stigne; AES-GCM samo ako ne blokira Fazu 2
- Ne logovati PII

**Ti (FE):**
- Register / login / logout
- Zona dokumenata (lista, upload, brisanje)
- GDPR + retention tekst
- Unos namere **otvoren bez logina**, uključujući “priloži uz ovaj zahtev”
- Polje opštine na registraciji ide u **Fazu 5** (BE već ima `municipality` na User/MeOut)

**Ako kasni:** demo nalog, matching ne čeka šifrovanje.

---

## Faza 2 — matching (MUST, ~6–8h)

Cilj: rečenica → 2–3 kartice → izbor ili dopuna.

**Kolega (BE):**
- `POST /cases` `{ text, document_ids? }` → candidates (slug, title, plain_summary, score, rationale), need_clarification, questions
- `POST /cases/{id}/retry` (novi tekst, isti prilozi)
- `POST /cases/{id}/clarify`
- `POST /cases/{id}/select`
- Prag poverenja; xAI nad katalogom
- Keš JSON za: `istekla mi je lična` i `selim se iz Pirota u Beograd`
- Ako Vision nije spreman: matching samo na tekst

**Ti (FE):**
- Textarea + mikrofon (Web Speech) → isti POST /cases
- “Priloži dokument (opciono)”
- Kartice: score bar, zašto, kratak opis; **nema** MUP kao naslov
- Dugme “Nijedna nije to — dopuni opis”
- Klik na karticu = select

**Izlaz:** demo rečenica daje 2–3 predloga i izbor radi.

---

## Faza 3 — dokumenta i validacija (~5–7h)

Cilj: ekstrakcija + provera roka/kompletnosti, nije overa.

**Kolega (BE):**
- Vision na priloge (prvi korak ili kasnije)
- `GET /cases/{id}/document-status`
- Statusi: complete, missing, expired (datum isteka u prošlosti), unreadable, mismatch
- Poređenje sa `required_documents` posle select
- Novčanik: isti tip dokumenta se vuče za novi case
- Poruke bez “dokument je originalan”

**Ti (FE):**
- Lista priloga na unosu
- Posle izbora: panel ima / fali / isteklo / nečitko / mismatch
- Disclaimer: “nije pravna overa”
- Radi i bez ijednog fajla (samo checklist “šta poneti”)

---

## Faza 4 — vodič i kancelarija (MUST, ~5–6h)

Cilj: posle izbora — koraci, dokumenta, **tačna adresa**.

**Kolega (BE):**
- `GET /cases/{id}/guide`: steps, checklist, institution, channel, related, source, last_verified_at
- Office resolver: from_place/to_place + jurisdiction_rule → red u `offices` (name, address, phone, lat, lng) ili `office_missing`
- Pirot→Beograd + `new_residence` → Ljermontova 12a, ne PU Pirot
- LLM ne vraća ulicu

**Ti (FE):**
- Step-by-step vodič
- Checklist + “kako pribaviti” što fali
- CTA eUprava ako `channel` ima online
- Blok “Gde da odeš”: ime, adresa, telefon (tekst obavezan)
- Related procedure, badge izvora i datuma
- Ako nema mesta u tekstu: polje „U kom mestu ste?“ (ne izmišljati ulicu)
- Mapa još **nije** obaveza (vidi Fazu 5)

**Izlaz:** scenario 2 radi do adrese u Beogradu.

---

## Faza 5 — extra (samo ako 2, 3 i 4 drže demo)

Cilj: pristupačnost i šalter bez ponovnog kucanja grada. Nije čet, nije nearby MUP.

### Zaključano

**3. TTS „Pročitaj vodič“ (ti, FE)**  
- Dugme na vodiču: `speechSynthesis`, `sr-RS` — naslov, koraci, adresa, šta fali. Dugme Stani.  
- Tekst sa stranice, ne iz LLM-a. Ako nema srpskog glasa: poruka, ne pad (isto kao mikrofon).  
- Glas na unosu već postoji (Faza 2).

**4. Mesto na nalogu → šalter (oba)**  
- Ti: na `/prijava` (register) polje Pirot / Beograd / Niš; vrednost ide u `AuthRegister.municipality`; prikaz na `/me` ako treba.  
- Kolega: `select` / `resolve_office` koristi `user.municipality` **samo** kad `extract_from_to` nije našao mesto.  
- Prioritet: mesta u tekstu (npr. Pirot→Beograd) **uvek** pobede nalog. Inače nalog. Inače pitanje na vodiču.  
- Gost bez naloga: i dalje „U kom mestu ste?“. LLM i dalje ne piše ulicu.

### Nije zaključano (razmišljamo)

**1. Mapa** — link `maps.google.com/?q=lat,lng` ili embed, pin na **istu** kancelariju iz `office`, ne nearby. Radi se samo ako ostane vreme posle TTS + municipality + skenova. Ako `office_missing`, nema pin.

Print/PDF checklist: isto, nije obaveza.

**Kolega (ostalo, ako stigne):** `explain_legal` iz kataloga (zašto prebivalište a ne boravište). Exa/Firecrawl preskočiti. Deploy API samo ako lokalni demo radi.

---

## Faza 6 — demo (zajedno)

Oboje: tri scenarija, disclaimer, pitch. **Synthetic skenovi su zaključani** (ideja 5) — bez pravih ličnih.

Folder npr. `demo/` (lažni podaci, krupan datum, u pitch-u reći da je sintetika):

| Fajl | Namena | Očekivani status na vodiču |
|------|--------|----------------------------|
| Istekla LK (datum u prošlosti) | gost + „istekla mi je lična“ | **Isteklo** + „važi do …“ |
| Mutna / isečena slika ili loš PDF | isti tok | **Nečitko** |
| Pasoš uz zahtev za LK | mismatch | **Ne odgovara**, ne „Imate ličnu“ |

Kartice izlaze **odmah** (matching samo tekst). Vision upisuje tip/rok posle selecta; FE crta samo `GET /document-status`.

Scenariji pred žirijem:

1. Istekla lična + sken → kartice → Isteklo + vodič (+ TTS ako je 5 gotova). Ako nema grada: mesto sa naloga ili pitanje na vodiču.  
2. Selim se iz Pirota u Beograd → Ljermontova 12a (tekst pobedi nalog).  
3. Nejasan unos → pitanja / retry.

Pitch: eUprava kad znaš ime usluge; mi iz namere i papira do nadležnog šaltera, bez eID-a.

---

## API ugovor (Faza 0)

Gost: POST /cases, POST /cases/{id}/documents, retry, clarify, select, GET guide.  
Nalog: auth, /documents, document-status, dashboard.

Kontrakt se ne lomi bez dogovora. Katalog i adrese samo na BE.

---

## Red sečenja

1. Faza 2 + 4 (must)  
2. Faza 3 + 1  
3. Faza 5 zaključano: TTS, municipality fallback, pa Faza 6 skenovi  
4. Mapa, print, `explain_legal`, deploy — samo ako 1–3 već rade pred žirijem
