#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Affilimax - Compilation video longue (~1 heure)
================================================================
Assemble les lecons pedagogiques + histoires enfants en une video
longue de ~60 minutes (format "1 heure d'apprentissage") : les
segments sont repetes en boucle avec une intro/outro (vrais MP4
de 8 s, encodes une seule fois), le tout concatene SANS re-encodage
(ffmpeg stream copy = rapide, quelques minutes).

Usage:
    python compile_long.py --minutes 60
    python compile_long.py --passes 5
"""

import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "video_factory" / "output"
OUT_LONG = OUTPUT_DIR / "longue"

# Versions 3 (10/08/2026) : 21 videos, fonds coherents verifies
# (12 lecons fonds PIL + 9 histoires miniatures locales verifiees)
SEGMENTS = [
    ("vf_20260810_205540_923", "Lecon 1 - Compter de 1 a 10"),
    ("vf_20260810_205540_895", "Lecon 2 - Les couleurs"),
    ("vf_20260810_205540_430", "Lecon 3 - Les formes"),
    ("vf_20260810_210114_708", "Lecon 4 - Les animaux de la ferme"),
    ("vf_20260810_210114_955", "Lecon 5 - L'alphabet"),
    ("vf_20260810_211230_347", "Lecon 6 - Les jours de la semaine"),
    ("vf_20260810_210114_146", "Lecon 7 - Les 4 saisons"),
    ("vf_20260810_210649_775", "Lecon 8 - Compter de 1 a 20"),
    ("vf_20260810_210649_140", "Lecon 9 - Les contraires"),
    ("vf_20260810_210649_497", "Lecon 10 - Le corps humain"),
    ("vf_20260810_211230_165", "Lecon 11 - Les fruits et legumes"),
    ("vf_20260810_211230_612", "Lecon 12 - Les transports"),
    ("vf_20260810_191819_717", "Histoire - Le petit renard"),
    ("vf_20260810_204614_573", "Histoire - Le petit dragon"),
    ("vf_20260810_204614_717", "Histoire - La petite etoile"),
    ("vf_20260810_204614_574", "Histoire - Le petit loup"),
    ("vf_20260810_204905_968", "Histoire - La petite licorne"),
    ("vf_20260810_204905_947", "Histoire - Le petit ours polaire"),
    ("vf_20260810_203136_286", "Histoire - Le petit chat"),
    ("vf_20260810_203136_326", "Histoire - Le petit singe"),
    ("vf_20260810_203136_453", "Histoire - Le petit elephant"),
]

INTRO = "1 HEURE POUR APPRENDRE ET REVER"
INTRO2 = "Lecons + histoires pour enfants 3-8 ans"
OUTRO = "BRAVO !"
OUTRO2 = "Tu as appris et reve pendant 1 heure. A bientot !"


def _ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def _probe_duration(ff, path):
    r = subprocess.run([ff, "-i", str(path)], capture_output=True, timeout=60)
    out = (r.stderr or b"").decode("utf-8", "ignore")
    for line in out.splitlines():
        if "Duration:" in line and "time=" not in line:
            part = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = part.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0


def _make_card_mp4(ff, title, sub, out_mp4, dur=8):
    """Encodes un vrai MP4 1280x720 (degrade + texte) de dur seconds."""
    font = "C:/Windows/Fonts/arialbd.ttf"
    if not Path(font).exists():
        font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    fesc = font.replace(":", "\\:")
    t1 = title.replace("'", "").replace(":", "\\:")
    t2 = sub.replace("'", "").replace(":", "\\:")
    vf = (
        f"drawbox=x=0:y=0:w=iw:h=ih:color=0x141432@1:t=fill,"
        f"drawtext=fontfile={fesc}:text='{t1}':fontcolor=0xffe082:fontsize=60:"
        f"x=(w-text_w)/2:y=(h/2)-100,"
        f"drawtext=fontfile={fesc}:text='{t2}':fontcolor=white:fontsize=34:"
        f"x=(w-text_w)/2:y=(h/2)+30,"
        f"drawtext=fontfile={fesc}:text='AFFILIMAX STUDIO':fontcolor=white@0.7:"
        f"fontsize=26:x=(w-text_w)/2:y=h-70"
    )
    subprocess.run(
        [ff, "-y", "-f", "lavfi", "-i", f"color=c=black:s=1280x720:r=24:d={dur}",
         "-vf", vf, "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-ar", "44100", "-ac", "2", "-shortest", str(out_mp4)],
        capture_output=True, timeout=120,
    )
    return out_mp4 if out_mp4.exists() and out_mp4.stat().st_size > 50000 else None


def main():
    ap = argparse.ArgumentParser(description="Compilation video ~1h")
    ap.add_argument("--minutes", type=int, default=60)
    ap.add_argument("--passes", type=int, default=0)
    args = ap.parse_args()

    ff = _ffmpeg()
    mp4s = []
    for d, _ in SEGMENTS:
        p = OUTPUT_DIR / d / "video.mp4"
        if p.exists():
            mp4s.append(p)
    if not mp4s:
        sys.exit("[ERREUR] Aucun segment trouve")

    one_pass = sum(_probe_duration(ff, p) for p in mp4s)
    print(f"Une passe = {one_pass/60:.1f} min ({len(mp4s)} segments)")

    n = args.passes or max(1, round(args.minutes / (one_pass / 60)))
    print(f"Passes: {n} -> ~{n * one_pass / 60:.0f} min")

    OUT_LONG.mkdir(parents=True, exist_ok=True)
    intro = _make_card_mp4(ff, INTRO, INTRO2, OUT_LONG / "intro.mp4")
    outro = _make_card_mp4(ff, OUTRO, OUTRO2, OUT_LONG / "outro.mp4")
    print(f"Intro: {intro} | Outro: {outro}")

    # Liste de concat : chemins ABSOLUS, uniquement des MP4 (memes codecs)
    entries = []
    if intro:
        entries.append(f"file '{intro}'")
    for _ in range(n):
        for p in mp4s:
            entries.append(f"file '{p.as_posix()}'")
    if outro:
        entries.append(f"file '{outro}'")
    lst = OUT_LONG / "concat.txt"
    lst.write_text("\n".join(entries), encoding="utf-8")

    final = OUT_LONG / "1H_APPRENDRE_ET_REVER.mp4"
    if final.exists():
        final.unlink()
    r = subprocess.run(
        [ff, "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c", "copy", "-movflags", "+faststart", str(final)],
        capture_output=True, timeout=1800,
    )
    if final.exists() and final.stat().st_size > 10_000_000:
        dur = _probe_duration(ff, final)
        print(f"OK: {final.name} | {dur/60:.1f} min | {final.stat().st_size//1024//1024} Mo")
    else:
        print("ERREUR:", (r.stderr or b"").decode("utf-8", "ignore")[-600:])


if __name__ == "__main__":
    main()
