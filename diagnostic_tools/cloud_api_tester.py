#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Outil de test et de diagnostic pour les API cloud utilisées par l'application.

Ce script permet de tester la connectivité et la configuration des différentes API cloud
(Google Cloud Vision, Azure Computer Vision, OpenAI, Hugging Face) utilisées par l'application d'analyse
de risque environnemental.
"""

import os
import sys
import json
import base64
import argparse
import requests
import time
from datetime import datetime

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer les modules nécessaires du projet
from logger import setup_logging, get_logger
from config import CLOUD_API_CONFIG
from cloud_api import CloudVisionAPI

# Configurer le logging
logger = setup_logging()
api_logger = get_logger("cloud_api_tester")

# Constantes pour les API
API_ENDPOINTS = {
    "google": "https://vision.googleapis.com/v1/images:annotate",
    "azure": "https://{region}.api.cognitive.microsoft.com/vision/v3.2/analyze",
    "openai": "https://api.openai.com/v1/chat/completions",
    "huggingface": "https://api-inference.huggingface.co/models/"
}

# Chemin de l'image de test
TEST_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "test_image.jpg")

def create_test_image():
    """
    Crée une image de test simple si elle n'existe pas déjà.
    
    Returns:
        str: Chemin vers l'image de test, ou None en cas d'erreur
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        if os.path.exists(TEST_IMAGE_PATH):
            api_logger.info(f"L'image de test existe déjà à {TEST_IMAGE_PATH}")
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
        d.text((50, 50), "Test des API Cloud Vision", fill=(0, 0, 0), font=font)
        d.text((50, 100), "Paramètres environnementaux: pH 7.2, température 25°C", fill=(0, 0, 0), font=font)
        
        # Sauvegarder l'image
        img.save(TEST_IMAGE_PATH)
        api_logger.info(f"Image de test créée à {TEST_IMAGE_PATH}")
        return TEST_IMAGE_PATH
        
    except ImportError:
        api_logger.error("La bibliothèque PIL/Pillow n'est pas installée. Impossible de créer une image de test.")
        api_logger.info("Installez PIL avec: pip install Pillow")
        return None
    except Exception as e:
        api_logger.error(f"Erreur lors de la création de l'image de test: {str(e)}")
        return None

