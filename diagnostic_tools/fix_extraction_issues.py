#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour diagnostiquer et corriger les problèmes d'extraction de paramètres environnementaux
dans le fichier EIE HUB TARFAYA GREEN AMMONIA v2.txt.

Ce script analyse en profondeur le fichier texte, identifie les problèmes potentiels
et propose des solutions pour améliorer l'extraction des paramètres environnementaux.
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
    "EIE HUB TARFAYA GREEN AMMONIA v2_texte_extrait.txt"
)

# Liste des paramètres environnementaux à rechercher
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
    "environnement", "environnemental", "écologie", "ecologie", "écologique", "ecologique",
    "pollution", "contamination", "impact", "risque", "danger", "qualité", "qualite",
    "eau", "air", "sol", "atmosphère", "atmosphere", "aquatique", "terrestre",
    "émission", "emission", "rejet", "effluent", "déchet", "dechet", "résidu", "residu",
    "toxique", "toxicité", "toxicite", "nocif", "dangereux", "hazardeux",
    "norme", "standard", "réglementation", "reglementation", "limite", "seuil",
    "surveillance", "monitoring", "mesure", "analyse", "échantillon", "echantillon",
    "concentration", "niveau", "valeur", "paramètre", "parametre", "indicateur"
]

# Patterns pour détecter les données structurées
STRUCTURED_DATA_PATTERNS = [
    # Tableaux avec séparateurs
    r"([\w\s]+)\s*[|]\s*([\d.,]+)\s*[|]\s*([\w\s/°]+)",  # Format: Paramètre | Valeur | Unité
    r"([\w\s]+)\s*[:]\s*([\d.,]+)\s*([\w\s/°]+)",       # Format: Paramètre : Valeur Unité
    r"([\w\s]+)\s*=\s*([\d.,]+)\s*([\w\s/°]+)",        # Format: Paramètre = Valeur Unité
    
    # Listes à puces
    r"[•\-\*]\s*([\w\s]+)\s*[:]\s*([\d.,]+)\s*([\w\s/°]+)",  # Format: • Paramètre : Valeur Unité
    
    # Formats de tableau potentiels
    r"\|\s*([\w\s]+)\s*\|\s*([\d.,]+)\s*\|\s*([\w\s/°]+)\s*\|",  # Format table Markdown
    r"\+[-]+\+[-]+\+[-]+\+"  # Détection de séparateurs de tableau ASCII
]


def read_file_with_multiple_encodings(file_path):
    """Tente de lire un fichier avec différents encodages."""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            logger.info(f"Fichier lu avec succès en utilisant l'encodage {encoding}")
            return content, encoding
        except UnicodeDecodeError:
            continue
    
    logger.error(f"Impossible de lire le fichier {file_path} avec les encodages disponibles")
    return None, None


def extract_parameters_from_text(text):
    """Extrait les paramètres environnementaux du texte en utilisant des expressions régulières."""
    found_parameters = {}
    
    for param_name, param_info in ENVIRONMENTAL_PARAMETERS.items():
        # Recherche avec regex
        matches = re.finditer(param_info["regex"], text, re.IGNORECASE)
        
        for match in matches:
            value = match.group(1)
            context = text[max(0, match.start() - 50):min(len(text), match.end() + 50)]
            
            if param_name not in found_parameters:
                found_parameters[param_name] = []
            
            found_parameters[param_name].append({
                "value": value,
                "context": context.strip(),
                "position": match.start()
            })
    
    return found_parameters


def extract_from_structured_data(text):
    """Extrait les paramètres environnementaux à partir de données structurées (tableaux, listes)."""
    structured_data = []
    
    # Détection de tableaux et de listes
    for pattern in STRUCTURED_DATA_PATTERNS:
        matches = re.finditer(pattern, text, re.MULTILINE)
        
        for match in matches:
            try:
                if len(match.groups()) >= 3:
                    param = match.group(1).strip()
                    value = match.group(2).strip()
                    unit = match.group(3).strip()
                    
                    # Vérifier si le paramètre correspond à un paramètre environnemental connu
                    for env_param, param_info in ENVIRONMENTAL_PARAMETERS.items():
                        if any(var.lower() in param.lower() for var in param_info["variations"]):
                            structured_data.append({
                                "parameter": env_param,
                                "detected_name": param,
                                "value": value,
                                "unit": unit,
                                "context": text[max(0, match.start() - 30):min(len(text), match.end() + 30)].strip(),
                                "position": match.start()
                            })
                            break
            except Exception as e:
                logger.error(f"Erreur lors de l'extraction de données structurées: {str(e)}")
    
    return structured_data


