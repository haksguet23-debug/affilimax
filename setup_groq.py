#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Affilimax - Setup Groq
======================
Configure la cle API Groq (mode IA complet) en quelques secondes.

La cle est stockee dans le fichier .env du projet (jamais commite, protege
par .gitignore). En production Render.com, utilise plutot les variables
d'environnement de Render Dashboard.

Usage:
  python setup_groq.py               # assistant interactif
  python setup_groq.py --status      # verifier ou est la cle + etat IA
  python setup_groq.py --set gsk_xxx # enregistrer la cle dans .env
  python setup_groq.py --test        # tester la cle avec un appel reel Groq
  python setup_groq.py --unset       # supprimer la cle du .env

Securite:
  - Ne JAMAIS partager ta cle dans un chat / un ticket / un commit.
  - Si une cle a fuité, revoque-la sur https://console.groq.com/keys
"""

import argparse
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
ENV_FILE = BASE_DIR / ".env"
GITIGNORE = BASE_DIR / ".gitignore"

MODEL_DEFAULT = "llama-3.3-70b-versatile"

# ==================== HELPERS .env ====================

def _read_env():
    """Lit le .env et retourne un dict {cle: valeur}."""
    data = {}
    if ENV_FILE.exists():
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, val = line.partition("=")
                    data[key.strip()] = val.strip().strip('"').strip("'")
        except Exception as e:
            print(f"  [X] Impossible de lire .env : {e}")
    return data


def _write_env(data):
    """Reecrit le .env en preservant commentaires et ordre, avec les valeurs a jour."""
    lines = []
    seen = set()
    if ENV_FILE.exists():
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            lines = []
    out = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.partition("=")[0].strip()
            if key in data:
                seen.add(key)
                out.append(f"{key}={data[key]}\n")
                continue
        out.append(line)
    for key, val in data.items():
        if key not in seen:
            out.append(f"{key}={val}\n")
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(out)


def _protect_gitignore():
    """Ajoute .env au .gitignore si absent (securite : ne jamais commiter la cle)."""
    if not GITIGNORE.exists():
        return False
    content = GITIGNORE.read_text(encoding="utf-8")
    if ".env" in content.splitlines():
        return False
    with open(GITIGNORE, "a", encoding="utf-8") as f:
        f.write("\n# Secrets locaux (cle API Groq / env) - JAMAIS commiter\n.env\n")
    return True


def _mask(key):
    if not key:
        return "(vide)"
    if len(key) <= 10:
        return key[:3] + "***"
    return key[:8] + "..." + key[-4:]


# ==================== COMMANDES ====================

def cmd_status():
    print("=" * 55)
    print("  AFFILIMAX - Statut de la cle Groq")
    print("=" * 55)

    env_val = os.environ.get("GROQ_API_KEY", "")
    dotenv_val = _read_env().get("GROQ_API_KEY", "")

    print("\n[1] Cle trouvee dans l'environnement Windows :")
    print(f"      {'OUI  -> ' + _mask(env_val) if env_val else 'NON  (variable GROQ_API_KEY absente)'}")

    print("\n[2] Cle trouvee dans le fichier .env :")
    if dotenv_val:
        print(f"      OUI  -> {_mask(dotenv_val)}  ({ENV_FILE})")
    else:
        print(f"      NON  (fichier .env absent ou sans cle)  -> {ENV_FILE}")

    model = os.environ.get("AI_MODEL", MODEL_DEFAULT)
    print(f"\n[3] Modele Groq utilise : {model}")
    print("      (configurable via AI_MODEL dans .env)")

    if env_val or dotenv_val:
        print("\n[OK] La cle est configuree. Le mode IA complet sera actif au")
        print("     prochain demarrage du serveur (Groq -> Gemini -> statique).")
    else:
        print("\n[!] Aucune cle trouvee. Pour l'activer :")
        print("      python setup_groq.py --set gsk_ta_cle_ici")
        print("    ou colle ta cle depuis https://console.groq.com/keys")

    # Etat IA complet (reimporte la config qui charge le .env)
    try:
        import ai_automator
        print("\n[4] Etat des fournisseurs IA :")
        print(f"      Groq   : {'ACTIF (' + ai_automator.GROQ_MODEL + ')' if ai_automator.GROQ_ENABLED else 'inactif (pas de cle)'}")
        print(f"      Gemini : {'ACTIF' if ai_automator.GEMINI_ENABLED else 'inactif (pas de cle)'}")
        print(f"      Mode   : {'IA complete (cascade Groq -> Gemini -> statique)' if ai_automator.AI_ENABLED else 'fallback statique uniquement'}")
    except Exception as e:
        print(f"      (import ai_automator impossible : {e})")
    print()


def cmd_set(key):
    key = key.strip()
    if not key.startswith("gsk_"):
        print("[!] Attention : une cle Groq commence normalement par 'gsk_'.")
        print("    (ex: gsk_abc123def456...)")
    data = _read_env()
    data["GROQ_API_KEY"] = key
    data.setdefault("AI_MODEL", MODEL_DEFAULT)
    _write_env(data)
    protected = _protect_gitignore()
    print(f"[OK] Cle enregistree dans {ENV_FILE}")
    print(f"     GROQ_API_KEY={_mask(key)}")
    print(f"     AI_MODEL={data.get('AI_MODEL')}")
    if protected:
        print("[OK] .env ajoute au .gitignore (la cle ne sera jamais commitee)")
    print("\n[!] Pense a redemarrer le serveur pour que la cle soit prise en compte.")
    print("    Test rapide :  python setup_groq.py --test")


def cmd_unset():
    data = _read_env()
    if "GROQ_API_KEY" not in data:
        print("[!] Aucune cle GROQ_API_KEY dans le .env.")
        return
    del data["GROQ_API_KEY"]
    _write_env(data)
    print("[OK] Cle GROQ_API_KEY supprimee du .env.")


def cmd_test():
    print("=" * 55)
    print("  AFFILIMAX - Test de connexion Groq")
    print("=" * 55)
    env_val = os.environ.get("GROQ_API_KEY", "")
    dotenv_val = _read_env().get("GROQ_API_KEY", "")
    key = env_val or dotenv_val
    if not key:
        print("\n[X] Aucune cle Groq configuree.")
        print("    Lance :  python setup_groq.py --set gsk_ta_cle_ici")
        return 1
    model = os.environ.get("AI_MODEL", MODEL_DEFAULT)
    print(f"\n    Cle : {_mask(key)}")
    print(f"    Modele : {model}")
    print("    Appel API en cours... (quelques secondes)")
    try:
        from openai import OpenAI
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=key)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Reponds uniquement: OK"}],
            max_tokens=10,
            temperature=0,
        )
        reponse = (resp.choices[0].message.content or "").strip()
        print(f"\n[OK] Connexion reussie ! Reponse du modele : {reponse[:40]}")
        print("     Le mode IA complet (Groq -> Gemini -> statique) est actif.")
        print("     Lance le dashboard puis ouvre /video-factory.html pour generer.")
        return 0
    except Exception as e:
        print(f"\n[X] Echec de connexion : {e}")
        msg = str(e)
        if "401" in msg or "invalid" in msg.lower():
            print("     -> La cle semble invalide. Verifie-la sur https://console.groq.com/keys")
            print("        puis : python setup_groq.py --set gsk_nouvelle_cle")
        elif "429" in msg:
            print("     -> Quota depasse pour le moment. Reessaie plus tard.")
        elif "timeout" in msg.lower() or "connect" in msg.lower():
            print("     -> Probleme de connexion internet / pare-feu.")
        return 1


# ==================== INTERACTIF ====================

def interactive():
    print("=" * 55)
    print("  AFFILIMAX - Configuration de la cle Groq (assistant)")
    print("=" * 55)
    print("\nTa cle Groq se trouve sur : https://console.groq.com/keys")
    print("(compte gratuit : https://console.groq.com/login)")
    print("\nRegles de securite :")
    print("  - colle UNIQUEMENT la cle (commence par gsk_)")
    print("  - pas d'espace, pas de guillemets")
    print("  - ne partage JAMAIS ta cle ailleurs\n")

    env_val = os.environ.get("GROQ_API_KEY", "")
    dotenv_val = _read_env().get("GROQ_API_KEY", "")
    if env_val or dotenv_val:
        print(f"[INFO] Une cle est deja configuree : {_mask(env_val or dotenv_val)}")

    cle = input("Colle ta cle Groq (ou laisse vide pour annuler) : ").strip()
    if not cle:
        print("[OK] Annule. Rien n'a change.")
        return 0
    cmd_set(cle)
    print("\nVeux-tu tester la connexion maintenant ? (o/N)")
    if input("> ").strip().lower() in ("o", "oui", "y", "yes"):
        return cmd_test()
    return 0


# ==================== MAIN ====================

def main():
    parser = argparse.ArgumentParser(description="Affilimax - Setup cle Groq")
    parser.add_argument("--status", action="store_true", help="Verifier ou est la cle + etat IA")
    parser.add_argument("--set", metavar="gsk_xxx", help="Enregistrer la cle dans .env")
    parser.add_argument("--test", action="store_true", help="Tester la connexion Groq")
    parser.add_argument("--unset", action="store_true", help="Supprimer la cle du .env")
    args = parser.parse_args()

    if args.status:
        sys.exit(cmd_status() or 0)
    if args.set:
        sys.exit(cmd_set(args.set) or 0)
    if args.test:
        sys.exit(cmd_test() or 0)
    if args.unset:
        sys.exit(cmd_unset() or 0)

    sys.exit(interactive() or 0)


if __name__ == "__main__":
    main()
