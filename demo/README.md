# Demo skenovi (sintetika)

Lažni podaci, krupan datum. U pitchu reći da **nije prava isprava**.

Kartice izlaze odmah (matching na tekst). Vision upisuje tip/rok posle uploada; FE crta `GET /document-status`.

| Fajl | Tok | Očekivani status |
|------|-----|------------------|
| `istekla-lk.png` | gost + `istekla mi je lična` + ovaj sken | **Isteklo** + „važi do …“ |
| `necitko.png` | isti tekst, mutna slika | **Nečitko** |
| `pasos-umesto-lk.png` | isti tekst, pasoš umesto LK | **Ne odgovara**, ne „Imate ličnu“ |

Ponovo napraviti slike: `backend/.venv/bin/python demo/make_scans.py`
