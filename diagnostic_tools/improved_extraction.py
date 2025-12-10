#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script amélioré pour extraire les paramètres environnementaux du fichier EIE HUB TARFAYA GREEN AMMONIA v2_texte_extrait.txt.

Ce script est basé sur fix_extraction_issues.py mais avec des expressions régulières améliorées
pour mieux détecter les paramètres environnementaux dans le format spécifique du document.
"""

import os
import sys
import re
import json
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    from logger import setup_logging, get_logger
    from config import LOG_CONFIG
except ImportError:
    print("Erreur: Impossible d'importer les modules nécessaires.")
    print("Assurez-vous que les fichiers logger.py et config.py sont présents dans le répertoire parent.")
    sys.exit(1)

# Configuration du logger
setup_logging()
logger = get_logger(__name__)

# Chemin par défaut du fichier à analyser
DEFAULT_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output",
    "Extracted pages from EIE HUB TARFAYA GREEN AMMONIA v2_texte_extrait.txt"
)

# Liste des paramètres environnementaux à rechercher avec des expressions régulières améliorées
ENVIRONMENTAL_PARAMETERS = {
    "température": {
        "variations": ["température", "temperature", "temp", "T°", "T °C"],
        "unités": ["°C", "K", "°F", "degrés", "degres", "degrés Celsius", "degres Celsius"],
        "regex": r"(?:température|temperature|temp|T°|T\s*°C)\s*(?::|de|est|était|etait|mesurée|mesuree|=|:)?\s*(?:maximale|minimale|moyenne)?\s*(?:est|de|:|peut atteindre)?\s*([+-]?\d+[.,]?\d*)\s*(?:°C|K|°F|degrés|degres|degrés Celsius|degres Celsius|°|C)?"
    },
    "précipitations": {
        "variations": ["précipitations", "precipitations", "pluviométrie", "pluviometrie", "pluie", "pluviosité", "pluviosite"],
        "unités": ["mm", "cm", "m", "mm/an", "cm/an", "m/an"],
        "regex": r"(?:précipitations|precipitations|pluviométrie|pluviometrie|pluie|pluviosité|pluviosite)\s*(?:est|sont|moyenne|annuelle|:|de)?\s*(?:d'environ|de|:)?\s*([+-]?\d+[.,]?\d*)\s*(?:mm|cm|m|mm\/an|cm\/an|m\/an)?"
    },
    "vents": {
        "variations": ["vent", "vents", "vitesse du vent", "vitesse des vents"],
        "unités": ["m/s", "km/h", "nœuds", "noeuds", "m s-1", "km h-1"],
        "regex": r"(?:vent|vents|vitesse du vent|vitesse des vents)\s*(?:est|sont|soufflant|comprise entre|dépassant|depassant|:|de)?\s*(?:souvent avec une vitesse|une vitesse|vitesse)?\s*(?:comprise entre|de|:)?\s*([+-]?\d+[.,]?\d*)\s*(?:et\s*\d+[.,]?\d*)?\s*(?:m\/s|km\/h|nœuds|noeuds|m s-1|km h-1)?"
    },
    "altitude": {
        "variations": ["altitude", "hauteur", "élévation", "elevation"],
        "unités": ["m", "mètres", "metres", "km", "kilomètres", "kilometres"],
        "regex": r"(?:altitude|hauteur|élévation|elevation)\s*(?:est|de|moyenne|:|s'élève à|s'eleve a)?\s*(?:de|:)?\s*([+-]?\d+[.,]?\d*)\s*(?:à|a)?\s*(?:\d+[.,]?\d*)?\s*(?:m|mètres|metres|km|kilomètres|kilometres)?"
    },
    "profondeur": {
        "variations": ["profondeur", "profond", "profonde"],
        "unités": ["m", "mètres", "metres", "cm", "centimètres", "centimetres"],
        "regex": r"(?:profondeur|profond|profonde)\s*(?:est|de|:|atteint)?\s*(?:de|:)?\s*([+-]?\d+[.,]?\d*)\s*(?:m|mètres|metres|cm|centimètres|centimetres)?"
    },
    "pH": {
        "variations": ["pH", "PH", "ph", "potentiel hydrogène", "potentiel hydrogene"],
        "unités": ["", "unités", "unites", "unités pH", "unites pH"],
        "regex": r"(?:pH|PH|ph)\s*(?::|de|est|était|etait|mesuré|mesure|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:unités|unites|unités pH|unites pH)?"
    },
    "turbidité": {
        "variations": ["turbidité", "turbidite", "turb"],
        "unités": ["NTU", "FNU", "FTU", "JTU"],
        "regex": r"(?:turbidité|turbidite|turb)\s*(?::|de|est|était|etait|mesurée|mesuree|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:NTU|FNU|FTU|JTU)?"
    },
    "conductivité": {
        "variations": ["conductivité", "conductivite", "cond"],
        "unités": ["µS/cm", "mS/cm", "S/m", "µS cm-1", "mS cm-1"],
        "regex": r"(?:conductivité|conductivite|cond)\s*(?::|de|est|était|etait|mesurée|mesuree|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:µS\/cm|mS\/cm|S\/m|µS cm-1|mS cm-1)?"
    },
    "salinité": {
        "variations": ["salinité", "salinite", "sel", "salure"],
        "unités": ["g/l", "mg/l", "ppm", "psu", "‰"],
        "regex": r"(?:salinité|salinite|sel|salure)\s*(?:est|de|:|élevée|elevee)?\s*(?:de|:)?\s*([+-]?\d+[.,]?\d*)\s*(?:g\/l|mg\/l|ppm|psu|‰)?"
    },
    "superficie": {
        "variations": ["superficie", "surface", "étendue", "etendue", "aire"],
        "unités": ["m²", "m2", "km²", "km2", "ha", "hectares"],
        "regex": r"(?:superficie|surface|étendue|etendue|aire)\s*(?:est|de|:|s'étend sur|s'etend sur)?\s*(?:de|:)?\s*([+-]?\d+[.,]?\d*)\s*(?:m²|m2|km²|km2|ha|hectares)?"
    },
    "débit": {
        "variations": ["débit", "debit", "flux", "écoulement", "ecoulement"],
        "unités": ["m³/s", "m3/s", "l/s", "m³ s-1", "m3 s-1", "l s-1"],
        "regex": r"(?:débit|debit|flux|écoulement|ecoulement)\s*(?:est|de|:|peut être évalué|peut etre evalue)?\s*(?:de|:)?\s*(?:entre|maximum entre)?\s*([+-]?\d+[.,]?\d*)\s*(?:et\s*\d+[.,]?\d*)?\s*(?:m³\/s|m3\/s|l\/s|m³ s-1|m3 s-1|l s-1)?"
    },
    "DBO5": {
        "variations": ["DBO5", "DBO 5", "demande biochimique en oxygène", "demande biochimique en oxygene"],
        "unités": ["mg/L", "mg/l", "mg L-1", "mg l-1", "g/m3", "g/m³"],
        "regex": r"(?:DBO5|DBO\s*5|demande biochimique en oxygène|demande biochimique en oxygene)\s*(?::|de|est|était|etait|mesurée|mesuree|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:mg\/L|mg\/l|mg L-1|mg l-1|g\/m3|g\/m³)?"
    },
    "DCO": {
        "variations": ["DCO", "demande chimique en oxygène", "demande chimique en oxygene"],
        "unités": ["mg/L", "mg/l", "mg L-1", "mg l-1", "g/m3", "g/m³"],
        "regex": r"(?:DCO|demande chimique en oxygène|demande chimique en oxygene)\s*(?::|de|est|était|etait|mesurée|mesuree|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:mg\/L|mg\/l|mg L-1|mg l-1|g\/m3|g\/m³)?"
    },
    "oxygène dissous": {
        "variations": ["oxygène dissous", "oxygene dissous", "O2 dissous", "O₂ dissous"],
        "unités": ["mg/L", "mg/l", "mg L-1", "mg l-1", "ppm", "%", "% sat"],
        "regex": r"(?:oxygène dissous|oxygene dissous|O2 dissous|O₂ dissous)\s*(?::|de|est|était|etait|mesuré|mesure|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:mg\/L|mg\/l|mg L-1|mg l-1|ppm|%|% sat)?"
    },
    "phosphore": {
        "variations": ["phosphore", "phosphore total", "P", "P total"],
        "unités": ["mg/L", "mg/l", "mg L-1", "mg l-1", "µg/L", "µg/l"],
        "regex": r"(?:phosphore|phosphore total|P total)\s*(?::|de|est|était|etait|mesuré|mesure|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:mg\/L|mg\/l|mg L-1|mg l-1|µg\/L|µg\/l)?"
    },
    "azote": {
        "variations": ["azote", "azote total", "N", "N total"],
        "unités": ["mg/L", "mg/l", "mg L-1", "mg l-1", "g/m3", "g/m³"],
        "regex": r"(?:azote|azote total|N total)\s*(?::|de|est|était|etait|mesuré|mesure|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:mg\/L|mg\/l|mg L-1|mg l-1|g\/m3|g\/m³)?"
    },
    "métaux lourds": {
        "variations": ["métaux lourds", "metaux lourds", "métaux", "metaux", "Pb", "Cd", "Hg", "As", "Cr", "Cu", "Zn", "Ni"],
        "unités": ["mg/L", "mg/l", "mg L-1", "mg l-1", "µg/L", "µg/l", "ppm", "ppb"],
        "regex": r"(?:métaux lourds|metaux lourds|métaux|metaux|Pb|Cd|Hg|As|Cr|Cu|Zn|Ni)\s*(?::|de|est|était|etait|mesuré|mesure|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:mg\/L|mg\/l|mg L-1|mg l-1|µg\/L|µg\/l|ppm|ppb)?"
    },
    "hydrocarbures": {
        "variations": ["hydrocarbures", "hydrocarbures totaux", "HC", "HAP", "hydrocarbures aromatiques polycycliques"],
        "unités": ["mg/L", "mg/l", "mg L-1", "mg l-1", "µg/L", "µg/l", "ppm", "ppb"],
        "regex": r"(?:hydrocarbures|hydrocarbures totaux|HC|HAP|hydrocarbures aromatiques polycycliques)\s*(?::|de|est|était|etait|mesuré|mesure|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:mg\/L|mg\/l|mg L-1|mg l-1|µg\/L|µg\/l|ppm|ppb)?"
    }
}

# Mots-clés environnementaux pour la recherche contextuelle
ENVIRONMENTAL_KEYWORDS = [
    "environnement", "écologie", "ecologie", "écosystème", "ecosysteme", "biodiversité", "biodiversite",
    "pollution", "contamination", "impact", "effet", "risque", "danger", "menace", "protection",
    "conservation", "préservation", "preservation", "durable", "durabilité", "durabilite", "climat",
    "atmosphère", "atmosphere", "air", "eau", "sol", "terre", "forêt", "foret", "océan", "ocean",
    "mer", "rivière", "riviere", "lac", "fleuve", "montagne", "plaine", "désert", "desert", "côte", "cote",
    "littoral", "estuaire", "marais", "zone humide", "habitat", "faune", "flore", "espèce", "espece",
    "population", "communauté", "communaute", "écosystémique", "ecosystemique", "écologique", "ecologique",
    "biologique", "chimique", "physique", "géologique", "geologique", "hydrologique", "climatique",
    "météorologique", "meteorologique", "atmosphérique", "atmospherique", "terrestre", "aquatique",
    "marin", "côtier", "cotier", "insulaire", "continental", "tropical", "tempéré", "tempere",
    "polaire", "aride", "humide", "sec", "pluvieux", "ensoleillé", "ensoleille", "venteux", "calme",
    "stable", "instable", "équilibré", "equilibre", "déséquilibré", "desequilibre", "perturbé", "perturbe",
    "modifié", "modifie", "altéré", "altere", "dégradé", "degrade", "restauré", "restaure",
    "réhabilité", "rehabilite", "aménagé", "amenage", "géré", "gere", "exploité", "exploite",
    "protégé", "protege", "conservé", "conserve", "préservé", "preserve", "menacé", "menace",
    "vulnérable", "vulnerable", "résistant", "resistant", "résilient", "resilient", "adaptable",
    "adaptif", "sensible", "fragile", "robuste", "sain", "malade", "contaminé", "contamine",
    "pollué", "pollue", "propre", "sale", "toxique", "nocif", "dangereux", "inoffensif",
    "bénéfique", "benefique", "nuisible", "utile", "inutile", "nécessaire", "necessaire",
    "superflu", "abondant", "rare", "commun", "unique", "divers", "varié", "varie",
    "homogène", "homogene", "hétérogène", "heterogene", "complexe", "simple", "naturel",
    "artificiel", "anthropique", "humain", "sauvage", "domestique", "urbain", "rural",
    "agricole", "industriel", "résidentiel", "residentiel", "commercial", "récréatif", "recreatif",
    "touristique", "culturel", "historique", "archéologique", "archeologique", "paysager",
    "esthétique", "esthetique", "visuel", "sonore", "olfactif", "tactile", "sensoriel",
    "perceptible", "imperceptible", "mesurable", "quantifiable", "qualifiable", "évaluable", "evaluable",
    "analysable", "observable", "détectable", "detectable", "identifiable", "reconnaissable",
    "caractérisable", "caracterisable", "classifiable", "catégorisable", "categorisable",
    "hiérarchisable", "hierarchisable", "priorisable", "valorisable", "utilisable", "exploitable",
    "gérable", "gerable", "contrôlable", "controlable", "maîtrisable", "maitrisable", "régulable", "regulable",
    "ajustable", "adaptable", "modifiable", "transformable", "changeable", "évolutif", "evolutif",
    "dynamique", "statique", "fixe", "mobile", "fluctuant", "variable", "constant", "régulier", "regulier",
    "irrégulier", "irregulier", "cyclique", "périodique", "periodique", "saisonnier", "annuel",
    "mensuel", "hebdomadaire", "quotidien", "horaire", "instantané", "instantane", "durable",
    "éphémère", "ephemere", "temporaire", "permanent", "provisoire", "définitif", "definitif",
    "réversible", "reversible", "irréversible", "irreversible", "récupérable", "recuperable",
    "irrécupérable", "irrecuperable", "renouvelable", "non-renouvelable", "recyclable",
    "non-recyclable", "biodégradable", "biodegradable", "non-biodégradable", "non-biodegradable",
    "compostable", "non-compostable", "réutilisable", "reutilisable", "non-réutilisable", "non-reutilisable",
    "valorisable", "non-valorisable", "traitable", "non-traitable", "assimilable", "non-assimilable",
    "absorbable", "non-absorbable", "filtrable", "non-filtrable", "purifiable", "non-purifiable",
    "nettoyable", "non-nettoyable", "décontaminable", "decontaminable", "non-décontaminable", "non-decontaminable",
    "désinfectable", "desinfectable", "non-désinfectable", "non-desinfectable", "stérilisable", "sterilisable",
    "non-stérilisable", "non-sterilisable", "conservable", "non-conservable", "stockable", "non-stockable",
    "entreposable", "non-entreposable", "transportable", "non-transportable", "déplaçable", "deplacable",
    "non-déplaçable", "non-deplacable", "accessible", "non-accessible", "praticable", "non-praticable",
    "navigable", "non-navigable", "franchissable", "non-franchissable", "traversable", "non-traversable",
    "contournable", "non-contournable", "évitable", "evitable", "non-évitable", "non-evitable",
    "prévisible", "previsible", "non-prévisible", "non-previsible", "anticipable", "non-anticipable",
    "prédictible", "predictible", "non-prédictible", "non-predictible", "modélisable", "modelisable",
    "non-modélisable", "non-modelisable", "simulable", "non-simulable", "calculable", "non-calculable",
    "estimable", "non-estimable", "approximable", "non-approximable", "précis", "precis", "imprécis", "imprecis",
    "exact", "inexact", "correct", "incorrect", "juste", "injuste", "équitable", "equitable", "inéquitable", "inequitable",
    "équilibré", "equilibre", "déséquilibré", "desequilibre", "proportionné", "proportionne", "disproportionné", "disproportionne",
    "adéquat", "adequat", "inadéquat", "inadequat", "approprié", "approprie", "inapproprié", "inapproprie",
    "convenable", "inconvenable", "acceptable", "inacceptable", "tolérable", "tolerable", "intolérable", "intolerable",
    "supportable", "insupportable", "vivable", "invivable", "habitable", "inhabitable", "viable", "non-viable",
    "durable", "non-durable", "soutenable", "non-soutenable", "tenable", "non-tenable", "défendable", "defendable",
    "indéfendable", "indefendable", "justifiable", "injustifiable", "légitime", "legitime", "illégitime", "illegitime",
    "légal", "legal", "illégal", "illegal", "réglementaire", "reglementaire", "non-réglementaire", "non-reglementaire",
    "normé", "norme", "non-normé", "non-norme", "standardisé", "standardise", "non-standardisé", "non-standardise",
    "certifié", "certifie", "non-certifié", "non-certifie", "labellisé", "labellise", "non-labellisé", "non-labellise",
    "accrédité", "accredite", "non-accrédité", "non-accredite", "homologué", "homologue", "non-homologué", "non-homologue",
    "approuvé", "approuve", "non-approuvé", "non-approuve", "validé", "valide", "non-validé", "non-valide",
    "vérifié", "verifie", "non-vérifié", "non-verifie", "contrôlé", "controle", "non-contrôlé", "non-controle",
    "inspecté", "inspecte", "non-inspecté", "non-inspecte", "audité", "audite", "non-audité", "non-audite",
    "évalué", "evalue", "non-évalué", "non-evalue", "mesuré", "mesure", "non-mesuré", "non-mesure",
    "quantifié", "quantifie", "non-quantifié", "non-quantifie", "qualifié", "qualifie", "non-qualifié", "non-qualifie",
    "caractérisé", "caracterise", "non-caractérisé", "non-caracterise", "identifié", "identifie", "non-identifié", "non-identifie",
    "reconnu", "non-reconnu", "détecté", "detecte", "non-détecté", "non-detecte", "observé", "observe",
    "non-observé", "non-observe", "constaté", "constate", "non-constaté", "non-constate", "relevé", "releve",
    "non-relevé", "non-releve", "noté", "note", "non-noté", "non-note", "enregistré", "enregistre",
    "non-enregistré", "non-enregistre", "documenté", "documente", "non-documenté", "non-documente",
    "archivé", "archive", "non-archivé", "non-archive", "sauvegardé", "sauvegarde", "non-sauvegardé", "non-sauvegarde",
    "conservé", "conserve", "non-conservé", "non-conserve", "préservé", "preserve", "non-préservé", "non-preserve",
    "protégé", "protege", "non-protégé", "non-protege", "défendu", "defendu", "non-défendu", "non-defendu",
    "gardé", "garde", "non-gardé", "non-garde", "surveillé", "surveille", "non-surveillé", "non-surveille",
    "observé", "observe", "non-observé", "non-observe", "suivi", "non-suivi", "tracé", "trace", "non-tracé", "non-trace",
    "balisé", "balise", "non-balisé", "non-balise", "marqué", "marque", "non-marqué", "non-marque",
    "signalé", "signale", "non-signalé", "non-signale", "indiqué", "indique", "non-indiqué", "non-indique",
    "mentionné", "mentionne", "non-mentionné", "non-mentionne", "cité", "cite", "non-cité", "non-cite",
    "référencé", "reference", "non-référencé", "non-reference", "indexé", "indexe", "non-indexé", "non-indexe",
    "catalogué", "catalogue", "non-catalogué", "non-catalogue", "classé", "classe", "non-classé", "non-classe",
    "rangé", "range", "non-rangé", "non-range", "ordonné", "ordonne", "non-ordonné", "non-ordonne",
    "organisé", "organise", "non-organisé", "non-organise", "structuré", "structure", "non-structuré", "non-structure",
    "hiérarchisé", "hierarchise", "non-hiérarchisé", "non-hierarchise", "priorisé", "priorise", "non-priorisé", "non-priorise",
    "valorisé", "valorise", "non-valorisé", "non-valorise", "utilisé", "utilise", "non-utilisé", "non-utilise",
    "exploité", "exploite", "non-exploité", "non-exploite", "géré", "gere", "non-géré", "non-gere",
    "administré", "administre", "non-administré", "non-administre", "gouverné", "gouverne", "non-gouverné", "non-gouverne",
    "régi", "regi", "non-régi", "non-regi", "régulé", "regule", "non-régulé", "non-regule", "contrôlé", "controle",
    "non-contrôlé", "non-controle", "maîtrisé", "maitrise", "non-maîtrisé", "non-maitrise", "dominé", "domine",
    "non-dominé", "non-domine", "influencé", "influence", "non-influencé", "non-influence", "affecté", "affecte",
    "non-affecté", "non-affecte", "impacté", "impacte", "non-impacté", "non-impacte", "touché", "touche",
    "non-touché", "non-touche", "atteint", "non-atteint", "frappé", "frappe", "non-frappé", "non-frappe",
    "heurté", "heurte", "non-heurté", "non-heurte", "percuté", "percute", "non-percuté", "non-percute",
    "cogné", "cogne", "non-cogné", "non-cogne", "tapé", "tape", "non-tapé", "non-tape", "frappé", "frappe",
    "non-frappé", "non-frappe", "battu", "non-battu", "vaincu", "non-vaincu", "défait", "defait", "non-défait", "non-defait",
    "perdu", "non-perdu", "gagné", "gagne", "non-gagné", "non-gagne", "remporté", "remporte", "non-remporté", "non-remporte",
    "obtenu", "non-obtenu", "acquis", "non-acquis", "conquis", "non-conquis", "pris", "non-pris", "saisi", "non-saisi",
    "capturé", "capture", "non-capturé", "non-capture", "attrapé", "attrape", "non-attrapé", "non-attrape",
    "chopé", "chope", "non-chopé", "non-chope", "pincé", "pince", "non-pincé", "non-pince", "coincé", "coince",
    "non-coincé", "non-coince", "piégé", "piege", "non-piégé", "non-piege", "traqué", "traque", "non-traqué", "non-traque",
    "poursuivi", "non-poursuivi", "chassé", "chasse", "non-chassé", "non-chasse", "traqué", "traque", "non-traqué", "non-traque",
    "pisté", "piste", "non-pisté", "non-piste", "suivi", "non-suivi", "filé", "file", "non-filé", "non-file",
    "espionné", "espionne", "non-espionné", "non-espionne", "surveillé", "surveille", "non-surveillé", "non-surveille",
    "observé", "observe", "non-observé", "non-observe", "regardé", "regarde", "non-regardé", "non-regarde",
    "vu", "non-vu", "aperçu", "apercu", "non-aperçu", "non-apercu", "distingué", "distingue", "non-distingué", "non-distingue",
    "discerné", "discerne", "non-discerné", "non-discerne", "repéré", "repere", "non-repéré", "non-repere",
    "localisé", "localise", "non-localisé", "non-localise", "situé", "situe", "non-situé", "non-situe",
    "placé", "place", "non-placé", "non-place", "positionné", "positionne", "non-positionné", "non-positionne",
    "disposé", "dispose", "non-disposé", "non-dispose", "arrangé", "arrange", "non-arrangé", "non-arrange",
    "ordonné", "ordonne", "non-ordonné", "non-ordonne", "aligné", "aligne", "non-aligné", "non-aligne",
    "niveau", "mesure", "analyse", "valeur", "limite", "standard", "indicateur", "qualité", "réglementation"
]

# Modèles pour détecter les données structurées (tableaux, listes, etc.)
STRUCTURED_DATA_PATTERNS = [
    # Tableaux avec des lignes et des colonnes
    r"\|[^|]*\|[^|]*\|",
    r"\+[-+]+\+",
    r"\|[-|]+\|",
    # Listes à puces
    r"^\s*[•\*\-\+]\s+.*$",
    r"^\s*\d+\.\s+.*$",
    r"^\s*[a-z]\)\s+.*$",
    r"^\s*\([a-z]\)\s+.*$",
    # Sections avec des titres et des valeurs
    r"^[A-Z][^:]*:\s*\d+[.,]?\d*\s*[a-zA-Z°/%]*$",
    # Paires clé-valeur
    r"^[^:]+:\s*\d+[.,]?\d*\s*[a-zA-Z°/%]*$"
]

def read_file_with_multiple_encodings(file_path):
    """Tente de lire un fichier avec différents encodages."""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
            return content, encoding
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Impossible de lire le fichier {file_path} avec les encodages disponibles.")

def extract_parameters_from_text(text):
    """Extrait les paramètres environnementaux du texte en utilisant des expressions régulières."""
    extracted_parameters = []
    
    for param_name, param_info in ENVIRONMENTAL_PARAMETERS.items():
        regex_pattern = param_info["regex"]
        matches = re.finditer(regex_pattern, text, re.IGNORECASE | re.MULTILINE)
        
        for match in matches:
            value = match.group(1)
            if value:
                # Récupérer le contexte (20 caractères avant et après)
                start_pos = max(0, match.start() - 50)
                end_pos = min(len(text), match.end() + 50)
                context = text[start_pos:end_pos].strip()
                
                # Déterminer l'unité si elle est présente dans le match
                unit = ""
                for u in param_info["unités"]:
                    if u in context:
                        unit = u
                        break
                
                extracted_parameters.append({
                    "parameter": param_name,
                    "value": value,
                    "unit": unit,
                    "context": context
                })
    
    return extracted_parameters

def extract_from_structured_data(text):
    """Extrait les paramètres environnementaux des données structurées."""
    structured_data = []
    
    # Recherche de modèles de données structurées
    for pattern in STRUCTURED_DATA_PATTERNS:
        matches = re.finditer(pattern, text, re.MULTILINE)
        for match in matches:
            line = match.group(0).strip()
            structured_data.append(line)
    
    # Extraction des paramètres des données structurées
    extracted_parameters = []
    for line in structured_data:
        for param_name, param_info in ENVIRONMENTAL_PARAMETERS.items():
            for variation in param_info["variations"]:
                if variation.lower() in line.lower():
                    # Recherche de valeurs numériques
                    value_match = re.search(r'\b(\d+[.,]?\d*)\b', line)
                    if value_match:
                        value = value_match.group(1)
                        
                        # Déterminer l'unité si elle est présente
                        unit = ""
                        for u in param_info["unités"]:
                            if u in line:
                                unit = u
                                break
                        
                        extracted_parameters.append({
                            "parameter": param_name,
                            "value": value,
                            "unit": unit,
                            "context": line
                        })
                        break
    
    return extracted_parameters

def analyze_text_content(file_path):
    """Analyse le contenu du fichier texte et extrait les paramètres environnementaux."""
    try:
        content, encoding = read_file_with_multiple_encodings(file_path)
        
        # Statistiques de base sur le fichier
        file_size = os.path.getsize(file_path) / 1024  # en KB
        char_count = len(content)
        line_count = content.count('\n') + 1
        word_count = len(content.split())
        
        # Extraction des paramètres environnementaux
        extracted_parameters = extract_parameters_from_text(content)
        
        # Extraction des paramètres à partir des données structurées
        structured_data = extract_from_structured_data(content)
        extracted_parameters.extend(structured_data)
        
        # Compter les occurrences des mots-clés environnementaux
        env_keyword_counts = {}
        for keyword in ENVIRONMENTAL_KEYWORDS:
            count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', content, re.IGNORECASE))
            if count > 0:
                env_keyword_counts[keyword] = count
        
        # Compter les occurrences de chaque paramètre
        parameter_counts = {}
        for param in extracted_parameters:
            param_name = param["parameter"]
            if param_name in parameter_counts:
                parameter_counts[param_name] += 1
            else:
                parameter_counts[param_name] = 1
        
        # Résultats de l'analyse
        analysis_results = {
            "file_path": file_path,
            "encoding": encoding,
            "file_size": file_size,
            "char_count": char_count,
            "line_count": line_count,
            "word_count": word_count,
            "extracted_parameters": extracted_parameters,
            "structured_data": structured_data,
            "env_keyword_counts": env_keyword_counts,
            "parameter_counts": parameter_counts,
            "total_parameters": len(extracted_parameters),
            "unique_parameters": len(parameter_counts)
        }
        
        return analysis_results
    
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du fichier {file_path}: {str(e)}")
        return None

def generate_suggestions(analysis_results):
    """Génère des suggestions pour améliorer l'extraction des paramètres environnementaux."""
    suggestions = []
    
    # Vérifier si des paramètres ont été trouvés
    if analysis_results["total_parameters"] == 0:
        suggestions.append({
            "type": "ERROR",
            "message": "Aucun paramètre environnemental n'a été trouvé dans le fichier.",
            "solution": "Ajoutez des paramètres environnementaux explicites dans le fichier, par exemple: 'température: 25°C', 'pH: 7.2', etc."
        })
    
    # Vérifier le nombre de mots-clés environnementaux
    if len(analysis_results["env_keyword_counts"]) < 10:
        suggestions.append({
            "type": "WARNING",
            "message": f"Seulement {len(analysis_results['env_keyword_counts'])} mots-clés environnementaux ont été trouvés dans le fichier.",
            "solution": "Ajoutez plus de mots-clés environnementaux pour améliorer la détection des paramètres."
        })
    
    # Vérifier si des données structurées ont été trouvées mais pas formatées correctement
    if len(analysis_results["structured_data"]) > 0 and analysis_results["total_parameters"] < 5:
        suggestions.append({
            "type": "WARNING",
            "message": "Des données structurées ont été détectées mais peu de paramètres ont été extraits.",
            "solution": "Assurez-vous que les données structurées (tableaux, listes) contiennent des paramètres environnementaux clairement identifiables avec leurs valeurs et unités."
        })
    
    # Vérifier les paramètres manquants
    missing_parameters = []
    for param_name in ENVIRONMENTAL_PARAMETERS.keys():
        if param_name not in analysis_results["parameter_counts"]:
            missing_parameters.append(param_name)
    
    if missing_parameters:
        suggestions.append({
            "type": "INFO",
            "message": f"Paramètres environnementaux manquants: {', '.join(missing_parameters)}.",
            "solution": "Ajoutez ces paramètres au fichier si vous disposez des informations correspondantes."
        })
    
    # Vérifier l'encodage du fichier
    if analysis_results["encoding"] != "utf-8":
        suggestions.append({
            "type": "INFO",
            "message": f"Le fichier utilise l'encodage {analysis_results['encoding']} au lieu de UTF-8.",
            "solution": "Envisagez de convertir le fichier en UTF-8 pour une meilleure compatibilité."
        })
    
    return suggestions

