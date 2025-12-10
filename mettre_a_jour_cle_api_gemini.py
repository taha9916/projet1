#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour mettre à jour la clé API Gemini dans l'application

Ce script permet de mettre à jour la clé API Gemini dans le fichier de configuration
de l'application d'analyse de risque environnemental.
"""

import os
import sys
import json
import argparse

# Importer les fonctions nécessaires depuis le module gemini_integration
try:
    from gemini_integration import load_gemini_config, save_gemini_config, initialize_gemini_api
except ImportError:
    print("Erreur: Impossible d'importer les modules nécessaires.")
    print("Assurez-vous que le fichier gemini_integration.py est présent dans le répertoire courant.")
    sys.exit(1)

def update_gemini_api_key(api_key, enable=True):
    """
    Met à jour la clé API Gemini dans le fichier de configuration.
    
    Args:
        api_key (str): Nouvelle clé API Gemini
        enable (bool): Activer ou désactiver l'API Gemini
        
    Returns:
        bool: True si la mise à jour a réussi, False sinon
    """
    # Charger la configuration actuelle
    config = load_gemini_config()
    
    # Mettre à jour la clé API et l'état d'activation
    config["api_key"] = api_key
    config["enabled"] = enable
    
    # Sauvegarder la configuration
    return save_gemini_config(config)

def test_gemini_api(api_key):
    """
    Teste la clé API Gemini en effectuant une requête simple.
    
    Args:
        api_key (str): Clé API Gemini à tester
        
    Returns:
        bool: True si le test a réussi, False sinon
    """
    try:
        # Créer une configuration temporaire pour le test
        temp_config = {
            "api_key": api_key,
            "enabled": True,
            "default_model": "gemini-2.0-pro-vision",
            "text_model": "gemini-2.0-flash",
            "max_tokens": 1024
        }
        
        # Sauvegarder temporairement la configuration
        save_gemini_config(temp_config)
        
        # Initialiser l'API Gemini avec la configuration
        gemini_api, _ = initialize_gemini_api()
        
        if not gemini_api:
            print("Erreur: Impossible d'initialiser l'API Gemini.")
            return False
        
        # Effectuer une requête simple pour tester la clé API
        response = gemini_api.generate_content("Test de la clé API Gemini")
        
        # Vérifier si la requête a réussi
        if response and isinstance(response, dict) and "error" not in response:
            print("Test réussi: La clé API Gemini est valide.")
            return True
        else:
            print("Erreur: La clé API Gemini est invalide ou la requête a échoué.")
            if isinstance(response, dict) and "error" in response:
                print(f"Détails de l'erreur: {response['error']}")
            return False
            
    except Exception as e:
        print(f"Erreur lors du test de la clé API Gemini: {str(e)}")
        return False

def main():
    # Configurer l'analyseur d'arguments
    parser = argparse.ArgumentParser(description="Met à jour la clé API Gemini dans le fichier de configuration")
    parser.add_argument("--api_key", help="Nouvelle clé API Gemini")
    parser.add_argument("--enable", action="store_true", help="Activer l'API Gemini")
    parser.add_argument("--disable", action="store_true", help="Désactiver l'API Gemini")
    parser.add_argument("--test", action="store_true", help="Tester la clé API Gemini")
    parser.add_argument("--show", action="store_true", help="Afficher la configuration actuelle")
    
    args = parser.parse_args()
    
    # Afficher la configuration actuelle si demandé
    if args.show:
        config = load_gemini_config()
        print("Configuration actuelle de l'API Gemini:")
        print(f"  API Key: {'*'*10 if config.get('api_key') else 'Non définie'}")
        print(f"  Enabled: {config.get('enabled', False)}")
        print(f"  Default Model: {config.get('default_model', 'gemini-2.0-pro-vision')}")
        print(f"  Text Model: {config.get('text_model', 'gemini-2.0-flash')}")
        print(f"  Max Tokens: {config.get('max_tokens', 1024)}")
        return
    
    # Tester la clé API actuelle si demandé
    if args.test and not args.api_key:
        config = load_gemini_config()
        if not config.get("api_key"):
            print("Erreur: Aucune clé API Gemini n'est définie dans la configuration.")
            return
        
        print("Test de la clé API Gemini actuelle...")
        test_gemini_api(config["api_key"])
        return
    
    # Vérifier si une nouvelle clé API est fournie
    if args.api_key:
        # Déterminer l'état d'activation
        enable = True
        if args.disable:
            enable = False
        
        # Tester la clé API si demandé
        if args.test:
            print(f"Test de la nouvelle clé API Gemini...")
            if not test_gemini_api(args.api_key):
                print("La mise à jour de la configuration a été annulée.")
                return
        
        # Mettre à jour la configuration
        print(f"Mise à jour de la clé API Gemini...")
        if update_gemini_api_key(args.api_key, enable):
            print("La clé API Gemini a été mise à jour avec succès.")
            print(f"L'API Gemini est maintenant {'activée' if enable else 'désactivée'}.")
        else:
            print("Erreur: Impossible de mettre à jour la clé API Gemini.")
    elif args.enable or args.disable:
        # Activer ou désactiver l'API Gemini sans changer la clé API
        config = load_gemini_config()
        if not config.get("api_key"):
            print("Erreur: Aucune clé API Gemini n'est définie dans la configuration.")
            print("Veuillez fournir une clé API avec l'option --api_key.")
            return
        
        enable = args.enable
        config["enabled"] = enable
        
        if save_gemini_config(config):
            print(f"L'API Gemini est maintenant {'activée' if enable else 'désactivée'}.")
        else:
            print("Erreur: Impossible de mettre à jour la configuration de l'API Gemini.")
    else:
        # Aucune option spécifiée, afficher l'aide
        parser.print_help()

# Point d'entrée du script
if __name__ == "__main__":
    main()