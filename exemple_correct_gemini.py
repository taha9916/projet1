#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exemple d'utilisation correcte de l'API Gemini avec la bibliothèque officielle

Ce script montre comment utiliser correctement l'API Gemini avec la bibliothèque
officielle google.generativeai, qui est la méthode recommandée par Google.
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

# Fonction pour obtenir la clé API Gemini
def get_gemini_api_key():
    """
    Obtient la clé API Gemini depuis différentes sources.
    
    Ordre de priorité:
    1. Variable d'environnement GEMINI_API_KEY
    2. Fichier de configuration gemini_api_config.json
    3. Demande à l'utilisateur
    
    Returns:
        str: Clé API Gemini
    """
    # 1. Vérifier la variable d'environnement
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        logger.info("Clé API Gemini trouvée dans la variable d'environnement.")
        return api_key
    
    # 2. Vérifier le fichier de configuration
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gemini_api_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                api_key = config.get("api_key")
                if api_key:
                    logger.info("Clé API Gemini trouvée dans le fichier de configuration.")
                    return api_key
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du fichier de configuration: {str(e)}")
    
    # 3. Demander à l'utilisateur
    logger.info("Aucune clé API Gemini trouvée. Veuillez la saisir manuellement.")
    api_key = input("Entrez votre clé API Gemini: ")
    
    # Sauvegarder la clé API dans le fichier de configuration
    if api_key:
        try:
            config = {"api_key": api_key, "enabled": True}
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info("Clé API Gemini sauvegardée dans le fichier de configuration.")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la clé API: {str(e)}")
    
    return api_key

# Fonction principale
def main():
    """
    Fonction principale pour tester l'API Gemini.
    """
    # Vérifier si le module google.generativeai est installé
    try:
        import google.generativeai as genai
    except ImportError:
        logger.error("Le module google.generativeai n'est pas installé.")
        logger.info("Installez-le avec la commande: pip install google-generativeai")
        return 1
    
    # Obtenir la clé API Gemini
    api_key = get_gemini_api_key()
    if not api_key:
        logger.error("Aucune clé API Gemini n'a été fournie.")
        return 1
    
    # Configurer l'API Gemini
    try:
        genai.configure(api_key=api_key)
        logger.info("API Gemini configurée avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors de la configuration de l'API Gemini: {str(e)}")
        return 1
    
    # Créer un modèle génératif
    try:
        model = genai.GenerativeModel('gemini-pro')
        logger.info("Modèle génératif créé avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors de la création du modèle génératif: {str(e)}")
        return 1
    
    # Générer du contenu pour tester
    try:
        prompt = "Explique-moi comment analyser les risques environnementaux en 3 points simples."
        logger.info(f"Envoi du prompt: {prompt}")
        
        response = model.generate_content(prompt)
        
        logger.info("Réponse reçue avec succès.")
        print("\n=== Réponse de Gemini ===\n")
        print(response.text)
        print("\n=========================\n")
        
        return 0
    except Exception as e:
        logger.error(f"Erreur lors de la génération de contenu: {str(e)}")
        return 1

# Point d'entrée du script
if __name__ == "__main__":
    sys.exit(main())