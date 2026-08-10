# 🔑 ACTIVER LES PAIEMENTS RÉELS — ÉTAPES EXACTES (2 min)

> Fait par Buffy le 10/08/2026. C'est LA seule action manuelle qui débloque
> les premiers vrais euros. Le webhook a été testé : une vente réelle
> crédite automatiquement la commission.

---

## 🎯 Pourquoi c'est indispensable

Aujourd'hui le webhook est **fail-closed** : sans clé configurée, **même une
vraie vente Amazon est refusée** (sécurité anti-fraude). Une fois la clé posée,
chaque vente réelle est créditée automatiquement.

## 📋 ÉTAPE 1 — Copier cette clé

```
AMAZON_WEBHOOK_SECRET=A1S1wUj5QQxdtpAid4wqqkrodEK-eHOvITSttyVVn1k
```

## 📋 ÉTAPE 2 — La coller dans Render (2 minutes)

1. Va sur **https://dashboard.render.com**
2. Clique sur ton service (afflimax)
3. Menu de gauche → **Environment**
4. Clique **Add Environment Variable**
   - Key : `AMAZON_WEBHOOK_SECRET`
   - Value : `A1S1wUj5QQxdtpAid4wqqkrodEK-eHOvITSttyVVn1k`
5. **Save Changes** → Render redémarre tout seul (~1 min)

## 📋 ÉTAPE 3 — Configurer Amazon Partenaires (1 fois)

1. Connecte-toi sur **partenaires.amazon.fr** (ton compte affiliation)
2. Menu : **Rapports** → **Notifications instantanées** (ou Webhooks)
3. URL du webhook : `https://afflimax.onrender.com/amazon/notification`
4. Header/secret : `X-Amzn-Webhook-Secret` = `A1S1wUj5QQxdtpAid4wqqkrodEK-eHOvITSttyVVn1k`
5. Active les notifications de **ventes**

> Si Amazon n'offre pas de webhook dans ton interface, tu peux aussi :
> - brancher ton flux de rapports via Zapier/Make vers la même URL, OU
> - m'envoyer le format de notification Amazon (JSON) et j'adapte le mapping.

## ✅ Vérification après configuration

Dis-moi « vérifie » et je teste en ligne que le webhook accepte une vente.

## 🧪 Preuve que ça marche (test local du 10/08)

| Test | Résultat |
|---|---|
| Vente réelle avec le bon secret | ✅ 16 € crédités |
| Requête avec mauvais secret | ✅ Rejetée (anti-fraude) |
| Même vente envoyée 2 fois | ✅ 1 seule fois comptée (anti-doublon) |

*Les données de test ont été supprimées après validation — les stats en ligne restent à 0 € (que du réel).*
