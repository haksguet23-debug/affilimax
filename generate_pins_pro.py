#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Affilimax - Generateur de visuels PRO (vraies photos produit Amazon)
====================================================================
Style pro : photo produit reelle (fond blanc Amazon), typo propre,
beaucoup d'espace blanc, badge prix, CTA. Aucune image IA.

Usage:
    python generate_pins_pro.py                # les 14 pins par defaut
    python generate_pins_pro.py --slug bose-quietcomfort-ultra
    python generate_pins_pro.py --list
"""

import argparse
import io
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = Path(__file__).parent.resolve()
LIENS_FILE = BASE_DIR / "liens_affiliation.json"
OUT_DIR = BASE_DIR / "assets" / "pins_pro"
OUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1000, 1500  # Pinterest 2:3

# Palette pro (Amazon)
NAVY = (35, 47, 62)        # #232F3E
ORANGE = (255, 153, 0)     # #FF9900
LIGHT = (250, 250, 248)
GRAY = (110, 118, 126)

FONTS = {
    "bold":   "C:/Windows/Fonts/segoeuib.ttf",
    "semibd": "C:/Windows/Fonts/seguisb.ttf",
    "reg":    "C:/Windows/Fonts/segoeui.ttf",
}

DEFAULT_SLUGS = [
    # Top commissions (high-tech / maison)
    "bose-quietcomfort-ultra",
    "roborock-q5-pro-plus",
    "sony-wh-1000xm5",
    "xiaomi-robot-aspirateur-s20",
    "tapis-marche-pliable-lontek",
    # Rentrée (gros volumes de recherche)
    "casio-fx92-college",
    "apple-airpods-4",
    "amazon-kindle-2024",
    "samsung-galaxy-tab-a9-plus",
    "ninja-foodi-max-air-fryer",
    "lego-ideas-notre-dame-paris",
    "faber-castell-crayons-24",
    "pilot-frixion-pack-4",
    "stabilo-boss-pack-6",
]


def font(name, size):
    return ImageFont.truetype(FONTS[name], size)


def fr_price(v):
    s = f"{v:.2f}".replace(".", ",")
    if s.endswith(",00"):
        s = s[:-3]
    return s + " \u20ac"


def wrap(draw, text, fnt, max_w):
    lines, cur = [], ""
    for word in text.split():
        test = (cur + " " + word).strip()
        if draw.textlength(test, font=fnt) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


CACHE_FILE = OUT_DIR / "_img_cache.json"
_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
       "Accept-Language": "fr-FR,fr;q=0.9"}


def _fetch(url, timeout=25):
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def get_product_photo(prod):
    """Vraie photo produit hi-res depuis la fiche Amazon (cache local)."""
    cache = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
    m = re.search(r"/dp/([A-Z0-9]{10})", prod["lien"])
    asin = m.group(1) if m else None
    if not asin:
        raise RuntimeError("ASIN introuvable")
    if asin in cache and cache[asin]:
        return _fetch(cache[asin])
    html = _fetch(f"https://www.amazon.fr/dp/{asin}").decode("utf-8", "ignore")
    # hiRes / large d'abord, puis n'importe quelle image produit SL500+
    img = None
    m1 = re.search(r'"hiRes"\s*:\s*"(https://m\.media-amazon\.com/images/I/[^"]+)"', html)
    m2 = re.search(r'"large"\s*:\s*"(https://m\.media-amazon\.com/images/I/[^"]+)"', html)
    m3 = re.search(r'(https://m\.media-amazon\.com/images/I/[A-Za-z0-9+._%-]+\._SL(5|10)00_\.jpg)', html)
    if m1:
        img = m1.group(1).replace("\\u0026", "&")
    elif m2:
        img = m2.group(1).replace("\\u0026", "&")
    elif m3:
        img = m3.group(1)
    if not img:
        raise RuntimeError("photo produit introuvable sur la fiche")
    cache[asin] = img
    CACHE_FILE.write_text(json.dumps(cache, indent=1))
    time.sleep(1.2)
    return _fetch(img)


def download_image(prod, timeout=25):
    data = get_product_photo(prod)
    img = Image.open(io.BytesIO(data)).convert("RGBA")
    # fond blanc si transparence
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    return Image.alpha_composite(bg, img).convert("RGB")


def rounded(draw, xy, radius, fill):
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def product_box_image(img, box_w, box_h):
    """Contient l'image dans box_w x box_h, retourne (image, (w,h))."""
    img.thumbnail((box_w, box_h), Image.LANCZOS)
    return img, img.size


