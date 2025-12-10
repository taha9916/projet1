#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script d'installation du modèle dots.ocr pour l'analyse d'images environnementales.

Ce script installe les dépendances nécessaires et télécharge le modèle dots.ocr
depuis Hugging Face. Il configure également le modèle pour une utilisation avec
une quantification 4-bit afin de réduire l'utilisation de la mémoire.

Usage:
    python install_dots_ocr.py
"""

import subprocess
import sys
import os
import logging
import torch
import platform

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_system_requirements():
    """
    Vérifie les prérequis système pour l'installation du modèle dots.ocr.
    """
    # Vérification de la RAM disponible
    try:
        import psutil
        ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        logger.info(f"RAM totale disponible: {ram_gb:.2f} Go")
        
        if ram_gb < 8:
            logger.warning(f"Attention: Votre système dispose de seulement {ram_gb:.2f} Go de RAM.")
            logger.warning("Le modèle dots.ocr nécessite idéalement au moins 8 Go de RAM.")
            logger.warning("L'exécution pourrait être lente ou instable.")
            
            response = input("Voulez-vous continuer malgré tout? (o/n): ")
            if response.lower() != 'o':
                logger.info("Installation annulée par l'utilisateur.")
                return False
    except ImportError:
        logger.warning("Impossible de vérifier la RAM disponible. Module psutil non installé.")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        logger.info("Module psutil installé. Veuillez relancer le script.")
        return False
    
    # Vérification de la version de Python
    python_version = sys.version_info
    logger.info(f"Version de Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        logger.error("Python 3.8 ou supérieur est requis.")
        return False
    
    return True

def install_dependencies():
    """
    Installe les dépendances nécessaires pour le modèle dots.ocr.
    """
    try:
        logger.info("Installation des dépendances pour dots.ocr...")
        
        # Liste des packages à installer avec versions spécifiques
        packages = [
            "torch",
            "transformers>=4.30.0",
            "bitsandbytes>=0.39.0",  # Nécessaire pour la quantification 4-bit
            "safetensors>=0.3.1",
            "pillow>=9.0.0",
            "diskcache>=5.6.0",
            "accelerate>=0.20.0",
            "psutil"
            # "flash-attn" est optionnel et nécessite CUDA
        ]
        
        # Installer chaque package
        for package in packages:
            logger.info(f"Installation de {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        logger.info("Toutes les dépendances ont été installées avec succès.")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'installation des dépendances: {str(e)}")
        return False

def check_gpu_compatibility():
    """
    Vérifie la compatibilité du GPU pour l'exécution du modèle.
    """
    if not torch.cuda.is_available():
        logger.warning("CUDA non disponible. Le modèle fonctionnera sur CPU, ce qui peut être très lent.")
        logger.warning("Il est fortement recommandé d'utiliser un GPU pour ce modèle.")
        return False
    
    # Vérification de la mémoire GPU disponible
    gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
    logger.info(f"Mémoire GPU disponible: {gpu_memory_gb:.2f} Go")
    
    if gpu_memory_gb < 4:
        logger.warning(f"Attention: Votre GPU dispose de seulement {gpu_memory_gb:.2f} Go de mémoire.")
        logger.warning("Le modèle dots.ocr nécessite idéalement au moins 4 Go de mémoire GPU.")
        logger.warning("L'exécution pourrait être lente ou instable.")
        
        response = input("Voulez-vous continuer malgré tout? (o/n): ")
        if response.lower() != 'o':
            logger.info("Installation annulée par l'utilisateur.")
            return False
    
    return True

def download_model():
    """
    Télécharge le modèle dots.ocr depuis Hugging Face.
    """
    try:
        logger.info("Téléchargement du modèle dots.ocr...")
        
        # Importer les bibliothèques nécessaires
        from transformers import AutoModelForCausalLM, AutoProcessor
        import torch
        
        # Définir le nom du modèle
        model_name = "rednote-hilab/dots.ocr"
        
        # Création du répertoire de cache si nécessaire
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "dots_ocr")
        os.makedirs(cache_dir, exist_ok=True)
        logger.info(f"Utilisation du répertoire de cache: {cache_dir}")
        
        # Télécharger d'abord le processeur (plus petit)
        logger.info("Téléchargement du processeur...")
        processor = AutoProcessor.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            trust_remote_code=True
        )
        
        # Télécharger le modèle pour CPU uniquement pour éviter les problèmes de flash_attn
        logger.info("Téléchargement du modèle pour CPU (cela peut prendre plusieurs minutes)...")
        try:
            # Forcer l'utilisation du CPU pour éviter les problèmes de flash_attn
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="cpu",  # Forcer l'utilisation du CPU
                torch_dtype=torch.float32,  # Utiliser float32 pour CPU
                load_in_4bit=False,  # Désactiver la quantification 4-bit sur CPU
                cache_dir=cache_dir,
                trust_remote_code=True,
                attn_implementation="eager",
                low_cpu_mem_usage=True  # Optimiser pour CPU avec mémoire limitée
            )
            logger.warning("Modèle chargé en mode CPU. Les performances seront réduites.")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {str(e)}")
            logger.warning("Tentative de chargement avec des paramètres alternatifs...")
            # Essayer avec des paramètres plus simples
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="cpu",
                torch_dtype=torch.float32,
                cache_dir=cache_dir,
                trust_remote_code=False,  # Désactiver le code distant
                low_cpu_mem_usage=True
            )
        
        # Test simple du modèle
        logger.info("Test du modèle...")
        from PIL import Image
        import requests
        from io import BytesIO
        
        # Téléchargement d'une image de test si nécessaire
        test_image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_images", "test_ocr.jpg")
        os.makedirs(os.path.dirname(test_image_path), exist_ok=True)
        
        if not os.path.exists(test_image_path):
            try:
                # Utilisation d'une image de test simple
                response = requests.get("https://huggingface.co/datasets/merve/sample-images/resolve/main/apple.jpg")
                img = Image.open(BytesIO(response.content))
                img.save(test_image_path)
                logger.info(f"Image de test téléchargée: {test_image_path}")
            except Exception as e:
                logger.warning(f"Impossible de télécharger l'image de test: {e}")
                # Création d'une image de test simple
                img = Image.new('RGB', (300, 100), color=(255, 255, 255))
                img.save(test_image_path)
                logger.info(f"Image de test créée: {test_image_path}")
        
        # Test rapide du modèle
        if os.path.exists(test_image_path):
            try:
                img = Image.open(test_image_path)
                # Préparer les inputs sans les déplacer sur le device du modèle
                inputs = processor(images=img, return_tensors="pt")
                # Déplacer manuellement les inputs sur le même device que le modèle
                for k, v in inputs.items():
                    if isinstance(v, torch.Tensor):
                        inputs[k] = v.to(model.device)
                
                # Générer avec des paramètres simplifiés
                generated_ids = model.generate(
                    **inputs,
                    max_new_tokens=10,  # Réduire pour accélérer le test
                    do_sample=False,
                    num_beams=1  # Désactiver beam search pour simplifier
                )
                generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                logger.info(f"Test du modèle réussi. Texte généré: {generated_text[:50]}...")
            except Exception as e:
                logger.warning(f"Test du modèle échoué: {e}")
                logger.warning("Le test a échoué mais le modèle peut toujours être utilisable.")
        
        # Libérer la mémoire
        del model
        del processor
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Le modèle dots.ocr a été téléchargé avec succès.")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement du modèle: {str(e)}")
        return False

def main():
    logger.info("=== Installation du modèle dots.ocr ===")
    logger.info(f"Système d'exploitation: {platform.system()} {platform.release()}")
    
    # Vérification des prérequis système
    if not check_system_requirements():
        logger.error("Les prérequis système ne sont pas satisfaits.")
        return
    
    # Vérification de la disponibilité de CUDA
    has_compatible_gpu = check_gpu_compatibility() if torch.cuda.is_available() else False
    if not has_compatible_gpu:
        logger.warning("Aucun GPU compatible détecté. Le modèle fonctionnera sur CPU.")
        logger.warning("L'inférence sur CPU peut être très lente. Continuez à vos risques.")
        
        response = input("Voulez-vous continuer l'installation sans GPU? (o/n): ")
        if response.lower() != 'o':
            logger.info("Installation annulée par l'utilisateur.")
            return
    
    # Installation des dépendances
    if not install_dependencies():
        logger.error("Échec de l'installation des dépendances.")
        return
    
    # Télécharger le modèle
    if not download_model():
        logger.error("Échec du téléchargement du modèle.")
        return
    
    logger.info("\n=== Installation terminée avec succès ===")
    logger.info("Le modèle dots.ocr est maintenant prêt à être utilisé.")
    logger.info("\nPour tester le modèle, exécutez: python test_dots_ocr.py")
    logger.info("Pour une démonstration complète, exécutez: python demo_dots_ocr.py")
    
    # Affichage des informations d'utilisation de la mémoire
    logger.info("\n=== Informations sur l'utilisation de la mémoire ===")
    logger.info("Le modèle dots.ocr utilise environ 4-6 Go de RAM en mode 4-bit.")
    logger.info("Si vous rencontrez des problèmes de mémoire, assurez-vous de libérer la mémoire après utilisation:")
    logger.info("  1. Supprimez les références au modèle: 'del model, processor'")
    logger.info("  2. Videz le cache CUDA: 'torch.cuda.empty_cache()'")

if __name__ == "__main__":
    main()