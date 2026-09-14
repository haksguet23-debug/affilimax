#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Affilimax - Video Factory (Groq/Gemini + edge-tts + moviepy)
============================================================
Usine a contenu video basee sur le concept "YoutubeFactory" :

  1. Script video (produit d'affiliation OU histoire pour enfants) via la
     cascade IA existante (Groq -> Gemini -> fallback statique)
  2. Metadonnees SEO YouTube (titre, description, tags, hashtags)
  3. Storyboard d'images (PIL, sans API, toujours disponible)
  4. Voix IA (edge-tts, gratuit, sans cle API)
  5. Sous-titres automatiques SRT (timings edge-tts) incrustes dans la video
  6. Montage MP4 (moviepy + FFmpeg embarque imageio-ffmpeg)

Usage CLI:
  python video_factory.py --script --product "SSD Samsung"     # script produit
  python video_factory.py --story --theme "un petit dragon"    # histoire enfant
  python video_factory.py --pipeline --kind product --product "SSD Samsung"
  python video_factory.py --pipeline --kind story --theme "un petit dragon"

Integration dashboard:
  GET  /api/video/health
  GET  /api/video/script?kind=product&product=...&duration=60s&style=testeur&scenes=5
  POST /api/video/job        {kind, product, theme, duration, style, scenes, voice, subtitles}
  GET  /api/video/job?id=...
  GET  /api/video/history
  GET  /api/video/download?id=...
"""

import asyncio
import json
import os
import random
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

# Reutilise la cascade IA d'affilimax (Groq -> Gemini -> statique)
from ai_automator import ask_ai, get_active_provider, AI_ENABLED, find_product

BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "video_factory" / "output"
HISTORY_FILE = BASE_DIR / "video_factory_history.json"
MAX_HISTORY = 20

# ==================== CONFIGURATION ====================

VOICES = {
    "Denise (femme, douce)": "fr-FR-DeniseNeural",
    "Elise (femme)": "fr-FR-EliseNeural",
    "Henri (homme)": "fr-FR-HenriNeural",
    "Remy (multilingue)": "fr-FR-RemyMultilingualNeural",
    "Sylvie (Quebec)": "fr-CA-SylvieNeural",
    "Antoine (Quebec)": "fr-CA-AntoineNeural",
}
DEFAULT_VOICE = "fr-FR-DeniseNeural"

DURATION_LABELS = {
    "30s": "30 secondes",
    "60s": "1 minute",
    "3min": "3 minutes",
    "5min": "5 minutes",
    "10min": "10 minutes",
}
STYLE_LABELS = {
    "testeur": "testeur honnete et direct",
    "storytelling": "storytelling immersif",
    "educatif": "educatif et pedagogique",
    "fun": "fun et energique",
    "minimaliste": "minimaliste et professionnel",
}
SCENE_THEMES = [
    "L'ouverture", "La decouverte", "Le probleme", "La solution",
    "Les specs", "L'essai reel", "Le verdict", "L'appel a l'action",
]
STORY_THEMES = [
    "L'arrivee", "L'aventure commence", "L'obstacle", "L'entraide",
    "La lecon", "Le retour", "La celebration",
]
LESSON_THEMES = [
    "Bienvenue a la lecon", "On decouvre ensemble", "On pratique",
    "On repete", "Petit quiz", "Le recap", "A bientot !",
]

# Catalogue de lecons pedagogiques pour enfants (3-8 ans)
# cle -> (titre, accroche, narration de la 1ere scene, mots-cles)
LESSONS = {
    "compter": {
        "titre": "Apprendre a compter de 1 a 10 - lecon educative",
        "accroche": "Aujourd'hui, on apprend a compter de 1 a 10 !",
        "contenu": [
            ("Les nombres 1 a 5", "Regarde bien : un, deux, trois, quatre, cinq. Repete avec moi : un, deux, trois, quatre, cinq. Bravo !"),
            ("Les nombres 6 a 10", "Maintenant les grands nombres : six, sept, huit, neuf, dix. Encore une fois : six, sept, huit, neuf, dix !"),
            ("On compte les doigts", "Comptons sur nos doigts : un pouce, deux pouces, trois, quatre, cinq doigts sur une main. Et dix doigts sur les deux mains !"),
            ("On compte les objets", "Comptons ensemble les objets de la maison : une pomme, deux pommes, trois pommes. Combien y en a-t-il ? Oui, trois pommes !"),
            ("Le quiz des nombres", "Petit quiz : quel nombre vient apres trois ? Un, deux, trois, quatre ! Oui, c'est quatre. Et apres sept ? Huit ! Excellent !"),
            ("Le recap", "Recapitulons : un, deux, trois, quatre, cinq, six, sept, huit, neuf, dix. Tu sais compter jusqu'a dix ! Bravo !"),
        ],
    },
    "couleurs": {
        "titre": "Apprendre les couleurs - lecon educative",
        "accroche": "Aujourd'hui, on découvre les belles couleurs !",
        "contenu": [
            ("Les couleurs chaudes", "Regarde le ciel rouge du soleil couchant : c'est rouge. Et le soleil ? Il est jaune et orange. Rouge, jaune, orange : ce sont les couleurs chaudes."),
            ("Les couleurs froides", "Le ciel est bleu, l'herbe est verte. Regarde la mer : elle est bleue aussi ! Bleu et vert sont des couleurs froides et apaisantes."),
            ("Rose et violet", "La fleur est rose, le raisin est violet. Rose et violet, ce sont des couleurs tres jolies, comme dans un arc-en-ciel."),
            ("On cherche les couleurs", "Cherchons les couleurs autour de nous : quelle couleur est la banane ? Oui, jaune ! Et la tomate ? Oui, rouge !"),
            ("Le quiz des couleurs", "Petit quiz : quelle couleur est le ciel ? Bleu ! Et le soleil ? Jaune ! Et l'herbe ? Verte ! Excellent, tu connais tes couleurs !"),
            ("Le recap", "On retient : rouge, jaune, orange, bleu, vert, rose et violet. Les couleurs sont partout autour de toi !"),
        ],
    },
    "formes": {
        "titre": "Apprendre les formes - lecon educative",
        "accroche": "Aujourd'hui, on apprend les formes geomeetriques !",
        "contenu": [
            ("Le cercle et le carre", "Voici le cercle : il est rond, comme une roue ou un ballon. Voici le carre : il a quatre cotes egaux, comme une fenetre."),
            ("Le triangle et le rectangle", "Le triangle a trois cotes, comme une part de pizza. Le rectangle a deux cotes longs et deux courts, comme une porte ou une feuille."),
            ("L'etoile et le coeur", "L'etoile a cinq branches, comme celle du ciel la nuit. Le coeur, lui, est le symbole de l'amour, comme celui qu'on dessine pour maman."),
            ("On cherche les formes", "Cherchons les formes : la roue de la voiture est un cercle ! La fenetre est un carre ! Le toit de la maison est un triangle !"),
            ("Le quiz des formes", "Petit quiz : quelle forme a un ballon ? Un cercle ! Et une piece de puzzle ? Un carre ! Et un toit ? Un triangle ! Bravo !"),
            ("Le recap", "On retient : cercle, carre, triangle, rectangle, etoile et coeur. Les formes sont partout autour de toi !"),
        ],
    },
    "animaux": {
        "titre": "Decouvrir les animaux de la ferme - lecon educative",
        "accroche": "Aujourd'hui, on visite la ferme et ses animaux !",
        "contenu": [
            ("La vache et le cheval", "A la ferme, la vache fait meuh et nous donne du lait. Le cheval fait hennit et court tres vite dans le pre."),
            ("Le mouton et la poule", "Le mouton est tout doux avec sa laine blanche, il fait beee. La poule fait cot cot et pond des oeufs delicieux."),
            ("Le cochon et le canard", "Le cochon est rose et adore se rouler dans la boue, il fait groin groin. Le canard nage dans la mare et fait coin coin."),
            ("On ecoute les animaux", "Ecoute bien : qui fait meuh ? La vache ! Qui fait coin coin ? Le canard ! Qui fait cot cot ? La poule ! Tu connais bien les animaux !"),
            ("Le quiz des animaux", "Petit quiz : quel animal donne du lait ? La vache ! Quel animal pond des oeufs ? La poule ! Quel animal a de la laine ? Le mouton !"),
            ("Le recap", "On retient : la vache, le cheval, le mouton, la poule, le cochon et le canard. Les animaux de la ferme sont nos amis !"),
        ],
    },
    "alphabet": {
        "titre": "Apprendre l'alphabet - lecon educative",
        "accroche": "Aujourd'hui, on chante l'alphabet ensemble !",
        "contenu": [
            ("Les lettres A a G", "Regarde : A comme Abeille, B comme Ballon, C comme Chat, D comme Dauphin, E comme Elephant, F comme Fleur, G comme Girafe."),
            ("Les lettres H a N", "Continuons : H comme Hibou, I comme Ile, J comme Jardin, K comme Koala, L comme Lion, M comme Maison, N comme Nuage."),
            ("Les lettres O a U", "Et maintenant : O comme Oiseau, P comme Papillon, Q comme Question, R comme Renard, S comme Soleil, T comme Tortue, U comme Univers."),
            ("Les lettres V a Z", "Enfin : V comme Voiture, W comme Wagon, X comme Xylophone, Y comme Yoyo, Z comme Zebre. Et voila tout l'alphabet !"),
            ("On chante l'alphabet", "Chantons ensemble : A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z. Bravo !"),
            ("Le recap", "Tu connais maintenant les 26 lettres de l'alphabet ! Chaque lettre a un son et une histoire. Tu progresses chaque jour !"),
        ],
    },
    "jours": {
        "titre": "Apprendre les jours de la semaine - lecon educative",
        "accroche": "Aujourd'hui, on apprend les jours de la semaine !",
        "contenu": [
            ("Lundi et mardi", "La semaine commence : lundi, on retourne a l'ecole. Mardi, on continue d'apprendre plein de choses nouvelles."),
            ("Mercredi et jeudi", "Mercredi, c'est souvent le jour des activites et du sport. Jeudi, on se rapproche du week-end, encore un petit effort !"),
            ("Vendredi, samedi, dimanche", "Vendredi, l'ecole est finie, on range les cahiers ! Samedi, on joue et on se repose. Dimanche, on passe du temps en famille."),
            ("On chante la semaine", "Chantons les jours : lundi, mardi, mercredi, jeudi, vendredi, samedi, dimanche. Sept jours pour toute une semaine !"),
            ("Le quiz des jours", "Petit quiz : quel jour vient apres lundi ? Mardi ! Et avant dimanche ? Samedi ! Et le premier jour de l'ecole ? Lundi !"),
            ("Le recap", "On retient les 7 jours : lundi, mardi, mercredi, jeudi, vendredi, samedi, dimanche. Chaque jour est une nouvelle aventure !"),
        ],
    },
    "saisons": {
        "titre": "Decouvrir les 4 saisons - lecon educative",
        "accroche": "Aujourd'hui, on decouvre les 4 saisons de l'annee !",
        "contenu": [
            ("Le printemps", "Au printemps, les fleurs poussent, les oiseaux chantent et il fait de plus en plus beau. C'est la saison du renouveau."),
            ("L'ete", "En ete, le soleil brille fort, on va a la plage et on mange des glaces. C'est la saison des grandes vacances."),
            ("L'automne", "En automne, les feuilles deviennent orange et tombent des arbres. On ramasse les champignons et on se couvre un peu."),
            ("L'hiver", "En hiver, il fait froid, parfois il neige et on fait des bonhommes de neige. On boit du chocolat chaud au coin du feu."),
            ("Le quiz des saisons", "Petit quiz : quelle saison est chaude ? L'ete ! Quelle saison est froide ? L'hiver ! Quelle saison fait pousser les fleurs ? Le printemps !"),
            ("Le recap", "Les 4 saisons : printemps, ete, automne, hiver. Chacune est belle et apporte ses surprises. L'annee tourne sans cesse !"),
        ],
    },
    "compter20": {
        "titre": "Apprendre a compter de 1 a 20 - lecon educative",
        "accroche": "Aujourd'hui, on compte encore plus loin : de 1 a 20 !",
        "contenu": [
            ("On revise 1 a 10", "On reprend ensemble : un, deux, trois, quatre, cinq, six, sept, huit, neuf, dix. Tres bien, tu te souviens !"),
            ("On decouvre 11 a 15", "Maintenant, on continue : onze, douze, treize, quatorze, quinze. Repete avec moi : onze, douze, treize, quatorze, quinze !"),
            ("On decouvre 16 a 20", "Et voici la fin du voyage : seize, dix-sept, dix-huit, dix-neuf, vingt. Encore une fois : seize, dix-sept, dix-huit, dix-neuf, vingt !"),
            ("On compte les jouets", "Comptons les jouets : un ballon, deux ballons, trois ballons... jusqu'a dix ! Puis onze, douze, treize... tu es un champion du comptage !"),
            ("Le quiz des grands nombres", "Petit quiz : quel nombre vient apres dix ? Onze ! Et apres quinze ? Seize ! Et apres dix-neuf ? Vingt ! Bravo !"),
            ("Le recap", "Tu sais compter de 1 a 20 ! C'est enorme. Compte avec tes parents quand tu ranges tes jouets ce soir. Bravo champion !"),
        ],
    },
    "contraires": {
        "titre": "Decouvrir les contraires - lecon educative",
        "accroche": "Aujourd'hui, on joue avec les contraires !",
        "contenu": [
            ("Grand et petit", "Un elephant est grand, une souris est petite. Grand et petit, ce sont des contraires. Le papa est grand, le bebe est petit !"),
            ("Chaud et froid", "Le chocolat chaud est chaud, la glace est froide. Chaud et froid, ce sont des contraires. Touche ta joue : elle est froide !"),
            ("Jour et nuit", "Le jour, le soleil brille. La nuit, la lune et les etoiles apparaissent. Jour et nuit, ce sont des contraires."),
            ("Vite et lentement", "Le guepard court vite, la tortue marche lentement. Vite et lentement, ce sont des contraires. Quelle bete va le plus vite ?"),
            ("Le quiz des contraires", "Petit quiz : quel est le contraire de grand ? Petit ! De chaud ? Froid ! De jour ? Nuit ! Tu es un champion des contraires !"),
            ("Le recap", "Grand-petit, chaud-froid, jour-nuit, vite-lent : les contraires sont partout autour de toi !"),
        ],
    },
    "corps": {
        "titre": "Decouvrir le corps humain - lecon educative",
        "accroche": "Aujourd'hui, on decouvre notre corps !",
        "contenu": [
            ("La tete", "Sur ta tete, il y a les yeux pour voir, les oreilles pour entendre, le nez pour sentir et la bouche pour parler et manger."),
            ("Les bras et les mains", "Tes bras te servent a porter et a serrer. Tes mains ont cinq doigts chacune : pouce, index, majeur, annulaire et auriculaire !"),
            ("Les jambes et les pieds", "Tes jambes te permettent de courir et de sauter. Tes pieds ont dix orteils et te portent toute la journee."),
            ("Le corps en mouvement", "Le corps peut courir, sauter, danser, grimper. Chaque partie a un role : regarde tes mains applaudir, tes pieds danser !"),
            ("Le quiz du corps", "Petit quiz : avec quoi vois-tu ? Les yeux ! Avec quoi entends-tu ? Les oreilles ! Avec quoi marches-tu ? Les jambes ! Bravo !"),
            ("Le recap", "Tete, yeux, oreilles, bras, mains, jambes, pieds : ton corps est magnifique et tu dois en prendre soin !"),
        ],
    },
    "fruits": {
        "titre": "Decouvrir les fruits et legumes - lecon educative",
        "accroche": "Aujourd'hui, on decouvre les fruits et les legumes !",
        "contenu": [
            ("Les fruits rouges", "La pomme est rouge et croquante, la fraise est petite et sucree, la cerise est ronde. Les fruits rouges sont pleins de vitamines !"),
            ("Les fruits jaunes", "La banane est jaune et toute douce, le citron est jaune et acide, l'ananas est jaune et juteux. Tu aimes les fruits jaunes ?"),
            ("Les legumes verts", "Le brocoli est vert, le haricot est vert, la courgette est verte. Les legumes verts donnent beaucoup d'energie pour jouer !"),
            ("Les legumes orange", "La carotte est orange et croquante, la courge est orange et douce. Les lapins adorent les carottes, et toi ?"),
            ("Le quiz des fruits", "Petit quiz : quel fruit est jaune et tout doux ? La banane ! Quel legume adorent les lapins ? La carotte ! Quel fruit est rouge ? La pomme !"),
            ("Le recap", "Pomme, banane, fraise, carotte, brocoli : mange 5 fruits et legumes par jour pour etre en pleine forme !"),
        ],
    },
    "transports": {
        "titre": "Decouvrir les moyens de transport - lecon educative",
        "accroche": "Aujourd'hui, on part en voyage : decouvrons les moyens de transport !",
        "contenu": [
            ("Sur la route", "La voiture roule sur la route, le bus transporte beaucoup de monde, le velo a deux roues et une sonnette : ding ding !"),
            ("Sur les rails", "Le train file sur les rails tres vite. Le TGV va encore plus vite ! Ecoute le train : tchou tchou !"),
            ("Dans le ciel", "L'avion vole haut dans le ciel, l'helicoptere a une grande helice qui tourne, la fusee va jusqu'aux etoiles !"),
            ("Sur l'eau", "Le bateau navigue sur la mer, le voilier utilise le vent, le sous-marin plonge sous les vagues !"),
            ("Le quiz des transports", "Petit quiz : quel vehicule vole dans le ciel ? L'avion ! Quel vehicule roule sur les rails ? Le train ! Quel vehicule navigue sur l'eau ? Le bateau !"),
            ("Le recap", "Voiture, bus, velo, train, avion, bateau : les moyens de transport nous aident a voyager partout dans le monde !"),
        ],
    },
}

# ==================== JOBS (GESTIONNAIRE) ====================

_JOBS = {}
_JOBS_LOCK = threading.Lock()
_event_cb = None  # callback optionnelle (SSE) injectee par server.py


def set_event_callback(cb):
    """Permet a server.py d'injecter un callback push temps-reel (SSE)."""
    global _event_cb
    _event_cb = cb


def _notify(job_id, kind, payload):
    if _event_cb:
        try:
            _event_cb(kind, {"job_id": job_id, **payload})
        except Exception:
            pass


def _log(job, msg):
    job["log"].append({"ts": datetime.utcnow().strftime("%H:%M:%S"), "msg": msg})
    if len(job["log"]) > 30:
        job["log"] = job["log"][-30:]


def _set_progress(job, progress, step):
    job["progress"] = min(100, int(progress))
    job["step"] = step
    _notify(job["id"], "progress", {
        "progress": job["progress"], "step": step, "status": job["status"]
    })


def _load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_history():
    history = _load_history()
    current = list(_JOBS.values())
    merged = {j["id"]: j for j in current}
    for j in history:
        merged.setdefault(j["id"], j)
    items = sorted(merged.values(), key=lambda x: x.get("created_at", ""), reverse=True)[:MAX_HISTORY]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[VF] Erreur sauvegarde historique: {e}")


def _new_job(kind, params):
    job_id = "vf_" + datetime.utcnow().strftime("%Y%m%d_%H%M%S") + "_" + str(random.randint(100, 999))
    job = {
        "id": job_id,
        "kind": kind,
        "status": "running",
        "progress": 0,
        "step": "initialisation",
        "title": "",
        "params": params,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "finished_at": None,
        "files": {"video": None, "script": None},
        "log": [],
        "error": None,
    }
    with _JOBS_LOCK:
        _JOBS[job_id] = job
    _log(job, "Job cree")
    _save_history()
    return job


def start_job(kind, params):
    """Lance un pipeline video en arriere-plan. Retourne le job."""
    job = _new_job(kind, params)
    t = threading.Thread(target=_run_job, args=(job["id"],), daemon=True)
    t.start()
    return job


def get_job(job_id):
    job = _JOBS.get(job_id)
    if job:
        return job
    for h in _load_history():
        if h.get("id") == job_id:
            return h
    return None


def list_jobs():
    history = _load_history()
    current = list(_JOBS.values())
    merged = {j["id"]: j for j in current}
    for j in history:
        merged.setdefault(j["id"], j)
    return sorted(merged.values(), key=lambda x: x.get("created_at", ""), reverse=True)[:MAX_HISTORY]


# ==================== HELPERS IA ====================

def _extract_json(text):
    """Extrait un objet JSON robuste depuis la reponse d'un LLM."""
    if not text:
        return None
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    candidate = text[start:end + 1]
    try:
        return json.loads(candidate)
    except Exception:
        pass
    # Derniere chance : supprimer les virgules finales de tableaux/objets
    candidate2 = re.sub(r",\s*([}\]])", r"\1", candidate)
    try:
        return json.loads(candidate2)
    except Exception:
        return None


def _ask_json(system_prompt, user_prompt, temperature=0.7, max_tokens=1600):
    text = ask_ai(system_prompt, user_prompt, temperature=temperature, max_tokens=max_tokens)
    return _extract_json(text)


def _clean_scenes(raw, fallback_titles, count):
    """Normalise la liste de scenes retournee par le LLM (robuste)."""
    scenes = []
    if isinstance(raw, list):
        for i, s in enumerate(raw):
            if not isinstance(s, dict) or len(scenes) >= count:
                continue
            title = fallback_titles[i % len(fallback_titles)] if i < len(fallback_titles) else f"Scene {i + 1}"
            scenes.append({
                "titre": str(s.get("titre") or title)[:90],
                "narration": str(s.get("narration") or s.get("texte") or title)[:600],
                "visuel": str(s.get("visuel") or "")[:400],
                "prompt_image": str(s.get("prompt_image") or s.get("prompt") or "")[:500],
            })
    while len(scenes) < count:
        i = len(scenes)
        title = fallback_titles[i % len(fallback_titles)]
        scenes.append({"titre": title, "narration": title, "visuel": "", "prompt_image": ""})
    return scenes


def _mode_label():
    if AI_ENABLED:
        return f"IA ({get_active_provider().upper()})"
    return "STATIQUE (fallback)"


# ==================== GENERATEURS DE SCRIPTS ====================

def _product_context(product):
    carac = product.get("caracteristiques") or []
    return (
        f"Produit: {product['nom']}\n"
        f"Categorie: {product.get('categorie', 'High-Tech')}\n"
        f"Prix: {product['prix']} EUR\n"
        f"Note: {product.get('note_moyenne', 4.5)}/5 ({product.get('avis_total', 0)} avis)\n"
        f"Commission: {product.get('commission_euro', 0)} EUR\n"
        f"Plateforme: {product.get('plateforme', 'Amazon')}\n"
        f"Caracteristiques: {', '.join(carac[:4]) if carac else 'Qualite premium'}"
    )


def _static_product_script(product, scenes=5, style="testeur", duration="60s"):
    nom = product["nom"]
    prix = product.get("prix", "?")
    note = product.get("note_moyenne", 4.5)
    avis = product.get("avis_total", 0)
    carac = product.get("caracteristiques") or []
    c1 = carac[0] if carac else "Qualite premium"
    c2 = carac[1] if len(carac) > 1 else "Excellent rapport qualite-prix"

    tpl = [
        ("L'ouverture",
         f"Vous vous demandez si le {nom} vaut vraiment son prix de {prix} EUR ? On l'a teste pour vous.",
         "Plan large du produit dans son emballage",
         f"Photo studio du {nom} sur fond sombre, eclairage premium, emballage ouvert"),
        ("Les specs qui comptent",
         f"Avec {c1}, ce produit coche toutes les cases. La note de {note}/5 sur {avis} avis parle d'elle-meme.",
         "Gros plans des caracteristiques techniques",
         f"Gros plan macro des details du {nom}, profondeur de champ"),
        ("En conditions reelles",
         f"{c2}, c'est ce qui fait la difference au quotidien. On l'a teste pendant des semaines.",
         "Scene d'utilisation reelle du produit",
         f"Personne utilisant le {nom} dans un salon moderne, lumiere naturelle"),
        ("Le verdict",
         f"A {prix} EUR, le {nom} est le meilleur choix de sa categorie. Ni surpaye, ni trop bon marche.",
         "Le testeur donne son verdict face camera",
         f"Presentateur souriant face camera avec le {nom} en main, fond flou"),
        ("Passez a l'action",
         "Profitez de l'offre aujourd'hui via le lien en description, et likez si ca vous a aide.",
         "Ecran avec le bouton commander",
         "Ecran d'achat en ligne avec bouton commander lumineux, style e-commerce moderne"),
    ]
    scenes_out = []
    for i in range(scenes):
        t, narr, vis, prom = tpl[i % len(tpl)]
        scenes_out.append({"titre": t, "narration": narr, "visuel": vis, "prompt_image": prom})
    return {
        "titre": f"{nom} : test complet et avis honnete ({prix} EUR)",
        "accroche": f"Le {nom} vaut-il ses {prix} EUR ? Verdict dans 60 secondes.",
        "scenes": scenes_out,
        "cta": f"Cliquez sur le lien en description pour decouvrir le {nom} au meilleur prix !",
        "seo": {
            "titre_youtube": f"{nom} - Avis complet {note}/5, vaut-il le coup en 2026 ?",
            "description": f"Test complet du {nom} a {prix} EUR. Note {note}/5 sur {avis} avis. {c1}. {c2}.\n\nLien produit en description.\n\n#Avis #Test #2026",
            "tags": [nom, "avis produit", "test 2026", "meilleur choix", "comparatif"],
            "hashtags": ["#Avis", "#TestProduit", "#BonPlan"],
        },
        "mode": "STATIQUE (fallback)",
        "duration": DURATION_LABELS.get(duration, duration),
        "style": style,
    }


def generate_product_script(product=None, scenes=5, style="testeur", duration="60s"):
    """Script video complet pour promouvoir un produit d'affiliation."""
    if product is None:
        product = find_product(None)
    if not product:
        return {"error": "Aucun produit trouve"}

    context = _product_context(product)
    style_label = STYLE_LABELS.get(style, style)
    dur_label = DURATION_LABELS.get(duration, duration)

    system = ("Tu es un scenariste video expert en marketing d'affiliation. "
              "Tu ecris des scripts YouTube complets, prets a tourner, qui convertissent. "
              "Reponds UNIQUEMENT en JSON valide, sans markdown, sans texte autour.")
    user = f"""{context}

Cree un script video YouTube complet pour promouvoir ce produit.
Duree cible: {dur_label} | Style: {style_label} | Nombre de scenes: {scenes}

JSON attendu (strict):
{{
  "titre": "titre de la video, accrocheur",
  "accroche": "phrase d'accroche des 5 premieres secondes, courte et punchy",
  "scenes": [
    {{
      "titre": "nom de la scene",
      "narration": "texte voix off (2 a 4 phrases, francais naturel)",
      "visuel": "description de ce qu'on voit a l'ecran",
      "prompt_image": "prompt image detaillle pour illustrer cette scene"
    }}
  ],
  "cta": "appel a l'action final"
}}

Regles:
- narration en francais naturel, ton {style_label}
- mentionne le prix et la note
- {scenes} scenes exactement
- la derniere scene doit contenir l'appel a l'action"""

    data = _ask_json(system, user, temperature=0.85, max_tokens=2200)

    if data and isinstance(data, dict):
        scenes_out = _clean_scenes(data.get("scenes"), SCENE_THEMES, scenes)
        result = {
            "titre": str(data.get("titre") or f"{product['nom']} : avis complet")[:120],
            "accroche": str(data.get("accroche") or "")[:200],
            "scenes": scenes_out,
            "cta": str(data.get("cta") or "")[:300],
            "mode": _mode_label(),
            "duration": dur_label,
            "style": style_label,
        }
    else:
        result = _static_product_script(product, scenes, style, duration)
        result["mode"] = _mode_label()

    # Metadonnees SEO (2e appel IA, degrade en fallback si KO)
    seo = _ask_json(
        "Tu es un expert SEO YouTube. Reponds UNIQUEMENT en JSON valide.",
        f"""Produis les metadonnees YouTube pour cette video:
Titre video: {result['titre']}
Accroche: {result['accroche']}
Produit: {product['nom']} a {product['prix']} EUR
Nombre de scenes: {len(result['scenes'])}

JSON attendu:
{{
  "titre_youtube": "titre YouTube <=100 caracteres, avec mot-cle principal",
  "description": "description 2-4 phrases + lien + hashtags",
  "tags": ["5 a 8 mots-cles"],
  "hashtags": ["3 a 5 hashtags"]
}}""",
        temperature=0.6, max_tokens=800
    )
    if seo and isinstance(seo, dict):
        result["seo"] = {
            "titre_youtube": str(seo.get("titre_youtube") or result["titre"])[:100],
            "description": str(seo.get("description") or "")[:1000],
            "tags": [str(t)[:40] for t in (seo.get("tags") or [])][:8],
            "hashtags": [str(h)[:30] for h in (seo.get("hashtags") or [])][:5],
        }
    else:
        result["seo"] = _static_product_script(product, scenes, style, duration)["seo"]

    result["produit"] = product["nom"]
    result["prix"] = product.get("prix")
    return result


def _static_story_script(theme="un petit renard", scenes=5, duration="5 min"):
    theme = theme.strip() or "un petit renard"
    tpl = [
        ("Il etait une fois",
         f"Dans une foret toute douce, vivait {theme}, qui adorait explorer le monde.",
         "Une foret lumineuse et coloree au lever du soleil",
         f"Foret magique coloree, personnage mignon ({theme}), lever de soleil"),
        ("La decouverte",
         "Un matin, il trouva une carte mysterieuse, cachee sous une feuille d'or.",
         "La carte decouverte sous une grande feuille",
         "Carte au tresor animee sous une feuille doree, eclats de lumiere"),
        ("L'obstacle",
         "Mais le chemin etait bloque par un grand fleuve. Que faire quand on est tout petit ?",
         "Un fleuve qui bloque le chemin",
         "Petit personnage devant un fleuve, pont de pierres en arriere-plan"),
        ("L'entraide",
         "Avec l'aide de ses amis, il construisit un radeau. Ensemble, tout devient possible.",
         "Les amis construisent un radeau ensemble",
         "Personnages mignons construisant un radeau, ambiance joyeuse"),
        ("La lecon",
         "Le tresor n'etait pas l'or, mais l'aventure et les amis qu'il avait rencontres.",
         "Le tresor decouvert et les amis reunis",
         "Tresor eclatant, personnages reunis, lumiere chaleureuse"),
        ("La morale",
         f"Et c'est ainsi que {theme} comprit : le vrai bonheur se partage.",
         "Tous les personnages se font un câlin au coucher du soleil",
         "Coucher de soleil chaleureux, personnages heureux ensemble"),
    ]
    scenes_out = []
    for i in range(scenes):
        t, narr, vis, prom = tpl[i % len(tpl)]
        scenes_out.append({"titre": t, "narration": narr, "visuel": vis, "prompt_image": prom})
    return {
        "titre": f"L'histoire de {theme} - histoire pour enfants",
        "accroche": f"Aujourd'hui, on raconte l'histoire de {theme}. Installe-toi bien...",
        "scenes": scenes_out,
        "cta": "Abonne-toi pour de nouvelles histoires chaque semaine, et dis-nous en commentaire : quelle aventure veux-tu ?",
        "seo": {
            "titre_youtube": f"{theme.capitalize()} - Histoire pour enfants (conte du soir)",
            "description": f"Une belle histoire pour enfants : l'aventure de {theme}. Conte du soir calme et educatif.\n\nAbonne-toi pour ne rien rater !\n\n#HistoirePourEnfants #Conte #2026",
            "tags": ["histoire pour enfants", "conte du soir", theme, "histoire en francais", "aventure"],
            "hashtags": ["#HistoirePourEnfants", "#ConteDuSoir", "#2026"],
        },
        "mode": "STATIQUE (fallback)",
        "duration": duration,
        "theme": theme,
    }


def generate_children_story(theme="", scenes=5, duration="5 min"):
    """Histoire originale pour enfants, structuree en scenes avec morale."""
    theme = (theme or "un petit renard").strip()

    system = ("Tu es un conteur et scenariste specialise dans les histoires pour enfants "
              "(3-8 ans). Tes histoires sont joyeuses, educatives, avec des personnages attachants. "
              "Reponds UNIQUEMENT en JSON valide, sans markdown.")
    user = f"""Cree une histoire originale pour enfants mettant en scene: {theme}
Duree: {duration} | Nombre de scenes: {scenes}

JSON attendu (strict):
{{
  "titre": "titre de l'histoire",
  "accroche": "phrase d'introduction racontee d'une voix douce",
  "scenes": [
    {{
      "titre": "nom de la scene",
      "narration": "texte raconte aux enfants (2 a 4 phrases)",
      "visuel": "description de l'image douce et coloree",
      "prompt_image": "prompt image dessin animee pour cette scene"
    }}
  ],
  "morale": "la lecon finale de l'histoire",
  "cta": "phrase de fin pour les enfants"
}}

Regles:
- langage simple, adapte aux enfants
- {scenes} scenes exactement
- une aventure avec un obstacle et une entraide
- fin heureuse et morale"""

    data = _ask_json(system, user, temperature=0.9, max_tokens=2200)

    if data and isinstance(data, dict):
        scenes_out = _clean_scenes(data.get("scenes"), STORY_THEMES, scenes)
        result = {
            "titre": str(data.get("titre") or f"L'histoire de {theme}")[:120],
            "accroche": str(data.get("accroche") or "")[:200],
            "scenes": scenes_out,
            "morale": str(data.get("morale") or "")[:300],
            "cta": str(data.get("cta") or "")[:300],
            "mode": _mode_label(),
            "duration": duration,
            "theme": theme,
        }
    else:
        result = _static_story_script(theme, scenes, duration)
        result["mode"] = _mode_label()

    seo = _ask_json(
        "Tu es un expert SEO YouTube pour chaines enfants. Reponds UNIQUEMENT en JSON valide.",
        f"""Produis les metadonnees YouTube pour cette histoire pour enfants:
Titre: {result['titre']}
Theme: {theme}
Nombre de scenes: {len(result['scenes'])}

JSON attendu:
{{
  "titre_youtube": "titre <=100 caracteres, adapte aux enfants",
  "description": "description 2-3 phrases + hashtags",
  "tags": ["5 a 8 mots-cles"],
  "hashtags": ["3 a 5 hashtags"]
}}""",
        temperature=0.6, max_tokens=800
    )
    if seo and isinstance(seo, dict):
        result["seo"] = {
            "titre_youtube": str(seo.get("titre_youtube") or result["titre"])[:100],
            "description": str(seo.get("description") or "")[:1000],
            "tags": [str(t)[:40] for t in (seo.get("tags") or [])][:8],
            "hashtags": [str(h)[:30] for h in (seo.get("hashtags") or [])][:5],
        }
    else:
        result["seo"] = _static_story_script(theme, scenes, duration)["seo"]

    return result


def _static_lesson_script(lesson_key, scenes=6, duration="5 min"):
    """Lecon pedagogique structuree : decouverte -> pratique -> quiz -> recap."""
    lesson = LESSONS.get(lesson_key, LESSONS["compter"])
    tpl = lesson["contenu"]
    scenes_out = []
    for i in range(scenes):
        t, narr = tpl[i % len(tpl)]
        scenes_out.append({
            "titre": t,
            "narration": narr,
            "visuel": f"Scene educative: {t}",
            "prompt_image": f"Illustration educative enfantine douce et coloree: {t}, dessin anime, lumineux",
        })
    return {
        "titre": lesson["titre"],
        "accroche": lesson["accroche"],
        "scenes": scenes_out,
        "cta": "Bravo ! Tu as appris quelque chose de nouveau aujourd'hui. Abonne-toi pour continuer d'apprendre en t'amusant !",
        "seo": {
            "titre_youtube": f"{lesson['titre']} (video educative 3-8 ans)",
            "description": f"{lesson['titre']}. Une lecon pedagogique douce et amusante pour les enfants de 3 a 8 ans.\n\nAbonne-toi pour de nouvelles lecons chaque semaine !\n\n#Lecon #Education #Enfants #Apprendre",
            "tags": ["lecon", "education", "enfants", "apprendre", "video educative", "maternelle", "primaire"],
            "hashtags": ["#Lecon", "#Education", "#Enfants", "#Apprendre"],
        },
        "mode": "STATIQUE (fallback)",
        "duration": duration,
        "theme": lesson_key,
    }


def generate_children_lesson(lesson_key="", scenes=6, duration="5 min"):
    """Lecon pedagogique pour enfants (3-8 ans), structuree : decouverte, pratique, quiz, recap."""
    lesson_key = (lesson_key or "compter").strip().lower()
    if lesson_key not in LESSONS:
        lesson_key = "compter"
    lesson = LESSONS[lesson_key]

    system = ("Tu es un professeur des ecoles specialise dans les lecons pedagogiques "
              "pour enfants de 3 a 8 ans. Tes lecons sont douces, progressives, "
              "avec repetition, quiz et recapitulatif. Reponds UNIQUEMENT en JSON valide.")
    user = f"""Cree une lecon pedagogique pour enfants sur le theme: {lesson['titre']}
Duree: {duration} | Nombre de scenes: {scenes}

JSON attendu (strict):
{{
  "titre": "titre de la lecon, simple et clair",
  "accroche": "phrase d'introduction encourageante pour l'enfant",
  "scenes": [
    {{
      "titre": "nom de l'etape",
      "narration": "texte pedagogique simple (2 a 4 phrases, voix douce)",
      "visuel": "description de l'image educative",
      "prompt_image": "prompt image dessin animee educative"
    }}
  ],
  "cta": "phrase de felicitation finale"
}}

Regles pedagogiques:
- langage tres simple, adapte aux 3-8 ans
- progression: decouverte -> pratique -> repetition -> petit quiz -> recap
- {scenes} scenes exactement
- ton encourageant et bienveillant
- le quiz doit poser une question simple et donner la reponse"""

    data = _ask_json(system, user, temperature=0.85, max_tokens=2200)

    if data and isinstance(data, dict):
        scenes_out = _clean_scenes(data.get("scenes"), LESSON_THEMES, scenes)
        result = {
            "titre": str(data.get("titre") or lesson["titre"])[:120],
            "accroche": str(data.get("accroche") or lesson["accroche"])[:200],
            "scenes": scenes_out,
            "cta": str(data.get("cta") or "")[:300],
            "mode": _mode_label(),
            "duration": duration,
            "theme": lesson_key,
        }
    else:
        result = _static_lesson_script(lesson_key, scenes, duration)
        result["mode"] = _mode_label()

    seo = _ask_json(
        "Tu es un expert SEO YouTube pour chaines educatives enfants. Reponds UNIQUEMENT en JSON valide.",
        f"""Produis les metadonnees YouTube pour cette lecon educative enfants:
Titre: {result['titre']}
Theme: {lesson['titre']}
Nombre de scenes: {len(result['scenes'])}

JSON attendu:
{{
  "titre_youtube": "titre <=100 caracteres, adapte aux enfants et aux parents",
  "description": "description 2-3 phrases + hashtags",
  "tags": ["5 a 8 mots-cles"],
  "hashtags": ["3 a 5 hashtags"]
}}""",
        temperature=0.6, max_tokens=800
    )
    if seo and isinstance(seo, dict):
        result["seo"] = {
            "titre_youtube": str(seo.get("titre_youtube") or result["titre"])[:100],
            "description": str(seo.get("description") or "")[:1000],
            "tags": [str(t)[:40] for t in (seo.get("tags") or [])][:8],
            "hashtags": [str(h)[:30] for h in (seo.get("hashtags") or [])][:5],
        }
    else:
        result["seo"] = _static_lesson_script(lesson_key, scenes, duration)["seo"]

    return result


# ==================== COMPILATION VIDEO LONGUE ====================

def compile_videos(mp4_paths, out_path, title="Compilation educative", intro_text="", fps=24):
    """Concatene plusieurs MP4 en une seule video longue (compilation).

    Ajoute une intro/outro de 8 s chacune (image degrade + texte) et
    enchaîne les segments avec 0.6 s de noir entre eux.
    Retourne le chemin du fichier final.
    """
    import numpy as np
    from PIL import Image as PILImage, ImageDraw as PILDraw
    from moviepy import ImageClip, VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip

    def _title_clip(text, dur=8.0):
        W, H = 1280, 720
        img = PILImage.new("RGB", (W, H), (30, 27, 75))
        d = PILDraw.Draw(img)
        for yy in range(0, H, 8):
            t = yy / H
            color = (int(30 * (1 - t) + 124 * t), int(27 * (1 - t) + 58 * t), int(75 * (1 - t) + 237 * t))
            d.rectangle([0, yy, W, yy + 8], fill=color)
        f_t = _load_font(72)
        f_s = _load_font(36)
        lines = _wrap_text(d, text, f_t, W - 120)[:3]
        yy = H // 2 - 120
        for line in lines:
            d.text((60, yy), line, font=f_t, fill=(255, 224, 130))
            yy += 90
        d.text((60, yy + 20), "Affilimax Studio - Videos educatives pour enfants", font=f_s, fill=(255, 255, 255))
        return ImageClip(np.array(img)).with_duration(dur)

    clips = []
    # Intro
    intro_text = intro_text or title
    clips.append(_title_clip("APPRENONS ENSEMBLE !\n" + intro_text))
    # Segments
    for p in mp4_paths:
        p = Path(p)
        if not p.exists():
            print(f"[VF] Segment manquant ignore: {p}")
            continue
        try:
            vc = VideoFileClip(str(p))
            clips.append(vc)
            # petite pause noire entre segments
            black = ImageClip(np.zeros((720, 1280, 3), dtype="uint8")).with_duration(0.6)
            clips.append(black)
        except Exception as e:
            print(f"[VF] Erreur segment {p.name}: {e}")
    # Outro
    clips.append(_title_clip("BRAVO !\nTu as appris plein de choses.\nA bientot !"))

    if not clips:
        raise RuntimeError("Aucun segment a compiler")
    final = concatenate_videoclips(clips, method="chain")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    temp_audio = str(out_path.parent / f"temp_audio_{out_path.stem}.m4a")
    final.write_videofile(
        str(out_path), fps=fps, codec="libx264", audio_codec="aac",
        preset="ultrafast", temp_audiofile=temp_audio, remove_temp=True, logger=None,
    )
    return out_path


# ==================== STORYBOARD (IMAGES PIL) ====================

_PALETTES = [
    ((124, 58, 237), (30, 27, 75)),   # violet profond
    ((240, 165, 0), (120, 53, 15)),   # or
    ((16, 185, 129), (6, 78, 59)),    # vert emeraude
    ((59, 130, 246), (30, 58, 138)),  # bleu
    ((236, 72, 153), (131, 24, 67)),  # rose
    ((34, 211, 238), (22, 78, 99)),   # cyan
]

_FONT_CANDIDATES = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/seguisb.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _load_font(size):
    from PIL import ImageFont
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default(size)


def _wrap_text(draw, text, font, max_width):
    words = str(text).split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


# Mots-cles LoremFlickr par theme de lecon (image de fond coherente)
LESSON_IMAGES = {
    "compter": "numbers,counting,kids,education",
    "couleurs": "colors,paint,rainbow,art",
    "formes": "shapes,geometry,blocks,kids",
    "animaux": "farm,animals,cow,sheep",
    "alphabet": "alphabet,letters,abc,kids",
    "jours": "calendar,week,days,school",
    "saisons": "seasons,four,weather,landscape",
}

# Mots-cles LoremFlickr par theme d'histoire + LOCK VERIFIE visuellement
# (les memes locks que les miniatures make_story_thumbs.py, controlees a l'ecran)
STORY_IMAGES = {
    "renard": ("fox,forest,cute,animal", 4441),
    "dragon": ("dragon,cute,fire,magic", 4442),
    "etoile": ("star,night,sky,cute,child", 4443),
    "loup": ("wolf,cute,forest,animal", 4444),
    "licorne": ("unicorn,toy,rainbow", 404),   # verifie: figurine licorne
    "ours": ("polar,bear,cute,snow", 4446),
    "chat": ("cat,kitten,cute,pet", 7051),        # verifie: chat gris mignon
    "elephant": ("elephant,cute,animal,safari", 7052),  # verifie: bebe elephant dans l'eau
    "singe": ("monkey,cute,animal,jungle", 5053),  # verifie: singe malicieux
}

# Priorite locale : si la miniature verifiee existe, on l'utilise direct
# (fallback local = jamais de photo hors-sujet)
def _theme_background_local(script):
    """Chemin de la miniature locale verifiee pour ce theme (si elle existe).

    Detection par MOT ENTIER uniquement (pas de sous-chaine) pour eviter
    les faux positifs : "jours" ne doit pas matcher "ours" ("ours" in "jours").
    """
    theme = str(script.get("theme") or "").strip().lower()
    if theme in LESSON_IMAGES:
        return None  # lecon -> fond PIL dedie, jamais de miniature d'histoire
    for key in STORY_IMAGES:
        if re.search(rf"\b{re.escape(key)}\b", theme):
            p = BASE_DIR / "assets" / "thumbs" / f"story_{key}.jpg"
            if p.exists():
                return p
    return None


def _theme_keywords(script):
    """Mots-cles LoremFlickr pour le fond d'une lecon ou d'une histoire.

    Retourne (keywords, lock) ou None si aucun mapping trouve.
    Priorite : 1) lesson theme, 2) story theme detecte dans le texte.
    """
    theme = str(script.get("theme") or "").strip().lower()
    if theme in LESSON_IMAGES:
        return LESSON_IMAGES[theme], hash(theme) % 5000 + 1000
    # detection dans un theme libre (ex: "un petit renard" -> renard)
    for key, (kw, lock) in STORY_IMAGES.items():
        if key in theme:
            return kw, lock
    return None, None


def _lesson_background_pil(theme, out_path):
    """Dessine un fond pedagogique PIL 100%% coherent pour une lecon.

    Pas de reseau, pas de photo hors-sujet : chiffres geants pour compter,
    pastilles de couleurs, formes geometriques, lettres, calendrier...
    Retourne le chemin si OK, None sinon.
    """
    from PIL import Image, ImageDraw

    W, H = 1280, 720
    img = Image.new("RGB", (W, H), (24, 26, 52))
    d = ImageDraw.Draw(img)
    # fond degrade sombre
    for yy in range(0, H, 8):
        t = yy / H
        color = tuple(int(30 * (1 - t) + 16 * t) for _ in range(1)) + tuple(
            [int(27 * (1 - t) + 18 * t), int(75 * (1 - t) + 40 * t)]
        )
        d.rectangle([0, yy, W, yy + 8], fill=(color[0], color[1], color[2]))
    # cercles doux
    rng = random.Random(abs(hash(theme)) % 9999)
    for _ in range(16):
        cx, cy, r = rng.randint(-80, W), rng.randint(-80, H), rng.randint(40, 150)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255), width=3)

    f_big = _load_font(110)
    f_med = _load_font(46)
    f_sm = _load_font(32)
    gold = (255, 224, 130)
    white = (245, 245, 255)
    # IMPORTANT : tout le contenu reste dans la bande haute (0-240px) pour
    # ne jamais chevaucher le titre de scene (y=250) ni la narration (y=380+)

    if theme == "compter":
        nums = "1 2 3 4 5 6 7 8 9 10".split()
        for i, n in enumerate(nums):
            d.text((45 + i * 120, 40), n, font=f_big, fill=gold)
        d.text((60, 175), "COMPTER DE 1 A 10", font=f_med, fill=white)
    elif theme == "couleurs":
        cols = [("ROUGE", (239, 68, 68)), ("JAUNE", (250, 204, 21)), ("VERT", (34, 197, 94)),
                ("BLEU", (59, 130, 246)), ("VIOLET", (168, 85, 247)), ("ROSE", (236, 72, 153))]
        for i, (label, col) in enumerate(cols):
            x = 105 + i * 182
            d.ellipse([x - 70, 95 - 70, x + 70, 95 + 70], fill=col, outline=white, width=6)
            d.text((x - 45, 185), label, font=f_sm, fill=white)
        d.text((60, 240), "LES COULEURS", font=f_med, fill=gold)
    elif theme == "formes":
        # cercle, carre, triangle, etoile (bande haute)
        cx0, cy0, s = 200, 130, 95
        d.ellipse([cx0 - s, cy0 - s, cx0 + s, cy0 + s], outline=gold, width=8)
        x2 = 480
        d.rounded_rectangle([x2 - s, cy0 - s, x2 + s, cy0 + s], radius=12, outline=gold, width=8)
        x3 = 760
        d.polygon([(x3, cy0 - s), (x3 - s, cy0 + s), (x3 + s, cy0 + s)], outline=gold, width=8)
        x4 = 1040
        d.regular_polygon((x4, cy0, s), 5, rotation=-90, outline=gold, width=8)
        d.text((60, 255), "CERCLE - CARRE - TRIANGLE - ETOILE", font=f_sm, fill=white)
    elif theme == "alphabet":
        for i, l in enumerate("ABCDEFG"):
            d.text((45 + i * 178, 40), l, font=f_big, fill=gold)
        d.text((60, 180), "L'ALPHABET", font=f_med, fill=white)
    elif theme == "jours":
        days = ["LUN", "MAR", "MER", "JEU", "VEN", "SAM", "DIM"]
        for i, day in enumerate(days):
            x = 50 + i * 172
            d.rounded_rectangle([x, 45, x + 155, 150], radius=16, fill=(40, 44, 90), outline=gold, width=4)
            d.text((x + 25, 70), day, font=_load_font(42), fill=white)
        d.text((60, 180), "LES JOURS DE LA SEMAINE", font=f_med, fill=gold)
    elif theme == "saisons":
        seasons = [("PRINTEMPS", (34, 197, 94)), ("ETE", (250, 204, 21)),
                   ("AUTOMNE", (249, 115, 22)), ("HIVER", (96, 165, 250))]
        for i, (label, col) in enumerate(seasons):
            x = 35 + i * 312
            d.rounded_rectangle([x, 40, x + 290, 230], radius=24, fill=(col[0], col[1], col[2]))
            d.text((x + 55, 85), label, font=f_med, fill=(15, 20, 40))
        d.text((60, 262), "LES 4 SAISONS", font=_load_font(40), fill=gold)
    elif theme == "animaux":
        animals = ["VACHE", "CHEVAL", "MOUTON", "POULE", "COCHON", "CANARD"]
        for i, label in enumerate(animals):
            x = 55 + (i % 3) * 400
            y = 35 + (i // 3) * 105
            d.rounded_rectangle([x, y, x + 370, y + 90], radius=16, fill=(40, 44, 90), outline=gold, width=4)
            d.text((x + 115, y + 18), label, font=_load_font(34), fill=white)
        d.text((60, 255), "LES ANIMAUX DE LA FERME", font=_load_font(38), fill=gold)
    elif theme == "compter20":
        nums = "1 2 3 4 5 6 7 8 9 10".split()
        for i, n in enumerate(nums):
            d.text((35 + i * 121, 30), n, font=f_big, fill=gold)
        nums2 = "11 12 13 14 15 16 17 18 19 20".split()
        for i, n in enumerate(nums2):
            d.text((20 + i * 124, 135), n, font=_load_font(80), fill=white)
        d.text((60, 245), "COMPTER DE 1 A 20", font=f_med, fill=gold)
    elif theme == "contraires":
        pairs = [("GRAND", "PETIT"), ("CHAUD", "FROID"), ("JOUR", "NUIT"), ("VITE", "LENT")]
        for i, (a, b) in enumerate(pairs):
            x = 60 + (i % 2) * 620
            y = 30 + (i // 2) * 105
            d.rounded_rectangle([x, y, x + 565, y + 90], radius=16, fill=(40, 44, 90), outline=gold, width=4)
            d.text((x + 100, y + 15), a, font=_load_font(38), fill=(255, 224, 130))
            d.text((x + 340, y + 15), b, font=_load_font(38), fill=white)
        d.text((60, 255), "LES CONTRAIRES", font=_load_font(38), fill=gold)
    elif theme == "corps":
        parts = ["YEUX", "OREILLES", "NEZ", "BOUCHE", "BRAS", "MAINS", "JAMBES", "PIEDS"]
        for i, label in enumerate(parts):
            x = 55 + (i % 4) * 300
            y = 30 + (i // 4) * 105
            d.rounded_rectangle([x, y, x + 270, y + 90], radius=16, fill=(40, 44, 90), outline=gold, width=4)
            d.text((x + 65, y + 18), label, font=_load_font(34), fill=white)
        d.text((60, 250), "LE CORPS HUMAIN", font=_load_font(38), fill=gold)
    elif theme == "fruits":
        items = ["POMME", "BANANE", "FRAISE", "CAROTTE", "BROCOLI", "CITRON"]
        for i, label in enumerate(items):
            x = 55 + (i % 3) * 400
            y = 35 + (i // 3) * 105
            d.rounded_rectangle([x, y, x + 370, y + 90], radius=16, fill=(40, 44, 90), outline=gold, width=4)
            d.text((x + 115, y + 18), label, font=_load_font(34), fill=white)
        d.text((60, 255), "LES FRUITS ET LEGUMES", font=_load_font(38), fill=gold)
    elif theme == "transports":
        items = ["VOITURE", "TRAIN", "AVION", "VELO", "BATEAU", "FUSEE"]
        for i, label in enumerate(items):
            x = 55 + (i % 3) * 400
            y = 35 + (i // 3) * 105
            d.rounded_rectangle([x, y, x + 370, y + 90], radius=16, fill=(40, 44, 90), outline=gold, width=4)
            d.text((x + 115, y + 18), label, font=_load_font(34), fill=white)
        d.text((60, 255), "LES MOYENS DE TRANSPORT", font=_load_font(38), fill=gold)
    else:
        return None

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "JPEG", quality=92)
    return out_path


def _load_product_image_url(product_name):
    """Retrouve l'URL d'image du produit (catalogue) pour illustrer les scenes.

    Les image_url du catalogue pointent vers des photos reelles pertinentes
    (LoremFlickr par mot-cle) -> la video montre le VRAI produit, pas un
    degrade generique. Retourne None si introuvable.
    """
    if not product_name:
        return None
    try:
        cfg = json.loads((BASE_DIR / "liens_affiliation.json").read_text(encoding="utf-8"))
    except Exception:
        return None
    q = str(product_name).lower()
    for p in cfg.get("produits", []):
        if q in str(p.get("nom", "")).lower() or q in str(p.get("slug", "")).lower():
            url = p.get("image_url") or ""
            if url:
                return url
    return None


def _download_background(url, dest, timeout=10):
    """Telecharge une image de fond (LoremFlickr) avec timeout court.

    Retourne le chemin si OK, None en cas d'echec (fallback degrade).
    """
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=timeout).read()
        if len(data) < 5000:
            return None
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return dest
    except Exception:
        return None


def _cover_resize(img, width, height):
    """Redimensionne en 'cover' (recadre le surplus) vers width x height."""
    from PIL import Image
    scale = max(width / img.size[0], height / img.size[1])
    new_size = (max(1, round(img.size[0] * scale)),
                max(1, round(img.size[1] * scale)))
    img = img.resize(new_size, Image.LANCZOS)
    left = (img.size[0] - width) // 2
    top = (img.size[1] - height) // 2
    return img.crop((left, top, left + width, top + height))


IA_STYLE = ("dessin anime pedagogique pour enfants, style livre pour enfants, "
            "couleurs douces et lumineuses, personnages mignons et souriants, "
            "fond simple et lisible, aucune texte, aucune ecriture")


def _generate_ai_background(hint, dest, width=1280, height=720, timeout=45):
    """Illustration anime generee par IA (Pollinations.ai / FLUX, GRATUIT).

    Aucune cle API requise. Retourne le chemin si OK, None en cas d'echec
    (le pipeline retombe alors sur LoremFlickr / degrade).
    """
    if not hint:
        return None
    try:
        import io
        import urllib.parse
        import urllib.request
        from PIL import Image
        prompt = f"{str(hint).strip()[:120]}, {IA_STYLE}"
        seed = abs(hash(prompt)) % 1000000
        url = ("https://image.pollinations.ai/prompt/"
               + urllib.parse.quote(prompt)
               + f"?width={min(width, 1536)}&height={min(height, 1536)}"
               + f"&nologo=true&seed={seed}")
        req = urllib.request.Request(url, headers={"User-Agent": "Affilimax/1.0"})
        data = urllib.request.urlopen(req, timeout=timeout).read()
        if len(data) < 5000:
            return None
        img = Image.open(io.BytesIO(data)).convert("RGB")
        img = _cover_resize(img, width, height)
        dest.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest, "JPEG", quality=90)
        return dest
    except Exception as exc:
        print(f"[VF] Illustration IA indisponible ({exc}) -> fallback")
        return None


def _build_scene_image(scene, index, total, out_path, background_path=None):
    """Genere une image storyboard 1280x720.

    Si background_path est fourni (photo produit reelle), elle est utilisee
    comme fond (assombrie pour la lisibilite) avec le texte par-dessus.
    Sinon, degrade + formes + texte (fallback sans reseau).
    """
    from PIL import Image, ImageDraw, ImageEnhance

    W, H = 1280, 720
    image = None
    if background_path and background_path.exists():
        try:
            im = Image.open(background_path).convert("RGB")
            im = im.resize((W, H), Image.LANCZOS)
            im = ImageEnhance.Brightness(im).enhance(0.62)  # assombrir pour le texte
            image = im
        except Exception:
            image = None

    if image is None:
        try:
            import numpy as np
            top, bottom = _PALETTES[index % len(_PALETTES)]
            y = np.linspace(0, 1, H)[:, None, None]
            top_a = np.array(top, dtype=float)[None, None, :]
            bot_a = np.array(bottom, dtype=float)[None, None, :]
            grad = top_a * (1 - y) + bot_a * y
            img = np.tile(grad, (1, W, 1)).astype("uint8")
            image = Image.fromarray(img, "RGB")
        except Exception:
            top, bottom = _PALETTES[index % len(_PALETTES)]
            image = Image.new("RGB", (W, H), top)
            draw = ImageDraw.Draw(image)
            for yy in range(0, H, 8):
                t = yy / H
                color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
                draw.rectangle([0, yy, W, yy + 8], fill=color)
    draw = ImageDraw.Draw(image)

    # Decor : cercles doux
    rng = random.Random(index * 7919)
    for _ in range(14):
        cx = rng.randint(-80, W)
        cy = rng.randint(-80, H)
        r = rng.randint(30, 140)
        alpha_color = tuple(min(255, int(c * 0.10 + 40)) for c in (255, 255, 255))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=alpha_color, width=3)

    # Badge haut gauche (pastille sombre semi-transparente pour rester
    # lisible sur n'importe quel fond : photo, PIL, degrade)
    badge = f"AFFILIMAX STUDIO  |  SCENE {index + 1}/{total}"
    f_badge = _load_font(30)
    from PIL import Image as _PILImg, ImageDraw as _PILDr
    _ov = _PILImg.new("RGBA", (W, H), (0, 0, 0, 0))
    _od = _PILDr.Draw(_ov)
    _bw = int(_od.textlength(badge, font=f_badge))
    _od.rounded_rectangle([36, 28, 52 + _bw + 16, 86], radius=14, fill=(5, 5, 20, 170))
    image = _PILImg.alpha_composite(image.convert("RGBA"), _ov).convert("RGB")
    draw = _PILDr.Draw(image)
    draw.text((48, 40), badge, font=f_badge, fill=(255, 255, 255))

    # Gros numero (contour sombre pour rester lisible sur tout fond)
    f_num = _load_font(190)
    draw.text((W - 260, 30), f"{index + 1:02d}", font=f_num, fill=(255, 255, 255),
              stroke_width=8, stroke_fill=(10, 10, 35))

    # Titre de scene
    f_title = _load_font(64)
    title = str(scene.get("titre") or f"Scene {index + 1}")[:42]
    draw.text((48, 250), title.upper(), font=f_title, fill=(255, 224, 130))

    # Narration (texte enroule)
    f_body = _load_font(34)
    narration = str(scene.get("narration") or "")
    lines = _wrap_text(draw, narration, f_body, W - 120)[:5]
    yy = 380
    for line in lines:
        draw.text((48, yy), line, font=f_body, fill=(245, 245, 255))
        yy += 52

    # Prompt image (bas de l'image)
    f_small = _load_font(24)
    prompt = str(scene.get("prompt_image") or "")[:140]
    p_lines = _wrap_text(draw, "[IMAGE] " + prompt, f_small, W - 120)[:2]
    yy = H - 120
    for line in p_lines:
        draw.text((48, yy), line, font=f_small, fill=(200, 200, 230))
        yy += 34

    image.save(out_path, "PNG")


def _build_scene_images(script, job_dir):
    img_dir = job_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    scenes = script.get("scenes") or []
    paths = []

    # Image de fond reelle et COHERENTE avec le contenu :
    #   - produit (catalogue) -> photo du vrai produit
    #   - lecon pedagogique -> photo du theme (nombres, couleurs, animaux...)
    #   - histoire enfant -> photo du personnage/univers (renard, dragon...)
    background_path = None
    product_name = script.get("produit") or script.get("product_name") or ""
    if product_name:
        url = _load_product_image_url(product_name)
        if url:
            bg_dest = job_dir / "images" / "background.jpg"
            background_path = _download_background(url, bg_dest)
    else:
        # 1) Miniature locale VERIFIEE (histoires) -> 100% coherente,
        #    jamais de photo hors-sujet (LoremFlickr est instable).
        local_bg = _theme_background_local(script)
        if local_bg:
            background_path = local_bg
            print(f"[VF] Fond theme local (verifie): {local_bg.name}")
        else:
            # 2) Lecon pedagogique -> fond PIL dessine (chiffres, couleurs,
            #    formes...). 100%% coherent, sans reseau, toujours disponible.
            theme = str(script.get("theme") or "").strip().lower()
            bg_dest = job_dir / "images" / "background.jpg"
            pil_bg = _lesson_background_pil(theme, bg_dest)
            if pil_bg:
                background_path = pil_bg
                print(f"[VF] Fond pedagogique PIL pour lecon '{theme}'")
            else:
                # 3) Illustration IA (Pollinations, GRATUIT) : dessin anime
                #    coherent avec le theme (personnage, univers...)
                ai_bg = _generate_ai_background(theme, bg_dest)
                if ai_bg:
                    background_path = ai_bg
                    print(f"[VF] Illustration IA Pollinations pour '{theme}'")
                else:
                    # 4) Dernier recours : photo LoremFlickr avec lock stable
                    keywords, lock = _theme_keywords(script)
                    if keywords:
                        url = f"https://loremflickr.com/1280/720/{keywords}?lock={lock}"
                        background_path = _download_background(url, bg_dest)
                        if background_path:
                            print(f"[VF] Fond theme '{script.get('theme')}': {keywords}")

    for i, scene in enumerate(scenes):
        out = img_dir / f"scene_{i + 1:02d}.png"
        _build_scene_image(scene, i, len(scenes), out, background_path=background_path)
        paths.append(out)
    return paths


# ==================== VOIX IA (edge-tts) ====================

def _tts_one(text, voice, out_path):
    """Synthetise un fichier mp3 avec edge-tts (asynchrone)."""
    ok, _ = _tts_one_with_timings(text, voice, out_path)
    return ok


def _tts_one_with_timings(text, voice, out_path):
    """Synthetise un mp3 et capture les timings par mot (WordBoundary).

    Retourne (ok, words) ou words est une liste de {"w", "t", "d"}
    (mot, debut en secondes, duree en secondes). Ces timings servent
    a generer les sous-titres SRT synchronises sur la narration.
    """
    try:
        import edge_tts
    except ImportError:
        return False, []
    words = []
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.exists():
            out_path.unlink()

        async def _run():
            nonlocal words
            comm = edge_tts.Communicate(text, voice)
            async for chunk in comm.stream():
                ctype = (chunk.get("type") or "").lower()
                if ctype == "wordboundary":
                    # edge-tts exprime offset/duration en unites de 100 ns
                    off = (chunk.get("offset", 0) or 0) / 1e7
                    dur = (chunk.get("duration", 0) or 0) / 1e7
                    txt = (chunk.get("text") or "").strip()
                    if txt:
                        words.append({"w": txt, "t": round(off, 3), "d": round(max(dur, 0.05), 3)})
                elif ctype == "sentenceboundary":
                    # edge-tts >= 7.2 : n'emet plus de WordBoundary mais des
                    # SentenceBoundary (phrase + offset/duration globaux).
                    # On decoupe la phrase en mots et on repartit la duree
                    # proportionnellement a la longueur de chaque mot pour
                    # conserver des sous-titres mot-a-mot synchronises.
                    off = (chunk.get("offset", 0) or 0) / 1e7
                    dur = (chunk.get("duration", 0) or 0) / 1e7
                    txt = (chunk.get("text") or "").strip()
                    if txt and dur > 0:
                        parts = txt.split()
                        total_len = sum(len(p) for p in parts) or 1
                        cursor = off
                        for p in parts:
                            wdur = max(dur * len(p) / total_len, 0.05)
                            words.append({"w": p, "t": round(cursor, 3), "d": round(wdur, 3)})
                            cursor += wdur
                elif ctype == "audio":
                    with open(out_path, "ab") as f:
                        f.write(chunk["data"])

        asyncio.run(_run())
        ok = out_path.exists() and out_path.stat().st_size > 500
        return ok, words
    except Exception as e:
        print(f"[VF] TTS erreur: {e}")
        return False, []


def _generate_voiceover(scenes, voice_key, job_dir):
    """Genere la narration + les timings par mot de chaque scene.

    Retourne (paths, timings) : paths = liste de chemins audio (None si KO),
    timings = liste de listes de mots {"w", "t", "d"} alignee sur paths.
    """
    voice = VOICES.get(voice_key, voice_key if voice_key else DEFAULT_VOICE)
    audio_dir = job_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    paths, timings = [], []
    ok_count = 0
    for i, scene in enumerate(scenes):
        narration = scene.get("narration") or ""
        if not narration:
            paths.append(None)
            timings.append([])
            continue
        out = audio_dir / f"scene_{i + 1:02d}.mp3"
        ok, words = _tts_one_with_timings(narration, voice, out)
        if ok:
            paths.append(out)
            timings.append(words)
            ok_count += 1
        else:
            paths.append(None)
            timings.append([])
    return paths, timings


# ==================== SOUS-TITRES (SRT + incrustation) ====================

def _fmt_srt_ts(seconds):
    """Formate une duree en secondes au format SRT (HH:MM:SS,mmm)."""
    seconds = max(0.0, float(seconds))
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms >= 1000:
        ms = 0
        seconds += 1
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _group_words_to_lines(words, max_chars=42, max_words=9, max_span=5.0):
    """Regroupe des mots horodates en lignes de sous-titres lisibles.

    Casse une ligne a la ponctuation forte, ou si elle devient trop
    longue (caracteres, nombre de mots ou duree maximale).
    """
    lines = []
    cur, cur_start, cur_end = [], None, None
    for w in words:
        wt = float(w.get("t", 0.0))
        wd = float(w.get("d", 0.5))
        if cur_start is None:
            cur_start = wt
        cur_end = wt + wd
        cur.append(w.get("w", ""))
        text = " ".join(cur)
        last = cur[-1] or ""
        if len(cur) >= max_words or len(text) > max_chars or (cur_end - cur_start) > max_span:
            lines.append({"start": round(cur_start, 3), "end": round(cur_end, 3), "text": " ".join(cur)})
            cur, cur_start, cur_end = [], None, None
        elif last and last[-1] in ".!?…":
            lines.append({"start": round(cur_start, 3), "end": round(cur_end, 3), "text": " ".join(cur)})
            cur, cur_start, cur_end = [], None, None
    if cur:
        lines.append({"start": round(cur_start, 3), "end": round(cur_end, 3), "text": " ".join(cur)})
    return lines


def _audio_durations(audios, padding=0.6, fallback=6.0):
    """Duree de chaque scene (voix + 0.6 s, ou 6 s par defaut si voix absente)."""
    from moviepy import AudioFileClip
    durs = []
    for a in audios:
        if a and a.exists():
            try:
                ac = AudioFileClip(str(a))
                try:
                    durs.append(ac.duration + padding)
                finally:
                    ac.close()
                continue
            except Exception:
                pass
        durs.append(fallback)
    return durs


def _build_srt(scenes, timings_by_scene, scene_offsets):
    """Construit les entrees SRT (temps absolus) depuis les timings par scene."""
    entries = []
    for i, words in enumerate(timings_by_scene):
        off = scene_offsets[i] if i < len(scene_offsets) else 0.0
        abs_words = [{"w": w["w"], "t": w["t"] + off, "d": w["d"]} for w in words]
        for line in _group_words_to_lines(abs_words):
            entries.append(line)
    entries.sort(key=lambda e: e["start"])
    # fusion des lignes identiques consecutives
    merged = []
    for e in entries:
        if merged and merged[-1]["text"] == e["text"] and abs(e["start"] - merged[-1]["end"]) < 0.05:
            merged[-1]["end"] = max(merged[-1]["end"], e["end"])
        else:
            merged.append(dict(e))
    return merged


def _srt_text(entries):
    """Serialise les entrees au format SRT standard (UTF-8)."""
    blocks = []
    for i, e in enumerate(entries, 1):
        blocks.append(f"{i}\n{_fmt_srt_ts(e['start'])} --> {_fmt_srt_ts(e['end'])}\n{e['text']}\n")
    return "\n".join(blocks)


def _draw_subtitle(text, base_img, font_size=46, width=1280):
    """Dessine un sous-titre sur l'image de scene (bandeau sombre arrondi).

    Retourne une nouvelle image RGB : image de scene + bandeau + texte.
    Utilise par le montage comme overlay opaque (pas de masque moviepy).
    """
    from PIL import Image, ImageDraw
    font = _load_font(font_size)
    base = base_img.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    pad_x, pad_y = 26, 14
    lines = _wrap_text(d, text, font, width - 280)
    line_h = font_size + pad_y * 2
    total_h = line_h * len(lines)
    y0 = base.size[1] - total_h - 44
    # bandeaux arrondis (d'abord, pour mesurer la largeur du texte)
    for li, ln in enumerate(lines):
        bw = int(d.textlength(ln, font=font)) + pad_x * 2
        bx = (base.size[0] - bw) // 2
        by = y0 + li * line_h
        d.rounded_rectangle([bx, by, bx + bw, by + line_h], radius=12, fill=(0, 0, 0, 160))
    # texte avec ombre portee
    for li, ln in enumerate(lines):
        tw = d.textlength(ln, font=font)
        tx = (base.size[0] - tw) / 2
        ty = y0 + li * line_h + pad_y
        d.text((tx + 2, ty + 2), ln, font=font, fill=(0, 0, 0, 235))
        d.text((tx, ty), ln, font=font, fill=(255, 255, 255, 255))
    return Image.alpha_composite(base, overlay).convert("RGB")


# ==================== MONTAGE MP4 (moviepy) ====================

_SILENCE_CACHE = {}
_SILENCE_LOCK = threading.Lock()


def _silence(duration, fps=44100):
    """Clip audio silencieux MONO (fallback si la voix d'une scene manque).

    Retourne un AudioFileClip d'un VRAI fichier mp3 silencieux genere une
    fois par duree via le FFmpeg embarque (imageio-ffmpeg). Pourquoi un
    fichier : dans cette version de moviepy, concatener des AudioClip custom
    (make_frame) produit un flux audio a la duree fausse (2x voire enorme),
    qui gonfle le conteneur MP4 et desynchronise les sous-titres. Le chemin
    "fichier" (AudioFileClip) est celui valide par les narrations reelles.
    """
    import subprocess
    duration = max(0.5, float(duration))
    key = round(duration, 1)
    with _SILENCE_LOCK:
        path = _SILENCE_CACHE.get(key)
    if not path or not Path(path).exists():
        try:
            import imageio_ffmpeg
            ff = imageio_ffmpeg.get_ffmpeg_exe()
            out = BASE_DIR / "video_factory" / "assets" / f"silence_{key}s.mp3"
            out.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [ff, "-y", "-hide_banner", "-loglevel", "error",
                 "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                 "-t", f"{key + 0.1:.1f}", "-c:a", "libmp3lame", "-q:a", "9",
                 str(out)],
                capture_output=True, timeout=60,
            )
            if out.exists() and out.stat().st_size > 100:
                with _SILENCE_LOCK:
                    _SILENCE_CACHE[key] = str(out)
                path = str(out)
        except Exception as e:
            print(f"[VF] generation silence: {e}")
            path = None
    if path:
        try:
            from moviepy import AudioFileClip
            return AudioFileClip(path)
        except Exception as e:
            print(f"[VF] AudioFileClip silence: {e}")
    # dernier recours : AudioClip custom (peut fausser la duree du conteneur)
    import numpy as np
    from moviepy import AudioClip

    def _frame(t):
        return np.zeros(len(np.atleast_1d(t)), dtype="float32")

    return AudioClip(_frame, duration=duration, fps=fps)


