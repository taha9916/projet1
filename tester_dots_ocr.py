#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de test rapide pour dots.ocr

Ce script teste rapidement dots.ocr sur une image d'exemple
pour vérifier que l'IA locale fonctionne correctement.
"""

import os
import sys
import logging
import time
from PIL import Image

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Vérifier si le module CloudVisionAPI est disponible
try:
    from cloud_api import CloudVisionAPI
    logger.info("Module CloudVisionAPI importé avec succès.")
except ImportError as e:
    logger.error(f"Impossible d'importer CloudVisionAPI: {e}")
    logger.error("Assurez-vous que le fichier cloud_api.py est présent dans le répertoire.")
    sys.exit(1)

def tester_dots_ocr():
    """
    Teste dots.ocr sur une image d'exemple.
    """
    print("\n" + "=" * 80)
    print("TEST RAPIDE DE DOTS.OCR")
    print("=" * 80 + "\n")
    
    # Vérifier si le répertoire exemples existe
    if not os.path.exists("exemples"):
        os.makedirs("exemples")
        logger.info("Répertoire exemples créé.")
    
    # Créer une image de test simple avec du texte
    image_path = "exemples/test_dots_ocr.png"
    
    try:
        # Créer une image de test si elle n'existe pas déjà
        if not os.path.exists(image_path):
            from PIL import Image, ImageDraw, ImageFont
            
            # Créer une image blanche
            img = Image.new('RGB', (800, 600), color=(255, 255, 255))
            d = ImageDraw.Draw(img)
            
            # Essayer de charger une police
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except IOError:
                font = ImageFont.load_default()
            
            # Ajouter du texte environnemental
            texte = [
                "RAPPORT D'ANALYSE ENVIRONNEMENTALE",
                "",
                "Site: Zone industrielle de Casablanca",
                "Date: 15 juin 2023",
                "",
                "PARAMÈTRES MESURÉS:",
                "- Qualité de l'air: PM2.5 = 35 µg/m³, PM10 = 75 µg/m³",
                "- Qualité de l'eau: pH = 7.2, Turbidité = 5 NTU",
                "- Bruit: 68 dB",
                "- Température: 28°C",
                "",
                "OBSERVATIONS:",
                "Présence de déchets industriels non traités",
                "Émissions de fumées noires visibles",
                "Odeurs chimiques détectées à proximité du canal d'évacuation",
                "",
                "RECOMMANDATIONS:",
                "1. Installer des filtres sur les cheminées d'évacuation",
                "2. Mettre en place un système de traitement des eaux usées",
                "3. Établir un plan de gestion des déchets solides"
            ]
            
            y_position = 50
            for ligne in texte:
                d.text((50, y_position), ligne, fill=(0, 0, 0), font=font)
                y_position += 25
            
            # Sauvegarder l'image
            img.save(image_path)
            logger.info(f"Image de test créée: {image_path}")
        
        # Analyser l'image avec dots.ocr
        print(f"Analyse de l'image {image_path} avec dots.ocr...")
        
        # Créer une instance de CloudVisionAPI avec dots_ocr comme fournisseur
        api = CloudVisionAPI(api_provider="dots_ocr")
        
        # Mesurer le temps d'exécution
        start_time = time.time()
        
        # Analyser l'image avec un prompt environnemental
        prompt = "Extrais toutes les informations environnementales de cette image, y compris les paramètres mesurés, les observations et les recommandations."
        df, response = api.analyze_image(image_path, prompt)
        
        # Calculer le temps d'exécution
        execution_time = time.time() - start_time
        
        # Afficher les résultats
        print(f"\nAnalyse terminée en {execution_time:.2f} secondes.")
        print("\nRésultat de l'analyse:")
        print("=" * 80)
        print(response)
        print("=" * 80)
        
        if df is not None and not df.empty:
            print("\nDonnées structurées:")
            print(df)
        
        # Libérer la mémoire
        if hasattr(api, 'cleanup'):
            api.cleanup()
        
        print("\n✅ Test de dots.ocr réussi!")
        return True
    
    except Exception as e:
        logger.error(f"Erreur lors du test de dots.ocr: {e}")
        print(f"\n❌ Erreur lors du test de dots.ocr: {e}")
        return False

def main():
    tester_dots_ocr()

if __name__ == "__main__":
    main()