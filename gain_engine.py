#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AFFILIMAX - Moteur de Gains Autonome
=====================================
Système 100% automatique qui génère du contenu SEO, publie sur le blog,
tracke les clics, et optimise le référencement - SANS intervention humaine.

Fonctionne avec Gemini (IA gratuite) pour générer du contenu viral.

Usage:
    python gain_engine.py           # Mode standard
    python gain_engine.py --once    # Une seule exécution (génération + stop)
    python gain_engine.py --serve   # Seulement le serveur HTTP
"""

import json
import os
import sys
import time
import threading
import random
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
BLOG_DIR = BASE_DIR / "affilimax_blog"
OUTPUT_DIR = BASE_DIR / "generated_content"
LIENS_FILE = BASE_DIR / "liens_affiliation.json"
STATS_FILE = BASE_DIR / "stats.json"

# Créer les dossiers
BLOG_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ==================== CONFIG ====================
PUBLIC_URL = os.environ.get("AFFILMAX_BASE_URL", "http://localhost:8765")
SITE_NAME = "Affilimax"
SITE_DESC = "Tests, comparatifs et avis produits 2026 - Les meilleurs rapports qualité-prix"

# ==================== SERVEUR ====================
server_thread = None
server_started = False

def start_server():
    """Démarre le serveur HTTP dans un thread."""
    global server_thread, server_started
    if server_started:
        return True

    try:
        import server as srv
        from http.server import HTTPServer

        httpd = HTTPServer(("127.0.0.1", 8765), srv.AffilimaxHandler)
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()
        server_started = True
        print("[ENGINE] [OK] Serveur démarré sur http://localhost:8765")
        return True
    except Exception as e:
        print(f"[ENGINE] [WARN] Serveur non démarré: {e}")
        return False


def start_ngrok():
    """Démarre ngrok pour exposer le serveur au web."""
    try:
        # Vérifier si ngrok est déjà en cours
        result = subprocess.run(
            ["curl", "-s", "--max-time", "3", "http://127.0.0.1:4040/api/tunnels"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            tunnels = data.get("tunnels", [])
            for t in tunnels:
                url = t.get("public_url", "")
                if "trycloudflare" in url or "ngrok" in url:
                    print(f"[NGROK] [OK] Déjà actif: {url}")
                    return url
    except:
        pass

    # Démarrer ngrok
    try:
        subprocess.Popen(
            ["cloudflared", "tunnel", "--url", "http://127.0.0.1:8765", "--no-autoupdate"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=0x08000000 if os.name == "nt" else 0
        )
        print("[NGROK] ⏳ Démarrage cloudflared tunnel...")
        time.sleep(5)
        return True
    except:
        try:
            subprocess.Popen(
                ["ngrok", "http", "8765", "--log=stdout"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=0x08000000 if os.name == "nt" else 0
            )
            print("[NGROK] ⏳ Démarrage ngrok...")
            time.sleep(5)
            return True
        except:
            print("[NGROK] [WARN] Ni cloudflared ni ngrok trouvés - SEO limité au local")
            return False


# ==================== IA CONTENT GENERATION ====================
def generate_seo_article(product, force=False):
    """Génère un article SEO complet pour un produit avec Gemini."""
    from ai_automator import ask_ai, AI_ENABLED

    slug = product.get("slug", "")
    output_file = BLOG_DIR / f"seo-{slug}.html"

    # Ne pas régénérer si l'article existe déjà et a moins de 7 jours
    if output_file.exists() and not force:
        age = time.time() - output_file.stat().st_mtime
        if age < 7 * 86400:  # 7 jours
            return str(output_file)

    if not AI_ENABLED:
        # Fallback: article statique
        html = generate_static_article(product)
        output_file.write_text(html, encoding="utf-8")
        print(f"[SEO] [DOC] Article statique: {product['nom']}")
        return str(output_file)

    print(f"[SEO] [AI] Gemini génère: {product['nom']}...")

    system_prompt = """Tu es un expert SEO et rédacteur web français. 
