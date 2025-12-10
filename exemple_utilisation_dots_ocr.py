#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exemple d'utilisation de la classe DotsOCRModel pour l'analyse d'images.

Ce script montre comment utiliser la classe DotsOCRModel pour analyser des images
avec le modèle dots.ocr de manière optimisée et robuste.
"""

import os
import sys
import logging
import argparse
from PIL import Image
import torch

# Import de la classe DotsOCRModel
from dots_ocr_model import DotsOCRModel

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyser_image(image_path, prompt=None, force_cpu=False):
    """
    Analyse une image avec le modèle dots.ocr.
    
    Args:
        image_path (str): Chemin vers l'image à analyser.
        prompt (str, optional): Instructions pour l'analyse.
        force_cpu (bool): Force l'utilisation du CPU même si un GPU est disponible.
        
    Returns:
        str: Résultat de l'analyse ou None en cas d'erreur.
    """
    # Créer une instance de DotsOCRModel
    model = DotsOCRModel()
    
    # Configurer pour CPU si demandé
    if force_cpu:
        model.device_map = "cpu"
        model.torch_dtype = torch.float32
        model.load_in_4bit = False
        logger.info("Utilisation forcée du CPU pour l'analyse")
    
    try:
        # Analyser l'image
        logger.info(f"Analyse de l'image: {image_path}")
        resultat = model.analyze_image(image_path, prompt)
        
        return resultat
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {str(e)}")
        return None
    finally:
        # Libérer la mémoire
        model.unload_model()

def main():
    # Configurer l'analyseur d'arguments
    parser = argparse.ArgumentParser(description="Analyse d'images avec dots.ocr")
    parser.add_argument("image_path", help="Chemin vers l'image à analyser")
    parser.add_argument("--prompt", help="Instructions pour l'analyse", default=None)
    parser.add_argument("--cpu", help="Force l'utilisation du CPU", action="store_true")
    parser.add_argument("--output", help="Chemin pour sauvegarder le résultat", default=None)
    
    # Analyser les arguments
    args = parser.parse_args()
    
    # Vérifier que l'image existe
    if not os.path.exists(args.image_path):
        logger.error(f"L'image {args.image_path} n'existe pas")
        return 1
    
    # Analyser l'image
    resultat = analyser_image(args.image_path, args.prompt, args.cpu)
    
    # Afficher et sauvegarder le résultat
    if resultat:
        print("\nRésultat de l'analyse:")
        print("=======================")
        print(resultat)
        print("=======================")
        
        # Sauvegarder le résultat si demandé
        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(resultat)
                logger.info(f"Résultat sauvegardé dans {args.output}")
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde du résultat: {str(e)}")
        
        return 0
    else:
        logger.error("Échec de l'analyse de l'image")
        return 1

if __name__ == "__main__":
    sys.exit(main())