def make_pin(prod, out_path):
    nom = prod["nom"].strip()
    prix = fr_price(float(prod["prix"]))
    comm = float(prod.get("commission_euro", 0))

    accroches = {
        "Scolaire": f"{nom} : le bon plan rentrée 2026",
        "High-Tech": f"{nom} : le test complet",
        "Audio": f"{nom} : ça vaut le coup ?",
        "Maison": f"{nom} : la maison plus maligne",
        "Cuisine": f"{nom} : test & avis 2026",
        "Sport": f"{nom} : test & avis 2026",
        "Gaming": f"{nom} : test & avis 2026",
    }
    titre = accroches.get(prod.get("categorie", ""), f"{nom} : test & avis 2026")

    img = Image.new("RGB", (W, H), LIGHT)
    d = ImageDraw.Draw(img)

    M = 64  # marge
    y = 90

    # ---- Titre (max 4 lignes) ----
    f_title = font("bold", 58)
    lines = wrap(d, titre, f_title, W - 2 * M)[:4]
    for ln in lines:
        d.text((W // 2, y), ln, font=f_title, fill=NAVY, anchor="ma")
        y += 68
    y += 10

    # ---- Chip "Testé & approuvé" ----
    f_chip = font("semibd", 30)
    chip_txt = "\u2713  Testé & approuvé"
    cw = d.textlength(chip_txt, font=f_chip)
    rounded(d, (W/2 - cw/2 - 26, y, W/2 + cw/2 + 26, y + 52), 26, (228, 233, 238))
    d.text((W/2, y + 26), chip_txt, font=f_chip, fill=NAVY, anchor="mm")
    y += 52 + 34

    # ---- Photo produit avec ombre douce ----
    box_w, box_h = W - 2 * M, 760
    try:
        photo = download_image(prod)
        photo, (pw, ph) = product_box_image(photo, box_w, box_h)
        px, py = (W - pw) // 2, y + (box_h - ph) // 2
        shadow = Image.new("RGBA", (pw + 80, ph + 80), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle((40, 40, pw + 40, ph + 40), radius=24, fill=(0, 0, 0, 60))
        shadow = shadow.filter(ImageFilter.GaussianBlur(18))
        img.paste(Image.new("RGB", shadow.size, LIGHT), (px - 40, py - 40), shadow)
        d = ImageDraw.Draw(img)
        img.paste(photo, (px, py))
    except Exception as e:
        print(f"   [warn] photo KO ({e}) -> panneau neutre")
        rounded(d, (M, y, W - M, y + box_h), 24, (232, 235, 238))
        d.text((W/2, y + box_h/2), nom, font=font("semibd", 44), fill=NAVY, anchor="mm")
    d = ImageDraw.Draw(img)
    y += box_h + 48

    # ---- Badge prix (orange, style Amazon) ----
    f_price = font("bold", 62)
    pw_txt = d.textlength(prix, font=f_price)
    bw = pw_txt + 120
    rounded(d, (W/2 - bw/2, y, W/2 + bw/2, y + 104), 52, ORANGE)
    d.text((W/2, y + 50), prix, font=f_price, fill=(255, 255, 255), anchor="mm")
    y += 104 + 30

    # ---- CTA ----
    f_cta = font("bold", 36)
    cta = "VOIR LE PRIX SUR AMAZON  \u2192"
    rounded(d, (M, y, W - M, y + 92), 46, NAVY)
    d.text((W/2, y + 45), cta, font=f_cta, fill=(255, 255, 255), anchor="mm")
    y += 92 + 26

    # ---- Footer marque ----
    d.text((W/2, H - 60), "AFFILIMAX  ·  Bons plans Amazon vérifiés",
           font=font("reg", 26), fill=GRAY, anchor="mm")

    img.save(out_path, quality=92)
    return comm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", action="append")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    data = json.loads(LIENS_FILE.read_text(encoding="utf-8"))
    by_slug = {p["slug"]: p for p in data["produits"]}

    if args.list:
        for s in DEFAULT_SLUGS:
            p = by_slug.get(s)
            print(f"{s:38} {p['nom'] if p else 'INTROUVABLE'}")
        return

    slugs = args.slug if args.slug else DEFAULT_SLUGS
    total_comm = 0.0
    for s in slugs:
        p = by_slug.get(s)
        if not p:
            print(f"[skip] {s} introuvable")
            continue
        out = OUT_DIR / f"{s}.jpg"
        comm = make_pin(p, out)
        total_comm += comm
        print(f"[ok] {s}  (+{comm} eur/vente)")
    print(f"\nDossier: {OUT_DIR}  ·  potentiel/vente si tout part: {total_comm:.2f} eur")


if __name__ == "__main__":
    main()
