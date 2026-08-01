#!/usr/bin/env python3
"""AFFILIMAX - Auto-Engine v3.0
Moteur d'automation 100% autonome. Tourne en arriere-plan, se corrige seul.
- Monitor le serveur local + Render
- Auto-heal (redemarre si crash)
- IndexNow automatique (Bing/Yandex)
- Stats en temps reel
- Logs rotatifs

Usage: python auto_engine.py
"""
import json, os, sys, time, ssl, urllib.request, subprocess, traceback
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.resolve()
LOCAL = "http://127.0.0.1:8765"
RENDER_URL = "https://afflimax.onrender.com"
INDEXNOW_KEY = "affilimax2026indexnowkey001"
LOG_FILE = BASE / "auto_engine.log"

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass

def http_get_local(url, timeout=8):
    """HTTP GET sans verification SSL (localhost uniquement)."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, method="GET")
    return urllib.request.urlopen(req, timeout=timeout, context=ctx)

def http_get_public(url, timeout=15):
    """HTTP GET avec verification SSL (URLs publiques comme Render)."""
    req = urllib.request.Request(url, method="GET")
    return urllib.request.urlopen(req, timeout=timeout)

def check_local():
    try:
        resp = http_get_local(f"{LOCAL}/healthz", timeout=5)
        data = json.loads(resp.read())
        return data.get("status") == "ok", data
    except:
        return False, {}

def check_render():
    try:
        resp = http_get_public(f"{RENDER_URL}/healthz", timeout=20)
        data = json.loads(resp.read())
        return data.get("status") == "ok", data
    except:
        return False, {}

def get_stats():
    try:
        resp = http_get_local(f"{LOCAL}/api/stats", timeout=5)
        return json.loads(resp.read())
    except:
        return {"resume": {"clics_aujourdhui": 0, "commissions_aujourdhui": 0.0}}

def restart_server():
    log("Auto-heal: redemarrage du serveur...", "HEAL")
    try:
        subprocess.Popen(
            [sys.executable, str(BASE / "server.py")],
            cwd=str(BASE),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=0x08000000 if os.name == "nt" else 0
        )
        time.sleep(4)
        ok, _ = check_local()
        if ok:
            log("Auto-heal: serveur redemarre avec succes", "HEAL")
            return True
    except Exception as e:
        log(f"Auto-heal: echec restart - {e}", "ERROR")
    return False

def ping_indexnow():
    try:
        produits = []
        try:
            with open(BASE / "liens_affiliation.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
            produits = [p for p in cfg.get("produits", []) if p.get("actif")]
        except:
            pass

        host = RENDER_URL.replace("https://", "").rstrip("/")
        urls = [f"{RENDER_URL}/", f"{RENDER_URL}/sitemap.xml"]

        blog = BASE / "affilimax_blog"
        if blog.exists():
            for f in sorted(blog.glob("*.html"))[:10]:
                urls.append(f"{RENDER_URL}/affilimax_blog/{f.name}")

        payload = {"host": host, "key": INDEXNOW_KEY, "keyLocation": f"{RENDER_URL}/affilimax_blog/{INDEXNOW_KEY}.txt", "urlList": urls[:20]}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request("https://api.indexnow.org/indexnow", data=data, headers={"Content-Type": "application/json"}, method="POST")
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        log(f"IndexNow: HTTP {resp.status} - {len(urls[:20])} URLs")
        return True
    except urllib.error.HTTPError as e:
        log(f"IndexNow: HTTP {e.code}", "WARN")
        return e.code == 202
    except Exception as e:
        log(f"IndexNow: {e}", "ERROR")
        return False

def refresh_seo():
    """Genere un article SEO frais via gain_engine (si disponible)."""
    try:
        result = subprocess.run(
            [sys.executable, str(BASE / "gain_engine.py"), "--seo"],
            cwd=str(BASE),
            capture_output=True, text=True, timeout=120,
            stdin=subprocess.DEVNULL
        )
        if result.returncode == 0:
            log("SEO: Contenu regenere avec succes")
            return True
        else:
            log(f"SEO: Echec (exit {result.returncode})", "WARN")
    except Exception as e:
        log(f"SEO: Erreur - {e}", "WARN")
    return False

def rotate_log():
    """Rotation du log si > 500KB."""
    try:
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > 500_000:
            bak = LOG_FILE.with_suffix(".log.bak")
            bak.write_text(LOG_FILE.read_text(encoding="utf-8", errors="replace")[-10000:], encoding="utf-8")
            LOG_FILE.write_text("", encoding="utf-8")
            log("Log rotate effectue", "INFO")
    except:
        pass

def run():        rotate_log()
    log("=" * 50, "START")
    log("AFFILIMAX AUTO-ENGINE v3.1 - Demarrage", "START")
    log(f"Local: {LOCAL} | Render: {RENDER_URL}", "START")

    cycle = 0
    last_indexnow = 0
    consecutive_fails = 0

    while True:
        cycle += 1
        now = time.time()

        # 1. Check local
        local_ok, local_data = check_local()

        # 2. Auto-heal if down
        if not local_ok:
            consecutive_fails += 1
            log(f"ALERTE: Serveur local DOWN ({consecutive_fails} echecs consecutifs)", "WARN")
            if consecutive_fails >= 2:
                restart_server()
                consecutive_fails = 0
        else:
            consecutive_fails = 0

        # 3. Check Render
        render_ok, render_data = check_render()

        # 4. Stats
        stats = get_stats()
        r = stats.get("resume", {})
        clics = r.get("clics_aujourdhui", 0)
        comms = r.get("commissions_aujourdhui", 0.0)

        # 5. Status line
        parts = [f"Cycle {cycle}"]
        parts.append(f"Local: {'UP' if local_ok else 'DOWN'}")
        parts.append(f"Render: {'UP' if render_ok else 'DOWN'}")
        parts.append(f"Clics: {clics}")
        parts.append(f"Comm: {comms}EUR")
        log(" | ".join(parts))

        # 6. Alert if clicks detected
        if clics > 0:
            log(f"*** {clics} CLICS DETECTES ! Commissions: {comms}EUR ***", "ALERT")

        # 7. IndexNow every hour
        if now - last_indexnow > 3600 and render_ok:
            ping_indexnow()
            last_indexnow = now

        # 8. SEO refresh every 12h
        if cycle % 144 == 0 and render_ok:  # 144 cycles * 5min = 12h
            refresh_seo()

        # 9. Log rotation every 100 cycles
        if cycle % 100 == 0:
            rotate_log()

        # Sleep 5 minutes
        time.sleep(300)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--once", action="store_true", help="Un seul cycle")
    args = p.parse_args()

    if args.once:
        local_ok, _ = check_local()
        render_ok, _ = check_render()
        stats = get_stats()
        r = stats.get("resume", {})
        print(f"Local: {'UP' if local_ok else 'DOWN'}")
        print(f"Render: {'UP' if render_ok else 'DOWN'}")
        print(f"Clics: {r.get('clics_aujourdhui', 0)} | Comm: {r.get('commissions_aujourdhui', 0.0)}EUR")
        if render_ok:
            ping_indexnow()
        sys.exit(0)

    run()
