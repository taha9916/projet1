#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exemple de fourniture explicite d'une clé API pour Gemini

Ce script montre comment fournir explicitement une clé API Gemini
au lieu d'utiliser des variables d'environnement.
"""

import os
import sys
import json
from google import genai

# Méthode 1: Utilisation de la bibliothèque officielle google-generativeai
def exemple_client_officiel(api_key):
    """
    Exemple d'utilisation de la bibliothèque officielle avec une clé API explicite.
    
    Args:
        api_key (str): Clé API Gemini
    """
    print("\n=== Méthode 1: Utilisation de la bibliothèque officielle google-generativeai ===")
    
    # Initialiser le client avec la clé API explicite
    client = genai.Client(api_key=api_key)
    
    # Générer du contenu avec le modèle Gemini
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents="Expliquez comment l'IA fonctionne en quelques mots"
    )
    
    # Afficher la réponse
    print("\nRéponse de Gemini:")
    print(response.text)


# Méthode 2: Utilisation de l'API REST directement
def exemple_api_rest(api_key):
    """
    Exemple d'utilisation directe de l'API REST avec une clé API explicite.
    
    Args:
        api_key (str): Clé API Gemini
    """
    import requests
    
    print("\n=== Méthode 2: Utilisation directe de l'API REST ===")
    
    # URL de l'API Gemini
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    
    # En-têtes avec la clé API
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': api_key
    }
    
    # Corps de la requête
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Expliquez comment l'IA fonctionne en quelques mots"
                    }
                ]
            }
        ]
    }
    
    # Effectuer la requête
    response = requests.post(url, headers=headers, json=data)
    
    # Vérifier si la requête a réussi
    if response.status_code == 200:
        result = response.json()
        try:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            print("\nRéponse de Gemini:")
            print(text)
        except (KeyError, IndexError) as e:
            print(f"Erreur lors de l'extraction de la réponse: {e}")
            print("Réponse brute:", json.dumps(result, indent=2))
    else:
        print(f"Erreur: {response.status_code}")
        print(response.text)


# Méthode 3: Utilisation de notre classe GeminiAPI personnalisée
def exemple_classe_personnalisee(api_key):
    """
    Exemple d'utilisation de notre classe GeminiAPI personnalisée avec une clé API explicite.
    
    Args:
        api_key (str): Clé API Gemini
    """
    from gemini_api import GeminiAPI
    
    print("\n=== Méthode 3: Utilisation de notre classe GeminiAPI personnalisée ===")
    
    # Initialiser l'API Gemini avec la clé API explicite
    gemini_api = GeminiAPI(api_key)
    
    # Générer du contenu textuel
    response = gemini_api.generate_content("Expliquez comment l'IA fonctionne en quelques mots")
    
    # Afficher la réponse
    print("\nRéponse de Gemini:")
    print(json.dumps(response, indent=2, ensure_ascii=False))


# Méthode 4: Mise à jour de la configuration dans un fichier
def exemple_mise_a_jour_config(api_key):
    """
    Exemple de mise à jour de la configuration dans un fichier avec une clé API explicite.
    
    Args:
        api_key (str): Clé API Gemini
    """
    from gemini_integration import save_gemini_config, load_gemini_config, initialize_gemini_api
    
    print("\n=== Méthode 4: Mise à jour de la configuration dans un fichier ===")
    
    # Créer une configuration avec la clé API
    config = {
        "api_key": api_key,
        "enabled": True,
        "default_model": "gemini-2.0-pro-vision",
        "text_model": "gemini-2.0-flash",
        "max_tokens": 1024
    }
    
    # Sauvegarder la configuration
    save_gemini_config(config)
    print("Configuration sauvegardée avec succès.")
    
    # Charger la configuration pour vérifier
    loaded_config = load_gemini_config()
    print(f"Configuration chargée: api_key={'*'*10 if loaded_config.get('api_key') else 'Non définie'}")
    
    # Initialiser l'API Gemini avec la configuration
    gemini_api, _ = initialize_gemini_api()
    if gemini_api:
        print("API Gemini initialisée avec succès.")
    else:
        print("Échec de l'initialisation de l'API Gemini.")


def main():
    # Vérifier si une clé API est fournie en argument
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        # Sinon, essayer de la récupérer depuis la variable d'environnement
        api_key = os.environ.get("GEMINI_API_KEY")
        
        # Si aucune clé n'est trouvée, demander à l'utilisateur
        if not api_key:
            print("Aucune clé API Gemini trouvée.")
            api_key = input("Veuillez entrer votre clé API Gemini: ")
    
    if not api_key:
        print("Erreur: Aucune clé API Gemini fournie.")
        sys.exit(1)
    
    # Exécuter les exemples
    try:
        # Exemple avec la bibliothèque officielle
        exemple_client_officiel(api_key)
    except ImportError:
        print("La bibliothèque google-generativeai n'est pas installée.")
        print("Installez-la avec: pip install google-generativeai")
    except Exception as e:
        print(f"Erreur lors de l'exemple avec la bibliothèque officielle: {str(e)}")
    
    try:
        # Exemple avec l'API REST
        exemple_api_rest(api_key)
    except Exception as e:
        print(f"Erreur lors de l'exemple avec l'API REST: {str(e)}")
    
    try:
        # Exemple avec notre classe personnalisée
        exemple_classe_personnalisee(api_key)
    except Exception as e:
        print(f"Erreur lors de l'exemple avec notre classe personnalisée: {str(e)}")
    
    try:
        # Exemple de mise à jour de la configuration
        exemple_mise_a_jour_config(api_key)
    except Exception as e:
        print(f"Erreur lors de l'exemple de mise à jour de la configuration: {str(e)}")


if __name__ == "__main__":
    main()