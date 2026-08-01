# 💳 MÉMO 01 — Brancher Stripe en mode LIVE

> **Étape où je me suis arrêté(e) :** prêt côté code, en attente de tes clés.

## ✅ Déjà fait (par moi)

- `stripe_config.py` détecte automatiquement si `STRIPE_SECRET_KEY` commence par `sk_live_` → bascule en mode LIVE.
- Webhook `/api/stripe/webhook` configuré avec **vérification de signature HMAC** (fail-closed si pas de secret).
- Endpoint `/api/stripe/onboard` crée de vrais comptes **Stripe Connect Express** (pays par défaut France).
- Endpoint `/api/stripe/payout` envoie de vrais `Transfer` vers les comptes Connect.
- Script `onboard_partners_live.py` permet d'onboarder en lot, avec `--dry-run` puis `--apply`.
- Garde-fou `AFFILMAX_REQUIRE_LIVE=1` → refuse de démarrer sans clé LIVE.

## ⏸ Ce qu'il te reste à faire (humain requis)

| # | Action | Où |
|---|---|---|
| 1 | Finaliser ton KYC Stripe (identité, IBAN, adresse) | https://dashboard.stripe.com/onboarding |
| 2 | Activer **Stripe Connect** dans le dashboard | https://dashboard.stripe.com/connect/overview |
| 3 | Récupérer `sk_live_...` et `pk_live_...` | https://dashboard.stripe.com/apikeys |
| 4 | Configurer le webhook Stripe (URL + secret) | https://dashboard.stripe.com/webhooks |
| 5 | Coller ces variables sur Render.com | Dashboard > Environment |

### Configuration du webhook Stripe

Sur https://dashboard.stripe.com/webhooks → "Add endpoint" :

- **URL** : `https://ton-domaine.example.com/api/stripe/webhook`
- **Events à écouter** (cocher au minimum) :
  - `account.updated` (KYC partenaire terminé)
  - `capability.updated` (capacités transfers actives)
  - `payout.paid` (payout envoyé)
  - `payout.failed` (payout en erreur)

Une fois créé, Stripe te donne un **signing secret** `whsec_...` → ajouter à `STRIPE_WEBHOOK_SECRET` sur Render.

## 🧪 Test de validation

```bash
# Démarre le serveur avec tes clés :
export STRIPE_SECRET_KEY=sk_live_xxxx
export STRIPE_PUBLISHABLE_KEY=pk_live_xxxx
export STRIPE_WEBHOOK_SECRET=whsec_xxxx
export AFFILMAX_REQUIRE_LIVE=1
export ADMIN_USER=ton_admin
export ADMIN_PASSWORD=motdepasse_long_et_aleatoire
python server.py
```

Dans un autre terminal :

```bash
# Le serveur doit refuser de démarrer si pas de sk_live_ :
curl http://localhost:8765/api/stripe/health
```

**Attendu :**
```json
{
  "mode": "live",
  "enabled": true,
  "available": [{"currency": "EUR", "amount_eur": 0.0}],
  "livemode": true,
  "default_country": "FR",
  "default_currency": "EUR"
}
```

## ▶ Reprise après interruption

Quand tu reviens et que tu as tes clés sous la main :

1. Ouvre `GO_LIVE_RUNBOOK.md` étape 1.
2. Colle tes clés sur Render.
3. Redémarre le serveur (`python server.py`).
4. Lance `curl http://localhost:8765/api/stripe/health` → vérifie `"mode": "live"`.
5. Si OK → passe au **mémo 02** (`MEMO_02_real-tracking.md`).

## 🆘 Si tu es bloqué

- **"Mode demo" alors que tu as mis sk_live_** → as-tu bien redémarré le serveur ? Render hot-reload ne marche pas pour les variables d'env.
- **Webhook signature invalid** → as-tu mis `STRIPE_WEBHOOK_SECRET` exactement comme affiché sur Stripe ?
- **AFFILMAX_REQUIRE_LIVE refuse de démarrer** → c'est normal, c'est le garde-fou. Soit tu mets la clé, soit tu retires `AFFILMAX_REQUIRE_LIVE=1` (déconseillé en prod).
