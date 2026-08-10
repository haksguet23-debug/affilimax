# 📥 IMPORT DES VENTES AMAZON — GUIDE PAS-À-PAS

> **Vérité importante :** Amazon Partenaires n'envoie PAS de notification de
> vente en temps réel (aucun webhook natif — c'est une limite d'Amazon, pas de
> notre site). Amazon met à jour ses **rapports de revenus** 1-2 fois par jour.
> On télécharge le rapport, on le lance dans notre script, et les ventes sont
> créditées automatiquement (stats + solde du bon partenaire).
>
> Testé le 10/08/2026 : import 2 ventes = 25,60 € crédités, re-import = ignoré
> (anti-doublon), attribution partenaire OK.

---

## 📋 ÉTAPE 1 — Télécharger le rapport chez Amazon (1 min)

1. Va sur **https://partenaires.amazon.fr** (connecte-toi)
2. Menu du haut : **Rapports** → **Rapports de revenus**
   (ou "Rapports de performance" selon ton interface)
3. Sélectionne la période (ex: aujourd'hui / hier)
4. Clique **Télécharger** → fichier `.csv` (ex: `revenus.csv`)
   → enregistre-le dans le dossier `affilimax/`

> Le rapport contient une ligne par article vendu : Order ID, Tracking ID,
> Item Name, ASIN, Quantity, Item Price, Referral Fee (commission)...

## 📋 ÉTAPE 2 — Vérifier avant d'importer (2 sec, sécurité)

```bash
cd affilimax
python import_amazon_report.py revenus.csv --dry-run
```

→ Affiche les ventes détectées **sans rien créditer** (colonnes auto-détectées,
ligne "Total" exclue, montant total du rapport).

## 📋 ÉTAPE 3 — Importer les ventes (crédit réel)

```bash
cd affilimax
python import_amazon_report.py revenus.csv --secret TA_CLE_SECRETE
```

> `--secret` = la valeur d'`AMAZON_WEBHOOK_SECRET` (celle posée sur Render).
> Par défaut le script envoie vers le webhook en ligne de Render.

Résultat attendu :
```
Creditees: 2 | Deja vues/ignorees: 0 | Erreurs: 0
```

## ✅ Vérifier dans le dashboard

Ouvre **https://afflimax.onrender.com/dashboard** → les commissions et
conversions apparaissent. Le solde du partenaire (si `Tracking ID` = id
partenaire, ex: `roxanne_famille`) est crédité automatiquement.

---

## 🔍 Comment ça marche (résumé)

```
rapport CSV Amazon ──> import_amazon_report.py ──> POST /amazon/notification
                                                      │  header X-Amzn-Webhook-Secret
                                                      ▼
                                              stats.json + partners.json
                                              (anti-doublon par order_id)
```

| Élément | Détail |
|---|---|
| Colonnes reconnues | Order ID, Tracking ID, Item Name, ASIN, Quantity, Item Price, Referral Fee (noms variants gérés) |
| Ligne "Total" | Exclue automatiquement (pas une vente) |
| Anti-doublon | Un même Order ID n'est crédité qu'une fois (même si le rapport est retéléchargé) |
| Attribution partenaire | Le `Tracking ID` du lien (`?ref=...`) crédite le bon partenaire |
| Sécurité | Requiert le secret webhook (`X-Amzn-Webhook-Secret`) — sans lui, refus |

## ⚠️ Fréquence conseillée

- **1 fois par jour** suffit (Amazon met à jour ses rapports 1-2 fois/jour).
- On peut automatiser plus tard avec une tâche planifiée (Windows Task Scheduler
  ou Render cron) qui télécharge + importe le rapport — dis-moi si tu veux.

*Guide généré par Buffy/Freebuff · 10/08/2026 · Script testé avec rapport d'exemple.*
