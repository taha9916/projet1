#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour vérifier la configuration de l'API Gemini au démarrage de l'application

Ce script peut être importé dans app.py pour vérifier automatiquement
la configuration de l'API Gemini au démarrage de l'application.
"""

import os
import sys
import json
import tkinter as tk
from tkinter import messagebox, simpledialog

# Importer les fonctions nécessaires depuis les modules existants
try:
    from gemini_integration import load_gemini_config, save_gemini_config, initialize_gemini_api
    from gemini_api import GeminiAPI
except ImportError:
    print("Erreur: Impossible d'importer les modules nécessaires.")
    print("Assurez-vous que les fichiers gemini_integration.py et gemini_api.py sont présents.")
    sys.exit(1)

def verifier_configuration_gemini():
    """
    Vérifie si l'API Gemini est correctement configurée et valide.
    
    Returns:
        tuple: (bool, str) - (Configurée, Message)
    """
    config = load_gemini_config()
    
    # Vérifier si une clé API est définie
    if not config.get("api_key"):
        return False, "Aucune clé API n'est configurée."
    
    # Vérifier si l'API est activée
    if not config.get("enabled", False):
        # Activer automatiquement si une clé est présente
        if config.get("api_key"):
            config["enabled"] = True
            save_gemini_config(config)
        else:
            return False, "L'API Gemini est désactivée dans la configuration."
    
    # Tester la validité de la clé API
    try:
        # Initialiser l'API pour tester la clé
        api = GeminiAPI(config.get("api_key"))
        # Faire une requête simple pour vérifier la validité de la clé
        response = api.list_models()
        if response and not response.get("error"):
            return True, "L'API Gemini est correctement configurée et la clé est valide."
        else:
            return False, "La clé API Gemini semble invalide ou a expiré."
    except Exception as e:
        return False, f"Erreur lors de la vérification de la clé API: {str(e)}"
    
    return True, "L'API Gemini est correctement configurée."

def afficher_dialogue_configuration(message_erreur=None):
    """
    Affiche un dialogue pour configurer l'API Gemini.
    
    Args:
        message_erreur (str, optional): Message d'erreur à afficher à l'utilisateur.
    
    Returns:
        bool: True si la configuration a été mise à jour, False sinon
    """
    # Créer une fenêtre Tkinter cachée
    root = tk.Tk()
    root.withdraw()
    
    # Afficher un message d'information avec le message d'erreur si disponible
    if message_erreur:
        messagebox.showinfo("Configuration requise", f"Problème avec la configuration de l'API Gemini:\n{message_erreur}\n\nVeuillez configurer une clé API valide pour utiliser ce service.")
    else:
        messagebox.showinfo("Configuration requise", "Aucune clé API n'est configurée pour Gemini.\nVeuillez configurer une clé API pour utiliser ce service.")
    
    # Demander la clé API
    api_key = simpledialog.askstring("Configuration de l'API Gemini", "Entrez votre clé API Gemini:\n(Vous pouvez l'obtenir sur https://ai.google.dev/)", show="*")
    
    if not api_key:
        return False
    
    # Mettre à jour la configuration
    config = load_gemini_config()
    config["api_key"] = api_key
    config["enabled"] = True
    
    # Sauvegarder la configuration
    if save_gemini_config(config):
        # Tester la validité de la clé API
        try:
            api = GeminiAPI(api_key)
            response = api.list_models()
            if response and not response.get("error"):
                messagebox.showinfo("Succès", "Configuration sauvegardée avec succès.\nL'API Gemini est maintenant activée et la clé est valide.")
                return True
            else:
                error_msg = response.get("error", {}).get("message", "Clé API invalide ou problème de connexion")
                messagebox.showerror("Erreur de validation", f"La clé API semble invalide:\n{error_msg}\n\nLa configuration a été sauvegardée, mais vous devrez peut-être entrer une clé valide ultérieurement.")
                return False
        except Exception as e:
            messagebox.showwarning("Avertissement", f"Configuration sauvegardée, mais impossible de vérifier la clé API:\n{str(e)}")
            return True
    else:
        messagebox.showerror("Erreur", "Impossible de sauvegarder la configuration.")
        return False

def verifier_et_configurer_gemini():
    """
    Vérifie la configuration de l'API Gemini et affiche un dialogue de configuration si nécessaire.
    
    Returns:
        bool: True si l'API Gemini est correctement configurée, False sinon
    """
    configuree, message = verifier_configuration_gemini()
    
    if not configuree:
        # Afficher un dialogue de configuration avec le message d'erreur
        return afficher_dialogue_configuration(message_erreur=message)
    
    return True

# Fonction à appeler au démarrage de l'application
def verifier_gemini_au_demarrage():
    """
    Vérifie la configuration de l'API Gemini au démarrage de l'application.
    
    Cette fonction peut être appelée depuis app.py pour vérifier automatiquement
    la configuration de l'API Gemini au démarrage de l'application.
    
    Returns:
        bool: True si l'API Gemini est correctement configurée, False sinon
    """
    # Vérifier d'abord si la configuration est valide sans afficher de dialogue
    configuree, message = verifier_configuration_gemini()
    
    # Si la configuration est valide, retourner True sans demander à l'utilisateur
    if configuree:
        return True
    
    # Sinon, afficher le dialogue de configuration
    return verifier_et_configurer_gemini()

# Test du script
if __name__ == "__main__":
    resultat = verifier_gemini_au_demarrage()
    print(f"Résultat de la vérification: {'Succès' if resultat else 'Échec'}")