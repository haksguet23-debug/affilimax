# Confort Bureau — Meilleur 2026 — Site statique SEO Amazon Partenaires

## Qu'est-ce que c'est ?

Un **mini-site statique** de 5 articles SEO optimises pour generer
du trafic organique Google, convertit ce trafic en **clics Amazon via /go/<slug>**
avec tag d'affiliation **confortbure07-21**, et te fait gagner 4-10% de commission
sur chaque vente.

## Architecture

```
affilimax_blog/
├── index.html                        (hub : top produits + 5 articles)
├── article-1-aspirateur-robots-2026.html
├── article-2-casque-audio-2026.html
├── article-3-air-fryer-2026.html
├── article-4-tapis-marche-2026.html
├── article-5-lego-adulte-2026.html
├── mentions-legales.html             (LCEN Article 6-III)
├── politique-confidentialite.html    (RGPD Article 13)
├── sitemap.xml                       (Google Search Console)
├── robots.txt                        (autorise crawl)
└── rss.xml                           (syndication)
```

Total : ~165 KB, 100% statique, 0 JS, 0 cookie.

## SEO Ready ✅

- **Schema JSON-LD** Article + FAQ + Product (etoiles Google)
- **BreadcrumbList** schema (navigation)
- **Open Graph + Twitter Card** meta tags
- **Canonical URL** auto-generee
- **Disclosure Amazon Partenaires** en 3 positions (header + avant 1er lien + footer)
- **Mobile-first** CSS (16px, 48x48px tap targets)
- **Sitemap.xml + robots.txt** prets pour Google Search Console

## Deploy sur Render.com (gratuit)

1. Creer compte sur render.com (gratuit)
2. New > Static Site
3. Build command : `python _build_static_site.py --partner sophie`
4. Publish directory : `affilimax_blog`
5. URL generee : `https://confort-bureau.onrender.com`

## Config Google Search Console (apres deploy)

1. Aller sur https://search.google.com/search-console
2. Ajouter la propriete (URL prefix)
3. Verifier via DNS TXT ou fichier HTML
4. Soumettre le sitemap : `https://confort-bureau.onrender.com/sitemap.xml`
5. Demander l'indexation des 5 articles

## Suites automatiques

```bash
# Quand tu rajoutes un produit ou change un lien : rebuild
python _build_static_site.py

# Deployer (si git + render connect)
git add affilimax_blog && git commit && git push
```
