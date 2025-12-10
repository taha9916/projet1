#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de démonstration pour l'utilisation de l'API Gemini dans le projet d'analyse environnementale.

Ce script montre comment utiliser la classe GeminiAPI pour analyser des images environnementales
et générer des rapports d'analyse.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, Optional
from gemini_api import GeminiAPI

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_arguments():
    """
    Parse les arguments de ligne de commande.
    
    Returns:
        argparse.Namespace: Arguments parsés.
    """
    parser = argparse.ArgumentParser(description="Démo de l'API Gemini pour l'analyse environnementale")
    parser.add_argument("--image", "-i", type=str, help="Chemin vers l'image à analyser")
    parser.add_argument("--prompt", "-p", type=str, help="Prompt personnalisé pour l'analyse")
    parser.add_argument("--api-key", "-k", type=str, help="Clé API Gemini (si non définie dans l'environnement)")
    parser.add_argument("--output", "-o", type=str, help="Chemin du fichier de sortie pour les résultats (JSON)")
    parser.add_argument("--text-only", "-t", action="store_true", help="Utiliser uniquement l'API de texte (sans image)")
    parser.add_argument("--query", "-q", type=str, help="Requête textuelle pour l'API (mode texte uniquement)")
    
    return parser.parse_args()

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Sauvegarde les résultats dans un fichier JSON.
    
    Args:
        results (Dict[str, Any]): Résultats à sauvegarder.
        output_path (str): Chemin du fichier de sortie.
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Résultats sauvegardés dans {output_path}")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des résultats: {str(e)}")

def analyze_environmental_image(api: GeminiAPI, image_path: str, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyse une image environnementale avec l'API Gemini.
    
    Args:
        api (GeminiAPI): Instance de l'API Gemini.
        image_path (str): Chemin vers l'image à analyser.
        custom_prompt (str, optional): Prompt personnalisé pour l'analyse.
        
    Returns:
        Dict[str, Any]: Résultats de l'analyse.
    """
    if not os.path.exists(image_path):
        logger.error(f"L'image {image_path} n'existe pas.")
        return {"erreur": f"L'image {image_path} n'existe pas."}
    
    try:
        if custom_prompt:
            # Utiliser le prompt personnalisé
            response = api.analyze_image(image_path, custom_prompt)
            return {"texte_brut": response}
        else:
            # Utiliser la fonction d'analyse environnementale
            return api.analyze_environmental_image(image_path)
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de l'image: {str(e)}")
        return {"erreur": str(e)}

def main():
    """
    Fonction principale du script de démonstration.
    """
    args = parse_arguments()
    
    # Initialiser l'API Gemini
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY") or "AIzaSyA7QfEziIgen9FNoJHb4G6imoBKeySQauE"
    gemini_api = GeminiAPI(api_key)
    
    if args.text_only:
        # Mode texte uniquement
        query = args.query or "Expliquez les principaux risques environnementaux dans les zones industrielles."
        logger.info(f"Génération de contenu textuel avec la requête: {query}")
        response = gemini_api.generate_content(query)
        results = {"texte_brut": response}
        print("\nRéponse:")
        print("-" * 50)
        print(response)
        print("-" * 50)
    elif args.image:
        # Mode analyse d'image
        logger.info(f"Analyse de l'image: {args.image}")
        results = analyze_environmental_image(gemini_api, args.image, args.prompt)
        print("\nRésultats de l'analyse:")
        print("-" * 50)
        print(json.dumps(results, indent=2, ensure_ascii=False))
        print("-" * 50)
    else:
        logger.error("Aucune image ou requête textuelle spécifiée. Utilisez --image ou --text-only avec --query.")
        sys.exit(1)
    
    # Sauvegarder les résultats si un chemin de sortie est spécifié
    if args.output:
        save_results(results, args.output)

if __name__ == "__main__":
    main()