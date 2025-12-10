#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de vérification de l'installation et de la configuration de dots.ocr

Ce script vérifie si dots.ocr est correctement installé et configuré
comme IA locale pour l'analyse d'images environnementales.
"""

import os
import sys
import json
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verifier_installation_dots_ocr():
    """
    Vérifie si dots.ocr est correctement installé et configuré.
    """
    print("\n" + "=" * 80)
    print("VÉRIFICATION DE L'INSTALLATION DE DOTS.OCR")
    print("=" * 80 + "\n")
    
    # Vérifier si le répertoire models/dots_ocr existe
    if os.path.exists("models/dots_ocr"):
        logger.info("✅ Le répertoire models/dots_ocr existe.")
        print("✅ Le modèle dots.ocr est installé.")
    else:
        logger.warning("❌ Le répertoire models/dots_ocr n'existe pas.")
        print("❌ Le modèle dots.ocr n'est pas installé.")
        print("   Pour installer dots.ocr, exécutez: python install_dots_ocr.py")
    
    # Vérifier si le fichier cloud_api_config.json existe
    if os.path.exists("cloud_api_config.json"):
        logger.info("✅ Le fichier cloud_api_config.json existe.")
        
        # Vérifier si dots_ocr est configuré comme fournisseur par défaut
        try:
            with open("cloud_api_config.json", "r") as f:
                config = json.load(f)
                
            if "default_provider" in config and config["default_provider"] == "dots_ocr":
                logger.info("✅ dots_ocr est configuré comme fournisseur par défaut.")
                print("✅ dots.ocr est configuré comme IA locale par défaut.")
            else:
                logger.warning("❌ dots_ocr n'est pas configuré comme fournisseur par défaut.")
                print("❌ dots.ocr n'est pas configuré comme IA locale par défaut.")
                print("   Pour configurer dots.ocr comme IA locale par défaut, ajoutez la ligne suivante au début de cloud_api_config.json:")
                print('   "default_provider": "dots_ocr",')            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de cloud_api_config.json: {e}")
            print(f"❌ Erreur lors de la lecture de cloud_api_config.json: {e}")
    else:
        logger.warning("❌ Le fichier cloud_api_config.json n'existe pas.")
        print("❌ Le fichier cloud_api_config.json n'existe pas.")
    
    # Vérifier si les scripts nécessaires existent
    scripts = [
        "demo_dots_ocr_local.py",
        "utiliser_dots_ocr.py",
        "utiliser_dots_ocr_api.py",
        "extraire_donnees_rapports.py",
        "demo_extraction_rapports.py"
    ]
    
    all_scripts_exist = True
    for script in scripts:
        if os.path.exists(script):
            logger.info(f"✅ Le script {script} existe.")
        else:
            logger.warning(f"❌ Le script {script} n'existe pas.")
            print(f"❌ Le script {script} n'existe pas.")
            all_scripts_exist = False
    
    if all_scripts_exist:
        print("✅ Tous les scripts nécessaires sont présents.")
    
    # Vérifier si le module cloud_api est importable
    try:
        from cloud_api import CloudVisionAPI
        logger.info("✅ Le module CloudVisionAPI est importable.")
        print("✅ Le module CloudVisionAPI est importable.")
    except ImportError as e:
        logger.error(f"❌ Impossible d'importer CloudVisionAPI: {e}")
        print(f"❌ Impossible d'importer CloudVisionAPI: {e}")
    
    print("\n" + "=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    
    if os.path.exists("models/dots_ocr") and \
       os.path.exists("cloud_api_config.json") and \
       all_scripts_exist:
        try:
            with open("cloud_api_config.json", "r") as f:
                config = json.load(f)
            
            if "default_provider" in config and config["default_provider"] == "dots_ocr":
                print("\n✅ dots.ocr est correctement installé et configuré comme IA locale par défaut.")
                print("   Vous pouvez maintenant utiliser dots.ocr pour analyser des images environnementales.")
                print("   Pour lancer une démonstration, exécutez: python demo_dots_ocr_local.py chemin/vers/image.jpg")
            else:
                print("\n⚠️ dots.ocr est installé mais n'est pas configuré comme IA locale par défaut.")
                print("   Pour configurer dots.ocr comme IA locale par défaut, ajoutez la ligne suivante au début de cloud_api_config.json:")
                print('   "default_provider": "dots_ocr",')            
        except Exception as e:
            print("\n⚠️ dots.ocr est installé mais il y a un problème avec la configuration.")
    else:
        print("\n❌ dots.ocr n'est pas correctement installé ou configuré.")
        print("   Veuillez suivre les instructions du GUIDE_DOTS_OCR.md pour installer et configurer dots.ocr.")

def main():
    verifier_installation_dots_ocr()

if __name__ == "__main__":
    main()