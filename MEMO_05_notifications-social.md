# 📣 MÉMO 05 — Notifications Telegram/Slack + Auto-post social

> **Étape où je me suis arrêté(e) :** code prêt, en attente de tes tokens.

## ✅ Déjà fait (par moi)

### Notifications

1. **Telegram** : `notifications.py` sait envoyer des messages sur les 3 événements :
   - `notify_payout(...)` — quand un transfert est payé
   - `notify_commission(...)` — quand une commission est ajoutée (optionnel)
   - `notify_threshold(...)` — quand un solde partenaire dépasse un seuil
2. **Slack** : même chose via Incoming Webhook.
3. **Email** : `email_sender.py` utilise **Resend** (transactionnel) — nécessite `RESEND_API_KEY`.
4. **Endpoints admin** :
   - `GET /api/notifications/config` (lit sans exposer les tokens)
   - `POST /api/notifications/save` (met à jour `notifications_config.json`)
   - `POST /api/notifications/test?platform=telegram|slack|all` (envoie un message de test)

### Auto-post social

1. **Twitter/X** : `twitter_poster.py`
   - `post_next_tweets(count=N)` — poste N tweets
   - `get_status()` — état du rate limit
   - Endpoint `POST /api/twitter/post`
2. **LinkedIn** : via `social_reseaux.py` (génération de texte)
3. **Facebook** : idem (génération de texte)
4. **Email marketing** : `email_sender.py` (Resend)
5. **Blog** : `social_reseaux.py` génère l'article Markdown
6. **Workflow global** : `promo_automator.py` orchestre tout avec cron
7. **Génération IA** : `ai_automator.py` (Groq par défaut, Gemini en fallback)

## ⏸ Ce qu'il te reste à faire

### Étape 5.1 — Telegram

1. Crée un bot via @BotFather sur Telegram → récupère le token (`123456:ABC-DEF...`).
2. Ajoute le bot à ton channel/groupe privé.
3. Récupère le chat_id via @userinfobot ou l'API `getUpdates`.
4. Sauvegarde via l'API :
   ```bash
   curl -X POST http://localhost:8765/api/notifications/save \
     -H "Content-Type: application/json" \
     -d '{
       "config": {
         "telegram": {
           "enabled": true,
           "bot_token": "123456:ABC-DEF...",
           "chat_id": "-10012345678",
           "notify_payout": true,
           "notify_commission": true,
           "notify_threshold": true
         }
       }
     }'
   ```
5. Test :
   ```bash
   curl -X POST http://localhost:8765/api/notifications/test \
     -H "Content-Type: application/json" \
     -d '{"platform":"telegram"}'
   ```
   Tu reçois un message "🎉 Test notification Affilimax" sur Telegram.

### Étape 5.2 — Slack

1. Crée une Incoming Webhook sur https://api.slack.com/messaging/webhooks
2. Sauvegarde :
   ```bash
   curl -X POST http://localhost:8765/api/notifications/save \
     -H "Content-Type: application/json" \
     -d '{
       "config": {
         "slack": {
           "enabled": true,
           "webhook_url": "https://hooks.slack.com/services/T.../B.../...",
           "notify_payout": true,
           "notify_commission": true,
           "notify_threshold": true
         }
       }
     }'
   ```
3. Test idem (`{"platform":"slack"}`).

### Étape 5.3 — Email (Resend)

Sur Render (variable d'env) :
```
RESEND_API_KEY=re_xxxxxxxx
RESEND_FROM=no-reply@tondomaine.com
```

Le module `email_sender.py` est déjà câblé sur `/api/email/send` et `/api/email/send-all`.

### Étape 5.4 — Twitter/X

Crée une **app** sur https://developer.twitter.com/en/portal/apps/new
Récupère les clés API et colle-les dans des variables d'environnement sur Render (suit le schéma attendu par `twitter_poster.py` — voir son code pour les noms exacts).

### Étape 5.5 — LinkedIn

1. Crée une app sur https://www.linkedin.com/developers/
2. Demande l'accès à `w_member_social` (nécessite approbation)
3. Génère un access token avec les scopes nécessaires
4. Colle le token dans `LINKEDIN_ACCESS_TOKEN` (ENV)

### Étape 5.6 — Activer le cron promo

Une fois tous les credentials en place :

```bash
curl -X POST http://localhost:8765/api/promo/start
```

Pour voir l'état :
```bash
curl http://localhost:8765/api/promo/stats
```

## 🧪 Test global

Une fois tout configuré :

```bash
# Simuler un payout (avec ta propre ID partenaire)
curl -u admin:password -X POST http://localhost:8765/api/stripe/payout \
  -H "Content-Type: application/json" \
  -d '{"partner_id":"TON_ID","amount":50}'

# Tu dois recevoir une notification Telegram ET Slack ET un email
# (selon ce que tu as activé)
```

## ⚠️ Erreurs courantes

| Symptôme | Cause |
|---|---|
| Telegram : "chat not found" | Bot pas ajouté au groupe, ou chat_id incorrect |
| Telegram : "Unauthorized" | bot_token incorrect ou révoqué |
| Slack : "no_service" | webhook URL mal collé (tronquée par accident) |
| Twitter : "401 Unauthorized" | clés API pas chargées (vérifier `get_status()`) |

## ▶ Reprise

```bash
python mode_reel_guard.py
```

Section "Notifications" et "Social" doivent être verts. Si oui → **MEMO FINAL** (`MEMO_FINAL_checklist.md`).
