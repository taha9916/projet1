#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour corriger les problèmes de clé API Gemini

Ce script permet de diagnostiquer et corriger les problèmes courants
liés à la configuration et l'utilisation de la clé API Gemini,
y compris l'erreur "'str' object has no attribute 'items'".
"""

import os
import sys
import json
import requests
import argparse

# Importer les fonctions nécessaires depuis les modules existants
try:
    from gemini_integration import load_gemini_config, save_gemini_config, initialize_gemini_api
    from gemini_api import GeminiAPI
except ImportError:
    print("Erreur: Impossible d'importer les modules nécessaires.")
    print("Assurez-vous que les fichiers gemini_integration.py et gemini_api.py sont présents.")
    sys.exit(1)

def verifier_cle_api(api_key):
    """
    Vérifie si la clé API Gemini est valide en effectuant une requête de test.
    
    Args:
        api_key (str): Clé API Gemini à vérifier
        
    Returns:
        tuple: (bool, str) - (Succès, Message d'erreur ou de succès)
    """
    if not api_key or api_key.strip() == "":
        return False, "La clé API est vide."
    
    # Vérifier le format de la clé API (commence généralement par "AIza")
    if not api_key.startswith("AIza"):
        return False, "Format de clé API incorrect. Les clés API Gemini commencent généralement par 'AIza'."
    
    # Effectuer une requête de test simple à l'API Gemini
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": "Test de la clé API Gemini"}
                ]
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            return True, "La clé API est valide et fonctionne correctement."
        elif response.status_code == 400:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "Erreur inconnue")
            return False, f"Erreur de requête: {error_message}"
        elif response.status_code == 401 or response.status_code == 403:
            return False, "Clé API invalide ou non autorisée. Vérifiez que la clé est correcte et activée."
        else:
            return False, f"Erreur de l'API (code {response.status_code}): {response.text}"
    except Exception as e:
        return False, f"Erreur lors de la vérification de la clé API: {str(e)}"

def verifier_configuration_gemini():
    """
    Vérifie la configuration actuelle de l'API Gemini.
    
    Returns:
        tuple: (bool, str) - (Succès, Message d'erreur ou de succès)
    """
    config = load_gemini_config()
    
    if not config.get("api_key"):
        return False, "Aucune clé API n'est configurée."
    
    if not config.get("enabled", False):
        return False, "L'API Gemini est désactivée dans la configuration."
    
    # Vérifier si la clé API est valide
    return verifier_cle_api(config["api_key"])

def corriger_probleme_cle_api(nouvelle_cle=None):
    """
    Corrige les problèmes courants avec la clé API Gemini.
    
    Args:
        nouvelle_cle (str, optional): Nouvelle clé API à configurer
        
    Returns:
        bool: True si la correction a réussi, False sinon
    """
    try:
        config = load_gemini_config()
        
        # Si une nouvelle clé est fournie, la configurer
        if nouvelle_cle:
            config["api_key"] = nouvelle_cle
        
        # S'assurer que l'API est activée
        config["enabled"] = True
        
        # Vérifier que les modèles sont correctement configurés
        if not config.get("default_model") or config.get("default_model") == "":
            config["default_model"] = "gemini-2.0-pro-vision"
        
        if not config.get("text_model") or config.get("text_model") == "":
            config["text_model"] = "gemini-2.0-flash"
        
        # Sauvegarder la configuration
        print(f"Tentative de sauvegarde de la configuration: {config}")
        return save_gemini_config(config)
    except Exception as e:
        print(f"Erreur détaillée lors de la correction du problème de clé API: {str(e)}")
        return False

def detecter_probleme_str_items():
    """
    Détecte et corrige le problème spécifique "'str' object has no attribute 'items'"
    qui peut survenir lors de la sauvegarde de la configuration Gemini.
    
    Returns:
        tuple: (bool, str) - (Problème détecté, Message d'information)
    """
    config_path = os.path.join(os.path.dirname(__file__), "gemini_api_config.json")
    
    if not os.path.exists(config_path):
        return False, "Le fichier de configuration n'existe pas."
    
    try:
        # Vérifier le contenu du fichier
        with open(config_path, "r") as f:
            content = f.read().strip()
        
        # Vérifier si le contenu est une simple chaîne au lieu d'un JSON
        if content and not content.startswith("{"):
            print(f"Problème détecté: Le fichier de configuration contient une chaîne au lieu d'un JSON.")
            print(f"Contenu actuel: {content[:50]}..." if len(content) > 50 else content)
            
            # Créer un dictionnaire de configuration correct
            corrected_config = {
                "api_key": content,  # Utiliser la chaîne comme clé API
                "default_models": {
                    "text": "gemini-pro",
                    "vision": "gemini-1.5-pro-latest"
                },
                "max_tokens": 2048,
                "enabled": True
            }
            
            # Sauvegarder la configuration corrigée
            with open(config_path, "w") as f:
                json.dump(corrected_config, f, indent=4)
            
            return True, "Problème 'str' object has no attribute 'items' corrigé avec succès."
        
        # Vérifier si le contenu est un JSON valide
        try:
            config = json.loads(content)
            if not isinstance(config, dict):
                # Convertir en dictionnaire si ce n'est pas déjà le cas
                corrected_config = {
                    "api_key": str(config),
                    "default_models": {
                        "text": "gemini-pro",
                        "vision": "gemini-1.5-pro-latest"
                    },
                    "max_tokens": 2048,
                    "enabled": True
                }
                
                # Sauvegarder la configuration corrigée
                with open(config_path, "w") as f:
                    json.dump(corrected_config, f, indent=4)
                
                return True, "Problème de format de configuration corrigé avec succès."
        except json.JSONDecodeError:
            return True, "Le fichier de configuration n'est pas un JSON valide, mais sera corrigé par la fonction corriger_probleme_cle_api."
        
        return False, "Aucun problème 'str' object has no attribute 'items' détecté."
    except Exception as e:
        return False, f"Erreur lors de la détection du problème: {str(e)}"

    config = load_gemini_config()
    
    # Si une nouvelle clé est fournie, la configurer
    if nouvelle_cle:
        config["api_key"] = nouvelle_cle
    
    # S'assurer que l'API est activée
    config["enabled"] = True
    
    # Vérifier que les modèles sont correctement configurés
    if not config.get("default_model") or config.get("default_model") == "":
        config["default_model"] = "gemini-2.0-pro-vision"
    
    if not config.get("text_model") or config.get("text_model") == "":
        config["text_model"] = "gemini-2.0-flash"
    
    # Sauvegarder la configuration
    return save_gemini_config(config)

def verifier_environnement():
    """
    Vérifie si la variable d'environnement GEMINI_API_KEY est définie.
    
    Returns:
        tuple: (bool, str) - (Définie, Valeur ou message)
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return True, api_key
    else:
        return False, "La variable d'environnement GEMINI_API_KEY n'est pas définie."

def main():
    parser = argparse.ArgumentParser(description="Diagnostique et corrige les problèmes de clé API Gemini")
    parser.add_argument("--cle", help="Nouvelle clé API Gemini à configurer")
    parser.add_argument("--verifier", action="store_true", help="Vérifier la configuration actuelle")
    parser.add_argument("--corriger", action="store_true", help="Corriger les problèmes de configuration")
    parser.add_argument("--fix-str-items", action="store_true", help="Corriger spécifiquement le problème 'str' object has no attribute 'items'")
    parser.add_argument("--diagnostic-complet", action="store_true", help="Exécuter un diagnostic complet et corriger tous les problèmes détectés")
    parser.add_argument("--env", action="store_true", help="Vérifier la variable d'environnement GEMINI_API_KEY")
    
    args = parser.parse_args()
    
    # Si aucune option n'est spécifiée, exécuter toutes les vérifications
    if not (args.verifier or args.corriger or args.env or args.cle or args.fix_str_items or args.diagnostic_complet):
        args.verifier = True
        args.env = True
        args.fix_str_items = True
    
    # Vérifier la configuration actuelle
    if args.verifier:
        print("\n=== Vérification de la configuration de l'API Gemini ===")
        succes, message = verifier_configuration_gemini()
        if succes:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
    
    # Vérifier la variable d'environnement
    if args.env:
        print("\n=== Vérification de la variable d'environnement GEMINI_API_KEY ===")
        definie, message = verifier_environnement()
        if definie:
            print(f"✅ Variable d'environnement définie: {message[:5]}...")
            # Vérifier si la clé dans la variable d'environnement est valide
            succes, msg = verifier_cle_api(message)
            if succes:
                print(f"✅ La clé API dans la variable d'environnement est valide.")
            else:
                print(f"❌ La clé API dans la variable d'environnement est invalide: {msg}")
        else:
            print(f"❌ {message}")
    
    # Corriger spécifiquement le problème 'str' object has no attribute 'items'
    if args.fix_str_items or args.diagnostic_complet:
        print("\n=== Vérification et correction du problème 'str' object has no attribute 'items' ===")
        probleme_detecte, message = detecter_probleme_str_items()
        if probleme_detecte:
            print(f"✅ {message}")
        else:
            print(f"ℹ️ {message}")
    
    # Corriger les problèmes de configuration
    if args.corriger or args.cle or args.diagnostic_complet:
        print("\n=== Correction de la configuration de l'API Gemini ===")
        
        # Si une nouvelle clé est fournie, l'utiliser
        nouvelle_cle = args.cle
        
        # Si aucune clé n'est fournie mais que la variable d'environnement est définie, l'utiliser
        if not nouvelle_cle:
            definie, env_key = verifier_environnement()
            if definie:
                nouvelle_cle = env_key
                print(f"Utilisation de la clé API depuis la variable d'environnement.")
        
        # Si toujours pas de clé, demander à l'utilisateur
        if not nouvelle_cle:
            nouvelle_cle = input("Veuillez entrer votre clé API Gemini: ")
        
        # Vérifier si la nouvelle clé est valide
        if nouvelle_cle:
            succes, message = verifier_cle_api(nouvelle_cle)
            if succes:
                print(f"✅ {message}")
                try:
                    # Vérifier si le fichier de configuration existe et est accessible en écriture
                    config_path = os.path.join(os.path.dirname(__file__), "gemini_api_config.json")
                    if os.path.exists(config_path):
                        try:
                            with open(config_path, "a") as f:
                                pass  # Test d'écriture
                            print(f"✅ Le fichier de configuration est accessible en écriture.")
                        except Exception as e:
                            print(f"❌ Le fichier de configuration existe mais n'est pas accessible en écriture: {str(e)}")
                    else:
                        print(f"ℹ️ Le fichier de configuration n'existe pas encore, il sera créé.")
                    
                    # Tenter de mettre à jour la configuration
                    if corriger_probleme_cle_api(nouvelle_cle):
                        print("✅ Configuration mise à jour avec succès.")
                    else:
                        print("❌ Erreur lors de la mise à jour de la configuration.")
                except Exception as e:
                    print(f"❌ Erreur détaillée lors de la mise à jour: {str(e)}")
            else:
                print(f"❌ {message}")
                print("La configuration n'a pas été mise à jour.")
        else:
            print("❌ Aucune clé API fournie. La configuration n'a pas été mise à jour.")

    # Afficher un message d'aide si aucune action n'a été effectuée
    if not any([args.verifier, args.corriger, args.env, args.cle, args.fix_str_items, args.diagnostic_complet]):
        parser.print_help()
        print("\nExemples d'utilisation:")
        print("  python corriger_probleme_cle_api_gemini.py --verifier                # Vérifier la configuration actuelle")
        print("  python corriger_probleme_cle_api_gemini.py --fix-str-items          # Corriger le problème 'str' object has no attribute 'items'")
        print("  python corriger_probleme_cle_api_gemini.py --diagnostic-complet     # Exécuter toutes les vérifications et corrections")
        print("  python corriger_probleme_cle_api_gemini.py --cle VOTRE_CLE_API      # Configurer une nouvelle clé API")

if __name__ == "__main__":
    main()