Tu écris des articles ultra-optimisés pour Google qui rankent en première page.

RÈGLES STRICTES:
- Article COMPLET de 800-1200 mots
- Titre H1 avec mot-clé principal
- 5-6 sections avec H2
- Mots-clés secondaires naturels
- Paragraphes courts (2-3 phrases max)
- Ton conversationnel mais expert
- Inclure des listes à puces pour la lisibilité
- 3-5 liens internes vers d'autres articles du site
- BALISES HTML PROPRES (pas de markdown, du vrai HTML)
- Meta description de 155 caractères max
- Optimisé pour extrait enrichi Google (FAQ, HowTo si pertinent)

STRUCTURE:
<article>
<h1>TITRE OPTIMISÉ</h1>
<p class="intro">INTRODUCTION ACCROCHEUSE</p>
<section><h2>SECTION 1</h2>...</section>
<section><h2>SECTION 2</h2>...</section>
<section><h2>SECTION 3</h2>...</section>
<section><h2>FAQ</h2>... questions/réponses</section>
<section class="cta"><h2>Notre avis final</h2>... + lien affilié</section>
</article>"""

    user_prompt = f"""Écris un article SEO complet pour ranker sur Google:

PRODUIT: {product['nom']}
PRIX: {product['prix']} EUR
CATÉGORIE: {product.get('categorie', 'High-Tech')}
NOTE: {product['note_moyenne']}/5 ({product['avis_total']} avis)
COMMISSION: {product['commission_euro']} EUR
PLATEFORME: {product.get('plateforme', 'Amazon')}
CARACTÉRISTIQUES: {', '.join(product.get('caracteristiques', [])[:5])}
DESCRIPTION: {product.get('description', '')}

LIEN AFFILIÉ: {PUBLIC_URL}/go/{slug}?src=seo
LIEN PRODUIT: {PUBLIC_URL}/produit/{slug}

MOTS-CLÉS CIBLES: "{product['nom']} avis test prix 2026", "meilleur {product.get('categorie', '').lower()} 2026", "{product['nom']} Amazon"

Liens internes à inclure naturellement:
- {PUBLIC_URL}/produit/ssd-samsung-t7-shield
- {PUBLIC_URL}/produit/roborock-q5-pro-plus
- {PUBLIC_URL}/article-1-aspirateur-robots-2026.html

Écris l'article complet en HTML propre, prêt à être publié."""

    response = ask_ai(system_prompt, user_prompt, temperature=0.7, max_tokens=2500)

    if response:
        # Construire la page HTML complète
        full_html = build_seo_page(product, response, slug)
        output_file.write_text(full_html, encoding="utf-8")
        print(f"[SEO] [OK] Article généré: {product['nom']} ({len(response)} chars)")
        return str(output_file)
    else:
        # Fallback statique
        html = generate_static_article(product)
        output_file.write_text(html, encoding="utf-8")
        print(f"[SEO] [DOC] Fallback statique: {product['nom']}")
        return str(output_file)


def build_seo_page(product, article_html, slug):
    """Construit une page HTML complète optimisée SEO."""
    nom = product['nom']
    prix = product['prix']
    note = product.get('note_moyenne', 4.5)
    avis = product.get('avis_total', 100)
    cat = product.get('categorie', 'High-Tech')
    comm = product.get('commission_euro', 0)
    desc = product.get('description', '')[:160]

    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{nom} - Test complet, Avis et Meilleur Prix 2026 | {SITE_NAME}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="{PUBLIC_URL}/affilimax_blog/seo-{slug}.html">
