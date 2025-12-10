#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exemple d'analyse d'image environnementale avec l'API Gemini

Ce script montre comment utiliser l'API Gemini pour analyser une image
environnementale en fournissant explicitement une clé API.
"""

import os
import sys
import json
from PIL import Image
import base64
import io
import requests

# Fonction pour encoder une image en base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Fonction pour analyser une image avec l'API Gemini
def analyze_image_with_gemini(image_path, api_key):
    """
    Analyse une image environnementale avec l'API Gemini.
    
    Args:
        image_path (str): Chemin vers l'image à analyser
        api_key (str): Clé API Gemini
        
    Returns:
        dict: Résultats de l'analyse
    """
    # URL de l'API Gemini Vision
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-pro-vision:generateContent"
    
    # Encoder l'image en base64
    try:
        image_data = encode_image(image_path)
    except Exception as e:
        print(f"Erreur lors de l'encodage de l'image: {str(e)}")
        return None
    
    # Préparer les en-têtes avec la clé API
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": api_key
    }
    
    # Préparer le prompt pour l'analyse environnementale
    prompt = """
    Analyse cette image d'un point de vue environnemental. Identifie:
    1. Les risques environnementaux visibles
    2. Les polluants potentiels
    3. Les impacts sur l'écosystème
    4. Des recommandations pour améliorer la situation
    
    Réponds au format JSON avec les clés suivantes:
    - risques: liste des risques identifiés
    - polluants: liste des polluants potentiels
    - impacts: liste des impacts sur l'écosystème
    - recommandations: liste des recommandations
    """
    
    # Préparer les données de la requête
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_data
                        }
                    }
                ]
            }
        ],
        "generation_config": {
            "temperature": 0.4,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
    }
    
    # Effectuer la requête
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        # Extraire le texte de la réponse
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        
        # Essayer de parser le JSON dans la réponse
        try:
            # Chercher le début et la fin du JSON dans la réponse
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = text[start_idx:end_idx+1]
                analysis_result = json.loads(json_str)
                return analysis_result
            else:
                return {"raw_response": text}
        except json.JSONDecodeError:
            return {"raw_response": text}
            
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la requête à l'API Gemini: {str(e)}")
        if hasattr(response, 'text'):
            print(f"Détails de l'erreur: {response.text}")
        return None

# Fonction principale
def main():
    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("Usage: python exemple_analyse_image_gemini.py <chemin_image> [clé_api]")
        sys.exit(1)
    
    # Récupérer le chemin de l'image
    image_path = sys.argv[1]
    
    # Vérifier si l'image existe
    if not os.path.exists(image_path):
        print(f"Erreur: L'image {image_path} n'existe pas.")
        sys.exit(1)
    
    # Récupérer la clé API
    if len(sys.argv) > 2:
        api_key = sys.argv[2]
    else:
        # Essayer de récupérer la clé API depuis la variable d'environnement
        api_key = os.environ.get("GEMINI_API_KEY")
        
        # Si aucune clé n'est trouvée, demander à l'utilisateur
        if not api_key:
            print("Aucune clé API Gemini trouvée.")
            api_key = input("Veuillez entrer votre clé API Gemini: ")
    
    if not api_key:
        print("Erreur: Aucune clé API Gemini fournie.")
        sys.exit(1)
    
    # Analyser l'image
    print(f"Analyse de l'image {image_path}...")
    result = analyze_image_with_gemini(image_path, api_key)
    
    # Afficher les résultats
    if result:
        print("\nRésultats de l'analyse:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Erreur: Impossible d'analyser l'image.")

# Point d'entrée du script
if __name__ == "__main__":
    main()