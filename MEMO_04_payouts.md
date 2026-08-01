# 💸 MÉMO 04 — Payouts réels vers les partenaires

> **Étape où je me suis arrêté(e) :** code prêt, à utiliser après le mémo 01 + 03.

## ✅ Déjà fait (par moi)

1. **Endpoint admin** `POST /api/stripe/payout` qui envoie un vrai `stripe.Transfer` vers un compte Connect.
2. **Vérifications automatiques** :
   - Solde suffisant côté partenaire
   - Montant minimum (25€ par défaut)
   - Capacité `transfers` active chez Stripe (sinon le transfer est refusé)
   - Idempotency key générée pour éviter les doublons sur retry réseau
3. **Webhook hooks** : `payout.paid` et `payout.failed` mettent à jour le statut.
4. **Facture PDF** générée automatiquement via `invoice_generator.py` (pense à le configurer via la variable d'env correspondante).
5. **Notifications** Telegram/Slack/Email envoyées automatiquement.

## ⏸ Ce qu'il te reste à faire

### Étape 4.1 — Accumuler des commissions

```bash
# Ajouter une commission à un partenaire (à l'API ou via admin.html)
curl -u admin:password -X PUT http://localhost:8765/api/partners/affilie_real_001 \
  -H "Content-Type: application/json" \
  -d '{"solde_en_attente": 47.50}'
```

En vrai, c'est ton **système de tracking des conversions** (mémo 02) qui appelle `add_commission_to_partner()` automatiquement quand Amazon envoie une conversion.

### Étape 4.2 — Vérifier que le solde est suffisant

```bash
curl -u admin:password http://localhost:8765/api/partners/affilie_real_001 | python -c \
  "import json,sys; d=json.load(sys.stdin); print('Solde en attente:', d.get('solde_en_attente', 0), '€')"
```

### Étape 4.3 — Déclencher un payout

```bash
curl -u admin:password -X POST http://localhost:8765/api/stripe/payout \
  -H "Content-Type: application/json" \
  -d '{"partner_id":"affilie_real_001","amount":47.50}'
```

Attendu (succès) :
```json
{
  "success": true,
  "transfer_id": "tr_xxxx",
  "amount": 47.50,
  "currency": "eur",
  "status": "in_transit",
  "idempotency_key": "affilmax-payout-affilie_real_001-47.5-29847362",
  "facture": "/path/to/facture.pdf"
}
```

Le transfer apparaîtra dans le dashboard Stripe sous "Connect → Transfers".

### Étape 4.4 — Vérifier l'arrivée à destination

Stripe notifie :
- `transfer.created` → transfer créé
- `transfer.paid` → fonds arrivés (généralement 2-7 jours selon le pays)
- `transfer.failed` → rejeté (compte partenaire pas encore actif, etc.)

Le webhook `/api/stripe/webhook` log tout ça.

## ⚠️ Sécurité de l'étape 4

Cette étape **envoie de l'argent réel**. Garde-fous en place :

1. **Auth admin obligatoire** : `POST /api/stripe/payout` exige HTTP Basic avec `ADMIN_USER`/`ADMIN_PASSWORD` (ou refuse en mode `AFFILMAX_REQUIRE_LIVE=1`).
2. **Idempotency** : pas de double payout sur retry réseau (clé `partner_id + amount + minute`).
3. **Vérif transfers** : avant chaque transfer, on lit `stripe.Account.retrieve()` pour confirmer que `capabilities.transfers == "active"`.
4. **Seuil minimum** : 25€ par défaut (configurable dans `stripe_config.MIN_PAYOUT_THRESHOLD`).
5. **Facture** : traçabilité PDF automatique.

## 📊 Suivi mensuel

Pour accumuler correctement, tu peux utiliser le workflow n8n `affilmax-monthly-invoice` (cf. `n8n_config.json`) qui :
- Agrège les commissions du mois par partenaire le 1er à 8h UTC
- Génère la facture PDF
- Envoie par email

Pour le déclencher en CLI manuellement : voir `n8n_config.json` workflow ID `affilmax-monthly-invoice`.

## ▶ Reprise

Si tu reviens après une interruption :

```bash
# 1. Vérifier que ton admin auth marche
curl -u admin:password http://localhost:8765/api/stripe/health

# 2. Vérifier la liste des partenaires onboardés
curl -u admin:password http://localhost:8765/api/partners

# 3. Voir l'historique payouts globaux
curl -u admin:password http://localhost:8765/api/payments/stats
```

Si tu as déjà fait des payouts dans le passé → passe au **mémo 05** (`MEMO_05_notifications-social.md`) et au mémo **final**.
