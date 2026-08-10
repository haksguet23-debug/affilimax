# 🎬 GUIDE YOUTUBE — VIDÉOS ENFANTS (upload automatique)

> **Objectif** : publier nos histoires pour enfants générées par `video_factory.py`
> sur une chaîne YouTube, en automatique.
> **Temps** : ~15 min pour tout configurer (une seule fois).

---

## 📊 OÙ ON EN EST (10/08/2026)

| Élément | État |
|---|---|
| Générateur d'histoires enfants (script IA + storyboard + voix + sous-titres) | ✅ Fonctionne |
| **3 histoires générées** (renard, dragon, étoile — 3 Mo chacune) | ✅ Prêtes |
| Métadonnées SEO YouTube (titre, description, tags) | ✅ Générées |
| Script d'upload (`youtube_uploader.py`) | ✅ Prêt |
| **Clé API YouTube** | ❌ **À créer** (étapes ci-dessous) |

---

## ÉTAPE 1 — Créer la chaîne YouTube (2 min)

1. Connecte-toi sur https://www.youtube.com avec un compte Google **dédié à Affilimax**
   (important : crée un compte Google séparé si tu n'en as pas — le canal sera à toi 100 %)
2. Clique sur ton avatar (en haut à droite) → **Créer une chaîne**
3. Nom : **« Histoires pour Enfants »** ou « Contes du soir » — description :
   > Histoires et contes du soir pour enfants. Nouvelles vidéos chaque semaine. 📚🌙
4. Ajoute une photo de profil + une bannière (tu peux utiliser nos visuels `assets/tiktok/*.jpg`)

---

## ÉTAPE 2 — Créer le projet Google Cloud (2 min)

1. Va sur https://console.cloud.google.com/ → **Créer un projet**
2. Nom du projet : `affilimax-youtube`
3. Sélectionne le projet (important, sinon tu configures le mauvais)

---

## ÉTAPE 3 — Activer l'API YouTube Data v3 (1 min)

1. Menu ☰ → **API et services** → **Bibliothèque**
2. Recherche **YouTube Data API v3** → clique → **Activer**

---

## ÉTAPE 4 — Écran de consentement OAuth (3 min)

1. Menu ☰ → **API et services** → **Écran de consentement OAuth**
2. Type d'utilisateur : **Externe** → Créer
3. Remplis : nom de l'app (`Affilimax Upload`), email de support (ton email)
4. **Scopes** : clique « Ajouter ou supprimer des scopes » → ajoute :
   `https://www.googleapis.com/auth/youtube.upload`
5. **Utilisateurs de test** : ajoute **TON adresse Gmail** (obligatoire en mode Test)
6. Publier : quand tout marche, tu pourras passer l'app en « En production »

---

## ÉTAPE 5 — Créer le fichier client_secrets.json (2 min)

1. Menu ☰ → **API et services** → **Identifiants** → **Créer des identifiants** → **ID client OAuth**
2. Type d'application : **Application de bureau**
3. Créer → **Télécharger le JSON**
4. Renomme le fichier en `client_secrets.json` et place-le **dans `affilimax/`**
   (à côté de `youtube_uploader.py`)

---

## ÉTAPE 6 — Installer la bibliothèque (1 min)

```bash
pip install --upgrade google-api-python-client google-auth-oauthlib google-auth-httplib2
```

---

## ÉTAPE 7 — Uploader les 3 histoires (2 min)

```bash
cd affilimax
python youtube_uploader.py --story --privacy unlisted
```

- La 1ʳᵉ fois : un navigateur s'ouvre → connecte-toi avec TON compte Google → « Autoriser »
- Les vidéos passent en **unlisted** (visibles uniquement par lien) → **vérifie-les** sur YouTube
- Quand tout est bon : `--privacy public` pour les rendre publiques

### Commandes utiles

```bash
python youtube_uploader.py --latest                # upload la dernière vidéo (produit ou histoire)
python youtube_uploader.py --story --made-for-kids # histoires marquées "fait pour les enfants" (COPPA)
python youtube_uploader.py --story --privacy public --made-for-kids
```

---

## ⚠️ IMPORTANT — Vidéos pour enfants (COPPA)

- Pour des histoires pour enfants, mets **toujours** `--made-for-kids`
  (sinon risque de sanction YouTube)
- En mode « fait pour les enfants » : pas de commentaires, pas de personnalisation
  → c'est normal, c'est la loi américaine (COPPA) appliquée par YouTube

---

## 📈 STRATÉGIE DE GAINS (monétisation)

1. **Monétisation YouTube** : il faut **1 000 abonnés + 4 000 h de visionnage**
   (ou 10 M de vues de Shorts) pour activer les revenus pub
2. **En attendant** : chaque vidéo = vitrine Affilimax → description + liens d'affiliation
   (les histoires mentionnent des produits pour enfants : cartable, gourde, boîte bento...)
3. **Rythme conseillé** : 2-3 histoires/semaine → à ce rythme, objectif 1 000 abonnés ≈ 4-6 mois
   (c'est un canal qui grandit seul, les parents partagent les contes du soir)

### Idées de thèmes (le générateur est infini)
```
python video_factory.py --pipeline --kind story --theme "un petit loup"
python video_factory.py --pipeline --kind story --theme "une petite licorne"
python video_factory.py --pipeline --kind story --theme "un petit ours polaire"
python video_factory.py --pipeline --kind story --theme "un petit astronaute"
```

---

## ✅ CHECKLIST

- [ ] Chaîne YouTube créée (« Histoires pour Enfants »)
- [ ] Projet Google Cloud `affilimax-youtube`
- [ ] YouTube Data API v3 activée
- [ ] Écran OAuth + ton email en testeur
- [ ] `client_secrets.json` téléchargé dans `affilimax/`
- [ ] `pip install google-api-python-client google-auth-oauthlib google-auth-httplib2`
- [ ] `python youtube_uploader.py --story --privacy unlisted`
- [ ] Vérifier les 3 vidéos sur YouTube
- [ ] `--privacy public` quand c'est bon

*Généré par Buffy/Freebuff · 10/08/2026*