def extract_parameters_from_file(file_path):
    """Analyse un fichier donné et extrait les paramètres environnementaux."""
    # Vérifier si le fichier existe
    if not os.path.isfile(file_path):
        logger.error(f"Le fichier {file_path} n'existe pas.")
        return None
    
    # Analyser le contenu du fichier
    analysis_results = analyze_text_content(file_path)
    if not analysis_results:
        return None
    
    # Générer des suggestions pour améliorer l'extraction
    suggestions = generate_suggestions(analysis_results)
    analysis_results["suggestions"] = suggestions
    
    return analysis_results

def save_results_to_excel(analysis_results, output_file):
    """Sauvegarde les résultats de l'analyse dans un fichier Excel."""
    try:
        # Créer un writer Excel
        writer = pd.ExcelWriter(output_file, engine='openpyxl')
        
        # Feuille de résumé
        summary_data = {
            "Métrique": [
                "Chemin du fichier",
                "Encodage",
                "Taille du fichier (KB)",
                "Nombre de caractères",
                "Nombre de lignes",
                "Nombre de mots",
                "Paramètres uniques trouvés",
                "Total des occurrences de paramètres"
            ],
            "Valeur": [
                analysis_results["file_path"],
                analysis_results["encoding"],
                f"{analysis_results['file_size']:.2f}",
                analysis_results["char_count"],
                analysis_results["line_count"],
                analysis_results["word_count"],
                analysis_results["unique_parameters"],
                analysis_results["total_parameters"]
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Résumé", index=False)
        
        # Feuille des paramètres extraits
        if analysis_results["extracted_parameters"]:
            params_df = pd.DataFrame(analysis_results["extracted_parameters"])
            params_df.to_excel(writer, sheet_name="Paramètres extraits", index=False)
        
        # Feuille des données structurées
        if analysis_results["structured_data"]:
            structured_data = {"Données structurées": analysis_results["structured_data"]}
            structured_df = pd.DataFrame(structured_data)
            structured_df.to_excel(writer, sheet_name="Données structurées", index=False)
        
        # Feuille des mots-clés environnementaux
        if analysis_results["env_keyword_counts"]:
            keywords_data = {
                "Mot-clé": list(analysis_results["env_keyword_counts"].keys()),
                "Occurrences": list(analysis_results["env_keyword_counts"].values())
            }
            keywords_df = pd.DataFrame(keywords_data)
            keywords_df = keywords_df.sort_values(by="Occurrences", ascending=False)
            keywords_df.to_excel(writer, sheet_name="Mots-clés environnementaux", index=False)
        
        # Feuille des suggestions
        if analysis_results["suggestions"]:
            suggestions_data = {
                "Type": [s["type"] for s in analysis_results["suggestions"]],
                "Message": [s["message"] for s in analysis_results["suggestions"]],
                "Solution": [s["solution"] for s in analysis_results["suggestions"]]
            }
            suggestions_df = pd.DataFrame(suggestions_data)
            suggestions_df.to_excel(writer, sheet_name="Suggestions", index=False)
        
        # Sauvegarder le fichier Excel
        writer.close()
        logger.info(f"Résultats sauvegardés dans {output_file}")
        return True
    
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des résultats dans Excel: {str(e)}")
        return False

def generate_report(analysis_results):
    """Génère un rapport textuel des résultats de l'analyse."""
    report = "" + "=" * 80 + "\n\n"
    
    # Informations sur le fichier
    report += "INFORMATIONS SUR LE FICHIER:\n"
    report += f"Fichier analysé: {analysis_results['file_path']}\n"
    report += f"Taille: {analysis_results['file_size']:.2f} KB\n"
    report += f"Encodage: {analysis_results['encoding']}\n"
    report += f"Nombre de caractères: {analysis_results['char_count']}\n"
    report += f"Nombre de lignes: {analysis_results['line_count']}\n"
    report += f"Nombre de mots: {analysis_results['word_count']}\n\n"
    
    # Résumé des paramètres trouvés
    report += "RÉSUMÉ DES PARAMÈTRES TROUVÉS:\n"
    report += f"Paramètres uniques trouvés: {analysis_results['unique_parameters']}\n"
    report += f"Total des occurrences de paramètres: {analysis_results['total_parameters']}\n"
    
    if analysis_results["total_parameters"] == 0:
        report += "  Aucun paramètre environnemental trouvé.\n\n"
    else:
        report += "\n"
    
    # Mots-clés environnementaux détectés
    report += "MOTS-CLÉS ENVIRONNEMENTAUX DÉTECTÉS:\n"
    if analysis_results["env_keyword_counts"]:
        sorted_keywords = sorted(analysis_results["env_keyword_counts"].items(), key=lambda x: x[1], reverse=True)
        for keyword, count in sorted_keywords:
            report += f"  - {keyword}: {count} occurrence(s)\n"
    else:
        report += "  Aucun mot-clé environnemental détecté.\n"
    report += "\n"
    
    # Détail des paramètres extraits
    report += "DÉTAIL DES PARAMÈTRES EXTRAITS:\n"
    if analysis_results["extracted_parameters"]:
        # Regrouper les paramètres par type
        params_by_type = {}
        for param in analysis_results["extracted_parameters"]:
            param_type = param["parameter"]
            if param_type not in params_by_type:
                params_by_type[param_type] = []
            params_by_type[param_type].append(param)
        
        # Afficher les paramètres par type
        for param_type, params in params_by_type.items():
            report += f"  {param_type.capitalize()}:\n"
            for param in params:
                value_with_unit = f"{param['value']} {param['unit']}".strip()
                report += f"    - Valeur: {value_with_unit}\n"
                report += f"      Contexte: \"{param['context']}\"\n\n"
    else:
        report += "  Aucun paramètre extrait.\n\n"
    
    # Suggestions d'amélioration
    report += "SUGGESTIONS D'AMÉLIORATION:\n\n"
    if analysis_results["suggestions"]:
        for suggestion in analysis_results["suggestions"]:
            report += f"  [{suggestion['type']}] {suggestion['message']}\n"
            report += f"  Solution: {suggestion['solution']}\n\n"
    else:
        report += "  Aucune suggestion d'amélioration.\n\n"
    
    # Conclusion
    report += "=" * 80 + "\n"
    report += "CONCLUSION: "
    if analysis_results["total_parameters"] > 0:
        report += f"{analysis_results['total_parameters']} paramètres environnementaux ont été trouvés dans le fichier.\n"
        report += "Suivez les suggestions ci-dessus pour améliorer davantage l'extraction.\n"
    else:
        report += "Aucun paramètre environnemental n'a été trouvé dans le fichier.\n"
        report += "Suivez les suggestions ci-dessus pour améliorer l'extraction.\n"
    report += "=" * 80 + "\n"
    
    return report

def main():
    """Fonction principale du script."""
    # Analyser les arguments de la ligne de commande
    parser = argparse.ArgumentParser(description="Outil de diagnostic et de correction des problèmes d'extraction de paramètres environnementaux.")
    parser.add_argument("--file", type=str, default=DEFAULT_FILE_PATH, help="Chemin vers le fichier à analyser")
    parser.add_argument("--output-excel", type=str, help="Chemin vers le fichier Excel de sortie")
    parser.add_argument("--output-report", type=str, help="Chemin vers le fichier de rapport de sortie")
    parser.add_argument("--show-report", action="store_true", help="Afficher le rapport dans la console")
    args = parser.parse_args()
    
    # Vérifier si le fichier existe
    if not os.path.isfile(args.file):
        logger.error(f"Le fichier {args.file} n'existe pas.")
        print(f"Erreur: Le fichier {args.file} n'existe pas.")
        return 1
    
    # Analyser le fichier
    logger.info(f"Analyse du fichier {args.file}...")
    analysis_results = extract_parameters_from_file(args.file)
    
    if not analysis_results:
        logger.error(f"Échec de l'analyse du fichier {args.file}.")
        print(f"Erreur: Échec de l'analyse du fichier {args.file}.")
        return 1
    
    # Générer le rapport
    report = generate_report(analysis_results)
    
    # Afficher le rapport si demandé
    if args.show_report:
        print(report)
    
    # Sauvegarder le rapport dans un fichier si demandé
    if args.output_report:
        try:
            with open(args.output_report, "w", encoding="utf-8") as f:
                f.write(report)
            logger.info(f"Rapport sauvegardé dans {args.output_report}")
            print(f"Rapport sauvegardé dans {args.output_report}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du rapport: {str(e)}")
            print(f"Erreur lors de la sauvegarde du rapport: {str(e)}")
    
    # Sauvegarder les résultats dans un fichier Excel si demandé
    if args.output_excel:
        if save_results_to_excel(analysis_results, args.output_excel):
            print(f"Résultats sauvegardés dans {args.output_excel}")
    
    # Afficher un résumé des résultats
    print(f"\nRésumé de l'analyse:")
    print(f"- Paramètres uniques trouvés: {analysis_results['unique_parameters']}")
    print(f"- Total des occurrences de paramètres: {analysis_results['total_parameters']}")
    print(f"- Nombre de suggestions: {len(analysis_results['suggestions'])}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())