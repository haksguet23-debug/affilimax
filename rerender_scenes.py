#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Affilimax - Re-rendu des scenes video (badge + numero lisibles sur tous fonds)
==============================================================================
Regenere UNIQUEMENT les images de scene (nouveau badge sur pastille sombre +
numero avec contour) et remonte le MP4 en REUTILISANT les audios et SRT
existants : pas de nouvelle IA ni de nouveau TTS (~3 min par video au lieu de ~8).

Usage:
    python rerender_scenes.py --id vf_20260810_205540_923
    python rerender_scenes.py --all
"""

import argparse
import json
import sys
from pathlib import Path

import video_factory as vf

BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "video_factory" / "output"


def _parse_srt(text):
    """Parse un fichier SRT en entrees {start, end, text} (temps absolus)."""
    entries = []
    for block in text.strip().split("\n\n"):
        lines = [l for l in block.strip().split("\n") if l.strip()]
        if len(lines) < 2:
            continue
        ts = lines[1].split("-->")
        if len(ts) != 2:
            continue
        def _t(s):
            s = s.strip().replace(",", ".")
            h, m, sec = s.split(":")
            return int(h) * 3600 + int(m) * 60 + float(sec)
        entries.append({
            "start": _t(ts[0]),
            "end": _t(ts[1]),
            "text": " ".join(lines[2:]),
        })
    return entries


def rerender(job_id):
    job_dir = OUTPUT_DIR / job_id
    if not job_dir.exists():
        print(f"[ERREUR] {job_dir} introuvable")
        return False
    script_file = job_dir / "script.json"
    srt_file = job_dir / "subtitles.srt"
    if not script_file.exists():
        print(f"[ERREUR] pas de script.json dans {job_id}")
        return False

    script = json.loads(script_file.read_text(encoding="utf-8"))
    scenes = script.get("scenes") or []

    # 1. Regenerer les images de scene (nouveau badge/numero + fonds coherents)
    images = vf._build_scene_images(script, job_dir)
    print(f"[RERENDER] {job_id}: {len(images)} images regenerees")

    # 2. Reutiliser les audios existants
    audio_dir = job_dir / "audio"
    audios = []
    for i in range(len(scenes)):
        a = audio_dir / f"scene_{i + 1:02d}.mp3"
        audios.append(a if a.exists() else None)

    # 3. Reutiliser le SRT existant
    sub_entries = None
    if srt_file.exists():
        sub_entries = _parse_srt(srt_file.read_text(encoding="utf-8"))

    # 4. Remonter le MP4
    video_path = job_dir / "video.mp4"
    vf._render_video(images, audios, video_path, scenes, sub_entries=sub_entries)
    size_mo = video_path.stat().st_size // 1024 // 1024
    print(f"[RERENDER] OK {job_id}: {size_mo} Mo")
    return True


def main():
    ap = argparse.ArgumentParser(description="Re-rendu scenes video")
    ap.add_argument("--id", type=str, default="", help="ID du job (vf_...)")
    ap.add_argument("--all", action="store_true", help="Tous les dossiers de sortie")
    args = ap.parse_args()

    if args.id:
        ok = rerender(args.id)
        sys.exit(0 if ok else 1)

    if args.all:
        dirs = sorted([p for p in OUTPUT_DIR.iterdir() if p.is_dir() and p.name.startswith("vf_")])
        ok = 0
        for d in dirs:
            try:
                if rerender(d.name):
                    ok += 1
            except Exception as e:
                print(f"[RERENDER] ERREUR {d.name}: {e}")
        print(f"\nRe-rendu: {ok}/{len(dirs)}")
        sys.exit(0)

    ap.print_help()


if __name__ == "__main__":
    main()