def analyze_text_content(file_path):
    """Analyse le contenu du fichier texte pour extraire les paramètres et générer des statistiques."""
    # Lire le fichier avec gestion des encodages
    content, encoding = read_file_with_multiple_encodings(file_path)
    if not content:
        return None
    
    # Statistiques de base
    stats = {
        "file_path": file_path,
        "encoding": encoding,
        "file_size": os.path.getsize(file_path),
        "character_count": len(content),
        "line_count": content.count('\n') + 1,
        "word_count": len(content.split())
    }
    
    # Extraction des paramètres
    extracted_parameters = extract_parameters_from_text(content)
    structured_data = extract_from_structured_data(content)
    
    # Comptage des mots-clés environnementaux
    keyword_counts = {}
    for keyword in ENVIRONMENTAL_KEYWORDS:
        count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', content, re.IGNORECASE))
        if count > 0:
            keyword_counts[keyword] = count
    
    # Statistiques sur les paramètres trouvés
    param_stats = {}
    for param, occurrences in extracted_parameters.items():
        param_stats[param] = len(occurrences)
    
    # Résultats de l'analyse
    analysis_results = {
        "stats": stats,
        "extracted_parameters": extracted_parameters,
        "structured_data": structured_data,
        "keyword_counts": keyword_counts,
        "parameter_counts": param_stats,
        "total_parameters_found": sum(param_stats.values()),
        "unique_parameters_found": len(param_stats)
    }
    
    # Génération de suggestions
    analysis_results["suggestions"] = generate_suggestions(analysis_results, content)
    
    return analysis_results


def generate_suggestions(analysis_results, content):
    """Génère des suggestions pour améliorer l'extraction des paramètres."""
    suggestions = []
    
    # Suggestion 1: Vérifier si le fichier contient des informations environnementales
    if sum(analysis_results["keyword_counts"].values()) < 10:
        suggestions.append({
            "type": "warning",
            "message": "Le fichier contient peu de mots-clés environnementaux. Vérifiez qu'il s'agit bien d'un document sur les risques environnementaux."
        })
    
    # Suggestion 2: Vérifier si des paramètres ont été trouvés
    if analysis_results["total_parameters_found"] == 0:
        suggestions.append({
            "type": "error",
            "message": "Aucun paramètre environnemental n'a été trouvé dans le fichier.",
            "solution": "Ajoutez des paramètres environnementaux explicites dans le fichier, par exemple: 'température: 25°C', 'pH: 7.2', etc."
        })
    
    # Suggestion 3: Vérifier si le fichier contient des tableaux mal formatés
    if any(pattern in content for pattern in ["tableau", "table", "valeur", "paramètre", "parametre"]):
        if len(analysis_results["structured_data"]) == 0:
            suggestions.append({
                "type": "warning",
                "message": "Le fichier semble contenir des tableaux ou des données structurées, mais ils ne sont pas correctement formatés pour l'extraction.",
                "solution": "Reformatez les tableaux pour qu'ils suivent un format standard, par exemple: 'Paramètre | Valeur | Unité'."
            })
    
    # Suggestion 4: Vérifier les paramètres manquants
    missing_params = [param for param in ENVIRONMENTAL_PARAMETERS.keys() 
                     if param not in analysis_results["extracted_parameters"]]
    if missing_params:
        suggestions.append({
            "type": "info",
            "message": f"Paramètres environnementaux manquants: {', '.join(missing_params)}.",
            "solution": "Ajoutez ces paramètres au fichier si vous disposez des informations correspondantes."
        })
    
    # Suggestion 5: Vérifier l'encodage du fichier
    if analysis_results["stats"]["encoding"] != "utf-8":
        suggestions.append({
            "type": "info",
            "message": f"Le fichier utilise l'encodage {analysis_results['stats']['encoding']} au lieu de UTF-8.",
            "solution": "Envisagez de convertir le fichier en UTF-8 pour une meilleure compatibilité."
        })
    
    return suggestions


