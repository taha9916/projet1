#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exemple simple de fourniture explicite d'une clé API pour Gemini

Ce script montre comment fournir explicitement une clé API Gemini
au lieu d'utiliser des variables d'environnement, en suivant l'exemple
fourni dans la documentation.
"""

from google import genai

# Fournir explicitement la clé API
def exemple_client_avec_cle_api():
    # Remplacez "YOUR_API_KEY" par votre clé API réelle
    client = genai.Client(api_key="YOUR_API_KEY")
    
    # Générer du contenu avec le modèle Gemini
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents="Explain how AI works in a few words"
    )
    
    # Afficher la réponse
    print(response.text)


# Si vous exécutez ce script directement
if __name__ == "__main__":
    # Vous pouvez également demander la clé API à l'utilisateur
    api_key = input("Entrez votre clé API Gemini: ")
    
    # Initialiser le client avec la clé API fournie
    client = genai.Client(api_key=api_key)
    
    # Générer du contenu avec le modèle Gemini
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents="Explain how AI works in a few words"
    )
    
    # Afficher la réponse
    print("\nRéponse de Gemini:")
    print(response.text)