#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exemple simple d'utilisation de l'API Gemini

Ce script montre comment utiliser l'API Gemini de manière simple et efficace
avec la bibliothèque officielle google.generativeai et via des appels REST directs.
"""

import os
import sys
import json
import base64
import argparse
import logging
from PIL import Image
import requests

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def encode_image(image_path):
    """Encode une image en base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def generate_text_with_gemini(prompt, api_key):
    """Génère du texte avec l'API Gemini."""
    # Utiliser l'API v1 au lieu de v1beta
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': api_key
    }
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erreur: {response.status_code}")
        print(response.text)
        return None

def analyze_image_with_gemini(image_path, prompt, api_key):
    """Analyse une image avec l'API Gemini."""
    # Utiliser l'API v1 au lieu de v1beta et le modèle correct
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro-latest:generateContent"
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': api_key
    }
    
    # Encoder l'image en base64
    base64_image = encode_image(image_path)
    
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": base64_image
                        }
                    }
                ]
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erreur: {response.status_code}")
        print(response.text)
        return None

def generate_with_official_library(prompt, api_key, image_path=None):
    """Génère du contenu avec la bibliothèque officielle google.generativeai."""
    try:
        import google.generativeai as genai
    except ImportError:
        logger.error("Le module google.generativeai n'est pas installé.")
        logger.info("Installez-le avec la commande: pip install google-generativeai")
        return None
    
    # Configurer l'API Gemini
    genai.configure(api_key=api_key)
    
    try:
        # Utiliser directement les modèles connus au lieu de les lister
        # Cela évite les problèmes d'API et accélère l'exécution
        if image_path:
            # Mode vision avec modèle fixe
            logger.info("Utilisation du modèle: gemini-1.5-pro-latest")
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            
            # Charger l'image
            img = Image.open(image_path)
            response = model.generate_content([prompt, img])
        else:
            # Mode texte avec modèle fixe
            logger.info("Utilisation du modèle: gemini-pro")
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
        
        return response.text
    except Exception as e:
        logger.error(f"Erreur avec la bibliothèque officielle: {str(e)}")
        # Afficher plus de détails sur l'erreur pour faciliter le débogage
        if hasattr(e, 'status_code'):
            logger.error(f"Code d'erreur HTTP: {e.status_code}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Exemple d'utilisation de l'API Gemini")
    parser.add_argument("--api_key", help="Clé API Gemini")
    parser.add_argument("--image", help="Chemin vers l'image à analyser")
    parser.add_argument("--prompt", default="Explique comment l'IA fonctionne en quelques mots", help="Prompt à envoyer à l'API")
    parser.add_argument("--mode", choices=["text", "image"], default="text", help="Mode d'utilisation (texte ou image)")
    parser.add_argument("--method", choices=["rest", "library"], default="library", 
                        help="Méthode d'utilisation (REST API ou bibliothèque officielle)")
    
    args = parser.parse_args()
    
    # Vérifier si la clé API est fournie
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("Veuillez fournir une clé API Gemini via --api_key ou la variable d'environnement GEMINI_API_KEY")
        sys.exit(1)
    
    # Vérifier l'image si nécessaire
    if args.mode == "image" and not args.image:
        logger.error("Veuillez fournir une image via --image pour le mode image")
        sys.exit(1)
    
    if args.mode == "image" and not os.path.exists(args.image):
        logger.error(f"L'image {args.image} n'existe pas")
        sys.exit(1)
    
    # Utiliser la méthode appropriée
    if args.method == "library":
        logger.info("Utilisation de la bibliothèque officielle google.generativeai")
        text = generate_with_official_library(
            args.prompt, 
            api_key, 
            args.image if args.mode == "image" else None
        )
        if text:
            print("\n=== Réponse de Gemini (Bibliothèque Officielle) ===\n")
            print(text)
            print("\n=================================================\n")
    else:
        logger.info("Utilisation de l'API REST Gemini")
        if args.mode == "text":
            # Générer du texte
            response = generate_text_with_gemini(args.prompt, api_key)
            if response:
                try:
                    text = response["candidates"][0]["content"]["parts"][0]["text"]
                    print("\n=== Réponse de Gemini (API REST) ===\n")
                    print(text)
                    print("\n===================================\n")
                except (KeyError, IndexError) as e:
                    logger.error(f"Erreur lors de l'extraction de la réponse: {e}")
                    logger.debug("Réponse brute: %s", json.dumps(response, indent=2))
        else:
            # Analyser une image
            response = analyze_image_with_gemini(args.image, args.prompt, api_key)
            if response:
                try:
                    text = response["candidates"][0]["content"]["parts"][0]["text"]
                    print("\n=== Réponse de Gemini (API REST) ===\n")
                    print(text)
                    print("\n===================================\n")
                except (KeyError, IndexError) as e:
                    logger.error(f"Erreur lors de l'extraction de la réponse: {e}")
                    logger.debug("Réponse brute: %s", json.dumps(response, indent=2))

if __name__ == "__main__":
    main()