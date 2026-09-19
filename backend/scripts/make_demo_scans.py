"""Sintetski skenovi za žiri (nije prava isprava).

Pokretanje iz backend/:
  .venv\\Scripts\\python.exe -m pip install pillow
  .venv\\Scripts\\python.exe scripts/make_demo_scans.py

Izlaz: ../demo/*.png i ../demo/necitko-sken.pdf
Pillow nije runtime zavisnost API-ja — samo ovaj skript.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "demo"

DISCLAIMER = "SINTETSKI PRIMER — NIJE PRAVA ISPRAVA — NAŠALTER DEMO"
FAKE_NAME = "Mila Jovanovic"
EXPIRED = "01.03.2024"
PASSPORT_EXPIRY = "15.08.2030"


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    windir = Path(r"C:\Windows\Fonts")
    names = (
        ("segoeuib.ttf", "arialbd.ttf", "calibrib.ttf")
        if bold
        else ("segoeui.ttf", "arial.ttf", "calibri.ttf")
    )
    for name in names:
        path = windir / name
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _card(size: tuple[int, int], bg: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", size, bg)
    return image, ImageDraw.Draw(image)


def _wrapped(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], font, fill: str) -> None:
    draw.text(xy, text, font=font, fill=fill)


def make_expired_lk(path: Path) -> None:
    image, draw = _card((1100, 700), "#0b2a4a")
    draw.rectangle((24, 24, 1076, 676), outline="#f4c430", width=6)
    draw.rectangle((24, 24, 1076, 150), fill="#123d66")
    _wrapped(draw, "REPUBLIKA SRBIJA", (48, 40), _font(36, bold=True), "#f4c430")
    _wrapped(draw, DISCLAIMER, (48, 92), _font(22), "#ffe08a")
    _wrapped(draw, "LIČNA KARTA", (48, 190), _font(72, bold=True), "#ffffff")
    _wrapped(draw, "lična karta / ID CARD  |  type=licna_karta", (48, 280), _font(28), "#cfe6ff")
    _wrapped(draw, f"Ime: {FAKE_NAME}  (izmišljeno)", (48, 340), _font(32), "#ffffff")
    _wrapped(draw, "Broj: DEMO-LK-0001  |  nema JMBG", (48, 390), _font(28), "#cfe6ff")
    draw.rectangle((48, 460, 1050, 600), fill="#7a1020")
    _wrapped(draw, "VAŽI DO / EXPIRY", (72, 478), _font(28, bold=True), "#ffd0d0")
    _wrapped(draw, EXPIRED, (72, 518), _font(64, bold=True), "#ffffff")
    _wrapped(draw, "YYYY-MM-DD: 2024-03-01  (rok je prošao)", (72, 640), _font(24), "#ffe08a")
    image.save(path, "PNG")


def make_passport(path: Path) -> None:
    image, draw = _card((1100, 700), "#4a1020")
    draw.rectangle((24, 24, 1076, 676), outline="#e8c872", width=6)
    draw.rectangle((24, 24, 1076, 150), fill="#2c0a12")
    _wrapped(draw, "REPUBLIKA SRBIJA", (48, 40), _font(36, bold=True), "#e8c872")
    _wrapped(draw, DISCLAIMER, (48, 92), _font(22), "#ffe08a")
    _wrapped(draw, "PASOŠ", (48, 190), _font(72, bold=True), "#ffffff")
    _wrapped(draw, "pasoš / PASSPORT  |  type=pasos  |  nije lična karta", (48, 280), _font(28), "#ffd9b0")
    _wrapped(draw, "Nije lična karta. Nije ID card.", (48, 330), _font(32, bold=True), "#ffffff")
    _wrapped(draw, f"Ime: {FAKE_NAME}  (izmišljeno)", (48, 390), _font(32), "#ffffff")
    _wrapped(draw, "Broj: DEMO-P-0001  |  nema JMBG", (48, 440), _font(28), "#ffd9b0")
    draw.rectangle((48, 510, 1050, 630), fill="#123018")
    _wrapped(draw, "VAŽI DO / EXPIRY", (72, 524), _font(28, bold=True), "#b8f0c4")
    _wrapped(draw, PASSPORT_EXPIRY, (72, 562), _font(56, bold=True), "#ffffff")
    image.save(path, "PNG")


def make_unreadable_pdf(path: Path) -> None:
    """PDF namerno ide u unreadable: Vision se ne zove za PDF."""
    path.write_bytes(
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 90]/Contents 4 0 R>>endobj\n"
        b"4 0 obj<</Length 68>>stream\n"
        b"BT /F1 10 Tf 8 50 Td (NASALTER DEMO ISECENI SKEN) Tj ET\n"
        b"endstream\nendobj\n"
        b"trailer<</Root 1 0 R>>\n%%EOF\n"
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    expired = OUT / "istekla-licna-karta.png"
    passport = OUT / "pasos.png"
    pdf = OUT / "necitko-sken.pdf"
    make_expired_lk(expired)
    make_passport(passport)
    make_unreadable_pdf(pdf)
    print(f"Wrote {expired}")
    print(f"Wrote {passport}")
    print(f"Wrote {pdf}")


if __name__ == "__main__":
    main()
