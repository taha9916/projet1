#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de démonstration pour l'utilisation de VLModelAdapter avec SmolVLM-Instruct
"""

import os
import sys
import logging
import argparse
from PIL import Image
from vlmodel_adapter import VLModelAdapter

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse les arguments de ligne de commande"""
    parser = argparse.ArgumentParser(description='Démonstration de VLModelAdapter avec SmolVLM-Instruct')
    parser.add_argument('--image', type=str, help='Chemin vers l\'image à analyser')
    parser.add_argument('--prompt', type=str, default='Décris cette image en détail.', 
                        help='Prompt à utiliser pour l\'analyse de l\'image')
    parser.add_argument('--model', type=str, default='HuggingFaceTB/SmolVLM-Instruct',
                        help='Nom ou chemin du modèle à utiliser')
    return parser.parse_args()

def create_test_image(output_path):
    """Crée une image de test simple si aucune image n'est fournie"""
    # Créer une image simple avec un fond blanc et un cercle rouge
    width, height = 300, 200
    image = Image.new('RGB', (width, height), color='white')
    
    # Dessiner un cercle rouge
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    draw.ellipse((100, 50, 200, 150), fill='red')
    
    # Dessiner un carré bleu
    draw.rectangle((50, 50, 100, 100), fill='blue')
    
    # Dessiner un triangle vert
    draw.polygon([(250, 50), (200, 150), (300, 150)], fill='green')
    
    # Sauvegarder l'image
    image.save(output_path)
    logger.info(f"Image de test créée et sauvegardée à {output_path}")
    return output_path

def display_image(image_path):
    """Affiche des informations sur l'image"""
    try:
        with Image.open(image_path) as img:
            print(f"\nInformations sur l'image:")
            print(f"- Chemin: {image_path}")
            print(f"- Dimensions: {img.width}x{img.height}")
            print(f"- Format: {img.format}")
            print(f"- Mode: {img.mode}\n")
    except Exception as e:
        logger.warning(f"Impossible d'afficher les informations de l'image: {e}")

def main():
    """Fonction principale"""
    args = parse_arguments()
    
    # Vérifier si une image a été fournie, sinon créer une image de test
    image_path = args.image
    if not image_path:
        image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_image.png')
        create_test_image(image_path)
    
    # Vérifier si l'image existe
    if not os.path.exists(image_path):
        logger.error(f"L'image {image_path} n'existe pas.")
        sys.exit(1)
    
    # Afficher des informations sur l'image
    display_image(image_path)
    
    # Initialiser l'adaptateur et charger le modèle
    logger.info(f"Initialisation de l'adaptateur avec le modèle {args.model}...")
    adapter = VLModelAdapter(args.model)
    
    logger.info("Chargement du modèle...")
    if not adapter.load_model():
        logger.error("Échec du chargement du modèle.")
        sys.exit(1)
    
    # Analyser l'image
    logger.info(f"Analyse de l'image avec le prompt: '{args.prompt}'")
    try:
        # Mesurer le temps d'inférence
        import time
        start_time = time.time()
        
        response = adapter.analyze_image(image_path, args.prompt)
        
        inference_time = time.time() - start_time
        logger.info(f"Temps d'inférence: {inference_time:.2f} secondes")
        
        print("\n" + "=" * 80)
        print(f"PROMPT: {args.prompt}")
        print("-" * 80)
        print(f"RÉPONSE:")
        print("-" * 80)
        print(f"{response}")
        print("=" * 80 + "\n")
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de l'image: {e}")
        sys.exit(1)
    
    # Décharger le modèle
    logger.info("Déchargement du modèle...")
    adapter.unload_model()
    
    logger.info("Démonstration terminée avec succès.")

if __name__ == "__main__":
    main()