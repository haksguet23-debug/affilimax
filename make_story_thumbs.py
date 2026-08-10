#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Affilimax - Miniatures YouTube 1280x720 pour les histoires enfants
================================================================
Cree une miniature YouTube (1280x720) pour chaque histoire :
photo du theme (LoremFlickr) + titre accrocheur + badge AFFILIMAX.

Usage:
    python make_story_thumbs.py            # les 6 histoires
    python make_story_thumbs.py --theme renard
"""

import argparse
import random
import sys
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
OUT_DIR = BASE_DIR / "assets" / "thumbs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1280, 720  # format miniature YouTube

_FONT_CANDIDATES = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/seguisb.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

# Theme -> (mots-cles LoremFlickr, lock stable, titre miniature)
STORIES = {
    "renard": ("fox,forest,cute,animal", 4441, "UN PETIT RENARD"),
    "dragon": ("dragon,cute,fire,magic", 4442, "UN PETIT DRAGON"),
    "etoile": ("star,night,sky,cute,child", 4443, "UNE PETITE ETOILE"),
    "loup": ("wolf,cute,forest,animal", 4444, "UN PETIT LOUP"),
    "licorne": ("unicorn,toy,rainbow", 404, "UNE PETITE LICORNE"),  # lock 404 verifie: figurine licorne
    "ours": ("polar,bear,cute,snow", 4446, "UN PETIT OURS POLAIRE"),
}

SUFFIXE = "HISTOIRE POUR ENFANTS | CONTE DU SOIR"


def _load_font(size):
    from PIL import ImageFont
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default(size)


def _download_photo(keywords, dest):
    url = f"https://loremflickr.com/1280/720/{keywords}?lock={random.randint(1, 9999)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=25).read()
        if len(data) < 8000:
            return False
        dest.write_bytes(data)
        return True
    except Exception:
        return False


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


def make_thumb(theme, force=False):
    from PIL import Image, ImageDraw, ImageEnhance

    if theme not in STORIES:
        print(f"  ERR theme inconnu: {theme}")
        return None

    keywords, lock, titre = STORIES[theme]
    out = OUT_DIR / f"story_{theme}.jpg"
    if out.exists() and not force:
        return out

    photo = OUT_DIR / f"story_{theme}_bg.jpg"
    if not _download_photo(f"{keywords}?lock={lock}", photo):
        # fallback degrade
        image = Image.new("RGB", (W, H), (30, 27, 75))
        draw = ImageDraw.Draw(image)
        for yy in range(0, H, 8):
            t = yy / H
            color = tuple(int(30 * (1 - t) + 124 * t) for _ in range(1)) + tuple(
                [int(27 * (1 - t) + 58 * t), int(75 * (1 - t) + 237 * t)]
            )
            draw.rectangle([0, yy, W, yy + 8], fill=(color[0], color[1], color[2]))
    else:
        im = Image.open(photo).convert("RGB")
        im = im.resize((W, H), Image.LANCZOS)
        im = ImageEnhance.Brightness(im).enhance(0.5)
        image = im

    draw = ImageDraw.Draw(image)

    # Badge haut gauche
    draw.text((40, 30), "AFFILIMAX  |  HISTOIRES", font=_load_font(32), fill=(255, 255, 255))

    # Bandeau bas
    band_h = 260
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([0, H - band_h, W, H], fill=(10, 10, 30, 210))
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(image)

    # Titre principal
    f_title = _load_font(88)
    lines = _wrap_text(draw, titre, f_title, W - 80)[:2]
    yy = H - band_h + 30
    for line in lines:
        draw.text((40, yy), line, font=f_title, fill=(255, 224, 130))
        yy += 110

    # Sous-titre
    f_sub = _load_font(40)
    draw.text((40, yy + 15), SUFFIXE, font=f_sub, fill=(255, 255, 255))

    image.save(out, "JPEG", quality=90)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Miniatures YouTube histoires enfants")
    ap.add_argument("--theme", type=str, help="Un seul theme (renard, dragon, etoile, loup, licorne, ours)")
    ap.add_argument("--force", action="store_true", help="Regenerer")
    args = ap.parse_args()

    themes = [args.theme] if args.theme else list(STORIES.keys())
    ok = 0
    for t in themes:
        try:
            out = make_thumb(t, force=args.force)
            if out:
                print(f"  OK {t} -> {out.name} ({out.stat().st_size//1024} Ko)")
                ok += 1
        except Exception as e:
            print(f"  ERR {t}: {str(e)[:70]}")
    print(f"\nMiniatures generees: {ok}/{len(themes)} dans {OUT_DIR}")
