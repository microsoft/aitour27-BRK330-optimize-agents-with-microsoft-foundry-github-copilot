#!/usr/bin/env python3
"""Generate deterministic, realistic-looking receipt images for the Contoso Travel
Concierge demo. Uses only PIL. Output goes to data/receipts/.
"""
from __future__ import annotations
import os, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "data" / "receipts"
OUT.mkdir(parents=True, exist_ok=True)

def _font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Courier New Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Courier New.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/Library/Fonts/Courier New.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def _paper(w, h, warm=True, seed=0):
    rnd = random.Random(seed)
    base = (252, 249, 240) if warm else (250, 250, 248)
    img = Image.new("RGB", (w, h), base)
    px = img.load()
    for y in range(h):
        for x in range(w):
            if rnd.random() < 0.02:
                r, g, b = px[x, y]
                jitter = rnd.randint(-8, 4)
                px[x, y] = (max(0, r + jitter), max(0, g + jitter), max(0, b + jitter))
    d = ImageDraw.Draw(img)
    for _ in range(6):
        x = rnd.randint(0, w - 1)
        shade = rnd.randint(230, 245)
        d.line([(x, 0), (x, h)], fill=(shade, shade, shade - 5), width=1)
    return img

def _finish(img, rotate=0.4):
    img = img.filter(ImageFilter.GaussianBlur(0.4))
    img = img.rotate(rotate, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255))
    return img

def _center(draw, text, y, font, w, fill=(30, 30, 30)):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) / 2, y), text, font=font, fill=fill)

def _line(draw, y, w, dashed=True):
    if dashed:
        for x in range(20, w - 20, 12):
            draw.line([(x, y), (x + 6, y)], fill=(60, 60, 60), width=1)
    else:
        draw.line([(20, y), (w - 20, y)], fill=(60, 60, 60), width=1)

def _barcode(draw, y, w, seed=0):
    rnd = random.Random(seed)
    x = 60
    while x < w - 60:
        bw = rnd.randint(1, 5)
        draw.rectangle([x, y, x + bw, y + 60], fill=(30, 30, 30))
        x += bw + rnd.randint(1, 4)

def rec_001():
    w, h = 640, 1040
    img = _paper(w, h, warm=True, seed=1)
    d = ImageDraw.Draw(img)
    f_h = _font(30, bold=True); f_m = _font(20, bold=True); f_r = _font(19); f_xs = _font(15)
    y = 40
    _center(d, "SEA-TAC INT'L AIRPORT", y, f_h, w); y += 38
    _center(d, "TERMINAL PARKING GARAGE", y, f_m, w); y += 30
    _center(d, "17801 International Blvd, Seattle WA", y, f_xs, w); y += 22
    _center(d, "Tel  (206) 555-0139   Lot: TG-4", y, f_xs, w); y += 30
    _line(d, y, w); y += 18
    for row in [
        "RECEIPT #  0025-778142",
        "TERMINAL:  4 - Blue B",
        "ENTRY   :  MAR 09 2026  06:12",
        "EXIT    :  MAR 12 2026  22:47",
        "DURATION:  3 days 16h 35m",
    ]:
        d.text((30, y), row, font=f_r, fill=(30, 30, 30)); y += 26
    y += 4; _line(d, y, w); y += 18
    for row in [
        "RATE   DAILY MAX             $ 42.00",
        "DAYS                             x 4",
        "SUBTOTAL                     $168.00",
        "WA STATE TAX  10.25%          $17.22",
        "AIRPORT FEE                    $2.50",
    ]:
        d.text((30, y), row, font=f_r, fill=(30, 30, 30)); y += 26
    y += 4; _line(d, y, w, dashed=False); y += 14
    d.text((30, y), "TOTAL USD                    $187.72", font=f_m, fill=(20, 20, 20)); y += 34
    _line(d, y, w, dashed=False); y += 20
    for row in ["PAID   VISA ***4128", "AUTH   840712", "MERCHANT ID  SEA-PKG-4"]:
        d.text((30, y), row, font=f_r, fill=(30, 30, 30)); y += 26
    y += 14
    _center(d, "THANK YOU  DRIVE SAFELY", y, f_m, w); y += 34
    _center(d, "Keep receipt for reimbursement", y, f_xs, w); y += 50
    _barcode(d, y, w, seed=11); y += 70
    _center(d, "0025 7781 42  SEA-TG-4",  y, f_xs, w)
    _finish(img, rotate=0.4).save(OUT / "REC-001.png", "PNG", optimize=True)