def encode_image(image_path):
    """
    Encode une image en base64.
    
    Args:
        image_path (str): Chemin vers l'image à encoder
        
    Returns:
        str: Image encodée en base64, ou None en cas d'erreur
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        api_logger.error(f"Erreur lors de l'encodage de l'image: {str(e)}")
        return None

def test_google_vision_api(api_key):
    """
    Teste l'API Google Cloud Vision.
    
    Args:
        api_key (str): Clé API Google Cloud Vision
        
    Returns:
        dict: Résultat du test
    """
    api_logger.info("Test de l'API Google Cloud Vision")
    
    # Créer une image de test
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
    url = f"{API_ENDPOINTS['google']}?key={api_key}"
    
    try:
        # Envoyer la requête à l'API
        api_logger.debug(f"Envoi de la requête à {API_ENDPOINTS['google']}")
        response = requests.post(url, json=request_data, timeout=(10, 30))
        
        # Analyser la réponse
        if response.status_code == 200:
            api_logger.info("Test de l'API Google Cloud Vision réussi")
            return {
                "status": "success",
                "message": "L'API Google Cloud Vision est accessible et fonctionne correctement",
                "response": response.json()
            }
        else:
            api_logger.error(f"Erreur {response.status_code} lors du test de l'API Google Cloud Vision: {response.text}")
            return {
                "status": "error",
                "code": response.status_code,
                "message": f"Erreur {response.status_code} lors du test de l'API Google Cloud Vision",
                "details": analyze_error_response(response),
                "response": response.text
            }
    except requests.exceptions.RequestException as e:
        api_logger.error(f"Erreur de connexion à l'API Google Cloud Vision: {str(e)}")
        return {
            "status": "error",
            "message": f"Erreur de connexion à l'API Google Cloud Vision: {str(e)}"
        }

def test_azure_vision_api(api_key, endpoint):
    """
    Teste l'API Azure Computer Vision.
    
    Args:
        api_key (str): Clé API Azure Computer Vision
        endpoint (str): Point de terminaison de l'API Azure
        
    Returns:
        dict: Résultat du test
    """
    api_logger.info("Test de l'API Azure Computer Vision")
    
    # Créer une image de test
    image_path = create_test_image()
    if not image_path:
        return {
            "status": "error",
            "message": "Impossible de créer ou de trouver l'image de test"
        }
    
    # Préparer l'URL de l'API
    url = f"{endpoint}/vision/v3.2/analyze?visualFeatures=Tags,Description,Text"
    
    # Préparer les en-têtes
    headers = {
        "Content-Type": "application/octet-stream",
        "Ocp-Apim-Subscription-Key": api_key
    }
    
    try:
        # Lire l'image en binaire
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        
        # Envoyer la requête à l'API
        api_logger.debug(f"Envoi de la requête à {url}")
        response = requests.post(url, headers=headers, data=image_data, timeout=(10, 60))
        
        # Analyser la réponse
        if response.status_code == 200:
            api_logger.info("Test de l'API Azure Computer Vision réussi")
            return {
                "status": "success",
                "message": "L'API Azure Computer Vision est accessible et fonctionne correctement",
                "response": response.json()
            }
        else:
            api_logger.error(f"Erreur {response.status_code} lors du test de l'API Azure Computer Vision: {response.text}")
            return {
                "status": "error",
                "code": response.status_code,
                "message": f"Erreur {response.status_code} lors du test de l'API Azure Computer Vision",
                "details": analyze_error_response(response),
                "response": response.text
            }
    except requests.exceptions.RequestException as e:
        api_logger.error(f"Erreur de connexion à l'API Azure Computer Vision: {str(e)}")
        return {
            "status": "error",
            "message": f"Erreur de connexion à l'API Azure Computer Vision: {str(e)}"
        }

def test_openai_api(api_key, model="gpt-3.5-turbo"):
    """
    Teste l'API OpenAI.
    
    Args:
        api_key (str): Clé API OpenAI
        model (str): Modèle OpenAI à utiliser
        
    Returns:
        dict: Résultat du test
    """
    api_logger.info(f"Test de l'API OpenAI avec le modèle {model}")
    
    # Préparer l'URL de l'API
    url = API_ENDPOINTS['openai']
    
    # Préparer les en-têtes
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Préparer les données de la requête
    request_data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Vous êtes un assistant spécialisé dans l'analyse de risques environnementaux."},
            {"role": "user", "content": "Extrayez les paramètres suivants: température 25°C, pH 7.2"}
        ],
        "max_tokens": 150
    }
    
    try:
        # Envoyer la requête à l'API
        api_logger.debug(f"Envoi de la requête à {url}")
        response = requests.post(url, headers=headers, json=request_data, timeout=(10, 60))
        
        # Analyser la réponse
        if response.status_code == 200:
            api_logger.info("Test de l'API OpenAI réussi")
            return {
                "status": "success",
                "message": "L'API OpenAI est accessible et fonctionne correctement",
                "response": response.json()
            }
        else:
            api_logger.error(f"Erreur {response.status_code} lors du test de l'API OpenAI: {response.text}")
            return {
                "status": "error",
                "code": response.status_code,
                "message": f"Erreur {response.status_code} lors du test de l'API OpenAI",
                "details": analyze_error_response(response),
                "response": response.text
            }
    except requests.exceptions.RequestException as e:
        api_logger.error(f"Erreur de connexion à l'API OpenAI: {str(e)}")
        return {
            "status": "error",
            "message": f"Erreur de connexion à l'API OpenAI: {str(e)}"
        }

def test_huggingface_text(api_key, model="microsoft/DialoGPT-medium", api_url=None, prompt=None, max_new_tokens=128):
    """
    Teste l'API Hugging Face (texte uniquement) via Inference API.
    - Timeout et retry/backoff sur 503 (model loading)
    - Fallback vers 'gpt2' sur 404
    """
    api_logger.info(f"Test de l'API Hugging Face (texte) avec le modèle {model}")
    base_url = api_url or API_ENDPOINTS["huggingface"]
    url = f"{base_url.rstrip('/')}/{model.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    if not prompt:
        prompt = (
            "Extrayez les paramètres suivants du texte: température 25°C, pH 7.2. "
            "Répondez en une phrase en français."
        )
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": max_new_tokens, "temperature": 0.7, "return_full_text": False}
    }

    def _call(u):
        api_logger.debug(f"Appel HF: {u}")
        return requests.post(u, headers=headers, json=payload, timeout=(10, 30))

    try:
        # 1er appel
        resp = _call(url)
        if resp.status_code == 503:
            # Model loading -> attendre estimated_time puis réessayer
            wait_s = 10
            try:
                data = resp.json()
                est = float(data.get("estimated_time", 0))
                if est:
                    wait_s = max(5, min(est, 45))
            except Exception:
                pass
            api_logger.warning(f"HF 503 (loading) - attente {wait_s}s puis retry")
            time.sleep(wait_s)
            resp = _call(url)

        if resp.status_code == 404:
            # Fallback vers gpt2
            fb_model = "gpt2"
            fb_url = f"{base_url.rstrip('/')}/{fb_model}"
            api_logger.warning(f"HF 404 pour {model}. Fallback vers {fb_model}")
            resp = _call(fb_url)

        if resp.status_code != 200:
            return {
                "status": "error",
                "code": resp.status_code,
                "message": f"Erreur {resp.status_code} lors du test Hugging Face",
                "response": resp.text
            }

        # Normaliser la réponse
        j = resp.json()
        text = None
        if isinstance(j, list) and j:
            item0 = j[0]
            if isinstance(item0, dict):
                text = item0.get("generated_text") or item0.get("summary_text") or str(item0)
            else:
                text = str(item0)
        elif isinstance(j, dict):
            text = j.get("generated_text") or j.get("summary_text") or str(j)
        else:
            text = str(j)
        return {
            "status": "success",
            "message": "L'API Hugging Face (texte) a répondu correctement",
            "response": {"preview": (text or "")[:200]}
        }
    except requests.exceptions.RequestException as e:
        api_logger.error(f"Erreur de connexion à l'API Hugging Face: {str(e)}")
        return {"status": "error", "message": f"Erreur de connexion à l'API Hugging Face: {str(e)}"}

def test_huggingface_image_integration(image_path, api_key, model="microsoft/DialoGPT-medium", api_url=None, prompt=None, max_tokens=256):
    """
    Teste l'intégration Hugging Face via la classe CloudVisionAPI du projet (OCR + texte).
    Permet de valider le chargement d'image (chemins Windows avec accents), l'OCR et l'appel texte HF.
    """
    api_logger.info("Test de l'intégration Hugging Face (OCR + texte) via CloudVisionAPI")
    if not os.path.exists(image_path):
        return {"status": "error", "message": f"Image introuvable: {image_path}"}
    try:
        vision = CloudVisionAPI(api_provider="huggingface")
        # Override de la configuration pour ce test
        vision.api_key = api_key
        vision.api_endpoint = (api_url or API_ENDPOINTS["huggingface"]).rstrip("/")
        vision.model = model
        vision.max_tokens = max_tokens
        if not prompt:
            prompt = (
                "Analysez ce texte extrait d'une image environnementale et produisez un résumé court."
            )
        df, response = vision.analyze_image(image_path, prompt)
        preview = (str(response) or "")[:200]
        return {
            "status": "success",
            "message": "Intégration Hugging Face (OCR + texte) réussie",
            "response": {"preview": preview, "rows": len(df) if df is not None else 0}
        }
    except Exception as e:
        api_logger.error(f"Erreur lors du test d'intégration Hugging Face: {str(e)}")
        return {"status": "error", "message": f"Erreur d'intégration Hugging Face: {str(e)}"}

def analyze_error_response(response):
    """
    Analyse une réponse d'erreur d'API pour déterminer la cause probable.
    
    Args:
        response (Response): Objet réponse de la requête
        
    Returns:
        dict: Analyse détaillée de l'erreur
    """
    error_details = {
        "causes_probables": [],
        "solutions_recommandees": []
    }
    
    # Essayer de parser le JSON de l'erreur
    try:
        error_data = response.json()
    except (json.JSONDecodeError, ValueError):
        error_data = {"error": {"message": response.text}}
    
    # Analyser le code d'erreur HTTP
    if response.status_code == 400:
        error_details["causes_probables"].append("Requête mal formée")
        error_details["solutions_recommandees"].append("Vérifiez le format de la requête et les paramètres envoyés")
    
    elif response.status_code == 401:
        error_details["causes_probables"].append("Authentification non valide")
        error_details["solutions_recommandees"].append("Vérifiez que la clé API est correcte")
    
    elif response.status_code == 403:
        error_details["causes_probables"].append("Accès refusé")
        error_details["solutions_recommandees"].append("Vérifiez que la clé API est valide et que l'API est activée")
        error_details["solutions_recommandees"].append("Vérifiez les quotas et restrictions de la clé API")
        
        # Analyse spécifique pour Google Cloud Vision
        if "google" in response.url:
            error_message = error_data.get("error", {}).get("message", "").lower()
            
            if "api key not valid" in error_message or "invalid api key" in error_message:
                error_details["causes_probables"].append("Clé API Google Cloud Vision invalide")
                error_details["solutions_recommandees"].append("Générez une nouvelle clé API dans la console Google Cloud")
            
            if "has not been used" in error_message or "has been disabled" in error_message:
                error_details["causes_probables"].append("API Vision non activée")
                error_details["solutions_recommandees"].append("Activez l'API Vision dans votre projet Google Cloud")
            
            if "billing" in error_message:
                error_details["causes_probables"].append("Facturation non activée")
                error_details["solutions_recommandees"].append("Activez la facturation pour votre projet Google Cloud")
    
    elif response.status_code == 404:
        error_details["causes_probables"].append("Ressource non trouvée")
        error_details["solutions_recommandees"].append("Vérifiez l'URL de l'API et les paramètres de la requête")
    
    elif response.status_code == 429:
        error_details["causes_probables"].append("Quota dépassé ou limite de débit atteinte")
        error_details["solutions_recommandees"].append("Attendez avant de réessayer ou augmentez votre quota")
    
    elif response.status_code >= 500:
        error_details["causes_probables"].append("Erreur serveur")
        error_details["solutions_recommandees"].append("Réessayez plus tard ou contactez le support du fournisseur d'API")
    
    # Ajouter le message d'erreur original
    if isinstance(error_data, dict) and "error" in error_data:
        if isinstance(error_data["error"], dict) and "message" in error_data["error"]:
            error_details["message_original"] = error_data["error"]["message"]
        else:
            error_details["message_original"] = str(error_data["error"])
    else:
        error_details["message_original"] = str(error_data)
    
    return error_details

def test_all_apis():
    """
    Teste toutes les API configurées dans l'application.
    
    Returns:
        dict: Résultats des tests pour chaque API
    """
    api_logger.info("Test de toutes les API configurées")
    
    results = {}
    
    # Tester l'API Google Cloud Vision
    if hasattr(CLOUD_API_CONFIG, "GOOGLE_API_KEY") and CLOUD_API_CONFIG.GOOGLE_API_KEY:
        api_logger.info("Test de l'API Google Cloud Vision avec la clé configurée")
        results["google"] = test_google_vision_api(CLOUD_API_CONFIG.GOOGLE_API_KEY)
    else:
        api_logger.warning("Aucune clé API Google Cloud Vision configurée")
        results["google"] = {
            "status": "skipped",
            "message": "Aucune clé API Google Cloud Vision configurée"
        }
    
    # Tester l'API Azure Computer Vision
    if hasattr(CLOUD_API_CONFIG, "AZURE_API_KEY") and hasattr(CLOUD_API_CONFIG, "AZURE_ENDPOINT") and CLOUD_API_CONFIG.AZURE_API_KEY and CLOUD_API_CONFIG.AZURE_ENDPOINT:
        api_logger.info("Test de l'API Azure Computer Vision avec la clé configurée")
        results["azure"] = test_azure_vision_api(CLOUD_API_CONFIG.AZURE_API_KEY, CLOUD_API_CONFIG.AZURE_ENDPOINT)
    else:
        api_logger.warning("Configuration incomplète pour l'API Azure Computer Vision")
        results["azure"] = {
            "status": "skipped",
            "message": "Configuration incomplète pour l'API Azure Computer Vision"
        }
    
    # Tester l'API OpenAI
    if hasattr(CLOUD_API_CONFIG, "OPENAI_API_KEY") and CLOUD_API_CONFIG.OPENAI_API_KEY:
        api_logger.info("Test de l'API OpenAI avec la clé configurée")
        model = CLOUD_API_CONFIG.OPENAI_MODEL if hasattr(CLOUD_API_CONFIG, "OPENAI_MODEL") else "gpt-3.5-turbo"
        results["openai"] = test_openai_api(CLOUD_API_CONFIG.OPENAI_API_KEY, model)
    else:
        api_logger.warning("Aucune clé API OpenAI configurée")
        results["openai"] = {
            "status": "skipped",
            "message": "Aucune clé API OpenAI configurée"
        }
    
    # Tester l'API Hugging Face
    if hasattr(CLOUD_API_CONFIG, "HUGGINGFACE_API_KEY") and CLOUD_API_CONFIG.HUGGINGFACE_API_KEY:
        api_logger.info("Test de l'API Hugging Face avec la clé configurée")
        model = CLOUD_API_CONFIG.HUGGINGFACE_MODEL if hasattr(CLOUD_API_CONFIG, "HUGGINGFACE_MODEL") else "microsoft/DialoGPT-medium"
        results["huggingface"] = test_huggingface_text(CLOUD_API_CONFIG.HUGGINGFACE_API_KEY, model)
    else:
        api_logger.warning("Aucune clé API Hugging Face configurée")
        results["huggingface"] = {
            "status": "skipped",
            "message": "Aucune clé API Hugging Face configurée"
        }
    
    return results

def generate_report(results):
    """
    Génère un rapport de test des API.
    
    Args:
        results (dict): Résultats des tests pour chaque API
        
    Returns:
        str: Rapport au format texte
    """
    report = []
    report.append("=" * 80)
    report.append("RAPPORT DE TEST DES API CLOUD")
    report.append("=" * 80)
    report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("" * 80)
    
    # Résumé global
    success_count = sum(1 for api, result in results.items() if result["status"] == "success")
    error_count = sum(1 for api, result in results.items() if result["status"] == "error")
    skipped_count = sum(1 for api, result in results.items() if result["status"] == "skipped")
    
    report.append("\nRÉSUMÉ:")
    report.append(f"Total des API testées: {len(results)}")
    report.append(f"Succès: {success_count}")
    report.append(f"Erreurs: {error_count}")
    report.append(f"Non testées: {skipped_count}")
    
    # Détails pour chaque API
    for api_name, result in results.items():
        report.append("\n" + "-" * 50)
        if api_name == "google":
            report.append("API GOOGLE CLOUD VISION:")
        elif api_name == "azure":
            report.append("API AZURE COMPUTER VISION:")
        elif api_name == "openai":
            report.append("API OPENAI:")
        elif api_name == "huggingface":
            report.append("API HUGGING FACE:")
        else:
            report.append(f"API {api_name.upper()}:")
        
        if result["status"] == "success":
            report.append("✅ STATUT: OK")
            report.append(f"Message: {result['message']}")
        elif result["status"] == "error":
            report.append("❌ STATUT: ERREUR")
            report.append(f"Message: {result['message']}")
            
            if "details" in result:
                report.append("\nDétails de l'erreur:")
                if "message_original" in result["details"]:
                    report.append(f"  Message d'erreur: {result['details']['message_original']}")
                
                if "causes_probables" in result["details"] and result["details"]["causes_probables"]:
                    report.append("\nCauses probables:")
                    for cause in result["details"]["causes_probables"]:
                        report.append(f"  - {cause}")
                
                if "solutions_recommandees" in result["details"] and result["details"]["solutions_recommandees"]:
                    report.append("\nSolutions recommandées:")
                    for solution in result["details"]["solutions_recommandees"]:
                        report.append(f"  - {solution}")
        else:  # skipped
            report.append("⚠️ STATUT: NON TESTÉ")
            report.append(f"Message: {result['message']}")
    
    # Recommandations générales
    report.append("\n" + "-" * 50)
    report.append("RECOMMANDATIONS GÉNÉRALES:")
    
    if error_count > 0:
        report.append("\n1. Pour les API en erreur:")
        if "google" in results and results["google"]["status"] == "error":
            report.append("   - Vérifiez que la clé API Google Cloud Vision est correctement saisie")
            report.append("   - Assurez-vous que l'API Vision est activée dans votre projet Google Cloud")
            report.append("   - Vérifiez les quotas et restrictions de votre clé API")
        
        if "azure" in results and results["azure"]["status"] == "error":
            report.append("   - Vérifiez que la clé API Azure et le point de terminaison sont correctement saisis")
            report.append("   - Assurez-vous que le service Computer Vision est provisionné dans votre abonnement Azure")
        
        if "openai" in results and results["openai"]["status"] == "error":
            report.append("   - Vérifiez que la clé API OpenAI est correctement saisie")
            report.append("   - Assurez-vous que votre compte OpenAI est actif et dispose de crédits suffisants")
        
        if "huggingface" in results and results["huggingface"]["status"] == "error":
            report.append("   - Vérifiez que la clé API Hugging Face est correctement saisie")
            report.append("   - Assurez-vous que votre compte Hugging Face est actif et dispose de crédits suffisants")
    
    report.append("\n2. Configuration recommandée:")
    report.append("   - Configurez plusieurs fournisseurs d'API pour assurer la redondance")
    report.append("   - Utilisez le mode d'analyse local comme solution de secours en cas de problème avec les API cloud")
    
    report.append("\n" + "=" * 80)
    return "\n".join(report)

def save_report(report, output_path="api_test_report.txt"):
    """
    Sauvegarde le rapport dans un fichier.
    
    Args:
        report (str): Le rapport à sauvegarder
        output_path (str): Le chemin du fichier de sortie
        
    Returns:
        bool: True si la sauvegarde a réussi, False sinon
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        api_logger.info(f"Rapport sauvegardé dans {output_path}")
        return True
    except Exception as e:
        api_logger.error(f"Erreur lors de la sauvegarde du rapport: {str(e)}")
        return False

