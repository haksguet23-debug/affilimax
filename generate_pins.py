#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Affilimax - Generateur de visuels reseaux sociaux
================================================================
Cree des visuels (photo produit + titre + prix + CTA) pour :
    --format pinterest : 1000x1500 (ratio 2:3)
    --format instagram : 1080x1080 (carre)
    --format tiktok    : 1080x1920 (story 9:16)

Usage:
    python generate_pins.py --all --format pinterest
    python generate_pins.py --product cartable --format instagram --force
    python generate_pins.py --list
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
LIENS_FILE = BASE_DIR / "liens_affiliation.json"

# Dimensions + dossiers de sortie par format
FORMATS = {
    "pinterest": {"w": 1000, "h": 1500, "dir": BASE_DIR / "assets" / "pins"},
    "instagram": {"w": 1080, "h": 1080, "dir": BASE_DIR / "assets" / "instagram"},
    "tiktok":    {"w": 1080, "h": 1920, "dir": BASE_DIR / "assets" / "tiktok"},
}

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

# Etiquettes selon le format
LABELS = {
    "pinterest": "AFFILIMAX  |  RENTREE 2026",
    "instagram": "AFFILIMAX",
    "tiktok":    "AFFILIMAX  |  RENTREE 2026",
}


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


def _scale(fmt, *vals):
    """Echelle les tailles de police selon la hauteur du format (base = 1500)."""
    h = FORMATS[fmt]["h"]
    k = h / 1500.0
    return tuple(int(v * k) for v in vals)


def make_visual(product, fmt="pinterest", force=False):
    """Cree un visuel (photo produit + titre + prix + CTA) pour le format donne."""
    from PIL import Image, ImageDraw, ImageEnhance

    conf = FORMATS[fmt]
    W, H = conf["w"], conf["h"]
    out_dir = conf["dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    nom = product.get("nom", "Produit")
    slug = product.get("slug", "produit")
    prix = product.get("prix", 0)
    note = product.get("note_moyenne", 4.5)
    avis = product.get("avis_total", 0)
    cat = product.get("categorie", "High-Tech")
    img_url = product.get("image_url", "")

    out_path = out_dir / f"{slug}.jpg"
    if out_path.exists() and not force:
        return out_path

    # 1. Fond : photo produit reelle (ou degrade si KO)
    bg_path = None
    if img_url:
        bg_path = _download_image(img_url, out_dir / f"{slug}_bg.jpg")
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

    # Tailles de police adaptees au format
    f_badge_s, f_title_s, f_price_s, f_small_s, f_cta_s = _scale(
        fmt, 34, 64, 58, 32, 42
    )

    # 2. Badge AFFILIMAX
    draw.text((int(W * 0.05), int(H * 0.027)), LABELS[fmt], font=_load_font(f_badge_s), fill=(255, 255, 255))

    # 3. Bandeau titre semi-transparent (bande sombre en bas)
    band_h = int(H * 0.35)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([0, H - band_h, W, H], fill=(10, 10, 30, 200))
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(image)

    # 4. Titre accrocheur
    titles = _TITLES.get(cat, _FALLBACK_TITLES)
    rng = random.Random(abs(hash(slug)) % 999)
    titre = rng.choice(titles).format(nom=nom)
    f_title = _load_font(f_title_s)
    lines = _wrap_text(draw, titre.upper(), f_title, W - int(W * 0.1))[:3]
    yy = H - band_h + int(H * 0.04)
    line_gap = int(H * 0.056)
    for line in lines:
        draw.text((int(W * 0.05), yy), line, font=f_title, fill=(255, 224, 130))
        yy += line_gap

    # 5. Prix + note
    draw.text((int(W * 0.05), yy + int(H * 0.013)), f"{prix} EUR", font=_load_font(f_price_s), fill=(255, 255, 255))
    draw.text(
        (int(W * 0.05), yy + int(H * 0.067)),
        f"Note {note}/5 - {avis} avis",
        font=_load_font(f_small_s),
        fill=(220, 220, 245),
    )

    # 6. CTA
    f_cta = _load_font(f_cta_s)
    cta_w, cta_h = int(W * 0.6), int(H * 0.047)
    draw.rounded_rectangle(
        [int(W * 0.05), H - cta_h - int(H * 0.013), int(W * 0.05) + cta_w, H - int(H * 0.013)],
        radius=int(H * 0.011),
        fill=(240, 165, 0),
    )
    cta_label = "VOIR SUR AMAZON" if fmt != "pinterest" else "VOIR LE PRIX SUR AMAZON"
    draw.text((int(W * 0.05) + 20, H - cta_h - int(H * 0.013) + 12), cta_label, font=f_cta, fill=(20, 20, 40))

    image.save(out_path, "JPEG", quality=88)
    return out_path


def load_products():
    try:
        with open(LIENS_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("produits", [])
    except Exception:
        return []


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generateur de visuels reseaux sociaux")
    ap.add_argument("--product", type=str, help="Slug du produit (sinon tous les scolaires)")
    ap.add_argument("--all", action="store_true", help="Tous les produits")
    ap.add_argument("--format", type=str, choices=list(FORMATS.keys()), default="pinterest", help="Format du visuel")
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
            out = make_visual(p, fmt=args.format, force=args.force)
            print(f"  OK {p['slug']} -> {out.name} ({out.stat().st_size//1024} Ko)")
            ok += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"  ERR {p['slug']}: {str(e)[:60]}")
    print(f"\nVisuels {args.format} generes: {ok}/{len(targets)} dans {FORMATS[args.format]['dir']}")
