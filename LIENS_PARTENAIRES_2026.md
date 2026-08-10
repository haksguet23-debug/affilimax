# 🔗 LIENS DE TRACKING PARTENAIRES — Affilimax

> **Objectif :** activer les 3 partenaires influents pour envoyer du trafic qualifié
> vers affilimax.onrender.com. Chaque clic est attribué au bon partenaire via `?ref=`,
> chaque conversion crédite automatiquement son solde (Stripe Connect).
>
> Généré le **10/08/2026** · Tag Amazon : `confortbure07-21`

---

## 🧮 Comment ça marche

1. Le partenaire reçoit son lien unique : `https://afflimax.onrender.com/go/{produit}?ref={partenaire}`
2. Le visiteur clique → redirection Amazon (tag `confortbure07-21`) + **clic attribué au partenaire**
3. Si le visiteur achète dans les 24h → conversion Amazon → **commission créditée au partenaire**
4. Le partenaire voit son solde sur `/partner.html` et se fait payer via Stripe Connect

---

## 🤝 1. Roxanne — BabyChouFamily (Instagram 200K+)

**Thème :** Famille, enfants, maison, bien-être.

| Produit | Lien de tracking |
|---|---|
| AirPods 4 | `https://afflimax.onrender.com/go/apple-airpods-4?ref=roxanne_famille` |
| Lego Notre-Dame | `https://afflimax.onrender.com/go/lego-ideas-notre-dame-paris?ref=roxanne_famille` |
| Kindle 2024 | `https://afflimax.onrender.com/go/amazon-kindle-2024?ref=roxanne_famille` |
| Tapis de marche pliable | `https://afflimax.onrender.com/go/tapis-marche-pliable-lontek?ref=roxanne_famille` |
| Enceinte JBL Go 4 | `https://afflimax.onrender.com/go/jbl-go-4-enceinte?ref=roxanne_famille` |
| **Lien vitrine** | `https://afflimax.onrender.com/?ref=roxanne_famille` |

**Discours suggéré (stories/reel) :**
> « Mes bons plans Amazon de la semaine 👇 J'ai testé pour vous, les liens sont en bio ! »

---

## 🤝 2. SerialDealer — Telegram (10K+)

**Thème :** Bons plans, tech, gaming, high-tech.

| Produit | Lien de tracking |
|---|---|
| Souris Logitech G502 | `https://afflimax.onrender.com/go/logitech-g502-hero?ref=serialdealer_deals` |
| Clavier mécanique | `https://afflimax.onrender.com/go/epomaker-aula-f75?ref=serialdealer_deals` |
| SSD Samsung T7 | `https://afflimax.onrender.com/go/ssd-samsung-t7-shield?ref=serialdealer_deals` |
| Power Bank Anker 20000 | `https://afflimax.onrender.com/go/anker-power-bank-20000?ref=serialdealer_deals` |
| Casque Bose QC Ultra | `https://afflimax.onrender.com/go/bose-quietcomfort-ultra?ref=serialdealer_deals` |
| **Lien vitrine** | `https://afflimax.onrender.com/?ref=serialdealer_deals` |

**Discours suggéré (message Telegram) :**
> 🔥 DERNIERS BONS PLANS — prix canon aujourd'hui sur Amazon, lien direct ci-dessous 👇

---

## 🤝 3. Frandroid — Média tech (mail+site)

**Thème :** High-tech, tests, guides d'achat.

| Produit | Lien de tracking |
|---|---|
| AirPods 4 | `https://afflimax.onrender.com/go/apple-airpods-4?ref=frandroid_tech` |
| Xiaomi Robot S20+ | `https://afflimax.onrender.com/go/xiaomi-robot-aspirateur-s20?ref=frandroid_tech` |
| Ninja Air Fryer | `https://afflimax.onrender.com/go/ninja-foodi-max-air-fryer?ref=frandroid_tech` |
| Roborock Q5 Pro+ | `https://afflimax.onrender.com/go/roborock-q5-pro-plus?ref=frandroid_tech` |
| Samsung Galaxy Tab A9+ | `https://afflimax.onrender.com/go/samsung-galaxy-tab-a9-plus?ref=frandroid_tech` |
| **Lien vitrine** | `https://afflimax.onrender.com/?ref=frandroid_tech` |

---

## 🤝 4. Madame Bons Plan — Instagram (~966K)

**Thème :** Bons plans généralistes + tech (compte connexe @madamet3ch) · cible familles/parents.
**Contact :** `madamebonplan@loopstr.fr` (bio officielle Instagram, agence Loopstr) · `hello@loopstr.fr`

| Produit | Lien de tracking |
|---|---|
| Apple AirPods 4 | `https://afflimax.onrender.com/go/apple-airpods-4?ref=madame_bons_plan` |
| Amazon Kindle 2024 | `https://afflimax.onrender.com/go/amazon-kindle-2024?ref=madame_bons_plan` |
| Tapis de marche LONTEK | `https://afflimax.onrender.com/go/tapis-marche-pliable-lontek?ref=madame_bons_plan` |
| Ninja Air Fryer | `https://afflimax.onrender.com/go/ninja-foodi-max-air-fryer?ref=madame_bons_plan` |
| Lego Notre-Dame | `https://afflimax.onrender.com/go/lego-ideas-notre-dame-paris?ref=madame_bons_plan` |
| **Lien vitrine** | `https://afflimax.onrender.com/?ref=madame_bons_plan` |

**Discours suggéré (story/reel bons plans) :**
> 🛍️ Mes bons plans Amazon de la semaine — Kindle, AirPods, air fryer… tout est dans le lien ! 👇

---

## ✅ CHECKLIST D'ACTIVATION (à faire par le fondateur)

- [ ] **1. Stripe Connect** : clé Stripe LIVE dans Render (`STRIPE_SECRET_KEY`) → `/payouts.html` → bouton "Connecter" pour chaque partenaire (onboarding Stripe)
- [ ] **2. Envoyer les liens** : copier le tableau ci-dessus et l'envoyer à chaque partenaire
- [ ] **3. Vérifier l'attribution** : après un clic, contrôler `/live.html` (activité récente → colonne "ref")
- [ ] **4. Premier payout** : quand un solde ≥ 25 €, déclencher le transfert via `/payouts.html`

---

## 🔧 URLS UTILES

| Page | URL |
|---|---|
| Vitrine publique (pour les visiteurs) | `https://afflimax.onrender.com/` |
| Dashboard fondateur | `https://afflimax.onrender.com/dashboard` |
| Live tracking | `https://afflimax.onrender.com/live.html` |
| Espace partenaire | `https://afflimax.onrender.com/partner.html` |
| Paiements | `https://afflimax.onrender.com/payouts.html` |
| Webhook ventes Amazon | `https://afflimax.onrender.com/amazon/notification` |

*Document généré par Buffy/Freebuff — les liens sont déjà actifs, il ne manque que l'envoi aux partenaires.*
