#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script d'installation de la bibliothèque officielle google-generativeai

Ce script vérifie si la bibliothèque google-generativeai est installée
et l'installe si nécessaire.
"""

import os
import sys
import subprocess
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_package_installed(package_name):
    """
    Vérifie si un package Python est installé.
    
    Args:
        package_name (str): Nom du package à vérifier.
        
    Returns:
        bool: True si le package est installé, False sinon.
    """
    try:
        __import__(package_name.replace('-', '.'))
        return True
    except ImportError:
        return False

def install_package(package_name):
    """
    Installe un package Python avec pip.
    
    Args:
        package_name (str): Nom du package à installer.
        
    Returns:
        bool: True si l'installation a réussi, False sinon.
    """
    try:
        logger.info(f"Installation du package {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        logger.info(f"Package {package_name} installé avec succès.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de l'installation du package {package_name}: {str(e)}")
        return False

def verify_installation():
    """
    Vérifie si l'installation a réussi en important le module.
    
    Returns:
        bool: True si l'importation réussit, False sinon.
    """
    try:
        import google.generativeai
        logger.info(f"Module google.generativeai importé avec succès (version {google.generativeai.__version__}).")
        return True
    except (ImportError, AttributeError) as e:
        logger.error(f"Erreur lors de l'importation du module google.generativeai: {str(e)}")
        return False

def main():
    """
    Fonction principale pour installer la bibliothèque google-generativeai.
    """
    logger.info("Vérification de l'installation de google-generativeai...")
    
    # Vérifier si le package est déjà installé
    if check_package_installed('google.generativeai'):
        logger.info("Le package google-generativeai est déjà installé.")
    else:
        logger.info("Le package google-generativeai n'est pas installé.")
        
        # Installer le package
        if not install_package('google-generativeai'):
            logger.error("Impossible d'installer le package google-generativeai.")
            return 1
    
    # Vérifier l'installation
    if not verify_installation():
        logger.error("L'installation du package google-generativeai a échoué.")
        return 1
    
    logger.info("Installation de google-generativeai terminée avec succès.")
    
    # Afficher un message d'aide pour l'utilisation
    print("\n=== Comment utiliser google-generativeai ===\n")
    print("1. Importez le module:")
    print("   import google.generativeai as genai")
    print("\n2. Configurez l'API avec votre clé:")
    print("   genai.configure(api_key=\"VOTRE_CLE_API\")")
    print("\n3. Créez un modèle génératif:")
    print("   model = genai.GenerativeModel('gemini-pro')")
    print("\n4. Générez du contenu:")
    print("   response = model.generate_content(\"Votre prompt ici\")")
    print("   print(response.text)")
    print("\n===========================================\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())