def extract_parameters_from_file(file_path):
    """Extrait les paramètres environnementaux d'un fichier texte."""
    try:
        logger.info(f"Analyse du fichier: {file_path}")
        
        # Vérifier que le fichier existe
        if not os.path.exists(file_path):
            logger.error(f"Le fichier {file_path} n'existe pas")
            return None
        
        # Analyser le contenu du fichier
        analysis_results = analyze_text_content(file_path)
        if not analysis_results:
            logger.error(f"Impossible d'analyser le contenu du fichier {file_path}")
            return None
        
        logger.info(f"Analyse terminée: {analysis_results['total_parameters_found']} paramètres trouvés")
        return analysis_results
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des paramètres: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def save_results_to_excel(analysis_results, output_file):
    """Sauvegarde les résultats de l'analyse dans un fichier Excel."""
    try:
        # Créer un writer Excel
        writer = pd.ExcelWriter(output_file, engine='openpyxl')
        
        # Feuille 1: Résumé
        summary_data = {
            "Métrique": [
                "Fichier analysé",
                "Taille du fichier",
                "Encodage",
                "Nombre de caractères",
                "Nombre de lignes",
                "Nombre de mots",
                "Paramètres uniques trouvés",
                "Total des occurrences de paramètres"
            ],
            "Valeur": [
                analysis_results["stats"]["file_path"],
                f"{analysis_results['stats']['file_size'] / 1024:.2f} KB",
                analysis_results["stats"]["encoding"],
                analysis_results["stats"]["character_count"],
                analysis_results["stats"]["line_count"],
                analysis_results["stats"]["word_count"],
                analysis_results["unique_parameters_found"],
                analysis_results["total_parameters_found"]
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Résumé", index=False)
        
        # Feuille 2: Paramètres extraits
        extracted_data = []
        for param, occurrences in analysis_results["extracted_parameters"].items():
            for i, occurrence in enumerate(occurrences):
                extracted_data.append({
                    "Paramètre": param,
                    "Occurrence": i + 1,
                    "Valeur": occurrence["value"],
                    "Contexte": occurrence["context"],
                    "Position": occurrence["position"]
                })
        
        if extracted_data:
            pd.DataFrame(extracted_data).to_excel(writer, sheet_name="Paramètres extraits", index=False)
        
        # Feuille 3: Données structurées
        if analysis_results["structured_data"]:
            structured_df = pd.DataFrame(analysis_results["structured_data"])
            structured_df.to_excel(writer, sheet_name="Données structurées", index=False)
        
        # Feuille 4: Mots-clés environnementaux
        keyword_data = {
            "Mot-clé": list(analysis_results["keyword_counts"].keys()),
            "Occurrences": list(analysis_results["keyword_counts"].values())
        }
        pd.DataFrame(keyword_data).to_excel(writer, sheet_name="Mots-clés", index=False)
        
        # Feuille 5: Suggestions
        suggestion_data = [
            {
                "Type": suggestion["type"],
                "Message": suggestion["message"],
                "Solution": suggestion.get("solution", "")
            }
            for suggestion in analysis_results["suggestions"]
        ]
        pd.DataFrame(suggestion_data).to_excel(writer, sheet_name="Suggestions", index=False)
        
        # Sauvegarder le fichier Excel
        writer.close()
        logger.info(f"Résultats sauvegardés dans {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des résultats: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def generate_report(analysis_results, output_file=None):
    """Génère un rapport texte détaillé de l'analyse."""
    try:
        # Créer le contenu du rapport
        report = []
        report.append("=" * 80)
        report.append(f"RAPPORT D'ANALYSE DES PARAMÈTRES ENVIRONNEMENTAUX")
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        
        # Informations sur le fichier
        report.append("\nINFORMATIONS SUR LE FICHIER:")
        report.append(f"Fichier analysé: {analysis_results['stats']['file_path']}")
        report.append(f"Taille: {analysis_results['stats']['file_size'] / 1024:.2f} KB")
        report.append(f"Encodage: {analysis_results['stats']['encoding']}")
        report.append(f"Nombre de caractères: {analysis_results['stats']['character_count']}")
        report.append(f"Nombre de lignes: {analysis_results['stats']['line_count']}")
        report.append(f"Nombre de mots: {analysis_results['stats']['word_count']}")
        
        # Résumé des paramètres trouvés
        report.append("\nRÉSUMÉ DES PARAMÈTRES TROUVÉS:")
        report.append(f"Paramètres uniques trouvés: {analysis_results['unique_parameters_found']}")
        report.append(f"Total des occurrences de paramètres: {analysis_results['total_parameters_found']}")
        
        if analysis_results["parameter_counts"]:
            report.append("\nDétail des paramètres:")
            for param, count in analysis_results["parameter_counts"].items():
                report.append(f"  - {param}: {count} occurrence(s)")
        else:
            report.append("  Aucun paramètre environnemental trouvé.")
        
        # Mots-clés environnementaux
        report.append("\nMOTS-CLÉS ENVIRONNEMENTAUX DÉTECTÉS:")
        if analysis_results["keyword_counts"]:
            # Trier par nombre d'occurrences décroissant
            sorted_keywords = sorted(analysis_results["keyword_counts"].items(), 
                                    key=lambda x: x[1], reverse=True)
            for keyword, count in sorted_keywords:
                report.append(f"  - {keyword}: {count} occurrence(s)")
        else:
            report.append("  Aucun mot-clé environnemental détecté.")
        
        # Détail des paramètres extraits
        report.append("\nDÉTAIL DES PARAMÈTRES EXTRAITS:")
        if analysis_results["extracted_parameters"]:
            for param, occurrences in analysis_results["extracted_parameters"].items():
                report.append(f"\n  {param.upper()}:")
                for i, occurrence in enumerate(occurrences):
                    report.append(f"    Occurrence {i+1}:")
                    report.append(f"      Valeur: {occurrence['value']}")
                    report.append(f"      Contexte: {occurrence['context']}")
        else:
            report.append("  Aucun paramètre extrait.")
        
        # Suggestions
        report.append("\nSUGGESTIONS D'AMÉLIORATION:")
        if analysis_results["suggestions"]:
            for suggestion in analysis_results["suggestions"]:
                report.append(f"\n  [{suggestion['type'].upper()}] {suggestion['message']}")
                if "solution" in suggestion:
                    report.append(f"  Solution: {suggestion['solution']}")
        else:
            report.append("  Aucune suggestion.")
        
        # Conclusion
        report.append("\n" + "=" * 80)
        if analysis_results["total_parameters_found"] > 0:
            report.append("CONCLUSION: Des paramètres environnementaux ont été trouvés dans le fichier.")
            report.append("Vous pouvez utiliser ces informations pour améliorer l'extraction dans l'application.")
        else:
            report.append("CONCLUSION: Aucun paramètre environnemental n'a été trouvé dans le fichier.")
            report.append("Suivez les suggestions ci-dessus pour améliorer l'extraction.")
        report.append("=" * 80)
        
        # Sauvegarder le rapport dans un fichier si demandé
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(report))
            logger.info(f"Rapport sauvegardé dans {output_file}")
        
        return "\n".join(report)
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def parse_arguments():
    """Parse les arguments de ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Outil de diagnostic et de correction des problèmes d'extraction de paramètres environnementaux"
    )
    
    parser.add_argument(
        "--file", 
        default=DEFAULT_FILE_PATH,
        help=f"Chemin du fichier texte à analyser (défaut: {DEFAULT_FILE_PATH})"
    )
    
    parser.add_argument(
        "--output-excel", 
        help="Chemin du fichier Excel de sortie pour les résultats détaillés"
    )
    
    parser.add_argument(
        "--output-report", 
        help="Chemin du fichier texte de sortie pour le rapport"
    )
    
    parser.add_argument(
        "--show-report", 
        action="store_true",
        help="Afficher le rapport dans la console"
    )
    
    return parser.parse_args()


def main():
    """Fonction principale."""
    args = parse_arguments()
    
    try:
        # Vérifier que le fichier existe
        if not os.path.exists(args.file):
            print(f"Erreur: Le fichier {args.file} n'existe pas.")
            return 1
        
        print(f"\nAnalyse du fichier: {args.file}")
        print("Veuillez patienter...\n")
        
        # Extraire les paramètres du fichier
        analysis_results = extract_parameters_from_file(args.file)
        if not analysis_results:
            print("Erreur: Impossible d'analyser le fichier.")
            return 1
        
        # Générer le rapport
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Définir les chemins de sortie par défaut si non spécifiés
        output_dir = os.path.join(os.path.dirname(args.file), "diagnostic_results")
        os.makedirs(output_dir, exist_ok=True)
        
        output_excel = args.output_excel or os.path.join(
            output_dir, f"extraction_analysis_{timestamp}.xlsx"
        )
        
        output_report = args.output_report or os.path.join(
            output_dir, f"extraction_report_{timestamp}.txt"
        )
        
        # Sauvegarder les résultats dans un fichier Excel
        save_results_to_excel(analysis_results, output_excel)
        
        # Générer et sauvegarder le rapport
        report = generate_report(analysis_results, output_report)
        
        # Afficher le rapport si demandé
        if args.show_report and report:
            print(report)
        else:
            print("\nRÉSULTATS DE L'ANALYSE:")
            print(f"Paramètres uniques trouvés: {analysis_results['unique_parameters_found']}")
            print(f"Total des occurrences de paramètres: {analysis_results['total_parameters_found']}")
            
            if analysis_results["suggestions"]:
                print("\nSUGGESTIONS PRINCIPALES:")
                for suggestion in analysis_results["suggestions"]:
                    print(f"  [{suggestion['type'].upper()}] {suggestion['message']}")
            
            print(f"\nRésultats détaillés sauvegardés dans: {output_excel}")
            print(f"Rapport complet sauvegardé dans: {output_report}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution: {str(e)}")
        import traceback
        print(f"\nERREUR: {str(e)}")
        print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())