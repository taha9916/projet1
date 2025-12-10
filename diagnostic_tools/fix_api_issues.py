#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour diagnostiquer et corriger les problèmes d'API Google Cloud Vision (erreur 403 Forbidden).

Ce script permet de :
1. Vérifier la validité de la clé API Google Cloud Vision
2. Tester la connectivité avec l'API
3. Analyser les erreurs 403 Forbidden
4. Proposer des solutions pour résoudre les problèmes
5. Tester les API alternatives (Azure, OpenAI)
"""

import os
import sys
import json
import base64
import argparse
import requests
import webbrowser
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    from logger import setup_logging, get_logger
    from config import CLOUD_API_CONFIG
except ImportError:
    print("Erreur: Impossible d'importer les modules nécessaires.")
    print("Assurez-vous que les fichiers logger.py et config.py sont présents dans le répertoire parent.")
    sys.exit(1)

# Configuration du logger
setup_logging()
logger = get_logger(__name__)

# Constantes pour les API
API_ENDPOINTS = {
    "google": "https://vision.googleapis.com/v1/images:annotate",
    "azure": "https://{region}.api.cognitive.microsoft.com/vision/v3.2/analyze",
    "openai": "https://api.openai.com/v1/chat/completions"
}

# Chemin du fichier de configuration des API cloud
CLOUD_API_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "cloud_api_config.json"
)


class APIFixer:
    """Classe pour diagnostiquer et corriger les problèmes d'API."""

    def __init__(self):
        """Initialise le correcteur d'API."""
        self.config = self._load_cloud_api_config()
        self.test_image_path = self._create_test_image()
        self.report = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tests": {},
            "recommendations": []
        }

    def _load_cloud_api_config(self):
        """Charge la configuration des API cloud depuis le fichier JSON."""
        try:
            # Essayer d'abord d'utiliser la configuration importée
            if CLOUD_API_CONFIG:
                logger.info("Configuration des API cloud chargée depuis le module config")
                return CLOUD_API_CONFIG
        except (NameError, TypeError):
            pass
        
        # Sinon, essayer de charger depuis le fichier JSON
        try:
            if os.path.exists(CLOUD_API_CONFIG_PATH):
                with open(CLOUD_API_CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                logger.info("Configuration des API cloud chargée depuis le fichier JSON")
                return config
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {str(e)}")
        
        # Si tout échoue, retourner une configuration vide
        logger.warning("Aucune configuration d'API cloud trouvée, utilisation d'une configuration vide")
        return {"google": {}, "azure": {}, "openai": {}}

    def _create_test_image(self):
        """Crée une image de test simple pour l'API Vision."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            test_dir = Path(__file__).parent / "test_data"
            test_dir.mkdir(exist_ok=True)
            
            test_image_path = test_dir / "test_image.jpg"
            
            # Si l'image de test existe déjà, on la réutilise
            if test_image_path.exists():
                logger.info(f"Image de test existante: {test_image_path}")
                return test_image_path
            
            # Sinon, on crée une image simple
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
            img.save(test_image_path)
            logger.info(f"Image de test créée: {test_image_path}")
            return test_image_path
            
        except ImportError:
            logger.error("La bibliothèque PIL/Pillow n'est pas installée. Impossible de créer une image de test.")
            logger.info("Création d'un fichier texte comme alternative...")
            
            # Créer un fichier texte comme alternative
            test_dir = Path(__file__).parent / "test_data"
            test_dir.mkdir(exist_ok=True)
            
            test_file_path = test_dir / "test_image.txt"
            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write("Ceci est un test pour l'API Google Cloud Vision.\n")
                f.write("Paramètres environnementaux: température 25°C, pH 7.2, conductivité 500 µS/cm.")
            
            logger.info(f"Fichier texte de test créé: {test_file_path}")
            return test_file_path

    def _encode_image(self, image_path):
        """Encode une image en base64 pour l'API Vision."""
        try:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"Erreur lors de l'encodage de l'image: {str(e)}")
            return None

    def test_google_api_key(self):
        """Teste la validité de la clé API Google Cloud Vision."""
        logger.info("Test de la clé API Google Cloud Vision")
        
        # Récupérer la clé API
        api_key = self.config.get("google", {}).get("api_key", "")
        if not api_key:
            result = {
                "status": "error",
                "message": "Aucune clé API Google Cloud Vision trouvée dans la configuration",
                "solution": "Ajoutez une clé API dans le fichier cloud_api_config.json"
            }
            self.report["tests"]["google_api_key"] = result
            return result
        
        # Vérification basique du format de la clé API
        if not api_key.startswith("AIza"):
            result = {
                "status": "error",
                "message": "Format de clé API invalide. Les clés API Google Cloud commencent généralement par 'AIza'",
                "solution": "Vérifiez que vous utilisez une clé API Google Cloud valide"
            }
            self.report["tests"]["google_api_key"] = result
            return result
        
        # Vérification de la longueur de la clé
        if len(api_key) < 30:
            result = {
                "status": "warning",
                "message": "La clé API semble trop courte pour être valide",
                "solution": "Vérifiez que la clé API est complète et correctement copiée"
            }
            self.report["tests"]["google_api_key"] = result
            return result
        
        # Masquer la clé API pour le rapport
        masked_key = api_key[:6] + "*" * (len(api_key) - 10) + api_key[-4:]
        
        result = {
            "status": "success",
            "message": "La clé API semble valide en format et longueur",
            "masked_key": masked_key
        }
        self.report["tests"]["google_api_key"] = result
        return result

    def test_google_vision_api(self):
        """Teste l'API Google Cloud Vision avec une image simple."""
        logger.info("Test de l'API Google Cloud Vision")
        
        # Récupérer la clé API
        api_key = self.config.get("google", {}).get("api_key", "")
        if not api_key:
            result = {
                "status": "error",
                "message": "Aucune clé API Google Cloud Vision trouvée dans la configuration",
                "solution": "Ajoutez une clé API dans le fichier cloud_api_config.json"
            }
            self.report["tests"]["google_vision_api"] = result
            return result
        
        # Vérifier que l'image de test existe
        if not os.path.exists(self.test_image_path):
            result = {
                "status": "error",
                "message": "Image de test non trouvée",
                "solution": "Exécutez à nouveau le script pour créer une image de test"
            }
            self.report["tests"]["google_vision_api"] = result
            return result
        
        # Encoder l'image en base64
        image_content = self._encode_image(self.test_image_path)
        if not image_content:
            result = {
                "status": "error",
                "message": "Impossible d'encoder l'image en base64",
                "solution": "Vérifiez que l'image de test est accessible et valide"
            }
            self.report["tests"]["google_vision_api"] = result
            return result
        
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
            logger.debug(f"Envoi de la requête à {API_ENDPOINTS['google']}")
            response = requests.post(url, json=request_data)
            
            # Analyser la réponse
            if response.status_code == 200:
                logger.info("Test de l'API réussi: La clé API est valide et l'API est accessible")
                result = {
                    "status": "success",
                    "message": "L'API Google Cloud Vision fonctionne correctement",
                    "response": response.json()
                }
                self.report["tests"]["google_vision_api"] = result
                return result
            elif response.status_code == 403:
                logger.error(f"Erreur 403 Forbidden: {response.text}")
                result = self._analyze_403_error(response)
                self.report["tests"]["google_vision_api"] = result
                return result
            else:
                logger.error(f"Erreur {response.status_code}: {response.text}")
                result = {
                    "status": "error",
                    "code": response.status_code,
                    "message": f"Erreur {response.status_code} lors de l'appel à l'API",
                    "response": response.text,
                    "solution": "Vérifiez la documentation Google Cloud pour comprendre cette erreur spécifique"
                }
                self.report["tests"]["google_vision_api"] = result
                return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de connexion: {str(e)}")
            result = {
                "status": "error",
                "message": f"Erreur de connexion: {str(e)}",
                "solution": "Vérifiez votre connexion internet et les paramètres de proxy si applicable"
            }
            self.report["tests"]["google_vision_api"] = result
            return result

    def _analyze_403_error(self, response):
        """Analyse une erreur 403 pour déterminer la cause probable."""
        logger.info("Analyse de l'erreur 403")
        
        # Essayer de parser le JSON de l'erreur
        try:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "")
            error_status = error_data.get("error", {}).get("status", "")
        except (json.JSONDecodeError, AttributeError):
            error_message = response.text
            error_status = "UNKNOWN"
        
        # Analyser le message d'erreur pour déterminer la cause
        causes = []
        solutions = []
        
        if "API key not valid" in error_message or "invalid API key" in error_message.lower():
            causes.append("Clé API invalide")
            solutions.append("Vérifiez que la clé API est correctement saisie dans la configuration")
            solutions.append("Générez une nouvelle clé API dans la console Google Cloud")
        
        if "has not been used" in error_message or "has been disabled" in error_message or "not enabled" in error_message:
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
        
        result = {
            "status": "error",
            "code": 403,
            "message": "Erreur 403 Forbidden: Accès refusé à l'API Google Cloud Vision",
            "error_message": error_message,
            "error_status": error_status,
            "causes_probables": causes,
            "solutions_recommandees": solutions,
            "response": error_message
        }
        
        return result

    def test_alternative_apis(self):
        """Teste les API alternatives (Azure, OpenAI) pour voir si elles fonctionnent."""
        logger.info("Test des API alternatives")
        
        results = {}
        working_apis = []
        
        # Test de l'API Azure Computer Vision
        azure_config = self.config.get("azure", {})
        if azure_config.get("api_key") and azure_config.get("endpoint"):
            azure_result = self._test_azure_api()
            results["azure"] = azure_result
            if azure_result["status"] == "success":
                working_apis.append("azure")
        else:
            results["azure"] = {
                "status": "warning",
                "message": "Configuration de l'API Azure Computer Vision non trouvée",
                "solution": "Ajoutez une configuration Azure dans le fichier cloud_api_config.json"
            }
        
        # Test de l'API OpenAI
        openai_config = self.config.get("openai", {})
        if openai_config.get("api_key"):
            openai_result = self._test_openai_api()
            results["openai"] = openai_result
            if openai_result["status"] == "success":
                working_apis.append("openai")
        else:
            results["openai"] = {
                "status": "warning",
                "message": "Configuration de l'API OpenAI non trouvée",
                "solution": "Ajoutez une configuration OpenAI dans le fichier cloud_api_config.json"
            }
        
        # Ajouter les résultats au rapport
        self.report["tests"]["alternative_apis"] = results
        self.report["working_apis"] = working_apis
        
        return results

    def _test_azure_api(self):
        """Teste l'API Azure Computer Vision."""
        logger.info("Test de l'API Azure Computer Vision")
        
        azure_config = self.config.get("azure", {})
        api_key = azure_config.get("api_key", "")
        endpoint = azure_config.get("endpoint", "")
        
        if not api_key or not endpoint:
            return {
                "status": "error",
                "message": "Configuration Azure incomplète",
                "solution": "Vérifiez que la clé API et l'endpoint sont configurés"
            }
        
        # Vérifier que l'image de test existe
        if not os.path.exists(self.test_image_path):
            return {
                "status": "error",
                "message": "Image de test non trouvée",
                "solution": "Exécutez à nouveau le script pour créer une image de test"
            }
        
        # Encoder l'image en base64
        try:
            with open(self.test_image_path, "rb") as f:
                image_data = f.read()
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de l'image: {str(e)}")
            return {
                "status": "error",
                "message": f"Impossible de lire l'image de test: {str(e)}",
                "solution": "Vérifiez que l'image de test est accessible"
            }
        
        # Construire l'URL de l'API
        url = f"{endpoint}/vision/v3.2/analyze?visualFeatures=Description,Tags"
        
        # Préparer les en-têtes
        headers = {
            "Content-Type": "application/octet-stream",
            "Ocp-Apim-Subscription-Key": api_key
        }
        
        try:
            # Envoyer la requête à l'API
            response = requests.post(url, headers=headers, data=image_data)
            
            # Analyser la réponse
            if response.status_code == 200:
                logger.info("Test de l'API Azure réussi")
                return {
                    "status": "success",
                    "message": "L'API Azure Computer Vision fonctionne correctement",
                    "response": response.json()
                }
            else:
                logger.error(f"Erreur {response.status_code}: {response.text}")
                return {
                    "status": "error",
                    "code": response.status_code,
                    "message": f"Erreur {response.status_code} lors de l'appel à l'API Azure",
                    "response": response.text,
                    "solution": "Vérifiez la documentation Azure pour comprendre cette erreur"
                }
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de connexion: {str(e)}")
            return {
                "status": "error",
                "message": f"Erreur de connexion: {str(e)}",
                "solution": "Vérifiez votre connexion internet et les paramètres de proxy si applicable"
            }

    def _test_openai_api(self):
        """Teste l'API OpenAI."""
        logger.info("Test de l'API OpenAI")
        
        openai_config = self.config.get("openai", {})
        api_key = openai_config.get("api_key", "")
        
        if not api_key:
            return {
                "status": "error",
                "message": "Clé API OpenAI non trouvée",
                "solution": "Ajoutez une clé API OpenAI dans la configuration"
            }
        
        # Préparer la requête pour l'API OpenAI
        url = API_ENDPOINTS["openai"]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # Utiliser un modèle simple pour le test
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Analyze environmental risks in a simple sentence."}
            ],
            "max_tokens": 50
        }
        
        try:
            # Envoyer la requête à l'API
            response = requests.post(url, headers=headers, json=data)
            
            # Analyser la réponse
            if response.status_code == 200:
                logger.info("Test de l'API OpenAI réussi")
                return {
                    "status": "success",
                    "message": "L'API OpenAI fonctionne correctement",
                    "response": response.json()
                }
            else:
                logger.error(f"Erreur {response.status_code}: {response.text}")
                return {
                    "status": "error",
                    "code": response.status_code,
                    "message": f"Erreur {response.status_code} lors de l'appel à l'API OpenAI",
                    "response": response.text,
                    "solution": "Vérifiez la documentation OpenAI pour comprendre cette erreur"
                }
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de connexion: {str(e)}")
            return {
                "status": "error",
                "message": f"Erreur de connexion: {str(e)}",
                "solution": "Vérifiez votre connexion internet et les paramètres de proxy si applicable"
            }

    def generate_recommendations(self):
        """Génère des recommandations basées sur les résultats des tests."""
        logger.info("Génération des recommandations")
        
        recommendations = []
        
        # Vérifier si l'API Google Cloud Vision fonctionne
        google_api_test = self.report["tests"].get("google_vision_api", {})
        if google_api_test.get("status") == "success":
            recommendations.append({
                "priority": "high",
                "message": "L'API Google Cloud Vision fonctionne correctement. Aucune action n'est nécessaire."
            })
        elif google_api_test.get("status") == "error" and google_api_test.get("code") == 403:
            # Recommandations spécifiques pour l'erreur 403
            causes = google_api_test.get("causes_probables", [])
            solutions = google_api_test.get("solutions_recommandees", [])
            
            for i, cause in enumerate(causes):
                if i < len(solutions):
                    recommendations.append({
                        "priority": "high",
                        "message": f"Problème: {cause}",
                        "solution": solutions[i]
                    })
            
            # Ajouter un lien vers la console Google Cloud
            recommendations.append({
                "priority": "medium",
                "message": "Accédez à la console Google Cloud pour vérifier la configuration de votre projet",
                "solution": "https://console.cloud.google.com/apis/library/vision.googleapis.com",
                "is_link": True
            })
        
        # Vérifier les API alternatives
        working_apis = self.report.get("working_apis", [])
        if "google" not in working_apis and working_apis:
            recommendations.append({
                "priority": "high",
                "message": f"Utilisez une API alternative qui fonctionne: {', '.join(working_apis)}",
                "solution": "Dans l'application, allez dans 'Configuration' > 'Fournisseur d'API cloud' et sélectionnez une API fonctionnelle"
            })
        elif not working_apis:
            recommendations.append({
                "priority": "critical",
                "message": "Aucune API cloud ne fonctionne actuellement",
                "solution": "Configurez au moins une API cloud (Google, Azure ou OpenAI) dans le fichier cloud_api_config.json"
            })
        
        # Ajouter les recommandations au rapport
        self.report["recommendations"] = recommendations
        
        return recommendations

    def update_cloud_api_config(self, provider, api_key, endpoint=None):
        """Met à jour la configuration des API cloud."""
        logger.info(f"Mise à jour de la configuration pour le fournisseur {provider}")
        
        # Vérifier que le fournisseur est valide
        if provider not in ["google", "azure", "openai"]:
            logger.error(f"Fournisseur d'API invalide: {provider}")
            return False
        
        # Charger la configuration actuelle
        try:
            if os.path.exists(CLOUD_API_CONFIG_PATH):
                with open(CLOUD_API_CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
            else:
                config = {}
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {str(e)}")
            config = {}
        
        # Mettre à jour la configuration
        if provider not in config:
            config[provider] = {}
        
        config[provider]["api_key"] = api_key
        if endpoint and provider == "azure":
            config[provider]["endpoint"] = endpoint
        
        # Sauvegarder la configuration
        try:
            with open(CLOUD_API_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration mise à jour pour {provider}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la configuration: {str(e)}")
            return False

    def open_google_cloud_console(self):
        """Ouvre la console Google Cloud pour activer l'API Vision."""
        url = "https://console.cloud.google.com/apis/library/vision.googleapis.com"
        logger.info(f"Ouverture de la console Google Cloud: {url}")
        
        try:
            webbrowser.open(url)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture du navigateur: {str(e)}")
            return False

    def run_full_diagnostic(self):
        """Exécute un diagnostic complet des API."""
        logger.info("Exécution du diagnostic complet des API")
        
        # Étape 1: Tester la clé API Google Cloud Vision
        self.test_google_api_key()
        
        # Étape 2: Tester l'API Google Cloud Vision
        self.test_google_vision_api()
        
        # Étape 3: Tester les API alternatives
        self.test_alternative_apis()
        
        # Étape 4: Générer des recommandations
        self.generate_recommendations()
        
        return self.report

    def save_report(self, output_file=None):
        """Sauvegarde le rapport dans un fichier JSON."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path(__file__).parent / "reports"
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / f"api_fix_report_{timestamp}.json"
        
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Rapport sauvegardé: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du rapport: {str(e)}")
            return None

    def print_report_summary(self):
        """Affiche un résumé du rapport dans la console."""
        print("\n" + "=" * 80)
        print(f"RAPPORT DE DIAGNOSTIC API - {self.report['timestamp']}")
        print("=" * 80)
        
        # Résumé des tests Google
        google_key_test = self.report["tests"].get("google_api_key", {})
        google_api_test = self.report["tests"].get("google_vision_api", {})
        
        print("\nTEST DE L'API GOOGLE CLOUD VISION:")
        if google_key_test:
            print(f"  Clé API: {google_key_test['status']}")
            print(f"  Message: {google_key_test['message']}")
        
        if google_api_test:
            print(f"  API Vision: {google_api_test['status']}")
            print(f"  Message: {google_api_test['message']}")
            
            if google_api_test.get("causes_probables"):
                print("\n  Causes probables:")
                for cause in google_api_test["causes_probables"]:
                    print(f"    - {cause}")
            
            if google_api_test.get("solutions_recommandees"):
                print("\n  Solutions recommandées:")
                for solution in google_api_test["solutions_recommandees"]:
                    print(f"    - {solution}")
        
        # Résumé des API alternatives
        alt_apis = self.report["tests"].get("alternative_apis", {})
        if alt_apis:
            print("\nTEST DES API ALTERNATIVES:")
            for api, result in alt_apis.items():
                print(f"  {api.upper()}: {result['status']}")
                print(f"  Message: {result['message']}")
        
        # Résumé des recommandations
        recommendations = self.report.get("recommendations", [])
        if recommendations:
            print("\nRECOMMANDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                priority = rec.get("priority", "")
                priority_str = f"[{priority.upper()}]" if priority else ""
                print(f"  {i}. {priority_str} {rec['message']}")
                if rec.get("solution"):
                    if rec.get("is_link"):
                        print(f"     Lien: {rec['solution']}")
                    else:
                        print(f"     Solution: {rec['solution']}")
        
        # Conclusion
        working_apis = self.report.get("working_apis", [])
        if "google" in working_apis or google_api_test.get("status") == "success":
            print("\nCONCLUSION: L'API Google Cloud Vision fonctionne correctement.")
        elif working_apis:
            print(f"\nCONCLUSION: L'API Google Cloud Vision ne fonctionne pas, mais les API alternatives suivantes fonctionnent: {', '.join(working_apis)}")
            print("Vous pouvez utiliser ces API comme alternative.")
        else:
            print("\nCONCLUSION: Aucune API cloud ne fonctionne actuellement.")
            print("Suivez les recommandations ci-dessus pour résoudre les problèmes.")
        
        print("\n" + "=" * 80)


def parse_arguments():
    """Parse les arguments de ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Outil de diagnostic et de correction des problèmes d'API Google Cloud Vision"
    )
    
    parser.add_argument(
        "--update-config",
        action="store_true",
        help="Mettre à jour la configuration des API cloud"
    )
    
    parser.add_argument(
        "--provider",
        choices=["google", "azure", "openai"],
        help="Fournisseur d'API à configurer"
    )
    
    parser.add_argument(
        "--api-key",
        help="Clé API à configurer"
    )
    
    parser.add_argument(
        "--endpoint",
        help="Endpoint pour l'API Azure"
    )
    
    parser.add_argument(
        "--open-console",
        action="store_true",
        help="Ouvrir la console Google Cloud pour activer l'API Vision"
    )
    
    parser.add_argument(
        "--output",
        help="Chemin du fichier de sortie pour le rapport JSON"
    )
    
    return parser.parse_args()


def main():
    """Fonction principale."""
    args = parse_arguments()
    
    try:
        # Initialiser le correcteur d'API
        fixer = APIFixer()
        
        # Mettre à jour la configuration si demandé
        if args.update_config and args.provider and args.api_key:
            if fixer.update_cloud_api_config(args.provider, args.api_key, args.endpoint):
                print(f"Configuration mise à jour pour {args.provider}")
            else:
                print(f"Erreur lors de la mise à jour de la configuration pour {args.provider}")
            return 0
        
        # Ouvrir la console Google Cloud si demandé
        if args.open_console:
            if fixer.open_google_cloud_console():
                print("Console Google Cloud ouverte dans le navigateur")
            else:
                print("Erreur lors de l'ouverture de la console Google Cloud")
            return 0
        
        # Exécuter le diagnostic complet
        fixer.run_full_diagnostic()
        
        # Sauvegarder le rapport
        report_file = fixer.save_report(args.output)
        
        # Afficher le résumé du rapport
        fixer.print_report_summary()
        
        if report_file:
            print(f"\nRapport complet sauvegardé: {report_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution: {str(e)}")
        import traceback
        print(f"\nERREUR: {str(e)}")
        print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())