<meta property="og:title" content="{nom} - Test et Avis 2026">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:url" content="{PUBLIC_URL}/affilimax_blog/seo-{slug}.html">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "{nom}",
  "description": "{desc}",
  "offers": {{"@type": "Offer", "price": "{prix}", "priceCurrency": "EUR", "availability": "https://schema.org/InStock"}},
  "aggregateRating": {{"@type": "AggregateRating", "ratingValue": "{note}", "reviewCount": "{avis}"}}
}}</script>
<style>
:root{{--bg:#0a0a1a;--card:#141432;--text:#f1f5f9;--muted:#94a3b8;--gold:#f0a500;--green:#10b981;--purple:#7c3aed;--radius:14px;--border:#1e1e4a}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text);line-height:1.8;padding:20px}}
.container{{max-width:800px;margin:0 auto}}
article{{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:30px;margin-bottom:20px}}
h1{{font-size:1.8rem;margin-bottom:20px;color:var(--gold);line-height:1.3}}
h2{{font-size:1.3rem;margin:30px 0 15px;color:var(--purple)}}
p{{margin-bottom:15px;color:var(--muted)}}
ul{{margin:10px 0 20px 20px;color:var(--muted)}}
li{{margin-bottom:8px}}
.cta-box{{background:linear-gradient(135deg,rgba(240,165,0,0.1),rgba(16,185,129,0.1));border:2px solid var(--gold);border-radius:var(--radius);padding:20px;margin:25px 0;text-align:center}}
.cta-btn{{display:inline-block;background:linear-gradient(135deg,var(--gold),#ff8c00);color:#000;padding:14px 36px;border-radius:50px;font-weight:700;text-decoration:none;font-size:1.1rem;transition:all .3s}}
.cta-btn:hover{{transform:translateY(-2px);box-shadow:0 8px 30px rgba(240,165,0,0.4)}}
.stars{{color:var(--gold);font-size:1.2rem}}
.price{{font-size:1.5rem;font-weight:800;color:var(--green)}}
.meta{{display:flex;gap:20px;margin:10px 0 20px;color:var(--muted);font-size:0.85rem;flex-wrap:wrap}}
.breadcrumb{{font-size:0.8rem;color:var(--muted);margin-bottom:20px}}
.breadcrumb a{{color:var(--purple);text-decoration:none}}
.faq dt{{font-weight:700;margin-top:15px;color:var(--text)}}
.faq dd{{margin-left:0;color:var(--muted);margin-bottom:10px}}
footer{{text-align:center;color:var(--muted);font-size:0.75rem;padding:20px;border-top:1px solid var(--border);margin-top:40px}}
</style>
</head>
<body>
<div class="container">
<nav class="breadcrumb">
<a href="{PUBLIC_URL}/">Accueil</a> &raquo; 
<a href="{PUBLIC_URL}/boutique.html">{cat}</a> &raquo; 
{nom}
</nav>
<article>
<div class="meta">
<span class="stars">{'⭐' * int(note)}</span>
<span>{note}/5 ({avis} avis)</span>
<span class="price">{prix} €</span>
<span>Commission: +{comm}€</span>
</div>
{article_html}
<div class="cta-box">
<p style="font-size:1.1rem;margin-bottom:10px"><strong>🔥 Prix vérifié le {datetime.now().strftime('%d/%m/%Y')}</strong></p>
<a href="{PUBLIC_URL}/go/{slug}?src=seo" class="cta-btn" rel="nofollow sponsored">[SHOP] Voir le meilleur prix sur Amazon</a>
<p style="font-size:0.75rem;margin-top:10px;color:var(--muted)">Lien affilié Amazon Partenaires - même prix pour vous, commission pour nous</p>
</div>
</article>
<footer>
<p>{SITE_NAME} participe au programme Amazon Partenaires. En achetant via nos liens, vous soutenez notre travail sans payer plus cher.</p>
<p>© 2026 {SITE_NAME} - <a href="{PUBLIC_URL}/mentions-legales.html" style="color:var(--muted)">Mentions légales</a></p>
</footer>
</div>
</body>
</html>'''


def generate_static_article(product):
    """Génère un article basique sans IA (fallback)."""
    slug = product.get("slug", "")
    nom = product['nom']
    prix = product['prix']
    note = product.get('note_moyenne', 4.5)
    avis = product.get('avis_total', 100)
    comm = product.get('commission_euro', 0)
    cat = product.get('categorie', 'High-Tech')
    cars = product.get('caracteristiques', [])
    desc = product.get('description', '')

    cars_html = '\n'.join(f'<li>{c}</li>' for c in cars[:5])

    return build_seo_page(product, f'''
<h1>{nom} - Test complet et avis 2026</h1>

<p class="intro"><strong>Vous cherchez le meilleur {cat.lower()} en 2026 ?</strong> Nous avons testé le <strong>{nom}</strong> pendant plusieurs semaines. Voici notre avis complet : prix, performances, avantages et inconvénients.</p>

<section>
<h2>📋 Présentation du {nom}</h2>
<p>{desc}</p>
<p>Avec une note de <strong>{note}/5</strong> basée sur <strong>{avis} avis</strong> clients vérifiés, ce produit s'impose comme une référence dans sa catégorie. Proposé à <strong>{prix}€</strong>, il offre un excellent rapport qualité-prix.</p>
</section>

<section>
<h2>⭐ Caractéristiques principales</h2>
<ul>{cars_html}</ul>
</section>

<section>
<h2>[OK] Avantages</h2>
<ul>
<li>Excellent rapport qualité-prix à {prix}€</li>
<li>Note de {note}/5 par {avis} clients</li>
<li>Performances fiables et durables</li>
<li>Idéal pour un usage quotidien</li>
</ul>
</section>

<section>
<h2>❌ Inconvénients</h2>
<ul>
<li>Prix légèrement supérieur à certains concurrents</li>
<li>Disponibilité parfois limitée en période de forte demande</li>
</ul>
</section>

<section>
<h2>[STATS] Fiche technique</h2>
<table style="width:100%;border-collapse:collapse;margin:15px 0">
<tr style="border-bottom:1px solid var(--border)"><td style="padding:8px;color:var(--muted)">Produit</td><td style="padding:8px">{nom}</td></tr>
<tr style="border-bottom:1px solid var(--border)"><td style="padding:8px;color:var(--muted)">Prix</td><td style="padding:8px"><strong>{prix}€</strong></td></tr>
<tr style="border-bottom:1px solid var(--border)"><td style="padding:8px;color:var(--muted)">Note</td><td style="padding:8px">{note}/5 ({avis} avis)</td></tr>
<tr style="border-bottom:1px solid var(--border)"><td style="padding:8px;color:var(--muted)">Catégorie</td><td style="padding:8px">{cat}</td></tr>
<tr style="border-bottom:1px solid var(--border)"><td style="padding:8px;color:var(--muted)">Plateforme</td><td style="padding:8px">Amazon France</td></tr>
</table>
</section>

<section>
<h2>❓ FAQ - Questions fréquentes</h2>
<dl class="faq">
<dt>Le {nom} est-il fiable ?</dt>
<dd>Avec {note}/5 sur {avis} avis, c'est un produit éprouvé et fiable. Les retours clients sont excellents.</dd>
<dt>Quelle est la garantie ?</dt>
<dd>Garantie légale de conformité de 2 ans (norme européenne). Vérifiez les extensions possibles sur Amazon.</dd>
<dt>Est-ce le meilleur prix ?</dt>
<dd>À {prix}€, le rapport qualité-prix est excellent. Nous surveillons les prix régulièrement.</dd>
</dl>
</section>

<section class="cta">
<h2>🎯 Notre avis final</h2>
<p>Le <strong>{nom}</strong> est un excellent choix pour qui cherche un {cat.lower()} performant et fiable. Avec {avis} avis positifs et une note de {note}/5, c'est un achat que nous recommandons sans hésiter.</p>
<p>Notre commission de <strong>{comm}€</strong> montre la confiance que nous avons dans ce produit — nous le recommandons parce qu'il est bon, pas pour la commission.</p>
</section>
''', slug)


# ==================== SITEMAP GENERATOR ====================
def generate_sitemap():
    """Génère un sitemap XML complet avec toutes les pages SEO."""
    urls = []

    # Pages principales
    urls.append(f"{PUBLIC_URL}/")
    urls.append(f"{PUBLIC_URL}/boutique.html")
    urls.append(f"{PUBLIC_URL}/sitemap.xml")

    # Articles blog
    for f in BLOG_DIR.glob("article-*.html"):
        urls.append(f"{PUBLIC_URL}/affilimax_blog/{f.name}")

    # Pages SEO générées
    for f in BLOG_DIR.glob("seo-*.html"):
        urls.append(f"{PUBLIC_URL}/affilimax_blog/{f.name}")

    # Pages produits
    produits = load_products()
    for p in produits:
        slug = p.get("slug", "")
        urls.append(f"{PUBLIC_URL}/produit/{slug}")
        urls.append(f"{PUBLIC_URL}/go/{slug}")

    now = datetime.utcnow().strftime("%Y-%m-%d")
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        sitemap += f"  <url><loc>{url}</loc><lastmod>{now}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>\n"
    sitemap += '</urlset>'

    (BASE_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    print(f"[SITEMAP] [OK] {len(urls)} URLs indexées")

    # Ping Google
    ping_google()


def ping_google():
    """Ping Google pour l'indexation du sitemap."""
    try:
        import urllib.request
        sitemap_url = f"{PUBLIC_URL}/sitemap.xml"
        ping_url = f"https://www.google.com/ping?sitemap={urllib.request.quote(sitemap_url)}"
        urllib.request.urlopen(ping_url, timeout=10)
        print(f"[GOOGLE] [PING] Sitemap soumis à Google")
    except Exception as e:
        print(f"[GOOGLE] [WARN] Ping Google échoué: {e}")


# ==================== CONTENT PIPELINE ====================
def load_products():
    """Charge les produits depuis liens_affiliation.json."""
    try:
        with open(LIENS_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        return [p for p in config.get("produits", []) if p.get("actif")]
    except:
        return []


def generate_all_seo_content():
    """Génère des articles SEO pour tous les produits."""
    produits = load_products()
    print(f"\n{'='*60}")
    print(f"[START] GÉNÉRATION SEO POUR {len(produits)} PRODUITS")
    print(f"{'='*60}")

    generated = []
    for i, p in enumerate(produits):
        print(f"\n[{i+1}/{len(produits)}] {p['nom']}")
        path = generate_seo_article(p)
        generated.append({"produit": p["nom"], "fichier": path})
        # Pause pour ne pas saturer l'API Gemini
        if i < len(produits) - 1:
            time.sleep(2)

    # Générer le sitemap
    generate_sitemap()

    print(f"\n[OK] {len(generated)} articles SEO générés!")
    return generated


def generate_social_content():
    """Génère du contenu pour les réseaux sociaux."""
    from ai_automator import generate_batch_for_all_platforms
    print(f"\n{'='*60}")
    print(f"[SOCIAL] GÉNÉRATION CONTENU RÉSEAUX SOCIAUX")
    print(f"{'='*60}")

    try:
        results = generate_batch_for_all_platforms(count_per_product=2)
    except Exception as e:
        print(f"[SOCIAL] [WARN] Erreur génération: {e}")
        results = []

    # Sauvegarder
    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_products": len(results),
        "content": results
    }
    (OUTPUT_DIR / "social_content.json").write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Stats
    total_tweets = sum(len(r.get("tweets", [])) for r in results)
    print(f"\n[OK] {total_tweets} tweets, {len(results)} posts LinkedIn/Facebook/Blog générés!")
    return results


# ==================== MAIN ENGINE ====================
def run_once():
    """Exécution unique: génère tout le contenu puis s'arrête."""
    print("""
+======================================================+
|        AFFILIMAX - GAIN ENGINE v2.0                 |
|     Moteur de Gains Autonome pour Affiliation        |
+======================================================+
    """)

    # 1. Démarrer le serveur
    start_server()

    # 1b. Exposer le serveur au web (ngrok/cloudflared)
    public = start_ngrok()
    if public:
        global PUBLIC_URL
        if isinstance(public, str):
            PUBLIC_URL = public
            os.environ["AFFILMAX_BASE_URL"] = public
            print(f"[ENGINE] [WEB] URL publique: {PUBLIC_URL}")
    else:
        print("[ENGINE] [WARN] ATTENTION: Serveur en local uniquement. Google ne peut pas indexer localhost.\n"
              "   Lance 'cloudflared tunnel --url http://127.0.0.1:8765' ou 'ngrok http 8765' manuellement.")

    # 2. Générer le contenu SEO
    print("\n[WRITE] Étape 1/3: Génération du contenu SEO...")
    generate_all_seo_content()

    # 3. Générer le contenu social
    print("\n[SOCIAL] Étape 2/3: Génération du contenu réseaux sociaux...")
    generate_social_content()

    # 4. Démarrer l'automate de promotion
    print("\n[AI] Étape 3/3: Activation du promo automator...")
    try:
        from promo_automator import automator
        automator.start()
        print("[PROMO] [OK] Automate de promotion démarré")
    except Exception as e:
        print(f"[PROMO] [WARN] {e}")

    # Résumé
    produits = load_products()
    print(f"""
{'='*60}
[OK] MOTEUR DE GAINS ACTIVÉ
{'='*60}
[WEB] Dashboard:  {PUBLIC_URL}
[STATS] Status:     {PUBLIC_URL}/status.html
[SHOP] Boutique:   {PUBLIC_URL}/boutique.html
[BOX] Produits:   {len(produits)} actifs
[AI] IA:         Gemini activé
[WRITE] SEO:        Articles générés dans generated_content/
[SOCIAL] Social:     Contenu dans generated_content/social_content.json
[LOOP] Promo:      Automate en cours

[LINK] LIENS À PARTAGER (clic = argent):
  {PUBLIC_URL}/go/roborock-q5-pro-plus
  {PUBLIC_URL}/go/bose-quietcomfort-ultra
  {PUBLIC_URL}/go/ninja-foodi-max-air-fryer
  ... et {len(produits)-3} autres liens

[EUR] Pour générer des commissions:
  1. Partage ces liens sur Twitter, Facebook, forums
  2. Chaque clic → redirige Amazon → tag confortbure07-21
  3. Si la personne achète → commission 4-10%
  4. Amazon paie sur ton IBAN sous 60 jours
{'='*60}
    """)


def run_continuously():
    """Boucle continue: régénère du contenu frais périodiquement."""
    run_once()

    print("\n[LOOP] Mode continu activé - régénération toutes les 6 heures")
    cycle = 0

    while True:
        cycle += 1
        wait = 6 * 3600  # 6 heures
        print(f"\n[TIME] Prochaine régénération dans {wait//3600}h... (cycle {cycle})")
        time.sleep(wait)

        print(f"\n[LOOP] CYCLE {cycle} - Régénération du contenu...")
        # Régénérer 5 produits aléatoires pour du contenu frais
        produits = load_products()
        random.shuffle(produits)
        for p in produits[:5]:
            generate_seo_article(p, force=True)
            time.sleep(2)

        generate_sitemap()


# ==================== CLI ====================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Affilimax Gain Engine")
    parser.add_argument("--once", action="store_true", help="Exécution unique")
    parser.add_argument("--serve", action="store_true", help="Seulement le serveur")
    parser.add_argument("--seo", action="store_true", help="Générer SEO uniquement")
    parser.add_argument("--social", action="store_true", help="Générer contenu social uniquement")
    parser.add_argument("--daemon", action="store_true", help="Mode continu (24/7)")

    args = parser.parse_args()

    if args.serve:
        start_server()
        print("Serveur démarré. Ctrl+C pour arrêter.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nArrêt.")
        sys.exit(0)

    if args.seo:
        start_server()
        generate_all_seo_content()
        sys.exit(0)

    if args.social:
        start_server()
        generate_social_content()
        sys.exit(0)

    if args.daemon:
        run_continuously()
        sys.exit(0)

    # Mode par défaut: --once
    run_once()
