# Demo skenovi (sintetika)

Lažni podaci, krupan datum. **Nisu prave isprave.** Pred žirijem reci da je sintetika.

Regeneracija (opciono):

```bash
cd backend
.venv\Scripts\python.exe -m pip install pillow
.venv\Scripts\python.exe scripts/make_demo_scans.py
```

| Fajl | Scena | Očekivani badge |
|------|--------|-----------------|
| `istekla-licna-karta.png` | gost + `istekla mi je lična` | **Isteklo** (važi do 2024-03-01) |
| `necitko-sken.pdf` | isti tok, loš prilog | **Nečitko** (PDF, Vision se ne zove) |
| `pasos.png` | isti tok, pogrešan dokument | **Ne odgovara** (pasoš uz zahtev za LK) |

Kartice izlaze odmah (matching na tekst). Status se crta posle uploada sa `GET /document-status`. Sačekaj ~2 s ako piše „Provera skena“.

Ne demoovati RFZO / APR / matičar ako pitch obećava adresu šaltera (nema kancelarije u katalogu).
