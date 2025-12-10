#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour corriger les problèmes d'interface avec l'API Gemini

Ce script permet de corriger les problèmes d'interface graphique
liés à la configuration et l'utilisation de la clé API Gemini.
"""

import os
import sys
import json
import tkinter as tk
from tkinter import messagebox, simpledialog
import requests

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

def corriger_probleme_cle_api(nouvelle_cle):
    """
    Corrige les problèmes courants avec la clé API Gemini.
    
    Args:
        nouvelle_cle (str): Nouvelle clé API à configurer
        
    Returns:
        bool: True si la correction a réussi, False sinon
    """
    config = load_gemini_config()
    
    # Configurer la nouvelle clé
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

class ConfigurationGeminiUI:
    """
    Interface utilisateur pour configurer l'API Gemini.
    """
    
    def __init__(self, root=None):
        """
        Initialise l'interface utilisateur.
        
        Args:
            root (tk.Tk, optional): Fenêtre racine Tkinter.
        """
        self.standalone = root is None
        
        if self.standalone:
            self.root = tk.Tk()
            self.root.title("Configuration de l'API Gemini")
            self.root.geometry("500x300")
            self.root.resizable(False, False)
        else:
            self.root = root
        
        self.config = load_gemini_config()
        self.create_widgets()
    
    def create_widgets(self):
        """
        Crée les widgets de l'interface utilisateur.
        """
        # Frame principal
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        title_label = tk.Label(main_frame, text="Configuration de l'API Gemini", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Frame pour la clé API
        api_key_frame = tk.Frame(main_frame)
        api_key_frame.pack(fill=tk.X, pady=5)
        
        api_key_label = tk.Label(api_key_frame, text="Clé API Gemini:")
        api_key_label.pack(side=tk.LEFT)
        
        self.api_key_var = tk.StringVar(value=self.config.get("api_key", ""))
        self.api_key_entry = tk.Entry(api_key_frame, textvariable=self.api_key_var, width=40, show="*")
        self.api_key_entry.pack(side=tk.LEFT, padx=5)
        
        show_key_button = tk.Button(api_key_frame, text="👁️", command=self.toggle_show_key)
        show_key_button.pack(side=tk.LEFT)
        
        # Frame pour l'activation
        enabled_frame = tk.Frame(main_frame)
        enabled_frame.pack(fill=tk.X, pady=5)
        
        self.enabled_var = tk.BooleanVar(value=self.config.get("enabled", False))
        enabled_check = tk.Checkbutton(enabled_frame, text="Activer l'API Gemini", variable=self.enabled_var)
        enabled_check.pack(side=tk.LEFT)
        
        # Frame pour les boutons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        test_button = tk.Button(button_frame, text="Tester la clé API", command=self.test_api_key)
        test_button.pack(side=tk.LEFT, padx=5)
        
        save_button = tk.Button(button_frame, text="Sauvegarder", command=self.save_config)
        save_button.pack(side=tk.LEFT, padx=5)
        
        if self.standalone:
            quit_button = tk.Button(button_frame, text="Quitter", command=self.root.destroy)
            quit_button.pack(side=tk.RIGHT, padx=5)
    
    def toggle_show_key(self):
        """
        Affiche ou masque la clé API.
        """
        if self.api_key_entry["show"] == "*":
            self.api_key_entry["show"] = ""
        else:
            self.api_key_entry["show"] = "*"
    
    def test_api_key(self):
        """
        Teste la clé API Gemini.
        """
        api_key = self.api_key_var.get()
        
        if not api_key:
            messagebox.showerror("Erreur", "Veuillez entrer une clé API.")
            return
        
        # Afficher un message de chargement
        self.root.config(cursor="wait")
        self.root.update()
        
        # Tester la clé API
        success, message = verifier_cle_api(api_key)
        
        # Restaurer le curseur
        self.root.config(cursor="")
        
        if success:
            messagebox.showinfo("Succès", message)
        else:
            messagebox.showerror("Erreur", message)
    
    def save_config(self):
        """
        Sauvegarde la configuration de l'API Gemini.
        """
        api_key = self.api_key_var.get()
        enabled = self.enabled_var.get()
        
        if not api_key and enabled:
            messagebox.showerror("Erreur", "Veuillez entrer une clé API ou désactiver l'API Gemini.")
            return
        
        # Mettre à jour la configuration
        self.config["api_key"] = api_key
        self.config["enabled"] = enabled
        
        # Sauvegarder la configuration
        if save_gemini_config(self.config):
            messagebox.showinfo("Succès", "Configuration sauvegardée avec succès.")
            
            # Si l'interface est autonome, fermer la fenêtre
            if self.standalone:
                self.root.destroy()
        else:
            messagebox.showerror("Erreur", "Impossible de sauvegarder la configuration.")
    
    def run(self):
        """
        Exécute l'interface utilisateur.
        """
        if self.standalone:
            self.root.mainloop()

def afficher_dialogue_configuration():
    """
    Affiche un dialogue simple pour configurer l'API Gemini.
    """
    # Créer une fenêtre Tkinter cachée
    root = tk.Tk()
    root.withdraw()
    
    # Charger la configuration actuelle
    config = load_gemini_config()
    
    # Afficher un message d'information
    messagebox.showinfo("Configuration requise", "Aucune clé API n'est configurée pour Gemini.\nVeuillez configurer une clé API pour utiliser ce service.")
    
    # Demander la clé API
    api_key = simpledialog.askstring("Configuration de l'API Gemini", "Entrez votre clé API Gemini:", show="*")
    
    if api_key:
        # Tester la clé API
        success, message = verifier_cle_api(api_key)
        
        if success:
            # Sauvegarder la configuration
            if corriger_probleme_cle_api(api_key):
                messagebox.showinfo("Succès", "Configuration sauvegardée avec succès.\nL'API Gemini est maintenant activée.")
                return True
            else:
                messagebox.showerror("Erreur", "Impossible de sauvegarder la configuration.")
        else:
            messagebox.showerror("Erreur", message)
    
    return False

def main():
    """
    Point d'entrée principal du script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Interface de configuration de l'API Gemini")
    parser.add_argument("--simple", action="store_true", help="Utiliser l'interface simple")
    
    args = parser.parse_args()
    
    if args.simple:
        afficher_dialogue_configuration()
    else:
        app = ConfigurationGeminiUI()
        app.run()

if __name__ == "__main__":
    main()