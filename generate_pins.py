#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Affilimax - Generateur d'Epingles Pinterest (visuels 1000x1500)
================================================================
Cree des visuels Pinterest au format vertical (1000x1500, ratio 2:3)
avec la VRAIE photo produit en fond + titre accrocheur + prix + CTA.

Usage:
    python generate_pins.py                    # toutes les epingles du calendrier
    python generate_pins.py --product cartable # une seule epingle
    python generate_pins.py --list             # liste les produits
"""

import argparse
import json
import os
import random
import re
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
OUT_DIR = BASE_DIR / "assets" / "pins"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LIENS_FILE = BASE_DIR / "liens_affiliation.json"

W, H = 1000, 1500  # format Pinterest (ratio 2:3)

_FONT_CANDIDATES = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/seguisb.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

_TITLES = {
    "Scolaire": [
        "RENTREE 2026 : {nom}",
        "L'indispensable pour la rentree ! {nom}",
        "{nom} - le bon plan des parents",
        "Back to school 2026 : {nom}",
    ],
    "High-Tech": [
        "Le meilleur rapport qualite-prix : {nom}",
        "{nom} - teste et approuve",
        "Tech 2026 : {nom} a decouvrir",
    ],
    "Maison": [
        "{nom} - la maison plus maligne",
        "Le bon plan maison : {nom}",
    ],
    "Cuisine": [
        "{nom} - cuisinez malin en 2026",
    ],
}

_FALLBACK_TITLES = [
    "{nom} - le bon plan 2026",
    "Decouvrez : {nom}",
    "{nom} a prix reduit",
]


def _load_font(size):
    from PIL import ImageFont
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default(size)


def _wrap_text(draw, text, font, max_width):
    words = str(text).split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def _download_image(url, dest, timeout=15):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=timeout).read()
        if len(data) < 5000:
            return None
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return dest
    except Exception:
        return None


def make_pin(product, force=False):
    """Cree une epingle Pinterest 1000x1500 pour un produit."""
    from PIL import Image, ImageDraw, ImageEnhance

    nom = product.get("nom", "Produit")
    slug = product.get("slug", "produit")
    prix = product.get("prix", 0)
    note = product.get("note_moyenne", 4.5)
    avis = product.get("avis_total", 0)
    cat = product.get("categorie", "High-Tech")
    img_url = product.get("image_url", "")
    comm = product.get("commission_euro", 0)

    out_path = OUT_DIR / f"{slug}.jpg"
    if out_path.exists() and not force:
        return out_path

    # 1. Fond : photo produit reelle (ou degrade si KO)
    bg_path = None
    if img_url:
        bg_path = _download_image(img_url, OUT_DIR / f"{slug}_bg.jpg")
    if bg_path and bg_path.exists():
        im = Image.open(bg_path).convert("RGB")
        im = im.resize((W, H), Image.LANCZOS)
        im = ImageEnhance.Brightness(im).enhance(0.55)
        image = im
    else:
        top = (30, 27, 75)
        bottom = (124, 58, 237)
        image = Image.new("RGB", (W, H), top)
        draw = ImageDraw.Draw(image)
        for yy in range(0, H, 8):
            t = yy / H
            color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
            draw.rectangle([0, yy, W, yy + 8], fill=color)

    draw = ImageDraw.Draw(image)

    # 2. Badge AFFILIMAX
    f_badge = _load_font(34)
    draw.text((48, 40), "AFFILIMAX  |  RENTREE 2026", font=f_badge, fill=(255, 255, 255))

    # 3. Bandeau titre semi-transparent (bande sombre en bas)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    band_h = 520
    od.rectangle([0, H - band_h, W, H], fill=(10, 10, 30, 200))
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(image)

    # 4. Titre accrocheur
    titles = _TITLES.get(cat, _FALLBACK_TITLES)
    rng = random.Random(abs(hash(slug)) % 999)
    titre = rng.choice(titles).format(nom=nom)
    f_title = _load_font(64)
    lines = _wrap_text(draw, titre.upper(), f_title, W - 100)[:3]
    yy = H - band_h + 60
    for line in lines:
        draw.text((50, yy), line, font=f_title, fill=(255, 224, 130))
        yy += 84

    # 5. Prix + note
    f_price = _load_font(58)
    draw.text((50, yy + 20), f"{prix} EUR", font=f_price, fill=(255, 255, 255))
    f_small = _load_font(32)
    draw.text((50, yy + 100), f"Note {note}/5 - {avis} avis | Comm {comm} EUR", font=f_small, fill=(220, 220, 245))

    # 6. CTA
    f_cta = _load_font(42)
    draw.rounded_rectangle([50, H - 110, 650, H - 40], radius=16, fill=(240, 165, 0))
    draw.text((90, H - 96), "VOIR LE PRIX SUR AMAZON", font=f_cta, fill=(20, 20, 40))

    image.save(out_path, "JPEG", quality=88)
    return out_path


def load_products():
    try:
        with open(LIENS_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("produits", [])
    except Exception:
        return []


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generateur d'epingles Pinterest")
    ap.add_argument("--product", type=str, help="Slug du produit (sinon tous les scolaires)")
    ap.add_argument("--all", action="store_true", help="Tous les produits")
    ap.add_argument("--force", action="store_true", help="Regenerer meme si existe")
    ap.add_argument("--list", action="store_true", help="Lister les produits scolaires")
    args = ap.parse_args()

    produits = load_products()

    if args.list:
        for p in produits:
            if p.get("categorie") == "Scolaire":
                print(f"  {p['slug']} | {p['nom']}")
        sys.exit(0)

    if args.product:
        targets = [p for p in produits if p.get("slug") == args.product]
    elif args.all:
        targets = produits
    else:
        targets = [p for p in produits if p.get("categorie") == "Scolaire"]

    ok = 0
    for p in targets:
        try:
            out = make_pin(p, force=args.force)
            print(f"  OK {p['slug']} -> {out.name} ({out.stat().st_size//1024} Ko)")
            ok += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"  ERR {p['slug']}: {str(e)[:60]}")
    print(f"\nEpingles generees: {ok}/{len(targets)} dans {OUT_DIR}")
