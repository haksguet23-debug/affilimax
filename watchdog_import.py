#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Affilimax - Watchdog d'import automatique des ventes Amazon
=============================================================
Surveille le dossier `rapports_amazon/` : dès qu'un fichier .csv y est
déposé (téléchargé depuis partenaires.amazon.fr), il est importé
automatiquement via le webhook (stats + solde partenaire crédités),
puis déplacé dans `rapports_amazon/importes/` avec un horodatage.

Lancement :
    python watchdog_import.py                 # surveille en continu (Ctrl+C pour arrêter)
    python watchdog_import.py --once          # importe les fichiers présents puis s'arrête
    python watchdog_import.py --dry-run       # montre ce qui serait importé sans rien créditer

Utilisé par la tâche planifiée Windows (au démarrage, en arrière-plan).
"""

import argparse
import datetime
import json
import os
import shutil
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==================== CONFIG ====================
CONFIG_FILE = os.path.join(BASE_DIR, "config_import.env")
POLL_SECONDS = 60  # vérifier le dossier toutes les 60 s


def load_config():
    """Charge la config : les variables d'environnement priment, sinon le
    fichier config_import.env (secrets locaux, jamais commité)."""
    cfg = {
        "AMAZON_WEBHOOK_SECRET": "",
        "AMAZON_WEBHOOK_URL": "https://afflimax.onrender.com/amazon/notification",
        "RAPPORTS_DIR": "rapports_amazon",
    }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    # Les variables d'environnement (si définies) écrasent le fichier
    for k in cfg:
        env_v = os.environ.get(k)
        if env_v:
            cfg[k] = env_v
    return cfg


def log(msg, level="INFO"):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    try:
        log_path = os.path.join(BASE_DIR, "rapports_amazon", "watchdog.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def import_one(csv_path, cfg, dry_run=False):
    """Importe un fichier CSV via le script d'import existant."""
    import subprocess
    cmd = [
        sys.executable,
        os.path.join(BASE_DIR, "import_amazon_report.py"),
        csv_path,
        "--webhook", cfg["AMAZON_WEBHOOK_URL"],
        "--secret", cfg["AMAZON_WEBHOOK_SECRET"],
    ]
    if dry_run:
        cmd.append("--dry-run")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300,
            cwd=BASE_DIR, encoding="utf-8", errors="replace",
        )
        output = (result.stdout or "") + (result.stderr or "")
        log(f"Import {os.path.basename(csv_path)} -> exit {result.returncode}")
        for line in output.strip().splitlines():
            log(f"  {line}")
        return result.returncode == 0
    except Exception as e:
        log(f"ERREUR import {csv_path}: {e}", "ERROR")
        return False


def archive(csv_path, cfg):
    """Déplace le fichier importé dans rapports_amazon/importes/."""
    dest_dir = os.path.join(BASE_DIR, cfg.get("RAPPORTS_DIR", "rapports_amazon"), "importes")
    os.makedirs(dest_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = os.path.splitext(os.path.basename(csv_path))[0]
    dest = os.path.join(dest_dir, f"{name}_{ts}.csv")
    try:
        shutil.move(csv_path, dest)
        log(f"Archive -> {os.path.basename(dest)}")
    except Exception as e:
        log(f"ERREUR archive: {e}", "ERROR")


def scan_and_import(cfg, dry_run=False):
    """Importe tous les CSV trouvés dans le dossier des rapports."""
    reports_dir = os.path.join(BASE_DIR, cfg.get("RAPPORTS_DIR", "rapports_amazon"))
    if not os.path.isdir(reports_dir):
        log(f"Dossier absent: {reports_dir}", "WARN")
        return 0

    # Ne pas scanner le sous-dossier importes/ (déjà traités)
    csvs = []
    for name in sorted(os.listdir(reports_dir)):
        full = os.path.join(reports_dir, name)
        if os.path.isfile(full) and name.lower().endswith(".csv"):
            csvs.append(full)

    if not csvs:
        log("Aucun rapport CSV à importer.")
        return 0

    if not cfg.get("AMAZON_WEBHOOK_SECRET"):
        log("SECRET MANQUANT: config_import.env absent ou AMAZON_WEBHOOK_SECRET vide. "
            "Aucune import possible tant que le secret n'est pas configuré.", "ERROR")
        return 0

    count = 0
    for csv_path in csvs:
        ok = import_one(csv_path, cfg, dry_run=dry_run)
        if ok and not dry_run:
            archive(csv_path, cfg)
        count += 1
    return count


def main():
    ap = argparse.ArgumentParser(description="Watchdog import ventes Amazon")
    ap.add_argument("--once", action="store_true", help="Importe les fichiers présents puis s'arrête")
    ap.add_argument("--dry-run", action="store_true", help="Affiche sans importer")
    args = ap.parse_args()

    cfg = load_config()
    reports_dir = os.path.join(BASE_DIR, cfg.get("RAPPORTS_DIR", "rapports_amazon"))
    os.makedirs(reports_dir, exist_ok=True)

    if args.once:
        n = scan_and_import(cfg, dry_run=args.dry_run)
        log(f"Terminé: {n} fichier(s) traité(s)")
        return

    log(f"Watchdog démarré - surveille {reports_dir} toutes les {POLL_SECONDS}s "
        f"(secret {'OK' if cfg.get('AMAZON_WEBHOOK_SECRET') else 'MANQUANT'})")
    if not cfg.get("AMAZON_WEBHOOK_SECRET"):
        log("⚠️  Complète config_import.env avec AMAZON_WEBHOOK_SECRET pour activer l'import.", "ERROR")
    while True:
        try:
            scan_and_import(cfg, dry_run=args.dry_run)
        except Exception as e:
            log(f"Erreur boucle: {e}", "ERROR")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
