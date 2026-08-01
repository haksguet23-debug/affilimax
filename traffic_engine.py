#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AFFILIMAX - Moteur de Trafic Autonome
======================================
Tourne 24/7 pour generer du vrai trafic vers les liens affilies :
- Ping Google + IndexNow (Bing/Yandex) toutes les heures
- Regeneration de contenu SEO frais
- Verification que le serveur et le tunnel sont UP
- Tracking des stats de clics

Usage: python traffic_engine.py
"""

import json
import os
import sys
import time
import random
import threading
import urllib.request
import urllib.parse
import ssl
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
BLOG_DIR = BASE_DIR / "affilimax_blog"
LIENS_FILE = BASE_DIR / "liens_affiliation.json"
STATS_FILE = BASE_DIR / "stats.json"

# URL publique (detectee automatiquement ou manuelle)
PUBLIC_URL = os.environ.get("AFFILMAX_BASE_URL") or "https://employees-happy-genre-endorsement.trycloudflare.com"
LOCAL_URL = "http://127.0.0.1:8765"

# IndexNow key (doit etre a la racine du serveur)
INDEXNOW_KEY = "affilimax2026indexnowkey001"
INDEXNOW_KEY_FILE = INDEXNOW_KEY + ".txt"


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


# ==================== HEALTH CHECK ====================
def check_server():
    """Verifie que le serveur local est UP."""
    try:
        req = urllib.request.Request(f"{LOCAL_URL}/healthz", method="GET")
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read())
        return data.get("status") == "ok"
    except:
        return False


def check_public_url():
    """Verifie que l'URL publique est accessible."""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(f"{PUBLIC_URL}/healthz", method="GET")
        urllib.request.urlopen(req, timeout=10, context=ctx)
        return True
    except:
        return False