def rec_002():
    w, h = 640, 1080
    img = _paper(w, h, warm=True, seed=2)
    d = ImageDraw.Draw(img)
    f_h = _font(28, bold=True); f_m = _font(20, bold=True); f_r = _font(19); f_xs = _font(15)
    y = 40
    _center(d, "AEROPORT PARIS - CDG", y, f_h, w); y += 34
    _center(d, "PARKING PC - TERMINAL 2E", y, f_m, w); y += 28
    _center(d, "95700 Roissy-en-France", y, f_xs, w); y += 20
    _center(d, "Tel 01 70 36 39 50   Lot: PC-B12", y, f_xs, w); y += 26
    _line(d, y, w); y += 16
    for row in [
        "RECU N   4471-902",
        "TICKET       B12-88245",
        "ENTREE      08 MARS 2026  17:24",
        "SORTIE      11 MARS 2026  09:52",
        "DUREE       2 j 16h 28m",
    ]:
        d.text((30, y), row, font=f_r, fill=(30, 30, 30)); y += 26
    y += 4; _line(d, y, w); y += 16
    for row in [
        "TARIF JOUR MAX              32,00 EUR",
        "JOURS FACTURES                    x 3",
        "SOUS-TOTAL HT              80,00 EUR",
        "TVA 20%                    16,00 EUR",
        "FRAIS AEROPORT              1,80 EUR",
    ]:
        d.text((30, y), row, font=f_r, fill=(30, 30, 30)); y += 26
    y += 4; _line(d, y, w, dashed=False); y += 14
    d.text((30, y), "MONTANT TTC                97,80 EUR",  font=f_m, fill=(20, 20, 20)); y += 34
    _line(d, y, w, dashed=False); y += 18
    for row in ["PAIEMENT   CB ***7712", "AUTORISATION  201884", "TVA N   FR 22 449 671 002"]:
        d.text((30, y), row, font=f_r, fill=(30, 30, 30)); y += 26
    y += 14
    _center(d, "MERCI DE VOTRE VISITE", y, f_m, w); y += 30
    _center(d, "Conservez ce ticket pour remboursement", y, f_xs, w); y += 40
    _barcode(d, y, w, seed=22); y += 70
    _center(d, "4471 9020  CDG PC-B12",  y, f_xs, w)
    _finish(img, rotate=-0.6).save(OUT / "REC-002.png", "PNG", optimize=True)

def rec_003():
    w, h = 780, 1080
    img = _paper(w, h, warm=False, seed=3)
    d = ImageDraw.Draw(img)
    f_h = _font(30, bold=True); f_m = _font(20, bold=True); f_r = _font(18); f_xs = _font(15)
    y = 44
    _center(d, "HOTEL LOUVRE RIVOLI",  y, f_h, w); y += 34
    _center(d, "12 rue de Rivoli, 75001 Paris",  y, f_xs, w); y += 20
    _center(d, "GUEST FOLIO",  y, f_m, w); y += 30
    _line(d, y, w); y += 20
    for row in [
        "Guest         Krystal McKinney",
        "Company       Caldova",
        "Room          412 (Superior King)",
        "Arrival       09 Mar 2026",
        "Departure     12 Mar 2026",
        "Folio #       LR-2026-04412",
    ]:
        d.text((40, y), row, font=f_r, fill=(30, 30, 30)); y += 24
    y += 6; _line(d, y, w); y += 16
    d.text((40, y), "Date       Description                      Amount", font=f_r, fill=(30, 30, 30)); y += 22
    _line(d, y, w); y += 12
    rows = [
        ("09 Mar", "Room  Superior King",             "285.00 EUR"),
        ("09 Mar", "City Tax / Taxe de sejour",       "  4.40 EUR"),
        ("10 Mar", "Room  Superior King",             "285.00 EUR"),
        ("10 Mar", "City Tax / Taxe de sejour",       "  4.40 EUR"),
        ("10 Mar", "Room service - Continental",      " 32.00 EUR"),
        ("11 Mar", "Room  Superior King",             "285.00 EUR"),
        ("11 Mar", "City Tax / Taxe de sejour",       "  4.40 EUR"),
        ("11 Mar", "Minibar (2x wine, 1x snacks)",    " 46.00 EUR"),
        ("11 Mar", "In-room movie",                   " 14.00 EUR"),
        ("12 Mar", "VAT 20% on room and services",    "192.16 EUR"),
    ]
    for date, desc, amt in rows:
        d.text((40,  y), date, font=f_r, fill=(30, 30, 30))
        d.text((150, y), desc, font=f_r, fill=(30, 30, 30))
        d.text((610, y), amt,  font=f_r, fill=(30, 30, 30))
        y += 22
    y += 6; _line(d, y, w); y += 14
    d.text((40,  y), "SUBTOTAL",  font=f_m, fill=(20, 20, 20))
    d.text((610, y), "1152.36 EUR", font=f_m, fill=(20, 20, 20)); y += 26
    d.text((40,  y), "TOTAL DUE", font=f_m, fill=(20, 20, 20))
    d.text((610, y), "1152.36 EUR", font=f_m, fill=(20, 20, 20)); y += 32
    _line(d, y, w, dashed=False); y += 18
    for row in ["Payment       VISA ****4128        Auth 771402", "Status        SETTLED"]:
        d.text((40, y), row, font=f_r, fill=(30, 30, 30)); y += 24
    y += 18
    _center(d, "Thank you for staying with us",  y, f_m, w); y += 30
    _center(d, "SIRET 449 671 002 00021   TVA FR22449671002",  y, f_xs, w)
    _finish(img, rotate=0.3).save(OUT / "REC-003.png", "PNG", optimize=True)

