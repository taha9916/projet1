#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Démonstration de l'utilisation du modèle dots.ocr pour l'analyse d'images environnementales.

Ce script montre comment utiliser le modèle dots.ocr pour analyser une image environnementale
et extraire des informations pertinentes. Il utilise l'interface CloudVisionAPI intégrée
dans le projet.

Usage:
    python demo_dots_ocr.py <chemin_image> [--prompt <prompt_personnalisé>]

Exemple:
    python demo_dots_ocr.py images/site_industriel.jpg
    python demo_dots_ocr.py images/rapport_pollution.jpg --prompt "Extrais tous les tableaux et données numériques de cette image."
"""

import argparse
import os
import sys
import logging
import pandas as pd
from datetime import datetime
import torch

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ajout du répertoire courant au chemin de recherche des modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import des modules du projet
from cloud_api import CloudVisionAPI, analyze_environmental_image_cloud
from utils import extract_markdown_tables


def demo_direct_api(image_path, prompt):
    """
    Démontre l'utilisation directe de CloudVisionAPI avec dots.ocr.
    
    Args:
        image_path (str): Chemin vers l'image à analyser
        prompt (str): Prompt à utiliser pour l'analyse
        
    Returns:
        str: Réponse brute du modèle
    """
    logger.info(f"Analyse directe avec CloudVisionAPI (dots.ocr) de l'image: {image_path}")
    
    # Création de l'instance CloudVisionAPI avec dots.ocr comme fournisseur
    cloud_api = CloudVisionAPI(api_provider="dots_ocr")
    
    # Analyse de l'image
    start_time = datetime.now()
    result = cloud_api.analyze_image(
        image_path=image_path,
        prompt=prompt
    )
    end_time = datetime.now()
    
    # Calcul du temps d'exécution
    execution_time = (end_time - start_time).total_seconds()
    logger.info(f"Temps d'exécution: {execution_time:.2f} secondes")
    
    # Libération de la mémoire
    if hasattr(cloud_api, 'model'):
        del cloud_api.model
    if hasattr(cloud_api, 'processor'):
        del cloud_api.processor
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        
    return result


def demo_environmental_analysis(image_path, prompt):
    """
    Démontre l'utilisation de analyze_environmental_image_cloud avec dots.ocr.
    
    Args:
        image_path (str): Chemin vers l'image à analyser
        prompt (str): Prompt à utiliser pour l'analyse
        
    Returns:
        tuple: (DataFrame des paramètres extraits, réponse brute)
    """
    logger.info(f"Analyse environnementale avec dots.ocr de l'image: {image_path}")
    
    # Analyse de l'image avec la fonction dédiée à l'analyse environnementale
    start_time = datetime.now()
    result_df, raw_response = analyze_environmental_image_cloud(
        image_path=image_path,
        api_provider="dots_ocr",
        prompt=prompt
    )
    end_time = datetime.now()
    
    # Calcul du temps d'exécution
    execution_time = (end_time - start_time).total_seconds()
    logger.info(f"Temps d'exécution: {execution_time:.2f} secondes")
    
    # Libération de la mémoire
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        
    return result_df, raw_response


def extract_tables_from_response(response):
    """
    Extrait les tableaux Markdown de la réponse.
    
    Args:
        response (str): Réponse brute du modèle
        
    Returns:
        list: Liste de DataFrames pandas contenant les tableaux extraits
    """
    tables = extract_markdown_tables(response)
    return tables


def main():
    # Analyse des arguments de la ligne de commande
    parser = argparse.ArgumentParser(description="Démo d'utilisation du modèle dots.ocr pour l'analyse d'images environnementales")
    parser.add_argument("image_path", help="Chemin vers l'image à analyser")
    parser.add_argument("--prompt", default="Analyse cette image environnementale et identifie tous les paramètres environnementaux visibles. Extrais les données sous forme de tableau avec les colonnes 'Paramètre', 'Valeur', 'Unité' et 'Commentaire'. Si des risques environnementaux sont visibles, liste-les également.", 
                        help="Prompt personnalisé pour l'analyse")
    parser.add_argument("--mode", choices=["direct", "environmental", "both"], default="both",
                        help="Mode de démonstration: direct (CloudVisionAPI), environmental (analyze_environmental_image_cloud), ou both (les deux)")
    
    args = parser.parse_args()
    
    # Vérification de l'existence de l'image
    if not os.path.isfile(args.image_path):
        logger.error(f"L'image {args.image_path} n'existe pas.")
        sys.exit(1)
    
    # Exécution des démos selon le mode choisi
    if args.mode in ["direct", "both"]:
        print("\n" + "=" * 80)
        print("DÉMONSTRATION 1: UTILISATION DIRECTE DE CloudVisionAPI")
        print("=" * 80)
        
        raw_result = demo_direct_api(args.image_path, args.prompt)
        
        print("\nRÉSULTAT BRUT:")
        print("-" * 40)
        print(raw_result)
        
        # Extraction des tableaux si présents
        tables = extract_tables_from_response(raw_result)
        if tables:
            print("\nTABLEAUX EXTRAITS:")
            print("-" * 40)
            for i, table in enumerate(tables):
                print(f"Tableau {i+1}:")
                print(table)
                print()
    
    if args.mode in ["environmental", "both"]:
        print("\n" + "=" * 80)
        print("DÉMONSTRATION 2: UTILISATION DE analyze_environmental_image_cloud")
        print("=" * 80)
        
        result_df, raw_response = demo_environmental_analysis(args.image_path, args.prompt)
        
        print("\nRÉSULTAT BRUT:")
        print("-" * 40)
        print(raw_response)
        
        print("\nPARAMÈTRES ENVIRONNEMENTAUX EXTRAITS:")
        print("-" * 40)
        if result_df is not None and not result_df.empty:
            print(result_df)
        else:
            print("Aucun paramètre environnemental n'a été extrait sous forme de tableau.")
            
            # Tentative d'extraction manuelle des tableaux
            tables = extract_tables_from_response(raw_response)
            if tables:
                print("\nTABLEAUX EXTRAITS MANUELLEMENT:")
                print("-" * 40)
                for i, table in enumerate(tables):
                    print(f"Tableau {i+1}:")
                    print(table)
                    print()
    
    print("\n" + "=" * 80)
    print("DÉMONSTRATION TERMINÉE")
    print("=" * 80)


if __name__ == "__main__":
    main()