def main():
    """
    Fonction principale du script de test des API.
    """
    parser = argparse.ArgumentParser(description="Outil de test des API cloud")
    parser.add_argument("--google-key", help="Clé API Google Cloud Vision à tester")
    parser.add_argument("--azure-key", help="Clé API Azure Computer Vision à tester")
    parser.add_argument("--azure-endpoint", help="Point de terminaison de l'API Azure Computer Vision")
    parser.add_argument("--openai-key", help="Clé API OpenAI à tester")
    parser.add_argument("--openai-model", default="gpt-3.5-turbo", help="Modèle OpenAI à utiliser")
    parser.add_argument("--output", default="api_test_report.txt", help="Chemin du fichier de sortie pour le rapport")
    parser.add_argument("--all", action="store_true", help="Tester toutes les API configurées")
    # Hugging Face
    parser.add_argument("--huggingface-key", help="Clé API Hugging Face à tester")
    parser.add_argument("--huggingface-model", default="microsoft/DialoGPT-medium", help="Modèle Hugging Face à utiliser")
    parser.add_argument("--huggingface-url", default=API_ENDPOINTS.get("huggingface", "https://api-inference.huggingface.co/models/"), help="Base URL de l'API Hugging Face")
    parser.add_argument("--huggingface-prompt", help="Prompt texte à utiliser pour le test Hugging Face")
    parser.add_argument("--huggingface-image", help="Chemin d'une image pour tester l'intégration (OCR + texte)")
    parser.add_argument("--huggingface-text-only", action="store_true", help="Forcer le test texte uniquement (sans OCR)")
    parser.add_argument("--huggingface-max-tokens", type=int, default=128, help="max_new_tokens pour Hugging Face")
    
    args = parser.parse_args()
    
    # Déterminer quelles API tester
    if args.all:
        # Tester toutes les API configurées
        results = test_all_apis()
    else:
        results = {}
        
        # Tester l'API Google Cloud Vision si une clé est fournie
        if args.google_key:
            api_logger.info("Test de l'API Google Cloud Vision avec la clé fournie")
            results["google"] = test_google_vision_api(args.google_key)
        elif not args.azure_key and not args.openai_key and hasattr(CLOUD_API_CONFIG, "GOOGLE_API_KEY") and CLOUD_API_CONFIG.GOOGLE_API_KEY:
            # Utiliser la clé configurée si aucune autre API n'est spécifiée
            api_logger.info("Test de l'API Google Cloud Vision avec la clé configurée")
            results["google"] = test_google_vision_api(CLOUD_API_CONFIG.GOOGLE_API_KEY)
        
        # Tester l'API Azure Computer Vision si une clé et un endpoint sont fournis
        if args.azure_key and args.azure_endpoint:
            api_logger.info("Test de l'API Azure Computer Vision avec la clé et l'endpoint fournis")
            results["azure"] = test_azure_vision_api(args.azure_key, args.azure_endpoint)
        
        # Tester l'API OpenAI si une clé est fournie
        if args.openai_key:
            api_logger.info(f"Test de l'API OpenAI avec la clé fournie et le modèle {args.openai_model}")
            results["openai"] = test_openai_api(args.openai_key, args.openai_model)
        
        # Tester Hugging Face si une clé est fournie
        if args.huggingface_key:
            if args.huggingface_image and not args.huggingface_text_only:
                api_logger.info("Test Hugging Face via intégration (OCR + texte)")
                results["huggingface"] = test_huggingface_image_integration(
                    image_path=args.huggingface_image,
                    api_key=args.huggingface_key,
                    model=args.huggingface_model,
                    api_url=args.huggingface_url,
                    prompt=args.huggingface_prompt,
                    max_tokens=args.huggingface_max_tokens,
                )
            else:
                api_logger.info("Test Hugging Face (texte uniquement)")
                results["huggingface"] = test_huggingface_text(
                    api_key=args.huggingface_key,
                    model=args.huggingface_model,
                    api_url=args.huggingface_url,
                    prompt=args.huggingface_prompt,
                    max_new_tokens=args.huggingface_max_tokens,
                )
    
    # Générer et sauvegarder le rapport
    if results:
        report = generate_report(results)
        if save_report(report, args.output):
            print(f"\nRapport de test des API sauvegardé dans {args.output}")
            
            # Afficher un résumé
            print("\nRésumé des tests:")
            for api_name, result in results.items():
                status = "✅ OK" if result["status"] == "success" else "❌ ERREUR" if result["status"] == "error" else "⚠️ NON TESTÉ"
                print(f"API {api_name.upper()}: {status}")
        
        # Afficher des recommandations spécifiques pour les erreurs 403 avec Google Cloud Vision
        if "google" in results and results["google"]["status"] == "error" and results["google"].get("code") == 403:
            print("\nRecommandations pour résoudre l'erreur 403 avec Google Cloud Vision:")
            print("1. Vérifiez que la clé API est correctement saisie dans la configuration")
            print("2. Assurez-vous que l'API Vision est activée dans votre projet Google Cloud:")
            print("   - Accédez à la console Google Cloud: https://console.cloud.google.com")
            print("   - Sélectionnez votre projet")
            print("   - Allez dans 'API et services' > 'Bibliothèque'")
            print("   - Recherchez 'Vision API' et activez-la")
            print("3. Vérifiez que la facturation est activée pour votre projet Google Cloud")
            print("4. Essayez d'utiliser un autre fournisseur d'API (Azure ou OpenAI) comme alternative")
    else:
        print("Aucune API n'a été testée. Utilisez --help pour voir les options disponibles.")

if __name__ == "__main__":
    main()