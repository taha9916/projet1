#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module d'intégration du modèle dots.ocr dans l'application principale.

Ce module fournit des fonctions pour intégrer facilement le modèle dots.ocr
dans l'application principale, en remplaçant l'implémentation qui cause l'erreur
'VLModel object has no attribute load_model'.
"""

import os
import logging
import tkinter as tk
from tkinter import messagebox
import torch

# Import de la classe DotsOCRModel
from dots_ocr_model import DotsOCRModel

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Variable globale pour stocker l'instance du modèle
_model_instance = None

def get_model_instance(model_path="models/dots_ocr", force_reload=False):
    """
    Récupère l'instance du modèle dots.ocr, en la créant si nécessaire.
    
    Args:
        model_path (str): Chemin vers le modèle dots.ocr ou nom du modèle sur Hugging Face.
        force_reload (bool): Force le rechargement du modèle même s'il est déjà chargé.
        
    Returns:
        DotsOCRModel: Instance du modèle dots.ocr.
    """
    global _model_instance
    
    # Créer une nouvelle instance si nécessaire
    if _model_instance is None or force_reload:
        _model_instance = DotsOCRModel(model_path)
    
    return _model_instance

def analyze_image_with_dots_ocr(image_path, prompt=None, show_ui_messages=True):
    """
    Analyse une image avec le modèle dots.ocr et gère les erreurs avec des messages UI si nécessaire.
    
    Args:
        image_path (str): Chemin vers l'image à analyser.
        prompt (str, optional): Instructions pour l'analyse.
        show_ui_messages (bool): Affiche des messages d'interface utilisateur en cas d'erreur.
        
    Returns:
        str: Résultat de l'analyse ou None en cas d'erreur.
    """
    # Vérifier que l'image existe
    if not os.path.exists(image_path):
        error_msg = f"L'image {image_path} n'existe pas"
        logger.error(error_msg)
        if show_ui_messages:
            messagebox.showerror("Erreur", error_msg)
        return None
    
    try:
        # Récupérer l'instance du modèle
        model = get_model_instance()
        
        # Charger le modèle
        if not model.load_model():
            error_msg = "Impossible de charger le modèle dots.ocr"
            logger.error(error_msg)
            if show_ui_messages:
                messagebox.showerror("Erreur", error_msg)
            return None
        
        # Analyser l'image
        logger.info(f"Analyse de l'image: {image_path}")
        resultat = model.analyze_image(image_path, prompt)
        
        return resultat
    except Exception as e:
        error_msg = f"Erreur lors de l'analyse: {str(e)}"
        logger.error(error_msg)
        if show_ui_messages:
            messagebox.showerror("Erreur", error_msg)
        return None

def unload_model():
    """
    Libère la mémoire en déchargeant le modèle dots.ocr.
    """
    global _model_instance
    
    if _model_instance is not None:
        _model_instance.unload_model()
        _model_instance = None
        logger.info("Modèle dots.ocr déchargé et mémoire libérée")

def check_system_compatibility():
    """
    Vérifie la compatibilité du système pour le modèle dots.ocr.
    
    Returns:
        dict: Informations sur la compatibilité du système.
    """
    compatibility_info = {
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
        "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "gpu_names": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())] if torch.cuda.is_available() else [],
        "ram_reserved": f"{torch.cuda.memory_reserved() / 1024**3:.2f} GB" if torch.cuda.is_available() else "N/A",
        "ram_allocated": f"{torch.cuda.memory_allocated() / 1024**3:.2f} GB" if torch.cuda.is_available() else "N/A",
    }
    
    logger.info(f"Compatibilité système: {compatibility_info}")
    return compatibility_info

# Fonction pour remplacer l'implémentation VLModel qui cause l'erreur
def initialize_dots_ocr_model(model_path="models/dots_ocr"): 
    """
    Initialise le modèle dots.ocr et retourne une instance compatible avec l'interface VLModel.
    Cette fonction est conçue pour remplacer l'implémentation qui cause l'erreur
    'VLModel object has no attribute load_model'.
    
    Args:
        model_path (str): Chemin vers le modèle dots.ocr ou nom du modèle sur Hugging Face.
        
    Returns:
        object: Instance du modèle dots.ocr compatible avec l'interface VLModel.
    """
    # Créer une instance de DotsOCRModel
    dots_ocr_model = DotsOCRModel(model_path)
    
    # Créer un adaptateur compatible avec l'interface VLModel
    class VLModelAdapter:
        def __init__(self, dots_ocr_model):
            self.dots_ocr_model = dots_ocr_model
            self.model_loaded = False
        
        def load_model(self):
            """
            Charge le modèle dots.ocr.
            
            Returns:
                bool: True si le chargement a réussi, False sinon.
            """
            self.model_loaded = self.dots_ocr_model.load_model()
            return self.model_loaded
        
        def analyze_image(self, image_path, prompt=None):
            """
            Analyse une image avec le modèle dots.ocr.
            
            Args:
                image_path (str): Chemin vers l'image à analyser.
                prompt (str, optional): Instructions pour l'analyse.
                
            Returns:
                str: Résultat de l'analyse ou None en cas d'erreur.
            """
            if not self.model_loaded:
                if not self.load_model():
                    return None
            
            return self.dots_ocr_model.analyze_image(image_path, prompt)
        
        def unload_model(self):
            """
            Libère la mémoire en déchargeant le modèle dots.ocr.
            """
            self.dots_ocr_model.unload_model()
            self.model_loaded = False
    
    # Retourner l'adaptateur
    return VLModelAdapter("models/dots_ocr")

# Exemple d'utilisation
def main():
    import sys
    
    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("Usage: python integration_dots_ocr.py <chemin_image> [prompt]")
        return 1
    
    # Récupérer les arguments
    image_path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Vérifier la compatibilité du système
    compatibility_info = check_system_compatibility()
    print("\nInformations de compatibilité système:")
    for key, value in compatibility_info.items():
        print(f"  {key}: {value}")
    
    # Analyser l'image
    try:
        resultat = analyze_image_with_dots_ocr(image_path, prompt, show_ui_messages=False)
        
        # Afficher le résultat
        if resultat:
            print("\nRésultat de l'analyse:")
            print("=======================")
            print(resultat)
            print("=======================")
            return 0
        else:
            print("Échec de l'analyse de l'image.")
            return 1
    finally:
        # Libérer la mémoire
        unload_model()

if __name__ == "__main__":
    sys.exit(main())