def rec_004():
    w, h = 780, 1040
    img = _paper(w, h, warm=False, seed=4)
    d = ImageDraw.Draw(img)
    f_h = _font(30, bold=True); f_m = _font(20, bold=True); f_r = _font(18); f_xs = _font(15)
    y = 44
    _center(d, "PREFERRED-AM CAR RENTAL",   y, f_h, w); y += 34
    _center(d, "Boston Logan Intl. - Terminal C",  y, f_xs, w); y += 20
    _center(d, "RENTAL AGREEMENT / RECEIPT", y, f_m, w); y += 30
    _line(d, y, w); y += 20
    for row in [
        "Renter         Krystal McKinney",
        "Agreement #    PA-BOS-2026-01184",
        "Vehicle        Midsize Sedan (2025)",
        "Class          Midsize",
        "Pickup         14 Apr 2026 09:20",
        "Return         17 Apr 2026 17:40",
        "Days billed    3",
    ]:
        d.text((40, y), row, font=f_r, fill=(30, 30, 30)); y += 24
    y += 6; _line(d, y, w); y += 16
    d.text((40, y), "Item                                       Amount", font=f_r, fill=(30, 30, 30)); y += 20
    _line(d, y, w); y += 12
    rows = [
        ("Base rate       3 x $62.00",       "$186.00"),
        ("Prepaid fuel option",               " $58.00"),
        ("Optional insurance (LDW)",          " $87.00"),
        ("Vehicle license fee",               "  $9.00"),
        ("Airport concession recovery",       " $22.35"),
        ("MA sales tax 6.25%",                " $22.72"),
    ]
    for desc, amt in rows:
        d.text((40,  y), desc, font=f_r, fill=(30, 30, 30))
        d.text((640, y), amt,  font=f_r, fill=(30, 30, 30))
        y += 22
    y += 6; _line(d, y, w); y += 14
    d.text((40,  y), "TOTAL USD", font=f_m, fill=(20, 20, 20))
    d.text((640, y), "$385.07",   font=f_m, fill=(20, 20, 20)); y += 32
    _line(d, y, w, dashed=False); y += 18
    for row in [
        "Payment      VISA ****4128     Auth 991284",
        "Fuel policy  Prepaid  (not consumed for reimb.)",
        "Insurance    LDW purchased at counter",
    ]:
        d.text((40, y), row, font=f_r, fill=(30, 30, 30)); y += 24
    y += 18
    _center(d, "Thank you for driving Preferred-Am",  y, f_m, w); y += 30
    _center(d, "Fed EIN  22-7018842   MA VRT  118-441",  y, f_xs, w)
    _finish(img, rotate=-0.35).save(OUT / "REC-004.png", "PNG", optimize=True)

if __name__ == "__main__":
    rec_001(); rec_002(); rec_003(); rec_004()
    print("Wrote:", sorted(p.name for p in OUT.glob("REC-*.png")))
