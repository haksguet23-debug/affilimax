#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Affilimax - Upload automatique de videos YouTube
================================================================
Upload les videos generees par video_factory.py vers votre chaine YouTube
via la YouTube Data API v3 (videos.insert, upload resumable).

PREREQUIS (une seule fois, ~10 minutes) :
  1. Google Cloud Console -> creer un projet
  2. Activer "YouTube Data API v3"
  3. Ecran de consentement OAuth (type Externe, scope youtube.upload)
  4. Identifiants -> Creer ID client OAuth -> "Application de bureau"
  5. Telecharger le JSON -> le renommer client_secrets.json -> a cote de ce fichier

USAGE :
  python youtube_uploader.py --file video_factory/output/vf_xxx/video.mp4
  python youtube_uploader.py --story    # upload les 3 dernieres histoires enfants
  python youtube_uploader.py --latest   # upload la video la plus recente
  python youtube_uploader.py --all-stories

OPTIONS :
  --title "Titre"            (sinon titre depuis script.json / nom du fichier)
  --description "Desc"       (sinon description SEO generee)
  --privacy public|unlisted|private   (defaut: unlisted pour verifier avant)
  --made-for-kids            (marquer comme cree pour les enfants - requis COPPA)
"""

import argparse
import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = BASE_DIR / "client_secrets.json"
TOKEN_FILE = BASE_DIR / "youtube_token.json"

STORY_TITLES = {
    "renard": "Un petit renard - Histoire pour enfants (conte du soir)",
    "dragon": "Un petit dragon - Histoire pour enfants (conte du soir)",
    "etoile": "Une petite etoile - Histoire pour enfants (conte du soir)",
}


def get_authenticated_service():
    """Authentification OAuth 2.0 avec sauvegarde du jeton (pas de reconnexion a chaque fois)."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        if not CLIENT_SECRETS_FILE.exists():
            sys.exit(
                f"[ERREUR] {CLIENT_SECRETS_FILE.name} introuvable.\n"
                "Suis le guide GUIDE_YOUTUBE.md (etape 1-5) puis relance."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
        creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def build_description(video_dir):
    """Construit une description YouTube a partir du script.json (si present)."""
    script_file = video_dir / "script.json"
    if script_file.exists():
        try:
            s = json.loads(script_file.read_text(encoding="utf-8"))
            seo = s.get("seo", {})
            desc = seo.get("description") or s.get("description") or ""
            tags = seo.get("tags") or ["histoire pour enfants", "conte du soir"]
            lines = [desc, "", "🔔 Abonne-toi pour plus d'histoires :",
                     "📌 https://afflimax.onrender.com",
                     "", "Tags: " + ", ".join(str(t) for t in tags[:10])]
            return "\n".join(lines)
        except Exception:
            pass
    return "Histoire pour enfants - Abonne-toi ! 📚 #histoire #conte #enfants"


def upload_video(youtube, file_path, title, description, privacy="unlisted", made_for_kids=False):
    from googleapiclient.http import MediaFileUpload

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:4900],
            "categoryId": "24",  # 24 = Education, 22 = People & Blogs
            "tags": ["histoire pour enfants", "conte du soir", "histoires",
                     "enfants", "education", "affilimax"],
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": made_for_kids,
        },
    }
    media = MediaFileUpload(str(file_path), chunksize=-1, resumable=True)
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    print(f"  Upload: {title[:60]}...")
    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            print(f"  Progression: {int(status.progress() * 100)}%")
    vid = response.get("id")
    print(f"  ✅ Video en ligne ! ID: {vid}")
    print(f"  → https://www.youtube.com/watch?v={vid}")
    return vid


def find_story_jobs():
    """Retourne les dossiers des jobs 'story' les plus recents."""
    hist_file = BASE_DIR / "video_factory_history.json"
    if not hist_file.exists():
        return []
    data = json.loads(hist_file.read_text(encoding="utf-8"))
    jobs = data.get("jobs", data) if isinstance(data, dict) else data
    stories = [j for j in (jobs if isinstance(jobs, list) else []) if j.get("kind") == "story"]
    dirs = []
    for j in stories:
        out = BASE_DIR / "video_factory" / "output" / str(j.get("id", "")) / "video.mp4"
        if out.exists():
            dirs.append((out.parent, out))
    return dirs


def main():
    ap = argparse.ArgumentParser(description="Upload YouTube automatise")
    ap.add_argument("--file", type=str, help="Chemin du fichier MP4")
    ap.add_argument("--story", action="store_true", help="Upload les histoires enfants generees")
    ap.add_argument("--latest", action="store_true", help="Upload la video la plus recente")
    ap.add_argument("--title", type=str, default="", help="Titre (sinon auto)")
    ap.add_argument("--description", type=str, default="", help="Description (sinon auto)")
    ap.add_argument("--privacy", type=str, default="unlisted", choices=["public", "unlisted", "private"])
    ap.add_argument("--made-for-kids", action="store_true", help="Marquer 'fait pour les enfants'")
    args = ap.parse_args()

    targets = []
    if args.file:
        targets = [(Path(args.file).parent, Path(args.file))]
    elif args.story:
        targets = find_story_jobs()
        if not targets:
            sys.exit("[INFO] Aucune histoire enfants trouvee. Lance d'abord: python video_factory.py --pipeline --kind story --theme 'un petit renard'")
    elif args.latest:
        all_mp4 = sorted((BASE_DIR / "video_factory" / "output").glob("*/video.mp4"),
                         key=lambda p: p.stat().st_mtime, reverse=True)
        if all_mp4:
            targets = [(p.parent, p) for p in all_mp4[:1]]
    else:
        ap.print_help()
        sys.exit(1)

    if not targets:
        sys.exit("[INFO] Aucune video trouvee.")

    youtube = get_authenticated_service()
    for vdir, mp4 in targets:
        title = args.title or STORY_TITLES.get(vdir.name.split("_")[-1], "")
        if not title:
            title = vdir.name  # fallback
        description = args.description or build_description(vdir)
        upload_video(youtube, mp4, title, description, args.privacy, args.made_for_kids)


if __name__ == "__main__":
    main()
