# AFFILIMAX — Mémo Récapitulatif Global
## Projet complet — 1er Août 2026

---

## 📌 QU'EST-CE QU'AFFILIMAX ?

Affilimax est un **site d'affiliation Amazon** automatisé. Le principe :
1. Des articles SEO comparent/recommandent des produits
2. Chaque lien est taggé `confortbure07-21` (Amazon Partenaires)
3. Un visiteur clique → cookie Amazon 24h → s'il achète → commission 4-10%
4. Amazon paie sur l'IBAN sous 60 jours

---

## 🌐 URLs

| Usage | URL |
|-------|-----|
| **Site public (Google indexable)** | https://afflimax.onrender.com |
| Dashboard live local | http://localhost:8765/live.html |
| Dashboard status | http://localhost:8765/status.html |
| GitHub (Render) | https://github.com/haksguet23-debug/afflimax |
| GitHub (backup) | https://github.com/haksguet23-debug/affilimax |
| Sitemap | https://afflimax.onrender.com/sitemap.xml |

---

## 📊 ÉTAT ACTUEL (1er Août 2026)

| Métrique | Valeur |
|----------|--------|
| Articles SEO en ligne | 58 |
| URLs dans le sitemap | 122 |
| Produits Amazon taggés | 30 |
| Tag affilié | `confortbure07-21` |
| Clics trackés | 5 |
| Commissions | 0,00 € |
| Serveur local | 🟢 UP |
| Render (cloud) | 🟢 UP |
| Auto-engine | 🟢 Tourne (PID variable) |
| Uptime Render | 7.7+ jours |

---

## 📁 STRUCTURE DU PROJET

### Emplacements

| Dossier | Rôle |
|---------|------|
| `C:\Windows\system32\` | Serveur local (historique) |
| `C:\Users\leordi\affilimax\` | Dépôt Git propre |
| `C:\Users\leordi\affilimax\affilimax_blog\` | 58 articles HTML |

### Fichiers principaux

| Fichier | Rôle |
|---------|------|
| `server.py` | Serveur HTTP principal (port 8765, API REST, SSE, redirects /go/) |
| `auto_engine.py` | Moteur d'automation 24/7 (auto-heal, IndexNow, monitoring) |
| `gain_engine.py` | Moteur de gains (SEO + social + serveur) |
| `traffic_engine.py` | Ancien moteur de trafic (remplacé par auto_engine.py) |
| `live.html` | Dashboard temps réel |
| `status.html` | Dashboard diagnostic brique par brique |
| `index.html` | Page d'accueil du site |
| `liens_affiliation.json` | 30 produits Amazon avec ASINs, prix, commissions |
| `render.yaml` | Configuration Render.com |
| `promo_automator.py` | Automate de promotion réseaux sociaux |
| `stripe_config.py` | Configuration Stripe Connect |
| `twitter_poster.py` | Publication automatique Twitter |
| `email_sender.py` | Envoi d'emails marketing |
| `notifications.py` | Notifications Telegram/Slack |
| `partner_auth.py` | Authentification partenaires |
| `social_reseaux.py` | Génération contenu réseaux sociaux |

---

## 🎮 COMMENT TOUT LANCER

### Sur le PC local

```bash
# 1. Lancer le serveur
cd C:\Windows\system32
python server.py

# 2. Lancer l'auto-engine en arrière-plan
python -c "import subprocess, os; subprocess.Popen(['python','-u','auto_engine.py'], stdin=subprocess.DEVNULL, stdout=open('auto_engine_out.log','a'), stderr=subprocess.STDOUT, creationflags=0x08000000)"

