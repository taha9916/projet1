#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comparaison des performances entre dots.ocr et les autres API cloud.

Ce script compare les performances (temps d'exécution, qualité des résultats) du modèle
dots.ocr avec les autres API cloud disponibles dans le projet (OpenAI, Azure, Google, etc.).

Usage:
    python compare_ocr_models.py <chemin_image> [--providers <liste_fournisseurs>] [--prompt <prompt>]

Exemple:
    python compare_ocr_models.py images/rapport.jpg
    python compare_ocr_models.py images/tableau.jpg --providers dots_ocr,openai,google
"""

import argparse
import os
import sys
import logging
import pandas as pd
import time
from datetime import datetime
import torch
import json

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ajout du répertoire courant au chemin de recherche des modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import des modules du projet
from cloud_api import CloudVisionAPI
from utils import extract_markdown_tables

# Liste des fournisseurs disponibles
AVAILABLE_PROVIDERS = ["dots_ocr", "openai", "azure", "google", "qwen", "openrouter"]


def load_api_config():
    """
    Charge la configuration des API depuis le fichier cloud_api_config.json.
    
    Returns:
        dict: Configuration des API
    """
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloud_api_config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration des API: {e}")
        return {}


def get_available_providers():
    """
    Détermine les fournisseurs d'API disponibles en fonction de la configuration.
    
    Returns:
        list: Liste des fournisseurs disponibles
    """
    config = load_api_config()
    available = ["dots_ocr"]  # dots.ocr est toujours disponible car local
    
    # Vérification des autres fournisseurs
    if config.get("openai", {}).get("api_key"):
        available.append("openai")
    if config.get("azure", {}).get("api_key"):
        available.append("azure")
    if config.get("google", {}).get("api_key"):
        available.append("google")
    if config.get("qwen", {}).get("api_key"):
        available.append("qwen")
    if config.get("openrouter", {}).get("api_key"):
        available.append("openrouter")
    
    return available


def compare_providers(image_path, providers, prompt):
    """
    Compare les performances des différents fournisseurs d'API.
    
    Args:
        image_path (str): Chemin vers l'image à analyser
        providers (list): Liste des fournisseurs à comparer
        prompt (str): Prompt à utiliser pour l'analyse
        
    Returns:
        dict: Résultats de la comparaison
    """
    results = {}
    
    for provider in providers:
        logger.info(f"Test du fournisseur: {provider}")
        
        try:
            # Création de l'instance CloudVisionAPI
            cloud_api = CloudVisionAPI(api_provider=provider)
            
            # Analyse de l'image avec mesure du temps d'exécution
            start_time = time.time()
            response = cloud_api.analyze_image(
                image_path=image_path,
                prompt=prompt
            )
            end_time = time.time()
            
            # Calcul du temps d'exécution
            execution_time = end_time - start_time
            
            # Extraction des tableaux si présents
            tables = extract_markdown_tables(response)
            
            # Stockage des résultats
            results[provider] = {
                "execution_time": execution_time,
                "response": response,
                "tables": tables,
                "table_count": len(tables),
                "response_length": len(response)
            }
            
            logger.info(f"Fournisseur {provider}: Temps d'exécution = {execution_time:.2f}s, Tableaux extraits = {len(tables)}")
            
            # Libération de la mémoire pour dots.ocr
            if provider == "dots_ocr":
                if hasattr(cloud_api, 'model'):
                    del cloud_api.model
                if hasattr(cloud_api, 'processor'):
                    del cloud_api.processor
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    
        except Exception as e:
            logger.error(f"Erreur avec le fournisseur {provider}: {e}")
            results[provider] = {
                "error": str(e),
                "execution_time": None,
                "response": None,
                "tables": [],
                "table_count": 0,
                "response_length": 0
            }
    
    return results


def create_comparison_table(results):
    """
    Crée un tableau de comparaison des performances.
    
    Args:
        results (dict): Résultats de la comparaison
        
    Returns:
        pandas.DataFrame: Tableau de comparaison
    """
    data = []
    
    for provider, result in results.items():
        data.append({
            "Fournisseur": provider,
            "Temps d'exécution (s)": round(result["execution_time"], 2) if result["execution_time"] else None,
            "Longueur de la réponse": result["response_length"],
            "Nombre de tableaux extraits": result["table_count"],
            "Erreur": result.get("error", "")
        })
    
    return pd.DataFrame(data)


def save_results(results, output_dir="results"):
    """
    Sauvegarde les résultats de la comparaison.
    
    Args:
        results (dict): Résultats de la comparaison
        output_dir (str): Répertoire de sortie
    """
    # Création du répertoire de sortie s'il n'existe pas
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Génération d'un nom de fichier basé sur la date et l'heure
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"comparison_{timestamp}"
    
    # Sauvegarde du tableau de comparaison
    comparison_table = create_comparison_table(results)
    comparison_table.to_csv(os.path.join(output_dir, f"{base_filename}_summary.csv"), index=False)
    
    # Sauvegarde des réponses brutes
    for provider, result in results.items():
        if result["response"]:
            with open(os.path.join(output_dir, f"{base_filename}_{provider}.txt"), "w", encoding="utf-8") as f:
                f.write(result["response"])
    
    # Sauvegarde des tableaux extraits
    for provider, result in results.items():
        if result["tables"]:
            for i, table in enumerate(result["tables"]):
                table.to_csv(os.path.join(output_dir, f"{base_filename}_{provider}_table_{i+1}.csv"), index=False)
    
    logger.info(f"Résultats sauvegardés dans le répertoire {output_dir}")


def main():
    # Analyse des arguments de la ligne de commande
    parser = argparse.ArgumentParser(description="Comparaison des performances entre dots.ocr et les autres API cloud")
    parser.add_argument("image_path", help="Chemin vers l'image à analyser")
    parser.add_argument("--providers", help="Liste des fournisseurs à comparer, séparés par des virgules")
    parser.add_argument("--prompt", default="Analyse cette image et extrais toutes les informations pertinentes. Si des tableaux sont présents, extrais-les sous forme de tableaux Markdown.", 
                        help="Prompt à utiliser pour l'analyse")
    parser.add_argument("--output", default="results", help="Répertoire de sortie pour les résultats")
    
    args = parser.parse_args()
    
    # Vérification de l'existence de l'image
    if not os.path.isfile(args.image_path):
        logger.error(f"L'image {args.image_path} n'existe pas.")
        sys.exit(1)
    
    # Détermination des fournisseurs disponibles
    available_providers = get_available_providers()
    logger.info(f"Fournisseurs disponibles: {', '.join(available_providers)}")
    
    # Sélection des fournisseurs à comparer
    if args.providers:
        providers = [p.strip() for p in args.providers.split(",")]
        # Vérification que les fournisseurs spécifiés sont disponibles
        for provider in providers:
            if provider not in available_providers:
                logger.warning(f"Le fournisseur {provider} n'est pas disponible et sera ignoré.")
        providers = [p for p in providers if p in available_providers]
    else:
        providers = available_providers
    
    if not providers:
        logger.error("Aucun fournisseur disponible pour la comparaison.")
        sys.exit(1)
    
    logger.info(f"Fournisseurs sélectionnés pour la comparaison: {', '.join(providers)}")
    
    # Comparaison des fournisseurs
    results = compare_providers(args.image_path, providers, args.prompt)
    
    # Affichage du tableau de comparaison
    comparison_table = create_comparison_table(results)
    print("\nRÉSULTATS DE LA COMPARAISON:")
    print("-" * 80)
    print(comparison_table)
    print("-" * 80)
    
    # Sauvegarde des résultats
    save_results(results, args.output)
    
    print(f"\nLes résultats détaillés ont été sauvegardés dans le répertoire {args.output}")


if __name__ == "__main__":
    main()