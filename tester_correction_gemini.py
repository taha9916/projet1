#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour tester la correction du problème de clé API Gemini

Ce script teste les différentes méthodes d'utilisation de l'API Gemini
pour s'assurer que la correction fonctionne correctement.
"""

import os
import sys
import json
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Vérifier si le module google.generativeai est installé
try:
    import google.generativeai as genai
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False
    logger.warning("Le module google.generativeai n'est pas installé. Certains tests seront ignorés.")

# Importer les modules du projet
try:
    from gemini_integration import load_gemini_config, initialize_gemini_api
    from gemini_api import GeminiAPI
    PROJECT_MODULES_AVAILABLE = True
except ImportError as e:
    PROJECT_MODULES_AVAILABLE = False
    logger.error(f"Impossible d'importer les modules du projet: {str(e)}")

def test_methode_officielle():
    """
    Teste la méthode officielle d'utilisation de l'API Gemini avec google.generativeai
    """
    if not GOOGLE_GENAI_AVAILABLE:
        logger.warning("Test ignoré: Le module google.generativeai n'est pas installé.")
        return False
    
    # Charger la configuration pour obtenir la clé API
    if PROJECT_MODULES_AVAILABLE:
        config = load_gemini_config()
        api_key = config.get("api_key", "")
    else:
        # Essayer de lire directement le fichier de configuration
        try:
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gemini_api_config.json")
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                api_key = config.get("api_key", "")
        except Exception as e:
            logger.error(f"Impossible de lire le fichier de configuration: {str(e)}")
            api_key = ""
    
    # Vérifier si une clé API est définie dans la variable d'environnement
    env_api_key = os.environ.get("GEMINI_API_KEY", "")
    if env_api_key and not api_key:
        api_key = env_api_key
        logger.info("Utilisation de la clé API depuis la variable d'environnement GEMINI_API_KEY")
    
    if not api_key:
        logger.error("Aucune clé API n'est configurée.")
        return False
    
    try:
        # Configurer l'API Gemini
        genai.configure(api_key=api_key)
        
        # Créer un modèle génératif
        model = genai.GenerativeModel('gemini-pro')
        
        # Générer du contenu pour tester
        response = model.generate_content("Bonjour, comment ça va?")
        
        # Vérifier si la réponse est valide
        if response and hasattr(response, 'text'):
            logger.info(f"Test réussi: Méthode officielle avec google.generativeai")
            logger.info(f"Réponse: {response.text[:100]}...")
            return True
        else:
            logger.error(f"Test échoué: Réponse invalide")
            return False
    except Exception as e:
        logger.error(f"Test échoué: {str(e)}")
        return False

def test_methode_projet():
    """
    Teste la méthode du projet pour utiliser l'API Gemini
    """
    if not PROJECT_MODULES_AVAILABLE:
        logger.warning("Test ignoré: Les modules du projet ne sont pas disponibles.")
        return False
    
    try:
        # Initialiser l'API Gemini avec la configuration du projet
        # initialize_gemini_api retourne un tuple (gemini_api, config)
        gemini_api, config = initialize_gemini_api()
        
        if not gemini_api:
            logger.error("Impossible d'initialiser l'API Gemini.")
            return False
        
        # Générer du contenu pour tester
        response = gemini_api.generate_content("Bonjour, comment ça va?")
        
        # Vérifier si la réponse est valide
        if response and isinstance(response, dict) and 'text' in response:
            logger.info(f"Test réussi: Méthode du projet avec initialize_gemini_api()")
            logger.info(f"Réponse: {response['text'][:100]}...")
            return True
        else:
            logger.error(f"Test échoué: Réponse invalide")
            return False
    except Exception as e:
        logger.error(f"Test échoué: {str(e)}")
        return False

def test_methode_directe():
    """
    Teste la méthode directe d'utilisation de l'API Gemini avec la classe GeminiAPI
    """
    if not PROJECT_MODULES_AVAILABLE:
        logger.warning("Test ignoré: Les modules du projet ne sont pas disponibles.")
        return False
    
    # Charger la configuration pour obtenir la clé API
    config = load_gemini_config()
    api_key = config.get("api_key", "")
    
    # Vérifier si une clé API est définie dans la variable d'environnement
    env_api_key = os.environ.get("GEMINI_API_KEY", "")
    if env_api_key and not api_key:
        api_key = env_api_key
        logger.info("Utilisation de la clé API depuis la variable d'environnement GEMINI_API_KEY")
    
    if not api_key:
        logger.error("Aucune clé API n'est configurée.")
        return False
    
    try:
        # Initialiser directement la classe GeminiAPI
        gemini_api = GeminiAPI(api_key=api_key)
        
        # Générer du contenu pour tester
        response = gemini_api.generate_content("Bonjour, comment ça va?")
        
        # Vérifier si la réponse est valide
        if response and isinstance(response, dict) and 'text' in response:
            logger.info(f"Test réussi: Méthode directe avec GeminiAPI")
            logger.info(f"Réponse: {response['text'][:100]}...")
            return True
        else:
            logger.error(f"Test échoué: Réponse invalide")
            return False
    except Exception as e:
        logger.error(f"Test échoué: {str(e)}")
        return False

def main():
    """
    Fonction principale pour exécuter les tests
    """
    logger.info("=== Test de la correction du problème de clé API Gemini ===")
    
    # Tester les différentes méthodes
    results = {
        "Méthode officielle": test_methode_officielle(),
        "Méthode du projet": test_methode_projet(),
        "Méthode directe": test_methode_directe()
    }
    
    # Afficher un résumé des résultats
    logger.info("\n=== Résumé des tests ===")
    for method, success in results.items():
        status = "✅ Réussi" if success else "❌ Échoué"
        logger.info(f"{method}: {status}")
    
    # Vérifier si tous les tests ont réussi
    if all(results.values()):
        logger.info("\n✅ Tous les tests ont réussi! La correction fonctionne correctement.")
        return 0
    else:
        logger.error("\n❌ Certains tests ont échoué. La correction ne fonctionne pas correctement.")
        return 1

if __name__ == "__main__":
    sys.exit(main())