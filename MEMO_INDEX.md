# 📑 MEMO INDEX — Mode réel Affilimax

> Tu peux **reprendre à n'importe quelle étape** en ouvrant simplement ce fichier. Chaque mémo documente :
> - ✅ ce que j'ai fait dans cette étape
> - ⏸ ce qu'il manque (variables d'environnement à fournir, clics à valider)
> - ▶ la commande exacte pour reprendre

## 📂 Sommaire des mémos

| # | Mémo | Quand l'ouvrir |
|---|---|---|
| **00** | [GO_LIVE_RUNBOOK.md](./GO_LIVE_RUNBOOK.md) | Runbook global (toutes les variables d'env, ordre des étapes) |
| **01** | [MEMO_01_stripe-live.md](./MEMO_01_stripe-live.md) | Pour brancher Stripe en mode LIVE (clés + webhooks) |
| **02** | [MEMO_02_real-tracking.md](./MEMO_02_real-tracking.md) | Pour que les clics/conversions Amazon soient réels |
| **03** | [MEMO_03_onboarding-partners.md](./MEMO_03_onboarding-partners.md) | Pour onboarder les vrais affiliés via Stripe Connect |
| **04** | [MEMO_04_payouts.md](./MEMO_04_payouts.md) | Pour payer les affiliés en EUR réel |
| **05** | [MEMO_05_notifications-social.md](./MEMO_05_notifications-social.md) | Pour Telegram/Slack et auto-post Twitter/LinkedIn |
| **99** | [MEMO_FINAL_checklist.md](./MEMO_FINAL_checklist.md) | Checklist finale avant de crier "EN LIGNE" |

## 🛠 Outils de diagnostic

- `python mode_reel_guard.py` → diagnostic complet en 10 secondes (où tu en es)
- `curl http://localhost:8765/api/go-live/status` → checklist depuis le serveur

## 🧭 État actuel (au moment où je m'arrête)

| Bloc | État | Code | Action restante pour toi |
|---|---|---|---|
| Stripe Live | 🟡 Code prêt, clés manquantes | `stripe_config.py` en mode DEMO | Récupérer sk_live_ + webhook secret |
| Tracking réel | 🟢 Endpoints prêts | `/api/click` et `/api/conversion` opérationnels | Aucun — il suffit que les visiteurs arrivent |
| Webhook Stripe | 🟢 Endpoint + handlers prêts | `/api/stripe/webhook` avec vérif signature | Configurer l'URL dans le dashboard Stripe |
| Onboarding partenaires | 🟢 Script + endpoint prêts | `onboard_partners_live.py`, `/api/stripe/onboard` | Remplir partners.json avec de vrais humains |
| Payouts réels | 🟢 Code prêt | `/api/stripe/payout` envoie via `stripe.Transfer.create` | Stripe doit être en LIVE (cf. mémo 01) |
| Notifications Telegram | 🟡 Code prêt | `notifications.py` désactivé | Mettre bot_token + chat_id |
| Notifications Slack | 🟡 Code prêt | `notifications.py` désactivé | Mettre webhook URL |
| Auto-post social | 🟡 Code prêt | `twitter_poster.py` désactivé | Mettre API keys Twitter/X |
| Auto-post LinkedIn | 🟡 Code prêt | `social_reseaux.py` désactivé | Mettre token LinkedIn |

🟢 = OK côté code ⏸ = en attente d'une action humaine

## 🔄 Reprise après interruption

Si tu fermes l'IDE et tu reviens demain :

```bash
# Étape 1 — diagnostic rapide
python mode_reel_guard.py

# Étape 2 — ouvre MEMO_INDEX.md (ce fichier) et choisis le bloc qui n'est pas vert
```

Si tu as perdu le fil : dis-moi "reprend" et je te relis l'état via ce mémo.
