"""Sintetski skenovi za demo. Nisu prave isprave. Treba Pillow."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent


def font(size: int) -> ImageFont.ImageFont:
    for name in ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def banner(draw: ImageDraw.ImageDraw, width: int, title: str) -> None:
    draw.rectangle((0, 0, width, 70), fill=(154, 46, 36))
    draw.text((24, 18), "SINTEZA — NIJE PRAVA ISPRAVA", fill="white", font=font(28))
    draw.text((24, 88), title, fill=(26, 24, 20), font=font(36))


def save_expired_lk() -> None:
    img = Image.new("RGB", (1100, 700), (236, 230, 218))
    draw = ImageDraw.Draw(img)
    banner(draw, 1100, "LIČNA KARTA  ·  DEMO")
    draw.text((48, 180), "Ime: DEMO DEMOVIĆ", fill=(26, 24, 20), font=font(34))
    draw.text((48, 240), "JMBG: 0000000000000 (lažno)", fill=(26, 24, 20), font=font(28))
    draw.text((48, 300), "VAŽI DO: 15.01.2020.", fill=(122, 46, 36), font=font(42))
    draw.text((48, 380), "Izdato: PU Beograd (sintetika)", fill=(92, 87, 78), font=font(26))
    draw.text((48, 520), "Žiri: očekivani status na vodiču = Isteklo", fill=(21, 92, 56), font=font(24))
    img.save(ROOT / "istekla-lk.png", "PNG")


def save_unreadable() -> None:
    img = Image.new("RGB", (900, 560), (40, 38, 36))
    draw = ImageDraw.Draw(img)
    draw.text((30, 40), "LIČNA KARTA", fill=(90, 88, 80), font=font(48))
    draw.text((30, 140), "VAŽI DO 2020", fill=(70, 68, 60), font=font(40))
    draw.text((30, 240), "DEMOVIĆ", fill=(80, 76, 70), font=font(36))
    noisy = ImageEnhance.Contrast(img.filter(ImageFilter.GaussianBlur(18))).enhance(0.35)
    crop = noisy.crop((80, 60, 620, 420)).resize((900, 560))
    crop.save(ROOT / "necitko.png", "PNG")


def save_passport() -> None:
    img = Image.new("RGB", (1100, 700), (210, 222, 232))
    draw = ImageDraw.Draw(img)
    banner(draw, 1100, "PASOŠ  ·  DEMO")
    draw.text((48, 180), "Tip dokumenta: PASOŠ (ne lična karta)", fill=(26, 24, 20), font=font(32))
    draw.text((48, 250), "Ime: DEMO DEMOVIĆ", fill=(26, 24, 20), font=font(34))
    draw.text((48, 310), "Broj: P0000000", fill=(26, 24, 20), font=font(28))
    draw.text((48, 370), "VAŽI DO: 01.01.2030.", fill=(21, 92, 56), font=font(36))
    draw.text((48, 520), "Žiri: uz „istekla mi je lična“ → Ne odgovara", fill=(122, 46, 36), font=font(24))
    img.save(ROOT / "pasos-umesto-lk.png", "PNG")


def main() -> None:
    save_expired_lk()
    save_unreadable()
    save_passport()
    print("wrote", ROOT / "istekla-lk.png")
    print("wrote", ROOT / "necitko.png")
    print("wrote", ROOT / "pasos-umesto-lk.png")


if __name__ == "__main__":
    main()
