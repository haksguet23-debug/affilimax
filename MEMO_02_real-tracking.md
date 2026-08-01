# 📊 MÉMO 02 — Tracking Amazon réel (clics + conversions)

> **Étape où je me suis arrêté(e) :** code prêt, à tester avec Amazon.

## ✅ Déjà fait (par moi)

Le serveur écoute **réellement** les clics depuis `/go/<slug>` :

```python
# server.py - extract de /go/<slug>
record_click(
    product_name=target["nom"],
    platform=target["plateforme"],
    source=source  # déduit de utm_source / ?src=
)
```

Et possède deux webhooks pour les conversions :

```
POST /api/click      → enregistre un clic (déjà câblé via /go/<slug>)
POST /api/conversion → enregistre une vente (à câbler chez Amazon)
```

Format de payload accepté (flexible FR/EN) :

```json
POST /api/click
{ "product": "Amazon Kindle 11", "platform": "Amazon", "source": "twitter" }

POST /api/conversion
{ "product": "Amazon Kindle 11", "platform": "Amazon", "commission": 5.50, "price": 89.99 }
```

## ⏸ Ce qu'il te reste à faire

### Étape 2.1 — Tester le tracking en local

```bash
# 1. Démarre le serveur
python server.py

# 2. Clique sur un lien /go/1 dans ton navigateur
# OU en CLI :
curl -L http://localhost:8765/go/1 -o /dev/null

# 3. Vérifie que le compteur a bougé
curl http://localhost:8765/api/stats | grep -E 'clics|commissions'
```

### Étape 2.2 — Brancher Amazon Instant Notification Script

1. Va sur https://affiliate-program.amazon.com → **Outils → Product Advertising API / Instant Notification**
2. Active **"SNS Topic"** dans une région AWS (eu-west-1 = Irlande pour la France).
3. Crée un **SNS subscription HTTPS** pointant vers :
   ```
   https://ton-domaine.example.com/api/conversion
   ```
4. Configure le SNS pour envoyer en `POST` avec un body JSON conforme.

### Étape 2.3 (optionnel) — Brancher ClickBank, ShareASale, Awin, etc.

Pour chaque plateforme d'affiliation, il faut renseigner son **"postback URL" / "S2S pixel"** dans ton dashboard :

```
https://ton-domaine.example.com/api/conversion?product=AUTOMATIC
```

La plateforme enverra un GET/POST avec `commission=X&orderId=Y` etc. Tu peux adapter le mapping dans `server.py` → `do_POST` → `/api/conversion` (voir handler actuel).

## 🧪 Test de bout en bout

```bash
# 1. Simuler un clic
curl -X POST http://localhost:8765/api/click \
  -H "Content-Type: application/json" \
  -d '{"product":"Amazon Kindle","platform":"Amazon","source":"twitter"}'

# Attendu : {"status":"ok","action":"click","produit":"Amazon Kindle","data":{...}}

# 2. Simuler une conversion
curl -X POST http://localhost:8765/api/conversion \
  -H "Content-Type: application/json" \
  -d '{"product":"Amazon Kindle","platform":"Amazon","price":89.99,"commission":3.50}'

# Attendu : {"status":"ok","action":"conversion","produit":"Amazon Kindle","data":{...}}

# 3. Vérifier dans stats
curl http://localhost:8765/api/stats
```

## 📂 Fichiers liés

- `server.py` — handlers `/api/click`, `/api/conversion`, `/go/<slug>`
- `stats.json` — persiste les compteurs (auto-sauvegardé)
- `record_click()` / `record_conversion()` — fonctions de calcul (server.py)
- `docs/AMAZON_SETUP.md` — si tu trouves une doc Amazon existante

## ▶ Reprise

Une fois les vrais clics arrivent :

```bash
curl http://localhost:8765/api/stats | python -m json.tool | grep -E 'clics_aujourdhui|commissions_aujourdhui'
```

Si ce n'est pas 0 après avoir eu du trafic → passe au **mémo 03** (`MEMO_03_onboarding-partners.md`).
