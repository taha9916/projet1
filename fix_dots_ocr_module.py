#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour corriger l'erreur de module manquant pour dots.ocr.

Ce script crée le module transformers_modules.rednote-hilab.dots
qui est nécessaire pour charger le modèle dots.ocr correctement.
"""

import os
import sys
import logging
import shutil

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_dots_ocr_module():
    """
    Crée le module transformers_modules.rednote-hilab.dots qui est manquant.
    """
    try:
        # Trouver le répertoire transformers_modules
        import transformers
        transformers_path = os.path.dirname(transformers.__file__)
        modules_path = os.path.join(transformers_path, "transformers_modules")
        
        # Créer le répertoire s'il n'existe pas
        os.makedirs(modules_path, exist_ok=True)
        
        # Créer le répertoire rednote-hilab
        vendor_path = os.path.join(modules_path, "rednote-hilab")
        os.makedirs(vendor_path, exist_ok=True)
        
        # Créer le répertoire dots
        dots_path = os.path.join(vendor_path, "dots")
        os.makedirs(dots_path, exist_ok=True)
        
        # Créer un fichier __init__.py vide dans chaque répertoire
        with open(os.path.join(modules_path, "__init__.py"), "w") as f:
            f.write("# Module transformers_modules\n")
        
        with open(os.path.join(vendor_path, "__init__.py"), "w") as f:
            f.write("# Module rednote-hilab\n")
        
        with open(os.path.join(dots_path, "__init__.py"), "w") as f:
            f.write("# Module dots\n")
        
        logger.info(f"Module transformers_modules.rednote-hilab.dots créé avec succès dans {dots_path}")
        return True
    
    except Exception as e:
        logger.error(f"Erreur lors de la création du module: {str(e)}")
        return False

def main():
    """
    Fonction principale.
    """
    logger.info("Correction du module manquant pour dots.ocr...")
    
    if fix_dots_ocr_module():
        logger.info("Correction terminée avec succès.")
        logger.info("Vous pouvez maintenant utiliser le modèle dots.ocr comme modèle par défaut.")
    else:
        logger.error("Échec de la correction du module.")
        logger.error("Veuillez vérifier les permissions et réessayer.")

if __name__ == "__main__":
    main()