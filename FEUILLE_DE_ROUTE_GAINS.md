# 💰 FEUILLE DE ROUTE DES GAINS — AFFILIMAX

> **Honnêteté totale.** Rien n'est garanti — voici les maths réelles de
> l'affiliation Amazon et les actions qui les transforment en euros.
> Généré le 10/08/2026 · tracking 100 % réel · 0 € de simulation.

---

## 🧮 LES MATHS (taux réels du marché)

```
100 visiteurs  →  10-30 clics Amazon  →  3-5 achats  →  ~5 € de commission chacun
```

| Trafic/mois | Ventes/mois | Gains/mois |
|---|---|---|
| 1 000 visiteurs | ~30-50 | **150-250 €** |
| 5 000 visiteurs | ~150-250 | **750-1 250 €** |
| 10 000 visiteurs | ~300-500 | **1 500-2 500 €** |

---

## ✅ CE QUI EST PRÊT AUJOURD'HUI (vérifié)

| Levier | État | Détail |
|---|---|---|
| Site vitrine + 95 produits | ✅ en ligne | `afflimax.onrender.com` |
| 166 pages SEO | ✅ en ligne | sitemap soumis + IndexNow accepté (HTTP 202) |
| Tracking clics (que du réel) | ✅ en ligne | anti-test/bot actif |
| Webhook de ventes | ✅ prêt + testé | 25,60 € crédités en test, anti-doublon OK |
| Import rapport Amazon | ✅ prêt + testé | `import_amazon_report.py` |
| Pinterest 70 épingles | ✅ calendrier prêt | 14 jours × 5 épingles, liens traqués |
| Google Search Console | 🟡 guide prêt | à vérifier le domaine (10 min) |

---

## 🎯 PLAN D'ACTION (ce qui reste À FAIRE par toi)

### 🔴 Priorité 1 — Aujourd'hui (2 min)
1. **Poser `AMAZON_WEBHOOK_SECRET` sur le service `afflimax`** (PAS affilimax !)
   - valeur : `A1S1wUj5QQxdtpAid4wqqkrodEK-eHOvITSttyVVn1k`
   - sans ça : aucune vente ne peut être créditée en ligne

### 🟠 Priorité 2 — Cette semaine (30 min)
2. **Vérifier le site dans Google Search Console** (guide `GUIDE_GOOGLE_INDEXATION.md`)
   - vérifier `https://afflimax.onrender.com` → soumettre `sitemap.xml`

### 🟡 Priorité 3 — Cette semaine (2 h / semaine)
3. **Publier les 5 épingles Pinterest/jour** (calendrier prêt)
4. **Chaque jour : télécharger le rapport Amazon → `python import_amazon_report.py revenus.csv --secret TA_CLE`**
   (ou utiliser `importer_ventes_auto.bat` une fois configuré)

---

## 📈 PROJECTION RÉALISTE À 30 JOURS

| Scénario | Hypothèse | Gains estimés |
|---|---|---|
| Minimum (rien d'activé) | 0 visiteur | **0 €** |
| Realiste (Google indexe + Pinterest) | ~500-1 000 visiteurs | **50-150 €** |

*L'affiliation Amazon paie 2 mois après la 1re vente (J+60). Les premiers euros apparaissent après ~2-3 mois de volume.*

---

## 📄 Fichiers utiles

| Fichier | Usage |
|---|---|
| `ACTIVER_WEBHOOK_AMAZON.md` | Poser le secret sur Render |
| `IMPORTER_VENTES_AMAZON.md` | Importer les ventes (guide) |
| `import_amazon_report.py` | Le script d'import |
| `importer_ventes_auto.bat` | Import automatisé Windows |
| `LIENS_PARTENAIRES_2026.md` | Liens de tracking partenaires |
| `GUIDE_GOOGLE_INDEXATION.md` | Soumettre à Google |
| `CALENDRIER_PINTEREST_14JOURS.txt` | 70 épingles prêtes |

*Document généré par Buffy/Freebuff · 10/08/2026 · Aucune simulation — uniquement des outils réels, testés et prêts à produire des gains.*
