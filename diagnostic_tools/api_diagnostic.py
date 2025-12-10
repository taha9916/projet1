#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Outil de diagnostic pour l'API Google Cloud Vision et l'extraction de paramètres environnementaux.

Ce script permet de :
1. Tester la validité de la clé API Google Cloud Vision
2. Vérifier l'activation de l'API Vision dans le projet Google Cloud
3. Diagnostiquer les problèmes d'extraction de paramètres environnementaux
"""

import os
import sys
import json
import requests
import argparse
from datetime import datetime

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer les modules nécessaires du projet
import json
from logger import setup_logging, get_logger
# Pas besoin d'importer LOG_CONFIG de config.py

# Configurer le logging
logger = setup_logging()
diag_logger = get_logger("api_diagnostic")

# Charger les configurations depuis le fichier cloud_api_config.json
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cloud_api_config.json")
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        CLOUD_API_CONFIG = json.load(f)
    diag_logger.info("Configurations des API cloud chargées avec succès depuis cloud_api_config.json")
except FileNotFoundError:
    CLOUD_API_CONFIG = {
        "google": {"api_key": "", "api_url": "https://vision.googleapis.com/v1/images:annotate"},
        "azure": {"api_key": "", "endpoint": ""},
        "openai": {"api_key": "", "api_url": "", "model": ""},
        "qwen": {"api_key": "", "api_url": "", "model": ""},
        "openrouter": {"api_key": "", "api_url": "", "model": ""}
    }
    diag_logger.warning("Fichier cloud_api_config.json non trouvé, utilisation des configurations par défaut")

# Constantes
GOOGLE_VISION_API_URL = "https://vision.googleapis.com/v1/images:annotate"
TEST_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "test_image.jpg")

def create_test_image():
    """
    Crée une image de test simple si elle n'existe pas déjà.
    Cette fonction utilise PIL pour créer une image basique avec du texte.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        if os.path.exists(TEST_IMAGE_PATH):
            diag_logger.info(f"L'image de test existe déjà à {TEST_IMAGE_PATH}")
            return TEST_IMAGE_PATH
            
        # Créer une image simple
        img = Image.new('RGB', (400, 200), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        
        # Essayer de charger une police, sinon utiliser la police par défaut
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font = ImageFont.load_default()
            
        # Ajouter du texte à l'image
        d.text((50, 50), "Test de l'API Google Cloud Vision", fill=(0, 0, 0), font=font)
        d.text((50, 100), "Paramètres environnementaux: pH, température", fill=(0, 0, 0), font=font)
        
        # Sauvegarder l'image
        img.save(TEST_IMAGE_PATH)
        diag_logger.info(f"Image de test créée à {TEST_IMAGE_PATH}")
        return TEST_IMAGE_PATH
        
    except ImportError:
        diag_logger.error("La bibliothèque PIL/Pillow n'est pas installée. Impossible de créer une image de test.")
        diag_logger.info("Installez PIL avec: pip install Pillow")
        return None
    except Exception as e:
        diag_logger.error(f"Erreur lors de la création de l'image de test: {str(e)}")
        return None

def encode_image(image_path):
    """
    Encode une image en base64 pour l'API Google Cloud Vision.
    """
    import base64
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        diag_logger.error(f"Erreur lors de l'encodage de l'image: {str(e)}")
        return None

def test_google_vision_api(api_key):
    """
    Teste la validité de la clé API Google Cloud Vision.
    
    Args:
        api_key (str): La clé API à tester
        
    Returns:
        dict: Résultat du test avec statut et message
    """
    diag_logger.info("Test de la clé API Google Cloud Vision")
    
    # Créer une image de test si nécessaire
    image_path = create_test_image()
    if not image_path:
        return {
            "status": "error",
            "message": "Impossible de créer ou de trouver l'image de test"
        }
    
    # Encoder l'image en base64
    image_content = encode_image(image_path)
    if not image_content:
        return {
            "status": "error",
            "message": "Impossible d'encoder l'image en base64"
        }
    
    # Préparer la requête pour l'API Vision
    request_data = {
        "requests": [
            {
                "image": {"content": image_content},
                "features": [{"type": "TEXT_DETECTION"}]
            }
        ]
    }
    
    # Construire l'URL avec la clé API
    url = f"{GOOGLE_VISION_API_URL}?key={api_key}"
    
    try:
        # Envoyer la requête à l'API
        diag_logger.debug(f"Envoi de la requête à {GOOGLE_VISION_API_URL}")
        response = requests.post(url, json=request_data)
        
        # Analyser la réponse
        if response.status_code == 200:
            diag_logger.info("Test de l'API réussi: La clé API est valide et l'API est accessible")
            return {
                "status": "success",
                "message": "La clé API est valide et l'API Google Cloud Vision est accessible",
                "response": response.json()
            }
        elif response.status_code == 403:
            diag_logger.error(f"Erreur 403 Forbidden: {response.text}")
            error_details = analyze_403_error(response.text)
            return {
                "status": "error",
                "code": 403,
                "message": "Erreur 403 Forbidden: Accès refusé à l'API Google Cloud Vision",
                "details": error_details,
                "response": response.text
            }
        else:
            diag_logger.error(f"Erreur {response.status_code}: {response.text}")
            return {
                "status": "error",
                "code": response.status_code,
                "message": f"Erreur {response.status_code} lors de l'appel à l'API",
                "response": response.text
            }
    except requests.exceptions.RequestException as e:
        diag_logger.error(f"Erreur de connexion: {str(e)}")
        return {
            "status": "error",
            "message": f"Erreur de connexion: {str(e)}"
        }

def analyze_403_error(error_text):
    """
    Analyse l'erreur 403 pour déterminer la cause probable.
    
    Args:
        error_text (str): Le texte de l'erreur retourné par l'API
        
    Returns:
        dict: Analyse détaillée de l'erreur avec causes probables et solutions
    """
    diag_logger.info("Analyse de l'erreur 403")
    
    # Essayer de parser le JSON de l'erreur
    try:
        error_data = json.loads(error_text)
        error_message = error_data.get("error", {}).get("message", "")
        error_status = error_data.get("error", {}).get("status", "")
    except (json.JSONDecodeError, AttributeError):
        error_message = error_text
        error_status = "UNKNOWN"
    
    # Analyser le message d'erreur pour déterminer la cause
    causes = []
    solutions = []
    
    if "API key not valid" in error_message or "invalid API key" in error_message.lower():
        causes.append("Clé API invalide")
        solutions.append("Vérifiez que la clé API est correctement saisie dans la configuration")
        solutions.append("Générez une nouvelle clé API dans la console Google Cloud")
    
    if "has not been used" in error_message or "has been disabled" in error_message:
        causes.append("API Vision non activée")
        solutions.append("Activez l'API Vision dans votre projet Google Cloud")
        solutions.append("Vérifiez que le projet associé à la clé API a l'API Vision activée")
    
    if "billing" in error_message.lower() or "enabled billing" in error_message.lower():
        causes.append("Facturation non activée")
        solutions.append("Activez la facturation pour votre projet Google Cloud")
    
    if "quota" in error_message.lower():
        causes.append("Quota dépassé")
        solutions.append("Augmentez le quota de l'API Vision dans la console Google Cloud")
        solutions.append("Attendez que le quota soit réinitialisé")
    
    if "permission" in error_message.lower() or "not authorized" in error_message.lower():
        causes.append("Permissions insuffisantes")
        solutions.append("Vérifiez les restrictions de la clé API (domaines autorisés, adresses IP, etc.)")
    
    # Si aucune cause spécifique n'a été identifiée
    if not causes:
        causes.append("Cause indéterminée")
        solutions.append("Vérifiez la console Google Cloud pour plus de détails")
        solutions.append("Essayez de générer une nouvelle clé API")
        solutions.append("Contactez le support Google Cloud")
    
    return {
        "error_message": error_message,
        "error_status": error_status,
        "causes_probables": causes,
        "solutions_recommandees": solutions
    }

def check_api_activation(api_key):
    """
    Vérifie si l'API Vision est activée dans le projet Google Cloud.
    
    Args:
        api_key (str): La clé API à tester
        
    Returns:
        dict: Résultat de la vérification
    """
    diag_logger.info("Vérification de l'activation de l'API Vision")
    
    # L'URL pour vérifier le statut de l'API
    # Note: Cette méthode est une approximation, car Google n'offre pas d'API publique
    # pour vérifier directement l'activation d'une API
    url = f"https://vision.googleapis.com/v1/operations?key={api_key}"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            diag_logger.info("L'API Vision est activée")
            return {
                "status": "success",
                "message": "L'API Vision est activée dans votre projet Google Cloud"
            }
        elif response.status_code == 403:
            # Analyser l'erreur 403 pour voir si c'est lié à l'activation de l'API
            error_details = analyze_403_error(response.text)
            if any("API Vision non activée" in cause for cause in error_details.get("causes_probables", [])):
                diag_logger.error("L'API Vision n'est pas activée")
                return {
                    "status": "error",
                    "message": "L'API Vision n'est pas activée dans votre projet Google Cloud",
                    "details": error_details
                }
            else:
                return {
                    "status": "unknown",
                    "message": "Impossible de déterminer si l'API Vision est activée",
                    "details": error_details
                }
        else:
            diag_logger.error(f"Erreur {response.status_code} lors de la vérification de l'activation de l'API")
            return {
                "status": "unknown",
                "message": f"Erreur {response.status_code} lors de la vérification de l'activation de l'API",
                "response": response.text
            }
    except requests.exceptions.RequestException as e:
        diag_logger.error(f"Erreur de connexion: {str(e)}")
        return {
            "status": "error",
            "message": f"Erreur de connexion: {str(e)}"
        }

def test_parameter_extraction(text_file_path):
    """
    Teste l'extraction de paramètres environnementaux à partir d'un fichier texte.
    
    Args:
        text_file_path (str): Chemin vers le fichier texte à analyser
        
    Returns:
        dict: Résultat de l'analyse avec les paramètres trouvés
    """
    diag_logger.info(f"Test de l'extraction de paramètres à partir de {text_file_path}")
    
    # Vérifier que le fichier existe
    if not os.path.exists(text_file_path):
        diag_logger.error(f"Le fichier {text_file_path} n'existe pas")
        return {
            "status": "error",
            "message": f"Le fichier {text_file_path} n'existe pas"
        }
    
    try:
        # Lire le contenu du fichier
        with open(text_file_path, 'r', encoding='utf-8') as file:
            text_content = file.read()
        
        # Liste des paramètres environnementaux à rechercher
        environmental_parameters = [
            "température", "temperature", "pH", "turbidité", "turbidite", "conductivité", "conductivite",
            "DBO5", "DCO", "oxygène dissous", "oxygene dissous", "phosphore", "azote", "nitrate",
            "métaux lourds", "metaux lourds", "hydrocarbures", "perméabilité", "permeabilite",
            "matière organique", "matiere organique", "carbone organique", "PM10", "PM2.5",
            "dioxyde de soufre", "SO2", "dioxyde d'azote", "NO2", "ozone", "O3",
            "monoxyde de carbone", "CO", "plomb", "Pb", "mercure", "Hg", "cadmium", "Cd",
            "arsenic", "As", "chrome", "Cr", "cuivre", "Cu", "zinc", "Zn"
        ]
        
        # Rechercher les paramètres dans le texte
        found_parameters = {}
        for param in environmental_parameters:
            # Rechercher le paramètre et son contexte
            index = text_content.lower().find(param.lower())
            if index != -1:
                # Extraire le contexte (50 caractères avant et après)
                start = max(0, index - 50)
                end = min(len(text_content), index + len(param) + 50)
                context = text_content[start:end]
                
                # Essayer d'extraire une valeur numérique
                import re
                # Rechercher un nombre après le paramètre
                value_match = re.search(r'{}\s*[:]?\s*(\d+[,.]?\d*)\s*([a-zA-Z°%]+)?'.format(re.escape(param)), 
                                        text_content[index:index+100], 
                                        re.IGNORECASE)
                
                if value_match:
                    value = value_match.group(1).replace(',', '.')
                    unit = value_match.group(2) if value_match.group(2) else ""
                    found_parameters[param] = {
                        "value": value,
                        "unit": unit,
                        "context": context
                    }
                else:
                    found_parameters[param] = {
                        "value": None,
                        "unit": None,
                        "context": context
                    }
        
        # Analyser les résultats
        if found_parameters:
            diag_logger.info(f"Paramètres trouvés: {', '.join(found_parameters.keys())}")
            return {
                "status": "success",
                "message": f"{len(found_parameters)} paramètres environnementaux trouvés",
                "parameters": found_parameters,
                "suggestions": []
            }
        else:
            diag_logger.warning("Aucun paramètre environnemental trouvé")
            
            # Analyser le contenu pour suggérer des améliorations
            suggestions = analyze_text_for_suggestions(text_content)
            
            return {
                "status": "warning",
                "message": "Aucun paramètre environnemental n'a pu être extrait du texte",
                "parameters": {},
                "suggestions": suggestions
            }
            
    except Exception as e:
        diag_logger.error(f"Erreur lors de l'analyse du fichier: {str(e)}")
        return {
            "status": "error",
            "message": f"Erreur lors de l'analyse du fichier: {str(e)}"
        }

def analyze_text_for_suggestions(text_content):
    """
    Analyse le contenu du texte pour suggérer des améliorations.
    
    Args:
        text_content (str): Le contenu du texte à analyser
        
    Returns:
        list: Liste de suggestions pour améliorer l'extraction
    """
    suggestions = []
    
    # Vérifier la longueur du texte
    if len(text_content) < 100:
        suggestions.append("Le fichier texte est très court. Assurez-vous qu'il contient suffisamment d'informations.")
    
    # Vérifier si le texte contient des mots-clés liés à l'environnement
    environmental_keywords = ["environnement", "écologie", "écologique", "pollution", "contamination", 
                             "risque", "impact", "étude d'impact", "EIE", "qualité", "eau", "air", "sol"]
    
    found_keywords = [keyword for keyword in environmental_keywords if keyword.lower() in text_content.lower()]
    
    if not found_keywords:
        suggestions.append("Le texte ne semble pas contenir de termes liés à l'environnement. "  
                         "Assurez-vous que le fichier est pertinent pour l'analyse de risque environnemental.")
    
    # Vérifier si le texte contient des unités de mesure
    units = ["°C", "mg/L", "µg/L", "ppm", "ppb", "µS/cm", "NTU", "pH", "%"]
    found_units = [unit for unit in units if unit in text_content]
    
    if not found_units:
        suggestions.append("Aucune unité de mesure n'a été trouvée dans le texte. "  
                         "L'ajout d'unités comme °C, mg/L, ppm, etc. peut aider à l'extraction des paramètres.")
    
    # Vérifier si le texte contient des tableaux ou des données structurées
    if not any(delimiter in text_content for delimiter in ["\t", ",", ";"]):
        suggestions.append("Le texte ne semble pas contenir de données tabulaires. "  
                         "L'utilisation de tableaux ou de formats structurés peut améliorer l'extraction.")
    
    # Suggestions générales
    suggestions.append("Essayez d'utiliser le mode d'analyse local si le mode cloud ne parvient pas à extraire les paramètres.")
    suggestions.append("Considérez l'ajout de mots-clés spécifiques comme 'température: 25°C' pour faciliter l'extraction.")
    
    return suggestions

def generate_report(api_test_result=None, activation_result=None, extraction_result=None):
    """
    Génère un rapport de diagnostic complet.
    
    Args:
        api_test_result (dict): Résultat du test de l'API
        activation_result (dict): Résultat de la vérification de l'activation
        extraction_result (dict): Résultat du test d'extraction
        
    Returns:
        str: Rapport au format texte
    """
    report = []
    report.append("=" * 80)
    report.append("RAPPORT DE DIAGNOSTIC - APPLICATION D'ANALYSE DE RISQUE ENVIRONNEMENTAL")
    report.append("=" * 80)
    report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("" * 80)
    
    # Section API Google Cloud Vision
    if api_test_result:
        report.append("\nI. DIAGNOSTIC DE L'API GOOGLE CLOUD VISION")
        report.append("-" * 50)
        
        if api_test_result["status"] == "success":
            report.append("✅ STATUT: OK")
            report.append(f"Message: {api_test_result['message']}")
        else:
            report.append("❌ STATUT: ERREUR")
            report.append(f"Message: {api_test_result['message']}")
            
            if "details" in api_test_result:
                report.append("\nDétails de l'erreur:")
                report.append(f"  Message d'erreur: {api_test_result['details']['error_message']}")
                report.append("\nCauses probables:")
                for cause in api_test_result['details']['causes_probables']:
                    report.append(f"  - {cause}")
                    
                report.append("\nSolutions recommandées:")
                for solution in api_test_result['details']['solutions_recommandees']:
                    report.append(f"  - {solution}")
    
    # Section Activation de l'API
    if activation_result:
        report.append("\nII. VÉRIFICATION DE L'ACTIVATION DE L'API VISION")
        report.append("-" * 50)
        
        if activation_result["status"] == "success":
            report.append("✅ STATUT: ACTIVÉE")
            report.append(f"Message: {activation_result['message']}")
        elif activation_result["status"] == "error":
            report.append("❌ STATUT: NON ACTIVÉE")
            report.append(f"Message: {activation_result['message']}")
            
            if "details" in activation_result:
                report.append("\nSolutions recommandées:")
                for solution in activation_result['details']['solutions_recommandees']:
                    report.append(f"  - {solution}")
        else:
            report.append("⚠️ STATUT: INDÉTERMINÉ")
            report.append(f"Message: {activation_result['message']}")
    
    # Section Extraction de paramètres
    if extraction_result:
        report.append("\nIII. DIAGNOSTIC DE L'EXTRACTION DE PARAMÈTRES ENVIRONNEMENTAUX")
        report.append("-" * 50)
        
        if extraction_result["status"] == "success":
            report.append("✅ STATUT: OK")
            report.append(f"Message: {extraction_result['message']}")
            
            report.append("\nParamètres trouvés:")
            for param, details in extraction_result["parameters"].items():
                value_str = f"{details['value']} {details['unit']}" if details['value'] else "(valeur non trouvée)"
                report.append(f"  - {param}: {value_str}")
                report.append(f"    Contexte: \"{details['context']}\"")
                report.append("")
        else:
            if extraction_result["status"] == "warning":
                report.append("⚠️ STATUT: AVERTISSEMENT")
            else:
                report.append("❌ STATUT: ERREUR")
                
            report.append(f"Message: {extraction_result['message']}")
            
            if extraction_result.get("suggestions"):
                report.append("\nSuggestions pour améliorer l'extraction:")
                for i, suggestion in enumerate(extraction_result["suggestions"], 1):
                    report.append(f"  {i}. {suggestion}")
    
    # Conclusion et recommandations générales
    report.append("\nIV. CONCLUSION ET RECOMMANDATIONS GÉNÉRALES")
    report.append("-" * 50)
    
    # Déterminer l'état global
    has_api_error = api_test_result and api_test_result["status"] != "success"
    has_activation_error = activation_result and activation_result["status"] == "error"
    has_extraction_error = extraction_result and extraction_result["status"] == "error"
    has_extraction_warning = extraction_result and extraction_result["status"] == "warning"
    
    if has_api_error or has_activation_error:
        report.append("⚠️ PROBLÈMES DÉTECTÉS AVEC L'API GOOGLE CLOUD VISION")
        report.append("Recommandations:")
        report.append("  1. Vérifiez que la clé API est correctement saisie dans la configuration")
        report.append("  2. Assurez-vous que l'API Vision est activée dans votre projet Google Cloud")
        report.append("  3. Vérifiez les quotas et restrictions de votre clé API")
        report.append("  4. Essayez d'utiliser un autre fournisseur d'API (OpenAI ou Azure) comme alternative")
    
    if has_extraction_error or has_extraction_warning:
        report.append("\n⚠️ PROBLÈMES DÉTECTÉS AVEC L'EXTRACTION DE PARAMÈTRES")
        report.append("Recommandations:")
        report.append("  1. Vérifiez que le fichier texte contient effectivement des informations environnementales")
        report.append("  2. Essayez d'utiliser le mode d'analyse local si le mode cloud ne parvient pas à extraire les paramètres")
        report.append("  3. Considérez l'ajout de mots-clés spécifiques dans le fichier pour faciliter l'extraction")
    
    if not (has_api_error or has_activation_error or has_extraction_error or has_extraction_warning):
        report.append("✅ AUCUN PROBLÈME MAJEUR DÉTECTÉ")
        report.append("L'application semble fonctionner correctement.")
    
    report.append("\n" + "=" * 80)
    return "\n".join(report)

def save_report(report, output_path="diagnostic_report.txt"):
    """
    Sauvegarde le rapport dans un fichier.
    
    Args:
        report (str): Le rapport à sauvegarder
        output_path (str): Le chemin du fichier de sortie
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        diag_logger.info(f"Rapport sauvegardé dans {output_path}")
        return True
    except Exception as e:
        diag_logger.error(f"Erreur lors de la sauvegarde du rapport: {str(e)}")
        return False

def main():
    """
    Fonction principale du script de diagnostic.
    """
    parser = argparse.ArgumentParser(description="Outil de diagnostic pour l'application d'analyse de risque environnemental")
    parser.add_argument("--api-key", help="Clé API Google Cloud Vision à tester")
    parser.add_argument("--text-file", help="Fichier texte à analyser pour l'extraction de paramètres")
    parser.add_argument("--output", default="diagnostic_report.txt", help="Chemin du fichier de sortie pour le rapport")
    parser.add_argument("--all", action="store_true", help="Exécuter tous les tests disponibles")
    
    args = parser.parse_args()
    
    # Récupérer la clé API de la configuration si non spécifiée
    api_key = args.api_key
    if not api_key and hasattr(CLOUD_API_CONFIG, "GOOGLE_API_KEY"):
        api_key = CLOUD_API_CONFIG.GOOGLE_API_KEY
        diag_logger.info("Utilisation de la clé API de la configuration")
    
    # Résultats des tests
    api_test_result = None
    activation_result = None
    extraction_result = None
    
    # Exécuter les tests demandés
    if api_key and (args.all or not args.text_file):
        diag_logger.info("Exécution des tests de l'API Google Cloud Vision")
        api_test_result = test_google_vision_api(api_key)
        
        if api_test_result["status"] != "success":
            activation_result = check_api_activation(api_key)
    
    if args.text_file and (args.all or not api_key):
        diag_logger.info(f"Exécution des tests d'extraction sur {args.text_file}")
        extraction_result = test_parameter_extraction(args.text_file)
    
    # Générer et sauvegarder le rapport
    report = generate_report(api_test_result, activation_result, extraction_result)
    if save_report(report, args.output):
        print(f"\nRapport de diagnostic sauvegardé dans {args.output}")
        print("\nRésumé des résultats:")
        
        if api_test_result:
            status = "✅ OK" if api_test_result["status"] == "success" else "❌ ERREUR"
            print(f"API Google Cloud Vision: {status}")
        
        if extraction_result:
            if extraction_result["status"] == "success":
                status = "✅ OK"
            elif extraction_result["status"] == "warning":
                status = "⚠️ AVERTISSEMENT"
            else:
                status = "❌ ERREUR"
            print(f"Extraction de paramètres: {status}")
    
    # Afficher le rapport complet si demandé
    if args.all:
        print(f"\n{report}")

if __name__ == "__main__":
    main()