#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script d'installation des modèles Vision-Language légers
pour l'application d'analyse de risque environnemental.

Ce script télécharge et configure les modèles spécifiés dans config.py.
"""

import os
import sys
import logging
import argparse
import torch
from transformers import AutoProcessor, AutoTokenizer
from config import MODEL_CONFIG

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_model(model_name=None):
    """
    Télécharge et configure le modèle spécifié.
    
    Args:
        model_name: Nom du modèle à installer (doit être dans MODEL_CONFIG["available_models"])
                   Si None, utilise le modèle par défaut de MODEL_CONFIG
    """
    if model_name is None:
        model_name = MODEL_CONFIG["model_name"]
        logger.info(f"Aucun modèle spécifié, utilisation du modèle par défaut: {model_name}")
    
    # Vérifier si le modèle est disponible dans la configuration
    if model_name not in MODEL_CONFIG.get("available_models", {}):
        logger.error(f"Modèle {model_name} non trouvé dans la configuration")
        print(f"Modèles disponibles: {list(MODEL_CONFIG.get('available_models', {}).keys())}")
        return False
    
    model_config = MODEL_CONFIG["available_models"][model_name]
    model_path = model_config["path"]
    model_type = model_config["type"]
    
    logger.info(f"Installation du modèle {model_name} ({model_type}) depuis {model_path}")
    
    try:
        # Vérifier l'espace disque disponible
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_gb = free // (2**30)
        logger.info(f"Espace disque disponible: {free_gb} GB")
        
        if free_gb < 5:  # Moins de 5 GB disponibles
            logger.warning(f"Attention: seulement {free_gb} GB d'espace disque disponible")
            proceed = input("Continuer quand même? (o/n): ").lower() == 'o'
            if not proceed:
                return False
        
        # Télécharger le processeur et le tokenizer
        logger.info(f"Téléchargement du processeur pour {model_name}...")
        processor = AutoProcessor.from_pretrained(model_path)
        
        logger.info(f"Téléchargement du tokenizer pour {model_name}...")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # Télécharger le modèle en fonction du type
        logger.info(f"Téléchargement du modèle {model_name}...")
        
        if model_type == "qwen2-vl":
            from transformers import Qwen2VLForConditionalGeneration
            model = Qwen2VLForConditionalGeneration.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto"
            )
        elif model_type == "smolvlm":
            from transformers import AutoModelForCausalLM
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto"
            )
        elif model_type == "moondream":
            from transformers import AutoModelForCausalLM
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto"
            )
        else:
            logger.error(f"Type de modèle non supporté: {model_type}")
            return False
        
        # Mettre à jour la configuration
        logger.info(f"Mise à jour de la configuration...")
        # Note: Cette partie est commentée car elle nécessiterait de modifier le fichier config.py
        # ce qui n'est pas recommandé dans ce script
        
        logger.info(f"Installation du modèle {model_name} terminée avec succès!")
        return True
    
    except Exception as e:
        logger.error(f"Erreur lors de l'installation du modèle {model_name}: {str(e)}")
        return False

def list_available_models():
    """
    Affiche la liste des modèles disponibles dans la configuration.
    """
    available_models = MODEL_CONFIG.get("available_models", {})
    
    if not available_models:
        print("Aucun modèle disponible dans la configuration.")
        return
    
    print("\nModèles disponibles:")
    print("-" * 80)
    for name, config in available_models.items():
        print(f"Nom: {name}")
        print(f"Type: {config.get('type', 'Non spécifié')}")
        print(f"Chemin: {config.get('path', 'Non spécifié')}")
        print(f"Description: {config.get('description', 'Aucune description')}")
        print("-" * 80)

def main():
    parser = argparse.ArgumentParser(description="Installation des modèles Vision-Language")
    parser.add_argument(
        "--model", 
        type=str, 
        help="Nom du modèle à installer (doit être dans la configuration)"
    )
    parser.add_argument(
        "--list", 
        action="store_true", 
        help="Afficher la liste des modèles disponibles"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_available_models()
        return
    
    setup_model(args.model)

if __name__ == "__main__":
    main()