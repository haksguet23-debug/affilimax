# 🤝 MÉMO 03 — Onboarding Stripe Connect des vrais partenaires

> **Étape où je me suis arrêté(e) :** script prêt, à lancer avec ta liste.

## ✅ Déjà fait (par moi)

1. **Endpoint admin** `POST /api/stripe/onboard` qui crée un compte Connect Express par partenaire (protégé par auth admin).
2. **Endpoint admin** `POST /api/stripe/regonboard/<id>` qui régénère un lien d'onboarding pour un partenaire qui a abandonné.
3. **Endpoint admin** `GET /api/stripe/partner-status/<id>` qui lit l'état live chez Stripe (`transfers_active`, `requirements_currently_due`, etc.).
4. **Webhook** `/api/stripe/webhook` qui reçoit `account.updated` de Stripe et bascule automatiquement `onboarded=true` dans `partners.json`.
5. **Script CLI** `onboard_partners_live.py` pour onboarder en lot, avec `--dry-run` par défaut et confirmation manuelle en mode `sk_live_`.

## ⏸ Ce qu'il te reste à faire

### Étape 3.1 — Remplacer partners.json par de vrais affiliés

**AVANT cette étape :** sauvegarde ton fichier actuel.

```bash
cp partners.json partners_demo_backup.json
```

Ouvre `partners.json` et remplace **chaque** partenaire `@example.com` par un vrai humain. Schéma minimum :

```json
{
  "id": "affilie_real_001",
  "nom": "Vrai Nom Affilieur",
  "email": "vrai.email@domaine-reel.com",
  "commission_rate": 15.0,
  "statut": "actif"
}
```

**Pourquoi c'est important :** le script `onboard_partners_live.py` **refuse par défaut** les emails `@example.com` en mode LIVE (sécurité anti-bruit).

### Étape 3.2 — Dry-run

```bash
export STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_BASE_URL=https://ton-domaine.example.com \
  python onboard_partners_live.py
```

Le script affiche la liste sans rien créer. Tu peux filtrer :
- `--partner-id UN_ID` → un seul
- `--include-demo` → inclut les @example.com (déconseillé en prod)

### Étape 3.3 — Onboarding réel

```bash
STRIPE_BASE_URL=https://ton-domaine.example.com \
  python onboard_partners_live.py --apply
```

Le script :
1. Crée un backup automatique (`partners.json.bak`).
2. Demande une confirmation **"OUI"** en majuscules (sécurité en mode live).
3. Crée un `Account` Stripe Connect Express par partenaire.
4. Met à jour `partners.json` avec `stripe_account_id`.
5. Affiche les **liens d'onboarding** KYC à envoyer par email à chaque partenaire.

### Étape 3.4 — Accompagner les partenaires (TOC)

Chaque partenaire doit compléter son KYC en cliquant sur son lien. Une fois fait, Stripe envoie un webhook `account.updated` que nous captons → `partners.json` se met à jour tout seul.

Si un partenaire abandonne :
```bash
python onboard_partners_live.py --partner-id UN_ID
```
Tu obtiens un nouveau lien à lui renvoyer.

## 🧪 Vérification après onboarding

```bash
# Lister les partenaires et leurs statuts
curl -u admin:password http://localhost:8765/api/partners

# Vérifier l'état Stripe d'UN partenaire
curl -u admin:password http://localhost:8765/api/stripe/partner-status/affilie_real_001
```

Attendu dans `requirements_currently_due`: `[]` quand le KYC est complet.

## ⚠️ Erreurs courantes

| Symptôme | Cause probable |
|---|---|
| `email invalide` chez Stripe | Format `@example.com` ou adresse jetable — utilisé `--include-demo` par erreur |
| `country mismatch` | Tu utilises un pays différent de `STRIPE_DEFAULT_COUNTRY` (FR par défaut) |
| `transfers not active` 5 min après onboarding | Le partenaire n'a pas encore cliqué sur le lien KYC, ou Stripe demande des infos supplémentaires (`requirements_currently_due` non vide) |
| Le webhook ne met pas `onboarded=true` | Le `STRIPE_WEBHOOK_SECRET` n'est pas le bon, ou l'URL configurée chez Stripe ne pointe pas vers `/api/stripe/webhook` |

## ▶ Reprise

Une fois tous tes partenaires avec `onboarded=true` :

```bash
python mode_reel_guard.py
```

Si "Stripe" et "Onboarding" sont verts → passe au **mémo 04** (`MEMO_04_payouts.md`).
