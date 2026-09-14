#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Affilimax - Stats YouTube (vues, likes, clics/CTR par video)
============================================================
Affiche les stats de la chaine et de chaque video uploadee.

USAGE :
  python youtube_stats.py                 # tableau console (trie par vues)
  python youtube_stats.py --top 10        # top 10 videos seulement
  python youtube_stats.py --json          # sortie JSON brute (stdout)
  python youtube_stats.py --save          # sauvegarde aussi youtube_stats.json
  python youtube_stats.py --days 60       # periode d'analyse clics/CTR

CE QUE LE SCRIPT AFFICHE :
  - Chaine : abonnes, vues totales, nb de videos
  - Video  : vues, likes, commentaires, date de publication
  - Clics  : impressions + CTR (clics sur la miniature) via la YouTube
             Analytics API (28 derniers jours par defaut)

PREREQUIS :
  1. client_secrets.json (cree par youtube_uploader.py)
  2. Ajouter dans Google Cloud -> Ecran de consentement OAuth :
       https://www.googleapis.com/auth/youtube.readonly
       https://www.googleapis.com/auth/youtubeAnalytics.readonly
     (la 1re execution demande une nouvelle autorisation, c'est normal)

NOTE JETON : ce script utilise SON PROPRE jeton (youtube_stats_token.json)
afin de ne pas ecraser youtube_token.json utilise par youtube_uploader.py
(les deux scripts ont des scopes OAuth differents).
"""

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
CLIENT_SECRETS_FILE = BASE_DIR / "client_secrets.json"
TOKEN_FILE = BASE_DIR / "youtube_stats_token.json"  # jeton dedie (scopes lecture)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtubeAnalytics.readonly",
]


def get_services():
    """Auth OAuth 2.0. Reutilise youtube_stats_token.json ; relance le flux
    si les scopes de lecture ne sont pas tous presents dans le jeton."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception:
            creds = None
    # Jeton present mais sans tous les scopes de lecture -> re-autorisation
    if creds and getattr(creds, "scopes", None) and not (set(SCOPES) <= set(creds.scopes)):
        print("[AUTH] Scopes de lecture manquants -> nouvelle autorisation.")
        creds = None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        if not CLIENT_SECRETS_FILE.exists():
            sys.exit(
                f"[ERREUR] {CLIENT_SECRETS_FILE.name} introuvable.\n"
                "Suis le guide GUIDE_YOUTUBE.md (etapes 1-5) puis relance."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
        creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return (
        build("youtube", "v3", credentials=creds),
        build("youtubeAnalytics", "v2", credentials=creds),
    )


def get_channel(youtube):
    """Infos de la chaine connectee (id, abonnes, vues totales, nb videos)."""
    r = youtube.channels().list(part="id,snippet,statistics", mine=True).execute()
    ch = r["items"][0]
    st = ch["statistics"]
    return {
        "id": ch["id"],
        "titre": ch["snippet"]["title"],
        "abonnes": int(st.get("subscriberCount", 0)),
        "vues_totales": int(st.get("viewCount", 0)),
        "nb_videos": int(st.get("videoCount", 0)),
    }


def get_upload_ids(youtube):
    """IDs de toutes les videos de la chaine (pagination incluse)."""
    up = youtube.channels().list(part="contentDetails", mine=True).execute()
    playlist = up["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, next_token = [], None
    while True:
        r = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=playlist,
            maxResults=50,
            pageToken=next_token or "",
        ).execute()
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        next_token = r.get("nextPageToken")
        if not next_token:
            break
    return ids


def get_videos_stats(youtube, ids):
    """Vues / likes / commentaires / date par video (lots de 50)."""
    out = []
    for i in range(0, len(ids), 50):
        batch = ids[i:i + 50]
        r = youtube.videos().list(
            part="snippet,statistics,contentDetails", id=",".join(batch)
        ).execute()
        for v in r.get("items", []):
            st = v["statistics"]
            out.append({
                "id": v["id"],
                "titre": v["snippet"]["title"],
                "publiee_le": v["snippet"]["publishedAt"][:10],
                "duree": v["contentDetails"]["duration"],
                "vues": int(st.get("viewCount", 0)),
                "likes": int(st.get("likeCount", 0)),
                "commentaires": int(st.get("commentCount", 0)),
            })
    return out


def get_analytics(ya, channel_id, days):
    """Impressions + CTR par video (clics). {} si API indisponible
    (scope manquant, quota, chaine trop jeune...)."""
    start = (date.today() - timedelta(days=days)).isoformat()
    end = date.today().isoformat()
    try:
        r = ya.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start,
            endDate=end,
            metrics="impressions,impressionsCtr",
            dimensions="video",
            maxResults=200,
        ).execute()
    except Exception as e:
        print(f"[INFO] Analytics indisponible ({str(e)[:60]}). Clics/CTR non affiches.")
        return {}
    out = {}
    for row in r.get("rows") or []:
        vid, impressions, ctr = row[0], float(row[1] or 0), float(row[2] or 0)
        if impressions > 0:
            out[vid] = {"impressions": int(impressions), "ctr_pct": ctr}
    return out


def fmt_int(n):
    return f"{int(n):,}".replace(",", " ")


def fmt_ctr(v):
    """L'API renvoie 4.2 (= 4.2 %) ou parfois 0.042. On affiche proprement."""
    v = float(v)
    return f"{v * 100:.2f} %" if v < 1 else f"{v:.2f} %"


def main():
    ap = argparse.ArgumentParser(description="Stats YouTube Affilimax")
    ap.add_argument("--top", type=int, default=0, help="Top N videos seulement")
    ap.add_argument("--json", action="store_true", help="Sortie JSON brute")
    ap.add_argument("--save", action="store_true", help="Sauvegarde youtube_stats.json")
    ap.add_argument("--days", type=int, default=28, help="Periode Analytics (defaut 28)")
    args = ap.parse_args()

    youtube, ya = get_services()

    channel = get_channel(youtube)
    ids = get_upload_ids(youtube)
    videos = get_videos_stats(youtube, ids)

    # Clics : impressions + CTR par video (meilleur effort)
    anal = {}
    if args.days > 0 and videos:
        anal = get_analytics(ya, channel["id"], args.days)

    for v in videos:
        v["analytics"] = anal.get(v["id"])

    videos.sort(key=lambda v: v["vues"], reverse=True)

    # Sauvegarde JSON (avant le retour --json pour ne pas l'ignorer)
    if args.save:
        out = BASE_DIR / "youtube_stats.json"
        out.write_text(
            json.dumps({"chaine": channel, "videos": videos},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  💾 Sauvegarde: {out}")

    if args.json:
        print(json.dumps({"chaine": channel, "videos": videos},
                         ensure_ascii=False, indent=2))
        return

    # -------- Tableau console --------
    n = args.top or len(videos)
    print("=" * 100)
    print(f"  📺 {channel['titre']}")
    print(f"  Abonnes: {fmt_int(channel['abonnes'])}   "
          f"Vues totales: {fmt_int(channel['vues_totales'])}   "
          f"Videos: {channel['nb_videos']}")
    print("=" * 100)

    if not videos:
        print("  Aucune video trouvee sur la chaine.")
        return

    hdr = f"{'#':>3} {'Titre':<46} {'Vues':>9} {'Likes':>7} {'Com.':>5} {'Impr.':>9} {'CTR':>8}  Publiee"
    print(hdr)
    print("-" * 100)
    tot_v = tot_l = tot_c = tot_i = tot_click = 0
    for i, v in enumerate(videos[:n], 1):
        a = v["analytics"]
        imp = a["impressions"] if a else 0
        ctr = a["ctr_pct"] if a else 0.0
        tot_v += v["vues"]
        tot_l += v["likes"]
        tot_c += v["commentaires"]
        tot_i += imp
        tot_click += imp * (ctr / 100.0)
        titre = v["titre"][:46]
        imp_s = fmt_int(imp) if a else "n/a"
        ctr_s = fmt_ctr(ctr) if a else ""
        print(f"{i:>3} {titre:<46} {fmt_int(v['vues']):>9} {fmt_int(v['likes']):>7} "
              f"{fmt_int(v['commentaires']):>5} {imp_s:>9} {ctr_s:>8}  {v['publiee_le']}")
    print("-" * 100)
    print(f"{'TOTAL':<50} {fmt_int(tot_v):>9} {fmt_int(tot_l):>7} {fmt_int(tot_c):>5}")
    if tot_i:
        print(f"  Clics (impressions -> CTR global): {fmt_int(tot_i)} impressions, "
              f"{fmt_int(tot_click)} clics estimes ({fmt_ctr(tot_click / tot_i * 100)})")
    else:
        print("  Clics : indisponibles (voir note Analytics)")

    # Meilleure video
    best = max(videos, key=lambda v: v["vues"])
    print()
    print(f"  🏆 Meilleure video : {best['titre'][:60]} "
          f"({fmt_int(best['vues'])} vues)")


if __name__ == "__main__":
    main()