def _render_video(images, audios, out_path, scenes, fps=24, sub_entries=None):
    """Assemble le diaporama + narration en MP4 (via imageio-ffmpeg embarquee).

    Si sub_entries est fourni (liste {"start", "end", "text"} en temps
    absolus), chaque sous-titre est incruste sur l'image de sa scene via un
    overlay PIL opaque (aucune dependance libass / ImageMagick).
    """
    import numpy as np
    from PIL import Image as PILImage
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip

    clips = []
    off = 0.0
    for i, img in enumerate(images):
        aud = audios[i] if i < len(audios) else None
        audio = None
        if aud and aud.exists():
            try:
                audio = AudioFileClip(str(aud))
            except Exception as e:
                print(f"[VF] AudioFileClip erreur scene {i + 1}: {e}")
                audio = None
        dur = (audio.duration + 0.6) if audio is not None else 6.0
        base_pil = PILImage.open(str(img)).convert("RGB")
        base_clip = ImageClip(np.array(base_pil)).with_duration(dur)
        base_clip = base_clip.with_audio(audio if audio is not None else _silence(dur))

        scene_clip = base_clip
        if sub_entries:
            overlays = []
            for e in sub_entries:
                if e["start"] >= off + dur or e["end"] <= off:
                    continue
                s0 = max(e["start"], off)
                s1 = min(e["end"], off + dur)
                if s1 - s0 <= 0.05:
                    continue
                frame = _draw_subtitle(e["text"], base_pil)
                oc = ImageClip(np.array(frame)).with_duration(s1 - s0).with_start(s0 - off)
                overlays.append(oc)
            if overlays:
                scene_clip = CompositeVideoClip([base_clip] + overlays, size=base_clip.size)
                scene_clip = scene_clip.with_audio(base_clip.audio)
        clips.append(scene_clip)
        off += dur

    if not clips:
        raise RuntimeError("Aucune scene a monter")

    final = concatenate_videoclips(clips, method="chain")
    # Fichier temp AUDIO UNIQUE par job : evite le conflit WinError 32
    # quand plusieurs montages tournent en parallele (moviepy ecrit
    # sinon dans un meme videoTEMP_MPY_wvf_snd.mp4 partage).
    temp_audio = str(out_path.parent / f"temp_audio_{out_path.stem}.m4a")
    final.write_videofile(
        str(out_path),
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        temp_audiofile=temp_audio,
        remove_temp=True,
        logger=None,
    )
    return out_path


