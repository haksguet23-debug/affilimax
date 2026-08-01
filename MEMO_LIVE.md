# 🔥 MEMO URGENT : GO-LIVE AFFILIMAX (AUJOURD'HUI)

Ton infrastructure backend tourne. L'automate de promotion est prêt. Les images sont générées. Le contenu social est rempli. Le funnel de test est injecté.

**Pour que l'argent REEL circule**, voici tes 5 actions à faire dans la journée :

---

## 1. Mettre ta clé Stripe en LIVE 💳

Va sur https://dashboard.stripe.com/apikeys → Récupère ta clé qui commence par `sk_live_...`

Va sur Render → Dashboard du Web Service → onglet **Environment** :

```
STRIPE_SECRET_KEY = sk_live_51N...
STRIPE_WEBHOOK_SECRET = whsec_...
```

Pour le webhook : Stripe Dashboard → Developers → Webhooks → Add endpoint
- URL : `https://<ton-app>.onrender.com/api/stripe/webhook`
- Events : `payout.paid`, `payout.failed`, `account.updated`, `capability.updated`
- Copie le **Signing secret** (commence par `whsec_`) dans `STRIPE_WEBHOOK_SECRET`

## 2. Bloquer le mode "bac à sable" 🔒

Sur Render → Environment :
```
AFFILMAX_REQUIRE_LIVE = 1
```

Ça empêche le serveur de démarrer si les clés live manquent (fail-closed).
Et le mode démo est désactivé → seules les vraies données passent.

## 3. KYC automatique (Stripe Connect) 🏦

Tes partenaires doivent s'auto-onboarder. Va dans ton dashboard :
- https://affilimax.onrender.com/payouts.html (login admin)
- Pour chaque partenaire : clique "Connect Stripe" → génère un lien
- Envoie-lui le lien → **il doit lui-même remplir son IBAN et sa pièce d'identité** via l'interface officielle Stripe
- Tu ne peux *absolument* pas le faire à sa place (Stripe te bannirait)

Le webhook `account.updated` mettra `partners.json` à `onboarded: true` automatiquement.

## 4. Brancher l'envoi d'emails (optionnel) ✉️

Pour que l'API envoie de vrais emails marketing aux partenaires :
- Crée un compte sur https://resend.com (gratuit jusqu'à 3000 emails/mois)
- Récupère ta clé `re_...`
- Sur Render Environment : `RESEND_API_KEY = re_...`

## 5. Brancher Twitter / Telegram / Slack (optionnel) 🐦

Pour que les posts soient publiés vraiment (pas juste planifiés) :

**Twitter** : Crée une app sur https://developer.twitter.com → 4 clés OAuth
→ Render Environment : `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_SECRET`

**Telegram** : Crée un bot via @BotFather → copie le token
**Slack** : Crée un webhook entrant sur ton workspace
→ Édite `notifications_config.json` (déjà chargé par l'API)

---

## 🎯 Une fois tout ça fait

Pousse un **Manual Deploy** sur Render (ou `git push` si auto-deploy).

**Ce qui se passe** :
1. Trafic capturé via `/go/<produit>` → redirection vers Amazon avec **ton vrai lien d'affiliation**
2. Ventes Amazon → commissions sur **ton compte Amazon Partenaires**
3. Tu déclenches un payout via `payouts.html` → **argent réel sur l'IBAN du partenaire**
4. Webhook `payout.paid` → notification Telegram/Slack → tu sais que ça a marché
5. L'automate continue à poster du contenu → **trafic constant = ventes constantes**

---

## 📊 État actuel (déjà fait par l'automate)

✅ Serveur stable
✅ 30 produits chargés avec liens d'affiliation Amazon
✅ 4 partenaires (sophie, thomas, emma, test1) avec leurs préférences email
✅ Images produits générées par IA (ou placeholder)
✅ ~50 contenus sociaux générés (tweets, LinkedIn, Facebook, blog, emails)
✅ PromoAutomator actif (poste toutes les X heures selon trafic)
✅ Dashboard admin `/admin/preferences.html` opérationnel
✅ Espace partenaire `/partner.html` opérationnel

## 🔴 Ce que TU dois faire aujourd'hui

1. **5 min** : KYC toi-même sur Stripe (ton compte pro, ton IBAN)
2. **5 min** : KYC tes partenaires (envoie-leur le lien d'onboarding)
3. **5 min** : Coller `sk_live_` + `whsec_` + `AFFILMAX_REQUIRE_LIVE=1` sur Render
4. **5 min** : Brancher Resend (optionnel) + Twitter (optionnel)
5. **∞** : Le système travaille pour toi 24/7

→ Premier payout réel attendu sous 7-14 jours (délai Amazon pour confirmer les ventes).
