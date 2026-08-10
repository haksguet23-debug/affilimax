# 🚀 MÉMO 06 — Correctifs pour débloquer les gains réels

> Généré le **10/08/2026** après audit complet. But : passer de **0 € réels** à des
> gains via des correctifs concrets + des leviers de trafic actionnables.

---

## 🔴 LES 6 PROBLÈMES IDENTIFIÉS (pourquoi 0 € malgré un système complet)

| # | Problème | Conséquence réelle |
|---|----------|--------------------|
| 1 | **Zéro trafic réel** : les 5 clics enregistrés datent tous du 01/08 et sont des **tests** (`referencement_direct`) | 0 visiteur réel en 15 jours = 0 clic = 0 vente |
| 2 | **La racine `/` servait le dashboard interne** (stats de commissions) au lieu de la vitrine produits | Tout visiteur Google atterrissait sur un dashboard technique → fuite de conversion |
| 3 | **Sitemap incomplet** : seules 99 URLs (produits) indexables, **les 70+ articles SEO absents** | Google ne découvrait pas les articles = 0 trafic organique |
| 4 | **robots.txt freiné** : `Crawl-delay: 10` (obsolète, ralentit Google) + `Allow: /payouts.html` (page 401) + `/go` (interne) | Indexation lente et pages internes indexées à tort |
| 5 | **Aucun webhook de ventes Amazon branché** : même si un client achetait, la vente n'était **jamais créditée** dans les stats ni au partenaire | Ventes invisibles = gains invisibles |
| 6 | **3 partenaires influents (200K+10K+média #1) jamais activés** : aucun lien de tracking prêt, aucun onboarding | Le levier de trafic le plus rapide est resté inexploité |

---

## ✅ LES CORRECTIFS APPLIQUÉS (dans `server.py` + dashboards)

### 1. Racine = vitrine publique, dashboard déplacé
- `/` sert maintenant `pub.html` (vitrine produits avec CTA Amazon) — c'est la page que Google indexe
- Dashboard interne conservé sur **`/dashboard`** (et `/index.html`)
- Liens « Dashboard » mis à jour dans **7 dashboards** (ai-content, live, partner, payouts, promo, status, video-factory)

### 2. Sitemap enrichi : 99 → 166 URLs
- Ajout de **67 articles SEO** (affilimax_blog : seo-*, guide-*, comparatif-*, top-*, article-*, checklist, liste-*)
- Retrait des pages internes `/payouts.html` et `/go` du sitemap
- Canonical ajouté dans pub.html (évite le contenu dupliqué `/` vs `/pub.html`)

### 3. robots.txt nettoyé
- ❌ `Crawl-delay: 10` supprimé (Google l'indexe plus vite)
- ❌ `Allow: /payouts.html` supprimé (page protégée 401)
- ❌ `Allow: /go` supprimé
- ✅ Désindexation des pages internes : /dashboard, /index.html, /live.html, /status.html, /ai-content.html, /video-factory.html, /payouts.html, /partner.html, /promo.html, /admin, /api, /healthz
- ✅ Autorisation explicite des articles : /affilimax_blog/

### 4. Webhook de ventes Amazon : `/amazon/notification`
- **Reçoit les ventes Amazon** (JSON ou XML Instant Notification) et les crédite automatiquement dans stats.json + partners.json
- **Sécurisé** : requiert `AMAZON_WEBHOOK_SECRET` (env var) dans le header `X-Amzn-Webhook-Secret` — sans lui, requête rejetée (testé : 403)
- **Anti-doublon** par `order_id` (fichier `amazon_orders_seen.json`, verrouillé)
- **Anti-fraude chiffres** : produit inconnu SANS commission fournie → conversion refusée (pas de faux 10 €)
- ⚠️ **À configurer chez Amazon** : Outils → Instant Notification / Webhooks → URL `https://afflimax.onrender.com/amazon/notification` + définir `AMAZON_WEBHOOK_SECRET` dans Render

### 5. Attribution partenaire (`?ref=`)
- Les clics `/go/<slug>?ref=<partenaire>` et `/api/click` enregistrent maintenant le **ref partenaire** dans l'activité récente + événements SSE
- Document : **`LIENS_PARTENAIRES_2026.md`** — liens de tracking prêts pour Roxanne, SerialDealer et Frandroid

---

## 🎯 PROCHAINES ACTIONS POUR DES GAINS RÉELS (priorité décroissante)

### ⚡ Action 1 — Activer les partenaires (le plus rapide, potentiel énorme)
1. Définir la clé Stripe **LIVE** dans Render (`STRIPE_SECRET_KEY`)
2. `/payouts.html` → « Connecter » pour chaque partenaire (onboarding Stripe)
3. Envoyer les liens de `LIENS_PARTENAIRES_2026.md` à chaque partenaire
4. **Un seul post de Roxanne (200K) ou SerialDealer (10K) = 100-1000+ clics réels**

### ⚡ Action 2 — Indexation Google
1. **Google Search Console** : vérifier `afflimax.onrender.com` + soumettre `sitemap.xml`
2. Cliquer « 📡 Forcer IndexNow » dans `/live.html` (Bing/Yandex déjà notifiés)
3. Attendre 2-4 semaines pour les premiers résultats organiques

### ⚡ Action 3 — Pinterest (calendrier 14 jours prêt)
- Publier les 70 épingles du calendrier (`CALENDRIER_PINTEREST_14JOURS.txt`) → trafic visuel immédiat

### ⚡ Action 4 — Brancher le webhook Amazon
- Configurer `/amazon/notification` chez Amazon + `AMAZON_WEBHOOK_SECRET` dans Render
- Sans ça, les ventes réelles ne seront pas créditées dans le dashboard

---

## 🔧 RAPPEL DES URLS

| Page | URL |
|---|---|
| Vitrine publique (indexée) | `https://afflimax.onrender.com/` |
| Dashboard fondateur | `https://afflimax.onrender.com/dashboard` |
| Live tracking | `/live.html` · Paiements : `/payouts.html` |
| Espace partenaire | `/partner.html` · Webhook Amazon : `/amazon/notification` |

*Document généré par Buffy/Freebuff · 10/08/2026*