# ==================== PIPELINE (JOB) ====================

def _run_job(job_id):
    job = _JOBS[job_id]
    kind = job["kind"]
    p = job["params"]
    try:
        job_dir = OUTPUT_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        # 1. Script IA
        _set_progress(job, 5, "Ecriture du script IA...")
        _log(job, "Script IA en cours...")
        if kind == "product":
            script = generate_product_script(
                find_product(p.get("product")),
                scenes=int(p.get("scenes", 5)),
                style=p.get("style", "testeur"),
                duration=p.get("duration", "60s"),
            )
        elif kind == "lesson":
            script = generate_children_lesson(
                p.get("theme", "compter"),
                scenes=int(p.get("scenes", 6)),
                duration=DURATION_LABELS.get(p.get("duration", "5min"), p.get("duration", "5min")),
            )
        else:
            script = generate_children_story(
                p.get("theme", ""),
                scenes=int(p.get("scenes", 5)),
                duration=DURATION_LABELS.get(p.get("duration", "5min"), p.get("duration", "5min")),
            )
        if "error" in script:
            raise RuntimeError(script["error"])
        job["title"] = script.get("titre") or script.get("seo", {}).get("titre_youtube", "")
        script_path = job_dir / "script.json"
        script_path.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
        job["files"]["script"] = f"video_factory/output/{job_id}/script.json"
        _set_progress(job, 15, "Script genere")
        _log(job, f"Script genere ({script.get('mode', '')}) - {len(script.get('scenes', []))} scenes")

        # 2. Storyboard images
        _set_progress(job, 20, "Generation du storyboard...")
        _log(job, "Storyboard images (PIL)...")
        images = _build_scene_images(script, job_dir)
        _set_progress(job, 45, "Storyboard termine")
        _log(job, f"{len(images)} images generees")

        # 3. Voix IA
        _set_progress(job, 50, "Synthese vocale...")
        _log(job, "Voix IA (edge-tts)...")
        audios, word_timings = _generate_voiceover(script.get("scenes", []), p.get("voice"), job_dir)
        ok_voices = sum(1 for a in audios if a is not None)
        _set_progress(job, 72, "Voix terminee")
        _log(job, f"Voix IA: {ok_voices}/{len(audios)} scenes")

        # 3b. Sous-titres SRT (timings edge-tts) + incrustation
        subtitles_on = p.get("subtitles", True)
        if isinstance(subtitles_on, str):
            subtitles_on = subtitles_on.lower() in ("1", "true", "on", "oui", "yes")
        sub_entries = []
        if subtitles_on:
            _set_progress(job, 74, "Generation des sous-titres SRT...")
            _log(job, "Sous-titres SRT (timings edge-tts)...")
            durs = _audio_durations(audios)
            offsets = []
            acc = 0.0
            for d in durs:
                offsets.append(acc)
                acc += d
            sub_entries = _build_srt(script.get("scenes", []), word_timings, offsets)
            if sub_entries:
                srt_path = job_dir / "subtitles.srt"
                srt_path.write_text(_srt_text(sub_entries), encoding="utf-8")
                job["files"]["srt"] = f"video_factory/output/{job_id}/subtitles.srt"
                _log(job, f"Sous-titres: {len(sub_entries)} lignes (incrustes dans la video)")
            else:
                _log(job, "Sous-titres: aucun timing disponible, ignores")

        # 4. Montage MP4 (+ incrustation sous-titres)
        _set_progress(job, 78, "Montage video MP4 + sous-titres...")
        _log(job, "Montage (moviepy + ffmpeg)...")
        video_path = job_dir / "video.mp4"
        _render_video(images, audios, video_path, script.get("scenes", []), sub_entries=sub_entries)
        job["files"]["video"] = f"video_factory/output/{job_id}/video.mp4"
        _set_progress(job, 100, "Video terminee")
        _log(job, "Video MP4 terminee")

        job["status"] = "done"
        _notify(job_id, "done", {"status": "done", "title": job["title"], "video": job["files"]["video"]})
    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)
        job["step"] = "Erreur"
        _log(job, f"ERREUR: {e}")
        print(f"[VF] Job {job_id} erreur: {e}")
        _notify(job_id, "error", {"status": "error", "error": str(e)})
    finally:
        job["finished_at"] = datetime.utcnow().isoformat() + "Z"
        _save_history()


