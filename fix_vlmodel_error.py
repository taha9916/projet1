#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour corriger l'erreur "VLModel object has no attribute load_model".

Ce script applique la solution recommandée dans le guide de dépannage
en remplaçant l'objet VLModel par l'adaptateur VLModelAdapter.
"""

import os
import sys
import logging
import argparse

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ajouter le répertoire courant au chemin de recherche des modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import de l'adaptateur VLModel
from vlmodel_adapter import create_vlmodel_adapter

def patch_app_vlmodel():
    """
    Applique un patch à l'application pour utiliser l'adaptateur VLModel.
    
    Cette fonction modifie le fichier app.py pour remplacer l'initialisation
    de VLModel par l'adaptateur VLModelAdapter.
    """
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
    
    if not os.path.exists(app_path):
        logger.error(f"Le fichier app.py n'existe pas à l'emplacement: {app_path}")
        return False
    
    # Lire le contenu du fichier app.py
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si l'adaptateur est déjà importé
    if "from vlmodel_adapter import" in content:
        logger.info("L'adaptateur VLModel est déjà importé dans app.py")
        return True
    
    # Remplacer l'import de VLModel
    content = content.replace(
        "from model_interface import analyze_environmental_image, VLModel",
        "from model_interface import analyze_environmental_image\nfrom vlmodel_adapter import create_vlmodel_adapter, VLModelAdapter"
    )
    
    # Remplacer l'initialisation de VLModel
    content = content.replace(
        "self.model = VLModel(model_path)",
        "self.model = create_vlmodel_adapter(model_path)"
    )
    
    # Sauvegarder les modifications
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("Le fichier app.py a été modifié avec succès pour utiliser l'adaptateur VLModel")
    return True

def main():
    """
    Fonction principale du script.
    """
    parser = argparse.ArgumentParser(description="Corrige l'erreur 'VLModel object has no attribute load_model'")
    parser.add_argument('--patch-app', action='store_true', help="Applique un patch à l'application pour utiliser l'adaptateur VLModel")
    args = parser.parse_args()
    
    if args.patch_app:
        if patch_app_vlmodel():
            logger.info("L'application a été corrigée avec succès")
        else:
            logger.error("Impossible de corriger l'application")
    else:
        # Afficher les instructions pour corriger manuellement l'erreur
        print("\nGuide de correction de l'erreur 'VLModel object has no attribute load_model':\n")
        print("1. Remplacez l'import de VLModel dans votre code:")
        print("   Avant: from model_interface import VLModel")
        print("   Après: from vlmodel_adapter import create_vlmodel_adapter, VLModelAdapter\n")
        print("2. Remplacez l'initialisation de VLModel:")
        print("   Avant: model = VLModel(model_path)")
        print("   Après: model = create_vlmodel_adapter(model_path)\n")
        print("3. Pour appliquer automatiquement ces modifications à app.py, exécutez:")
        print("   python fix_vlmodel_error.py --patch-app\n")

if __name__ == "__main__":
    main()