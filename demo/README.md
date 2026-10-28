# Demo skenovi (sintetika)

Lažni podaci, krupan datum. **Nisu prave isprave.** Pred žirijem reci da je sintetika.

Regeneracija (opciono):

```bash
cd backend
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install pillow
python scripts/make_demo_scans.py
```

Pred live demo na Renderu (Free se gasi posle mirovanja):

```bash
bash demo/warmup.sh
```

Na sceni, pored skenova: „Reci naglas“ (Chrome/Edge, dozvola mikrofona) i prilog **na vodiču** (`demo/istekla-licna-karta.png`).

Koristiti samo ova imena:

| Fajl | Scena | Očekivani badge |
|------|--------|-----------------|
| `istekla-licna-karta.png` | gost + `istekla mi je lična` | **Isteklo** (važi do 2024-03-01) |
| `necitko-sken.pdf` | isti tok, loš prilog | **Nečitko** (PDF, Vision se ne zove) |
| `pasos.png` | isti tok, pogrešan dokument | **Ne odgovara** (pasoš uz zahtev za ličnu kartu) |

Kartice izlaze odmah (matching na tekst). Status se crta posle uploada sa `GET /document-status`. Ako piše „Čitam sken…“, sačekaj par sekundi.

Šalteri u katalogu (Pirot / Beograd / Niš): MUP, matičar, RFZO (dom zdravlja), APR, plus Gradska uprava Pirot za lokalne usluge. Adrese su orijentacione. Ako u tekstu nema mesta, vodič pita „U kom mestu ste?“.
