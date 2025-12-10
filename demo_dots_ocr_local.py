#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Démonstration de l'utilisation de dots.ocr comme IA locale

Ce script montre comment utiliser dots.ocr pour analyser des images
et extraire des données environnementales en local.
"""

import os
import sys
import argparse
import logging
import time
from PIL import Image

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importer les fonctions nécessaires
try:
    from cloud_api import CloudVisionAPI, analyze_environmental_image_cloud
    logger.info("Module CloudVisionAPI importé avec succès.")
except ImportError as e:
    logger.error(f"Impossible d'importer CloudVisionAPI: {e}")
    logger.error("Assurez-vous que le fichier cloud_api.py est présent dans le répertoire.")
    sys.exit(1)

def analyser_image_avec_dots_ocr(image_path, prompt=None):
    """
    Analyse une image avec dots.ocr et affiche les résultats.
    
    Args:
        image_path (str): Chemin vers l'image à analyser
        prompt (str, optional): Prompt personnalisé pour l'analyse
    """
    if not os.path.exists(image_path):
        logger.error(f"L'image {image_path} n'existe pas.")
        return
    
    try:
        # Créer une instance de CloudVisionAPI avec dots_ocr comme fournisseur
        api = CloudVisionAPI(api_provider="dots_ocr")
        
        # Mesurer le temps d'exécution
        start_time = time.time()
        
        # Analyser l'image
        logger.info(f"Analyse de l'image {image_path} avec dots.ocr...")
        
        if prompt:
            # Utiliser le prompt personnalisé
            df, response = api.analyze_image(image_path, prompt)
        else:
            # Utiliser analyze_environmental_image_cloud avec dots_ocr comme fournisseur
            df, response = analyze_environmental_image_cloud(image_path, api_provider="dots_ocr")
        
        # Calculer le temps d'exécution
        execution_time = time.time() - start_time
        logger.info(f"Analyse terminée en {execution_time:.2f} secondes.")
        
        # Afficher les résultats
        print("\n" + "=" * 80)
        print("RÉSULTATS DE L'ANALYSE")
        print("=" * 80)
        
        # Afficher la réponse brute
        print("\nRéponse brute:")
        print(response)
        
        # Afficher le DataFrame s'il existe
        if df is not None and not df.empty:
            print("\nDonnées structurées:")
            print(df)
        
        # Libérer la mémoire
        if hasattr(api, 'cleanup'):
            api.cleanup()
        
        return df, response
    
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de l'image: {e}")
        return None, None

def main():
    # Configurer l'analyseur d'arguments
    parser = argparse.ArgumentParser(description="Démonstration de l'utilisation de dots.ocr comme IA locale")
    parser.add_argument("image_path", help="Chemin vers l'image à analyser")
    parser.add_argument("-p", "--prompt", help="Prompt personnalisé pour l'analyse")
    
    # Analyser les arguments
    args = parser.parse_args()
    
    # Analyser l'image
    analyser_image_avec_dots_ocr(args.image_path, args.prompt)

if __name__ == "__main__":
    main()