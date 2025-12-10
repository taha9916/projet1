#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Outil d'extraction améliorée des paramètres environnementaux.

Ce script permet d'améliorer l'extraction des paramètres environnementaux à partir de fichiers texte
en utilisant des techniques avancées de traitement du langage naturel et des expressions régulières.
"""

import os
import sys
import re
import json
import argparse
import pandas as pd
from datetime import datetime

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer les modules nécessaires du projet
from logger import setup_logging, get_logger

# Configurer le logging
logger = setup_logging()
extractor_logger = get_logger("parameter_extractor")

# Définition des paramètres environnementaux et leurs variations
ENVIRONMENTAL_PARAMETERS = {
    "température": {
        "variations": ["température", "temperature", "temp", "T°", "T °C"],
        "unités": ["°C", "K", "°F", "degrés", "degres", "degrés Celsius", "degres Celsius"],
        "regex": r"(?:température|temperature|temp|T°|T\s*°C)\s*(?::|de|est|était|etait|mesurée|mesuree|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:°C|K|°F|degrés|degres|degrés Celsius|degres Celsius|°|C)?"
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
    "DBO5": {
        "variations": ["DBO5", "DBO 5", "demande biochimique en oxygène", "demande biochimique en oxygene"],
        "unités": ["mg/L", "mg/l", "mg L-1", "mg.L-1", "mg O₂/L"],
        "regex": r"(?:DBO5|DBO\s*5|demande biochimique en oxygène|demande biochimique en oxygene)\s*(?::|de|est|était|etait|mesurée|mesuree|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:mg\/L|mg\/l|mg L-1|mg\.L-1|mg O₂\/L)?"
    },
    "DCO": {
        "variations": ["DCO", "demande chimique en oxygène", "demande chimique en oxygene"],
        "unités": ["mg/L", "mg/l", "mg L-1", "mg.L-1", "mg O₂/L"],
        "regex": r"(?:DCO|demande chimique en oxygène|demande chimique en oxygene)\s*(?::|de|est|était|etait|mesurée|mesuree|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:mg\/L|mg\/l|mg L-1|mg\.L-1|mg O₂\/L)?"
    },
    "oxygène dissous": {
        "variations": ["oxygène dissous", "oxygene dissous", "O2 dissous", "O₂ dissous"],
        "unités": ["mg/L", "mg/l", "mg L-1", "mg.L-1", "%", "% sat"],
        "regex": r"(?:oxygène dissous|oxygene dissous|O2 dissous|O₂ dissous)\s*(?::|de|est|était|etait|mesuré|mesure|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:mg\/L|mg\/l|mg L-1|mg\.L-1|%|% sat)?"
    },
    "phosphore": {
        "variations": ["phosphore", "phosphore total", "P", "P total", "phosphates", "PO4", "PO₄"],
        "unités": ["mg/L", "mg/l", "mg L-1", "mg.L-1", "mg P/L", "µg/L"],
        "regex": r"(?:phosphore|phosphore total|P total|phosphates|PO4|PO₄)\s*(?::|de|est|était|etait|mesuré|mesure|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:mg\/L|mg\/l|mg L-1|mg\.L-1|mg P\/L|µg\/L)?"
    },
    "azote": {
        "variations": ["azote", "azote total", "N", "N total", "nitrates", "NO3", "NO₃", "nitrites", "NO2", "NO₂", "ammonium", "NH4", "NH₄"],
        "unités": ["mg/L", "mg/l", "mg L-1", "mg.L-1", "mg N/L", "µg/L"],
        "regex": r"(?:azote|azote total|N total|nitrates|NO3|NO₃|nitrites|NO2|NO₂|ammonium|NH4|NH₄)\s*(?::|de|est|était|etait|mesuré|mesure|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:mg\/L|mg\/l|mg L-1|mg\.L-1|mg N\/L|µg\/L)?"
    },
    "métaux lourds": {
        "variations": ["métaux lourds", "metaux lourds", "plomb", "Pb", "mercure", "Hg", "cadmium", "Cd", "arsenic", "As", "chrome", "Cr", "cuivre", "Cu", "zinc", "Zn"],
        "unités": ["mg/L", "mg/l", "mg L-1", "mg.L-1", "µg/L", "µg/l", "ppb", "ppm"],
        "regex": r"(?:métaux lourds|metaux lourds|plomb|Pb|mercure|Hg|cadmium|Cd|arsenic|As|chrome|Cr|cuivre|Cu|zinc|Zn)\s*(?::|de|est|était|etait|mesuré|mesure|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:mg\/L|mg\/l|mg L-1|mg\.L-1|µg\/L|µg\/l|ppb|ppm)?"
    },
    "hydrocarbures": {
        "variations": ["hydrocarbures", "hydrocarbures totaux", "HCT", "HAP", "hydrocarbures aromatiques polycycliques"],
        "unités": ["mg/L", "mg/l", "mg L-1", "mg.L-1", "µg/L", "µg/l", "ppb", "ppm"],
        "regex": r"(?:hydrocarbures|hydrocarbures totaux|HCT|HAP|hydrocarbures aromatiques polycycliques)\s*(?::|de|est|était|etait|mesuré|mesure|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:mg\/L|mg\/l|mg L-1|mg\.L-1|µg\/L|µg\/l|ppb|ppm)?"
    },
    "perméabilité": {
        "variations": ["perméabilité", "permeabilite", "conductivité hydraulique", "conductivite hydraulique"],
        "unités": ["m/s", "cm/s", "mm/h", "m/j", "m/jour"],
        "regex": r"(?:perméabilité|permeabilite|conductivité hydraulique|conductivite hydraulique)\s*(?::|de|est|était|etait|mesurée|mesuree|=|:)\s*([+-]?\d+[.,]?\d*(?:[eE][+-]?\d+)?)\s*(?:m\/s|cm\/s|mm\/h|m\/j|m\/jour)?"
    },
    "matière organique": {
        "variations": ["matière organique", "matiere organique", "MO", "teneur en matière organique", "teneur en matiere organique"],
        "unités": ["%", "g/kg", "mg/g"],
        "regex": r"(?:matière organique|matiere organique|MO|teneur en matière organique|teneur en matiere organique)\s*(?::|de|est|était|etait|mesurée|mesuree|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:%|g\/kg|mg\/g)?"
    },
    "carbone organique": {
        "variations": ["carbone organique", "carbone organique total", "COT", "carbone organique dissous", "COD"],
        "unités": ["mg/L", "mg/l", "mg L-1", "mg.L-1", "g/kg", "%"],
        "regex": r"(?:carbone organique|carbone organique total|COT|carbone organique dissous|COD)\s*(?::|de|est|était|etait|mesuré|mesure|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:mg\/L|mg\/l|mg L-1|mg\.L-1|g\/kg|%)?"
    },
    "PM10": {
        "variations": ["PM10", "PM 10", "particules PM10", "particules en suspension PM10"],
        "unités": ["µg/m³", "µg/m3", "µg m-3", "µg.m-3"],
        "regex": r"(?:PM10|PM\s*10|particules PM10|particules en suspension PM10)\s*(?::|de|est|était|etait|mesuré|mesure|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:µg\/m³|µg\/m3|µg m-3|µg\.m-3)?"
    },
    "PM2.5": {
        "variations": ["PM2.5", "PM 2.5", "PM2,5", "PM 2,5", "particules PM2.5", "particules en suspension PM2.5"],
        "unités": ["µg/m³", "µg/m3", "µg m-3", "µg.m-3"],
        "regex": r"(?:PM2\.5|PM\s*2\.5|PM2,5|PM\s*2,5|particules PM2\.5|particules en suspension PM2\.5)\s*(?::|de|est|était|etait|mesuré|mesure|=|:)\s*([+-]?\d+[.,]?\d*)\s*(?:µg\/m³|µg\/m3|µg m-3|µg\.m-3)?"
    }
}

# Mots-clés contextuels pour améliorer la détection
CONTEXTUAL_KEYWORDS = [
    "environnement", "environnemental", "écologie", "ecologie", "écologique", "ecologique",
    "pollution", "contamination", "risque", "impact", "étude d'impact", "etude d'impact", "EIE",
    "qualité", "qualite", "eau", "air", "sol", "surveillance", "monitoring", "mesure",
    "analyse", "échantillon", "echantillon", "prélèvement", "prelevement", "concentration",
    "limite", "seuil", "norme", "standard", "réglementation", "reglementation", "directive",
    "évaluation", "evaluation", "caractérisation", "caracterisation", "diagnostic"
]

# Expressions régulières pour détecter les tableaux et les données structurées
TABLE_PATTERNS = [
    # Motif pour les lignes de tableau avec séparateurs
    r"([\w\s.,%]+)[\|\t;,]+([\w\s.,%]+)[\|\t;,]+([\w\s.,%]+)",
    # Motif pour les lignes de type "Paramètre: valeur unité"
    r"([\w\s]+)\s*:\s*([\d.,]+)\s*([\w/³²°%]+)",
    # Motif pour les lignes de type "Paramètre = valeur unité"
    r"([\w\s]+)\s*=\s*([\d.,]+)\s*([\w/³²°%]+)"
]

def extract_parameters_from_text(text_content):
    """
    Extrait les paramètres environnementaux d'un texte en utilisant des expressions régulières avancées.
    
    Args:
        text_content (str): Le contenu du texte à analyser
        
    Returns:
        dict: Dictionnaire des paramètres trouvés avec leurs valeurs, unités et contexte
    """
    extractor_logger.info("Extraction des paramètres environnementaux du texte")
    
    found_parameters = {}
    
    # Rechercher les paramètres avec les expressions régulières spécifiques
    for param_name, param_info in ENVIRONMENTAL_PARAMETERS.items():
        regex_pattern = param_info["regex"]
        matches = re.finditer(regex_pattern, text_content, re.IGNORECASE)
        
        for match in matches:
            # Extraire la valeur numérique
            value = match.group(1).replace(',', '.')
            
            # Extraire le contexte (50 caractères avant et après)
            start = max(0, match.start() - 50)
            end = min(len(text_content), match.end() + 50)
            context = text_content[start:end]
            
            # Déterminer l'unité si possible
            unit = ""
            for potential_unit in param_info["unités"]:
                if potential_unit in context[match.end() - start:]:  # Chercher après la valeur
                    unit = potential_unit
                    break
            
            # Ajouter le paramètre trouvé
            if param_name not in found_parameters:
                found_parameters[param_name] = []
            
            found_parameters[param_name].append({
                "value": value,
                "unit": unit,
                "context": context,
                "position": match.start()
            })
    
    # Rechercher les paramètres dans les tableaux et données structurées
    extract_from_structured_data(text_content, found_parameters)
    
    # Consolider les résultats (prendre la première occurrence de chaque paramètre)
    consolidated_parameters = {}
    for param_name, occurrences in found_parameters.items():
        if occurrences:  # S'il y a au moins une occurrence
            # Trier par position dans le texte (prendre la première occurrence)
            occurrences.sort(key=lambda x: x["position"])
            consolidated_parameters[param_name] = occurrences[0]
    
    extractor_logger.info(f"Paramètres trouvés: {', '.join(consolidated_parameters.keys())}")
    return consolidated_parameters

def extract_from_structured_data(text_content, found_parameters):
    """
    Extrait les paramètres environnementaux à partir de données structurées (tableaux, listes).
    
    Args:
        text_content (str): Le contenu du texte à analyser
        found_parameters (dict): Dictionnaire des paramètres déjà trouvés (sera mis à jour)
    """
    extractor_logger.info("Recherche de paramètres dans les données structurées")
    
    # Rechercher les lignes qui ressemblent à des tableaux
    lines = text_content.split('\n')
    
    for i, line in enumerate(lines):
        # Vérifier chaque motif de tableau
        for pattern in TABLE_PATTERNS:
            matches = re.finditer(pattern, line)
            
            for match in matches:
                # Analyser les groupes capturés
                if len(match.groups()) >= 2:  # Au moins un paramètre et une valeur
                    param_text = match.group(1).strip().lower()
                    value_text = match.group(2).strip()
                    unit_text = match.group(3).strip() if len(match.groups()) >= 3 else ""
                    
                    # Vérifier si le paramètre correspond à l'un des paramètres environnementaux
                    for param_name, param_info in ENVIRONMENTAL_PARAMETERS.items():
                        for variation in param_info["variations"]:
                            if variation.lower() in param_text:
                                # Extraire le contexte (la ligne entière)
                                context = line
                                
                                # Ajouter des lignes avant et après pour le contexte
                                if i > 0:
                                    context = f"{lines[i-1]}\n{context}"
                                if i < len(lines) - 1:
                                    context = f"{context}\n{lines[i+1]}"
                                
                                # Ajouter le paramètre trouvé
                                if param_name not in found_parameters:
                                    found_parameters[param_name] = []
                                
                                found_parameters[param_name].append({
                                    "value": value_text.replace(',', '.'),
                                    "unit": unit_text,
                                    "context": context,
                                    "position": text_content.find(line)
                                })
                                break

def analyze_text_content(text_content):
    """
    Analyse complète du contenu du texte pour l'extraction de paramètres environnementaux.
    
    Args:
        text_content (str): Le contenu du texte à analyser
        
    Returns:
        dict: Résultat de l'analyse avec les paramètres trouvés et des statistiques
    """
    extractor_logger.info("Analyse complète du contenu du texte")
    
    # Statistiques sur le texte
    stats = {
        "longueur": len(text_content),
        "nombre_lignes": text_content.count('\n') + 1,
        "mots_cles_contextuels": 0,
        "unites_mesure": 0
    }
    
    # Compter les mots-clés contextuels
    for keyword in CONTEXTUAL_KEYWORDS:
        count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_content, re.IGNORECASE))
        stats["mots_cles_contextuels"] += count
    
    # Compter les unités de mesure
    all_units = [unit for param_info in ENVIRONMENTAL_PARAMETERS.values() for unit in param_info["unités"] if unit]
    for unit in all_units:
        count = len(re.findall(re.escape(unit), text_content))
        stats["unites_mesure"] += count
    
    # Extraire les paramètres
    parameters = extract_parameters_from_text(text_content)
    
    # Déterminer si le texte contient des données structurées
    has_structured_data = any(re.search(pattern, text_content) for pattern in TABLE_PATTERNS)
    stats["donnees_structurees"] = has_structured_data
    
    # Préparer le résultat
    result = {
        "status": "success" if parameters else "warning",
        "message": f"{len(parameters)} paramètres environnementaux trouvés" if parameters else "Aucun paramètre environnemental n'a pu être extrait du texte",
        "parameters": parameters,
        "stats": stats,
        "suggestions": generate_suggestions(text_content, stats, parameters)
    }
    
    return result

def generate_suggestions(text_content, stats, parameters):
    """
    Génère des suggestions pour améliorer l'extraction des paramètres.
    
    Args:
        text_content (str): Le contenu du texte analysé
        stats (dict): Statistiques sur le texte
        parameters (dict): Paramètres trouvés
        
    Returns:
        list: Liste de suggestions
    """
    suggestions = []
    
    # Vérifier la longueur du texte
    if stats["longueur"] < 100:
        suggestions.append("Le fichier texte est très court. Assurez-vous qu'il contient suffisamment d'informations.")
    
    # Vérifier la présence de mots-clés contextuels
    if stats["mots_cles_contextuels"] < 5:
        suggestions.append("Le texte contient peu de termes liés à l'environnement. "  
                         "Assurez-vous que le fichier est pertinent pour l'analyse de risque environnemental.")
    
    # Vérifier la présence d'unités de mesure
    if stats["unites_mesure"] < 3:
        suggestions.append("Peu d'unités de mesure ont été trouvées dans le texte. "  
                         "L'ajout d'unités comme °C, mg/L, ppm, etc. peut aider à l'extraction des paramètres.")
    
    # Vérifier la présence de données structurées
    if not stats["donnees_structurees"]:
        suggestions.append("Le texte ne semble pas contenir de données tabulaires. "  
                         "L'utilisation de tableaux ou de formats structurés peut améliorer l'extraction.")
    
    # Suggestions basées sur les paramètres manquants
    missing_important_params = []
    important_params = ["température", "pH", "conductivité", "oxygène dissous", "DBO5", "DCO"]
    for param in important_params:
        if param not in parameters:
            missing_important_params.append(param)
    
    if missing_important_params:
        suggestions.append(f"Paramètres importants manquants: {', '.join(missing_important_params)}. "  
                         "Considérez l'ajout de ces paramètres pour une analyse plus complète.")
    
    # Suggestions générales
    suggestions.append("Essayez d'utiliser le mode d'analyse local si le mode cloud ne parvient pas à extraire les paramètres.")
    suggestions.append("Considérez l'ajout de mots-clés spécifiques comme 'température: 25°C' pour faciliter l'extraction.")
    
    return suggestions

def extract_parameters_from_file(file_path):
    """
    Extrait les paramètres environnementaux à partir d'un fichier texte.
    
    Args:
        file_path (str): Chemin vers le fichier texte à analyser
        
    Returns:
        dict: Résultat de l'analyse
    """
    extractor_logger.info(f"Extraction des paramètres à partir de {file_path}")
    
    # Vérifier que le fichier existe
    if not os.path.exists(file_path):
        extractor_logger.error(f"Le fichier {file_path} n'existe pas")
        return {
            "status": "error",
            "message": f"Le fichier {file_path} n'existe pas"
        }
    
    try:
        # Lire le contenu du fichier avec différents encodages
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        text_content = None
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    text_content = file.read()
                extractor_logger.info(f"Fichier lu avec l'encodage {encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        if text_content is None:
            extractor_logger.error("Impossible de lire le fichier avec les encodages disponibles")
            return {
                "status": "error",
                "message": "Impossible de lire le fichier avec les encodages disponibles"
            }
        
        # Analyser le contenu du texte
        result = analyze_text_content(text_content)
        
        # Ajouter des informations sur le fichier
        result["file_info"] = {
            "path": file_path,
            "size": os.path.getsize(file_path),
            "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return result
        
    except Exception as e:
        extractor_logger.error(f"Erreur lors de l'analyse du fichier: {str(e)}")
        return {
            "status": "error",
            "message": f"Erreur lors de l'analyse du fichier: {str(e)}"
        }

def save_results_to_excel(result, output_path):
    """
    Sauvegarde les résultats de l'extraction dans un fichier Excel.
    
    Args:
        result (dict): Résultat de l'analyse
        output_path (str): Chemin du fichier Excel de sortie
        
    Returns:
        bool: True si la sauvegarde a réussi, False sinon
    """
    try:
        # Créer un DataFrame pour les paramètres
        if result["parameters"]:
            data = []
            for param_name, param_info in result["parameters"].items():
                data.append({
                    "Paramètre": param_name,
                    "Valeur": param_info["value"],
                    "Unité": param_info["unit"],
                    "Contexte": param_info["context"]
                })
            
            df = pd.DataFrame(data)
            
            # Créer un writer Excel
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Écrire les paramètres
                df.to_excel(writer, sheet_name='Paramètres', index=False)
                
                # Écrire les statistiques
                stats_df = pd.DataFrame([
                    {"Métrique": "Longueur du texte", "Valeur": result["stats"]["longueur"]},
                    {"Métrique": "Nombre de lignes", "Valeur": result["stats"]["nombre_lignes"]},
                    {"Métrique": "Mots-clés contextuels", "Valeur": result["stats"]["mots_cles_contextuels"]},
                    {"Métrique": "Unités de mesure", "Valeur": result["stats"]["unites_mesure"]},
                    {"Métrique": "Données structurées", "Valeur": "Oui" if result["stats"]["donnees_structurees"] else "Non"}
                ])
                stats_df.to_excel(writer, sheet_name='Statistiques', index=False)
                
                # Écrire les suggestions
                suggestions_df = pd.DataFrame({
                    "Suggestions": result["suggestions"]
                })
                suggestions_df.to_excel(writer, sheet_name='Suggestions', index=False)
            
            extractor_logger.info(f"Résultats sauvegardés dans {output_path}")
            return True
        else:
            extractor_logger.warning("Aucun paramètre à sauvegarder")
            return False
    except Exception as e:
        extractor_logger.error(f"Erreur lors de la sauvegarde des résultats: {str(e)}")
        return False

def generate_report(result, output_path="extraction_report.txt"):
    """
    Génère un rapport textuel des résultats de l'extraction.
    
    Args:
        result (dict): Résultat de l'analyse
        output_path (str): Chemin du fichier de sortie
        
    Returns:
        bool: True si la génération a réussi, False sinon
    """
    try:
        report = []
        report.append("=" * 80)
        report.append("RAPPORT D'EXTRACTION DES PARAMÈTRES ENVIRONNEMENTAUX")
        report.append("=" * 80)
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Informations sur le fichier
        if "file_info" in result:
            report.append("\nINFORMATIONS SUR LE FICHIER:")
            report.append(f"Chemin: {result['file_info']['path']}")
            report.append(f"Taille: {result['file_info']['size']} octets")
            report.append(f"Dernière modification: {result['file_info']['last_modified']}")
        
        # Statistiques
        report.append("\nSTATISTIQUES:")
        report.append(f"Longueur du texte: {result['stats']['longueur']} caractères")
        report.append(f"Nombre de lignes: {result['stats']['nombre_lignes']}")
        report.append(f"Mots-clés contextuels: {result['stats']['mots_cles_contextuels']}")
        report.append(f"Unités de mesure: {result['stats']['unites_mesure']}")
        report.append(f"Données structurées: {'Oui' if result['stats']['donnees_structurees'] else 'Non'}")
        
        # Paramètres trouvés
        report.append("\nPARAMÈTRES ENVIRONNEMENTAUX TROUVÉS:")
        if result["parameters"]:
            for param_name, param_info in result["parameters"].items():
                value_str = f"{param_info['value']} {param_info['unit']}" if param_info['value'] else "(valeur non trouvée)"
                report.append(f"\n{param_name}: {value_str}")
                report.append(f"Contexte: \"{param_info['context']}\"")
        else:
            report.append("Aucun paramètre environnemental trouvé.")
        
        # Suggestions
        report.append("\nSUGGESTIONS POUR AMÉLIORER L'EXTRACTION:")
        for i, suggestion in enumerate(result["suggestions"], 1):
            report.append(f"{i}. {suggestion}")
        
        # Conclusion
        report.append("\nCONCLUSION:")
        if result["status"] == "success":
            report.append(f"✅ {result['message']}")
        else:
            report.append(f"⚠️ {result['message']}")
        
        report.append("\n" + "=" * 80)
        
        # Écrire le rapport dans un fichier
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report))
        
        extractor_logger.info(f"Rapport généré dans {output_path}")
        return True
    except Exception as e:
        extractor_logger.error(f"Erreur lors de la génération du rapport: {str(e)}")
        return False

def main():
    """
    Fonction principale du script d'extraction de paramètres.
    """
    parser = argparse.ArgumentParser(description="Outil d'extraction améliorée des paramètres environnementaux")
    parser.add_argument("--file", required=True, help="Fichier texte à analyser")
    parser.add_argument("--output-excel", help="Chemin du fichier Excel de sortie")
    parser.add_argument("--output-report", default="extraction_report.txt", help="Chemin du fichier de rapport")
    parser.add_argument("--verbose", action="store_true", help="Afficher les détails de l'extraction")
    
    args = parser.parse_args()
    
    # Extraire les paramètres du fichier
    result = extract_parameters_from_file(args.file)
    
    # Générer le rapport
    generate_report(result, args.output_report)
    
    # Sauvegarder les résultats dans un fichier Excel si demandé
    if args.output_excel and result["status"] != "error":
        save_results_to_excel(result, args.output_excel)
    
    # Afficher un résumé
    print(f"\nAnalyse du fichier: {args.file}")
    if result["status"] == "success":
        print(f"✅ {result['message']}")
        if args.verbose:
            for param_name, param_info in result["parameters"].items():
                value_str = f"{param_info['value']} {param_info['unit']}" if param_info['value'] else "(valeur non trouvée)"
                print(f"  - {param_name}: {value_str}")
    elif result["status"] == "warning":
        print(f"⚠️ {result['message']}")
        print("\nSuggestions:")
        for i, suggestion in enumerate(result["suggestions"][:3], 1):  # Afficher seulement les 3 premières suggestions
            print(f"  {i}. {suggestion}")
    else:
        print(f"❌ {result['message']}")
    
    print(f"\nRapport complet généré dans: {args.output_report}")
    if args.output_excel and result["status"] != "error":
        print(f"Résultats détaillés sauvegardés dans: {args.output_excel}")

if __name__ == "__main__":
    main()