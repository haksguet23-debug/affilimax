# ✅ MÉMO FINAL — Checklist de mise en ligne

> **Le moment de vérité : tu es en ligne ?**

## 🚦 Diagnostic en une commande

```bash
python mode_reel_guard.py
```

Sortie attendue si **tout est vert** :

```
====================================================
  Affilimax — Diagnostic mode réel
====================================================
  ✅ Stripe              : LIVE (sk_live_xxxxx, balance: 0.00 EUR)
  ✅ Webhook Stripe      : signé HMAC (whsec_xxxxx)
  ✅ ADMIN_USER          : défini
  ✅ ADMIN_PASSWORD      : défini (longueur: 16)
  ✅ AUTH affiliate      : require_live ON
  ✅ partners.json       : 5 partenaires, 0 @example.com
  ✅ Telegram            : activé
  ✅ Slack               : activé
  ✅ Resend (email)      : RESEND_API_KEY défini
  ✅ Twitter             : 4 clés API définies
  ✅ LinkedIn            : token défini
  ✅ Stats               : réelles (clics_aujourdhui=0, en attente de trafic)

RÉSULTAT : 🟢 PRÊT POUR LA PRODUCTION
====================================================
```

## ✅ Checklist manuelle (si tu n'as pas `mode_reel_guard.py`)

| # | Vérification | OK ? | Comment tester |
|---|---|---|---|
| 1 | Stripe en mode live | ☐ | `curl /api/stripe/health` → `"mode":"live"` |
| 2 | Webhook Stripe signé | ☐ | `STRIPE_WEBHOOK_SECRET` non vide |
| 3 | ADMIN_USER défini | ☐ | `echo $ADMIN_USER` |
| 4 | ADMIN_PASSWORD défini (+12 caractères) | ☐ | `echo $ADMIN_PASSWORD \| wc -c > 12` |
| 5 | AFFILMAX_REQUIRE_LIVE=1 | ☐ | `echo $AFFILMAX_REQUIRE_LIVE` |
| 6 | 0 partenaire @example.com dans partners.json | ☐ | `grep -c example partners.json` retourne 0 |
| 7 | Telegram marche | ☐ | `POST /api/notifications/test platform=telegram` → message reçu |
| 8 | Slack marche | ☐ | idem slack |
| 9 | Resend marche | ☐ | `POST /api/email/send to=mon@email.com product="Kindle"` |
| 10 | Twitter marche | ☐ | `POST /api/twitter/post count=1` |
| 11 | UptimeRobot ping OK | ☐ | test du `/healthz?keyword=Affilimax` |
| 12 | Un vrai clic a été enregistré | ☐ | `curl /api/stats` → `clics_aujourdhui >= 1` |
| 13 | Une vraie conversion | ☐ | idem |
| 14 | un vrai transfert Stripe envoyé | ☐ | dashboard Stripe → Connect → Transfers |
| 15 | Une vraie notification Telegram reçue | ☐ | message reçu simultanément |

Si **tous** sont OK → tu es officiellement en ligne 🎉

## 🔍 Tests automatisés

```bash
# 1. Health check global
curl http://localhost:8765/api/go-live/status | python -m json.tool

# 2. Sécurité (auth admin)
curl -i http://localhost:8765/admin.html
# Attendu : 401 Unauthorized
curl -i -u admin:password http://localhost:8765/admin.html
# Attendu : 200 OK

# 3. Partners (volontairement vide)
curl -u admin:password http://localhost:8765/api/partners | python -c \
  "import json,sys; d=json.load(sys.stdin); print(len(d['partenaires']), 'partenaires')"

# 4. Stats en temps réel
watch -n 2 'curl -s http://localhost:8765/api/stats | python -c \
  "import json,sys; d=json.load(sys.stdin); print(d[\"resume\"])"'
```

## 📊 Indicateurs de succès (à 7 jours)

| Métrique | Objectif réaliste |
|---|---|
| Clics/jour | ≥ 100 |
| Taux de conversion | 1-3% |
| Commissions/jour | ≥ 10€ |
| Partenaires onboardés | ≥ 3 |
| Payouts effectués | ≥ 1 |
| Uptime Render | ≥ 99% |

## 🆘 Si tu as un incident

### Étape d'urgence : passer en mode "réduit"

Sur Render, modifier temporairement :
- `AFFILMAX_REQUIRE_LIVE=0` → autorise DEMO

Cela ne désactive pas Stripe, juste relâche le fail-closed (utile pour debug).

### Rollback

Si quelque chose casse en prod, Render permet de rollback en 1 clic :
- Dashboard → Manual Deploy → sélectionne le commit précédent

## 📞 Contacts utiles

- Stripe support : https://support.stripe.com (réponse en quelques heures)
- Render status : https://status.render.com
- Telegram bot API : https://core.telegram.org/bots/api

## 🎯 Suite (à plus long terme)

Une fois en ligne stable, tu peux :

1. **Brancher d'autres plateformes** : ClickBank, ShareASale, CJ Affiliate, Awin, Impact (cf. `affilmax_config.json`)
2. **Activer les workflows n8n** : 8 workflows prêts (cf. `n8n_config.json`)
3. **Activer la génération IA** : Groq + Gemini via `ai_automator.py`
4. **Brancher UptimeRobot** : `python uptimerobot_setup.py` (déjà écrit)
5. **Backups DB** : Render backup quotidien 02:00 UTC (déjà configuré)
6. **Scaling** : Render auto-scale sur instance >0.5 CPU pending

## 🏁 Récap de tout ce que j'ai fait

Voici la liste exhaustive des modifications :

| Fichier | Action |
|---|---|
| `MEMO_INDEX.md` | ✨ Créé |
| `GO_LIVE_RUNBOOK.md` | ✨ Créé |
| `MEMO_01_stripe-live.md` | ✨ Créé |
| `MEMO_02_real-tracking.md` | ✨ Créé |
| `MEMO_03_onboarding-partners.md` | ✨ Créé |
| `MEMO_04_payouts.md` | ✨ Créé |
| `MEMO_05_notifications-social.md` | ✨ Créé |
| `MEMO_FINAL_checklist.md` | ✨ Créé (ce fichier) |
| `mode_reel_guard.py` | ✨ Créé |
| `stripe_config.py` | 🔧 Ajout du warning LIVE+demo-data |
| `server.py` | 🔧 Ajout endpoint `/api/go-live/status` |

Le projet était déjà très bien architecturé côté code. Il ne manquait principalement que **tes credentials** et **les mémos** pour reprendre.

Bon courage pour la mise en ligne ! 🚀