# 3. Ouvrir le dashboard
start http://localhost:8765/live.html
```

### Double-clic : `start.bat`

---

## 📝 LES 58 ARTICLES SEO

### Articles générés automatiquement (seo-*.html)
30 articles individuels par produit (Roborock, Bose, Sony, Ninja, Kindle, Lego, etc.)

### Articles thématiques (créés manuellement)

| Article | Thème |
|---------|-------|
| article-1 à 5 | Aspirateur robot, Casque audio, Air Fryer, Tapis marche, Lego |
| comparatif-aspirateurs-robots-2026 | Roborock vs Xiaomi |
| comparatif-casques-audio-2026 | Bose vs Sony |
| comparatif-ecouteurs-sans-fil-2026 | AirPods 4 vs JBL vs Bose |
| comparatif-objets-connectes-2026 | Galaxy Tab, AirPods, AirTag, Renpho, Hue |
| guide-ninja-air-fryer-2026 | Tout sur le Ninja Foodi Max |
| guide-tapis-marche-2026 | Tapis LONTEK pour télétravail |
| guide-bureau-high-tech-2026 | Setup bureau complet |
| guide-cadeaux-noel-2026 | Cadeaux par budget |
| guide-voyage-2026 | Accessoires indispensables |
| guide-gaming-2026 | Setup gamer complet |
| guide-cuisine-connectee-2026 | Air Fryer, café, Hue, tablette |
| guide-maison-connectee-2026 | 6 produits Smart Home |
| guide-sport-maison-2026 | Tapis, balance, enceinte |
| guide-investissement-2026 | 4 livres finance/crypto |
| top-10-high-tech-2026 | Sélection best-sellers |
| top-5-livres-2026 | Psychologie argent, ETF, crypto, marketing |
| top-5-smartphones-accessoires-2026 | Tab, SSD, AirTag |
| top-high-tech-moins-100-euros-2026 | Bons plans <100€ |
| top-cadeaux-high-tech-2026 | Idées cadeaux |
| top-materiel-photo-video-2026 | Setup créateur contenu |

---

## 🤖 AUTO-ENGINE — Ce qu'il fait 24/7

| Tâche | Fréquence |
|-------|-----------|
| Vérifie serveur local | 5 minutes |
| Vérifie Render | 5 minutes |
| Auto-heal (redémarre si 2 échecs) | Automatique |
| Ping IndexNow (Bing/Yandex) | 1 heure |
| Refresh SEO | 12 heures |
| Rotation logs | 500 cycles |
| Alerte clics détectés | En continu |

**Logs :** `auto_engine_out.log` + `auto_engine.log`

---

## 💰 COMMENT LES COMMISSIONS ARRIVENT

```
1. Visiteur humain trouve le site via Google
2. Il lit un article et clique sur /go/produit
3. Cookie Amazon 24h posé (tag confortbure07-21)
4. Il achète SUR AMAZON (le produit cliqué ou n'importe quoi d'autre)
5. Amazon expédie → commission visible J+2 à J+5
6. Amazon paie sur IBAN → J+60
```

### Exemples de commissions par produit

| Produit | Prix | Taux | Commission |
|---------|------|------|------------|
| Bose QuietComfort Ultra | 399,99€ | 4% | 16,00€ |
| Roborock Q5 Pro+ | 379,99€ | 4% | 15,20€ |
| Sony WH-1000XM5 | 299,99€ | 4% | 12,00€ |
| Samsung Galaxy Tab A9+ | 219,99€ | 4% | 8,80€ |
| Ninja Foodi Max | 174,99€ | 5% | 8,75€ |

---

## 🔧 CORRECTIFS APPLIQUÉS (historique)

| Bug | Solution |
|-----|----------|
| Tracking /go/ ne fonctionnait pas | Correction dans server.py |
| Indentation error dans gain_engine.py | Réécriture de la ligne |
| Emojis causant crashes Unicode | Remplacement par ASCII |
| echo. non reconnu dans start.bat | Remplacement par echo |
| Google n'indexait pas (trycloudflare) | Déploiement Render.com |
| IndexNow HTTP 422 | Réduction du nombre d'URLs |
| .env.render commité | Ajout au .gitignore |
| SSL désactivé pour Render | http_get_public avec vrai SSL |
| stdin manquant sur restart | Ajout stdin=DEVNULL |
| pingIndexNow factice dans live.html | Appel réel à l'API IndexNow |

---

## 🔑 CLÉS API NÉCESSAIRES

| Variable | Utilité | Status |
|----------|---------|--------|
| STRIPE_SECRET_KEY | Paiements partenaires | ❌ Pas configuré |
| GEMINI_API_KEY | Génération IA contenu | ❌ Quota épuisé |
| GROQ_API_KEY | Génération IA (fallback) | ❌ Pas configuré |
| RESEND_API_KEY | Emails marketing | ❌ Pas configuré |
| TELEGRAM_BOT_TOKEN | Notifications | ❌ Pas configuré |

---

## 📈 SESSIONS DE TRAVAIL

| Session | Date | Contenu |
|---------|------|---------|
| 1 | 1er Août | Serveur réparé, bugs corrigés |
| 2 | 1er Août | Tunnel cloudflared, traffic_engine |
| 3 | 1er Août | 4 articles comparatifs |
| 4 | 1er Août | 4 articles lifestyle |
| 5 | 1er Août | Browser tests, 4 clics |
| 6 | 1er Août | 4 articles finance/sport |
| 7 | 1er Août | 4 articles tech/maison |
| 8 | 1er Août | Vérification tunnel + Google |
| 9 | 1er Août | 4 articles + 5ème clic |
| 10 | 1er Août | Déploiement Render |
| 11 | 1er Août | Auto-engine + Dashboard live + Nettoyage PC |

---

## ⚠️ POINTS D'ATTENTION

- **Render free tier** : le serveur se met en veille après 15 min d'inactivité. Le premier visiteur peut attendre 50s.
- **URL trycloudflare** : l'ancien tunnel est obsolète, ne plus l'utiliser.
- **Stripe** : mode DEMO (pas de clé). Les partenaires ne peuvent pas être payés.
- **Gemini** : quota gratuit épuisé. Nécessite une clé API payante pour régénérer du contenu IA.
- **GitHub CLI** : authentifié en tant que `haksguet23-debug`.

---

## 🚀 PROCHAINES ÉTAPES POUR DES GAINS RÉELS

1. ✅ Site en ligne sur une vraie URL (Render)
2. ✅ Sitemap soumis à Google
3. ⏳ Attendre l'indexation Google (24-72h)
4. ⏳ Premiers visiteurs humains
5. ⏳ Premiers clics → premières ventes
6. ⏳ Premières commissions (J+60 après vente)

---

*Mémo généré le 1er Août 2026 — Dernière mise à jour : Session 11*
*Fichier : MEMO_GLOBAL_Affilimax.md*
