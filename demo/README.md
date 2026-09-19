# Demo skenovi (sintetika)

Lažni podaci, krupan datum. **Nisu prave isprave.** Pred žirijem reci da je sintetika.

Regeneracija (opciono):

```bash
cd backend
.venv\Scripts\python.exe -m pip install pillow
.venv\Scripts\python.exe scripts/make_demo_scans.py
```

Koristiti **ova** imena (stari trio `istekla-lk.png` / `necitko.png` / `pasos-umesto-lk.png` je isti sadržaj, ne mešati na sceni):

| Fajl | Scena | Očekivani badge |
|------|--------|-----------------|
| `istekla-licna-karta.png` | gost + `istekla mi je lična` | **Isteklo** (važi do 2024-03-01) |
| `necitko-sken.pdf` | isti tok, loš prilog | **Nečitko** (PDF, Vision se ne zove) |
| `pasos.png` | isti tok, pogrešan dokument | **Ne odgovara** (pasoš uz zahtev za ličnu kartu) |

Kartice izlaze odmah (matching na tekst). Status se crta posle uploada sa `GET /document-status`. Ako piše „Čitam sken…“, sačekaj par sekundi.

Šalteri u katalogu (Pirot / Beograd / Niš): MUP, matičar, RFZO (dom zdravlja), APR, plus Gradska uprava Pirot za lokalne usluge. Adrese su orijentacione. Ako u tekstu nema mesta, vodič pita „U kom mestu ste?“.