def get_public_url_from_tunnel():
    """Essaie de detecter l'URL publique depuis les logs cloudflared."""
    global PUBLIC_URL
    try:
        import subprocess
        result = subprocess.run(
            ["grep", "-oE", r"https://[a-z0-9.-]+\.trycloudflare\.com", "/tmp/cf_tunnel.log"],
            capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip():
            url = result.stdout.strip().split("\n")[-1]
            PUBLIC_URL = url
            os.environ["AFFILMAX_BASE_URL"] = url
            return url
    except:
        pass
    return None


# ==================== INDEXNOW (Bing/Yandex) ====================
def ensure_indexnow_key():
    """S'assure que le fichier de cle IndexNow est accessible publiquement a la racine."""
    # Le serveur sert depuis BASE_DIR, donc le fichier doit etre a la racine
    key_path = BASE_DIR / INDEXNOW_KEY_FILE
    if not key_path.exists():
        key_path.write_text(INDEXNOW_KEY, encoding="utf-8")
        log(f"INDEXNOW: Cle creee dans {key_path}")


def ping_indexnow():
    """Soumet les URLs principales a IndexNow (Bing + Yandex)."""
    try:
        produits = load_products()
        host = PUBLIC_URL.replace("https://", "").replace("http://", "").rstrip("/")

        # Construire la liste d'URLs
        url_list = [
            f"{PUBLIC_URL}/",
            f"{PUBLIC_URL}/sitemap.xml",
            f"{PUBLIC_URL}/boutique.html",
            f"{PUBLIC_URL}/status.html",
        ]

        # Ajouter les articles SEO
        for f in sorted(BLOG_DIR.glob("seo-*.html"))[:10]:
            url_list.append(f"{PUBLIC_URL}/affilimax_blog/{f.name}")

        # Ajouter quelques pages produits
        for p in produits[:5]:
            slug = p.get("slug", "")
            url_list.append(f"{PUBLIC_URL}/produit/{slug}")
            url_list.append(f"{PUBLIC_URL}/go/{slug}")

        payload = {
            "host": host,
            "key": INDEXNOW_KEY,
            "keyLocation": f"{PUBLIC_URL}/{INDEXNOW_KEY_FILE}",
            "urlList": url_list,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://api.indexnow.org/indexnow",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        log(f"INDEXNOW: HTTP {resp.status} - {len(url_list)} URLs soumises (Bing+Yandex)")
        return True
    except Exception as e:
        log(f"INDEXNOW: Erreur - {e}")
        return False


# ==================== GOOGLE PING ====================

# ==================== CONTENT REFRESH ====================
def load_products():
    """Charge les produits actifs."""
    try:
        with open(LIENS_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        return [p for p in config.get("produits", []) if p.get("actif")]
    except:
        return []


def refresh_seo_content():
    """Regenere le contenu SEO pour quelques produits (fraicheur)."""
    produits = load_products()
    if not produits:
        return

    # En choisir 3 aleatoires
    random.shuffle(produits)
    refreshed = 0

    for p in produits[:3]:
        slug = p.get("slug", "")
        output_file = BLOG_DIR / f"seo-{slug}.html"

        # Regenerer seulement si plus vieux que 3 jours ou absent
        if output_file.exists():
            age = time.time() - output_file.stat().st_mtime
            if age < 3 * 86400:
                continue

        try:
            # Regenerer via gain_engine
            import subprocess
            subprocess.run(
                ["python", str(BASE_DIR / "gain_engine.py"), "--seo"],
                capture_output=True, timeout=120
            )
            refreshed += 1
        except:
            pass

    if refreshed > 0:
        log(f"SEO: {refreshed} articles regeneres")
    return refreshed


# ==================== STATS TRACKING ====================
def get_current_stats():
    """Lit les stats actuelles de clics/commissions."""
    try:
        req = urllib.request.Request(f"{LOCAL_URL}/api/stats", method="GET")
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read())
        r = data.get("resume", {})
        return {
            "clics": r.get("clics_aujourdhui", 0),
            "commissions": r.get("commissions_aujourdhui", 0),
            "conversions": r.get("conversions_aujourdhui", 0),
        }
    except:
        return {"clics": 0, "commissions": 0, "conversions": 0}


# ==================== MAIN LOOP ====================
def run():
    """Boucle principale du moteur de trafic."""
    print("""
============================================================
   AFFILIMAX - MOTEUR DE TRAFIC AUTONOME
   Generation de trafic reel 24/7
============================================================
    """)

    # Initialisation
    ensure_indexnow_key()

    # Tenter de detecter l'URL publique
    tunnel = get_public_url_from_tunnel()
    if tunnel:
        log(f"TUNNEL: URL publique detectee: {PUBLIC_URL}")

    cycle = 0
    last_seo_refresh = 0
    last_indexnow = 0

    while True:
        cycle += 1
        now = time.time()

        # 1. Verifier que tout est UP
        local_ok = check_server()
        public_ok = check_public_url() if PUBLIC_URL != LOCAL_URL else False

        if not local_ok:
            log("ALERTE: Serveur local DOWN - tentative de restart...")
            try:
                import subprocess
                subprocess.Popen(
                    ["python", str(BASE_DIR / "server.py")],
                    creationflags=0x08000000 if os.name == "nt" else 0
                )
                time.sleep(5)
            except:
                pass

        # 2. Afficher les stats
        stats = get_current_stats()
        status_line = f"[Cycle {cycle}] Local: {'UP' if local_ok else 'DOWN'}"
        if public_ok:
            status_line += f" | Public: UP ({PUBLIC_URL[:40]}...)"
        status_line += f" | Clics: {stats['clics']} | Comm: {stats['commissions']}EUR"
        log(status_line)

        # 3. IndexNow toutes les heures
        if now - last_indexnow > 3600 and public_ok:
            ping_indexnow()
                        last_indexnow = now

        # 4. Refresh SEO toutes les 6 heures
        if now - last_seo_refresh > 21600:
            refresh_seo_content()
            last_seo_refresh = now

        # 5. Si des clics ont ete enregistres, celebration !
        if stats['clics'] > 0:
            log(f"*** ATTENTION: {stats['clics']} CLICS REELS DETECTES ! ***")
            log(f"*** Commissions: {stats['commissions']}EUR ***")

        # Pause avant le prochain cycle
        time.sleep(300)  # 5 minutes


# ==================== CLI ====================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Un seul cycle")
    args = parser.parse_args()

    if args.once:
        ensure_indexnow_key()
        local_ok = check_server()
        public_ok = check_public_url()
        stats = get_current_stats()
        print(f"Local: {'UP' if local_ok else 'DOWN'}")
        print(f"Public: {'UP' if public_ok else 'DOWN'} ({PUBLIC_URL})")
        print(f"Clics: {stats['clics']} | Commissions: {stats['commissions']}EUR | Conversions: {stats['conversions']}")
        if public_ok:
            ping_indexnow()
                    sys.exit(0)

    run()