# ==================== HEALTH CHECK ====================

def health_check():
    """Etat du module : IA, voix, ffmpeg, dossiers."""
    ffmpeg_ok = False
    ffmpeg_path = None
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_ok = bool(ffmpeg_path)
    except Exception:
        pass

    tts_ok = False
    try:
        import edge_tts
        tts_ok = True
    except Exception:
        pass

    from ai_automator import health_check as ai_health
    ai = ai_health()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "ok": True,
        "ia": ai,
        "tts": {"ready": tts_ok, "voices": list(VOICES.keys()) if tts_ok else []},
        "ffmpeg": {"ready": ffmpeg_ok, "path": ffmpeg_path},
        "output_dir": str(OUTPUT_DIR),
        "output_writable": os.access(OUTPUT_DIR, os.W_OK),
        "videos_total": sum(1 for j in list_jobs() if j.get("files", {}).get("video")),
    }


# ==================== CLI ====================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Affilimax - Video Factory")
    parser.add_argument("--script", action="store_true", help="Generer un script produit")
    parser.add_argument("--story", action="store_true", help="Generer une histoire enfant")
    parser.add_argument("--pipeline", action="store_true", help="Lancer le pipeline complet (MP4)")
    parser.add_argument("--kind", default="product", choices=["product", "story", "lesson"])
    parser.add_argument("--product", type=str, help="Nom ou slug du produit")
    parser.add_argument("--theme", type=str, default="un petit renard", help="Theme de l'histoire")
    parser.add_argument("--duration", default="60s", help="Duree cible (30s, 60s, 3min, 5min, 10min)")
    parser.add_argument("--style", default="testeur", help="Style (testeur, storytelling, educatif, fun)")
    parser.add_argument("--scenes", type=int, default=4, help="Nombre de scenes")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="Voix edge-tts")
    parser.add_argument("--no-subtitles", action="store_true", help="Desactiver les sous-titres SRT")
    parser.add_argument("--health", action="store_true", help="Health check")

    args = parser.parse_args()

    if args.health:
        print(json.dumps(health_check(), indent=2, ensure_ascii=False))
        sys.exit(0)

    if args.pipeline:
        job = start_job(args.kind, {
            "product": args.product, "theme": args.theme,
            "duration": args.duration, "style": args.style,
            "scenes": args.scenes, "voice": args.voice,
            "subtitles": not args.no_subtitles,
        })
        print(f"Job demarre: {job['id']}")
        while True:
            time.sleep(1.5)
            cur = get_job(job["id"])
            print(f"\r[{cur['status']}] {cur['progress']}% - {cur['step']}   ", end="", flush=True)
            if cur["status"] in ("done", "error"):
                print()
                print("Fichiers:", cur["files"])
                print("Log:", json.dumps(cur["log"], ensure_ascii=False, indent=2))
                break
        sys.exit(0)

    if args.script:
        result = generate_product_script(find_product(args.product), scenes=args.scenes,
                                         style=args.style, duration=args.duration)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    if args.story:
        result = generate_children_story(args.theme, scenes=args.scenes, duration=args.duration)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    parser.print_help()
