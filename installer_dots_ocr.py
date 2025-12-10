#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script d'installation pour le modèle dots.ocr.

Ce script installe les dépendances nécessaires pour utiliser le modèle dots.ocr
et vérifie que l'environnement est correctement configuré.
"""

import os
import sys
import subprocess
import logging
import argparse
import platform

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(command, description=None):
    """
    Exécute une commande shell et affiche le résultat.
    
    Args:
        command (str): Commande à exécuter.
        description (str, optional): Description de la commande.
        
    Returns:
        bool: True si la commande a réussi, False sinon.
    """
    if description:
        logger.info(description)
    
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de l'exécution de la commande: {e}")
        logger.error(e.stderr)
        return False

def check_python_version():
    """
    Vérifie que la version de Python est compatible.
    
    Returns:
        bool: True si la version de Python est compatible, False sinon.
    """
    logger.info("Vérification de la version de Python...")
    
    python_version = sys.version_info
    logger.info(f"Version de Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        logger.error("Python 3.8 ou supérieur est requis")
        return False
    
    logger.info("Version de Python compatible")
    return True

def check_pip():
    """
    Vérifie que pip est installé.
    
    Returns:
        bool: True si pip est installé, False sinon.
    """
    logger.info("Vérification de pip...")
    
    return run_command("pip --version", "Vérification de la version de pip...")

def upgrade_pip():
    """
    Met à jour pip.
    
    Returns:
        bool: True si la mise à jour a réussi, False sinon.
    """
    logger.info("Mise à jour de pip...")
    
    return run_command("pip install --upgrade pip", "Mise à jour de pip...")

def install_dependencies():
    """
    Installe les dépendances nécessaires.
    
    Returns:
        bool: True si l'installation a réussi, False sinon.
    """
    logger.info("Installation des dépendances...")
    
    # Installer torch
    if not run_command("pip install --upgrade torch torchvision torchaudio", "Installation de PyTorch..."):
        return False
    
    # Installer transformers
    if not run_command("pip install --upgrade transformers", "Installation de transformers..."):
        return False
    
    # Installer pillow
    if not run_command("pip install --upgrade pillow", "Installation de Pillow..."):
        return False
    
    # Installer tqdm
    if not run_command("pip install --upgrade tqdm", "Installation de tqdm..."):
        return False
    
    # Installer accelerate
    if not run_command("pip install --upgrade accelerate", "Installation de accelerate..."):
        return False
    
    # Installer bitsandbytes (pour la quantification 4-bit)
    if not run_command("pip install --upgrade bitsandbytes", "Installation de bitsandbytes..."):
        logger.warning("Impossible d'installer bitsandbytes. La quantification 4-bit ne sera pas disponible.")
    
    logger.info("Dépendances installées avec succès")
    return True

def install_dots_ocr():
    """
    Installe le modèle dots.ocr.
    
    Returns:
        bool: True si l'installation a réussi, False sinon.
    """
    logger.info("Installation du modèle dots.ocr...")
    
    # Essayer d'installer depuis GitHub
    if run_command("pip install git+https://github.com/rednote-hilab/dots.ocr.git", "Installation de dots.ocr depuis GitHub..."):
        return True
    
    # Si l'installation depuis GitHub échoue, essayer de cloner le dépôt et d'installer localement
    logger.warning("Installation depuis GitHub échouée. Tentative d'installation locale...")
    
    # Créer un répertoire temporaire
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Cloner le dépôt
    if not run_command(f"git clone https://github.com/rednote-hilab/dots.ocr.git {temp_dir}", "Clonage du dépôt dots.ocr..."):
        return False
    
    # Installer localement
    if not run_command(f"cd {temp_dir} && pip install -e .", "Installation locale de dots.ocr..."):
        return False
    
    logger.info("Modèle dots.ocr installé avec succès")
    return True

def check_cuda():
    """
    Vérifie si CUDA est disponible.
    
    Returns:
        bool: True si CUDA est disponible, False sinon.
    """
    logger.info("Vérification de CUDA...")
    
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        logger.info(f"CUDA disponible: {cuda_available}")
        
        if cuda_available:
            cuda_version = torch.version.cuda
            logger.info(f"Version de CUDA: {cuda_version}")
            
            gpu_count = torch.cuda.device_count()
            logger.info(f"Nombre de GPUs: {gpu_count}")
            
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                logger.info(f"GPU {i}: {gpu_name}")
        
        return cuda_available
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de CUDA: {str(e)}")
        return False

def create_cache_directory():
    """
    Crée un répertoire de cache pour le modèle dots.ocr.
    
    Returns:
        bool: True si la création a réussi, False sinon.
    """
    logger.info("Création du répertoire de cache...")
    
    try:
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "dots_ocr")
        os.makedirs(cache_dir, exist_ok=True)
        logger.info(f"Répertoire de cache créé: {cache_dir}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la création du répertoire de cache: {str(e)}")
        return False

def check_transformers():
    """
    Vérifie que transformers est correctement installé.
    
    Returns:
        bool: True si transformers est correctement installé, False sinon.
    """
    logger.info("Vérification de transformers...")
    
    try:
        import transformers
        logger.info(f"Version de transformers: {transformers.__version__}")
        return True
    except ImportError:
        logger.error("La bibliothèque transformers n'est pas installée")
        return False

def check_pillow():
    """
    Vérifie que Pillow est correctement installé.
    
    Returns:
        bool: True si Pillow est correctement installé, False sinon.
    """
    logger.info("Vérification de Pillow...")
    
    try:
        from PIL import Image, __version__ as pil_version
        logger.info(f"Version de Pillow: {pil_version}")
        return True
    except ImportError:
        logger.error("La bibliothèque Pillow n'est pas installée")
        return False

def check_torch():
    """
    Vérifie que PyTorch est correctement installé.
    
    Returns:
        bool: True si PyTorch est correctement installé, False sinon.
    """
    logger.info("Vérification de PyTorch...")
    
    try:
        import torch
        logger.info(f"Version de PyTorch: {torch.__version__}")
        return True
    except ImportError:
        logger.error("La bibliothèque PyTorch n'est pas installée")
        return False

def main():
    # Configurer l'analyseur d'arguments
    parser = argparse.ArgumentParser(description="Installation du modèle dots.ocr")
    parser.add_argument("--skip-dependencies", help="Saute l'installation des dépendances", action="store_true")
    parser.add_argument("--skip-dots-ocr", help="Saute l'installation du modèle dots.ocr", action="store_true")
    parser.add_argument("--force", help="Force la réinstallation même si déjà installé", action="store_true")
    
    # Analyser les arguments
    args = parser.parse_args()
    
    # Afficher les informations système
    logger.info(f"Système d'exploitation: {platform.system()} {platform.release()}")
    logger.info(f"Architecture: {platform.machine()}")
    
    # Vérifier la version de Python
    if not check_python_version():
        logger.error("Version de Python incompatible. Python 3.8 ou supérieur est requis.")
        return 1
    
    # Vérifier pip
    if not check_pip():
        logger.error("pip n'est pas installé. Veuillez installer pip avant de continuer.")
        return 1
    
    # Mettre à jour pip
    if not upgrade_pip():
        logger.warning("Impossible de mettre à jour pip. Continuez à vos risques et périls.")
    
    # Installer les dépendances
    if not args.skip_dependencies:
        if not install_dependencies():
            logger.error("Impossible d'installer les dépendances. Veuillez vérifier les erreurs ci-dessus.")
            return 1
    else:
        logger.info("Installation des dépendances ignorée")
    
    # Vérifier les dépendances
    if not check_torch():
        logger.error("PyTorch n'est pas correctement installé. Veuillez installer PyTorch avant de continuer.")
        return 1
    
    if not check_transformers():
        logger.error("transformers n'est pas correctement installé. Veuillez installer transformers avant de continuer.")
        return 1
    
    if not check_pillow():
        logger.error("Pillow n'est pas correctement installé. Veuillez installer Pillow avant de continuer.")
        return 1
    
    # Vérifier CUDA
    cuda_available = check_cuda()
    if not cuda_available:
        logger.warning("CUDA n'est pas disponible. Le modèle sera exécuté sur CPU, ce qui peut être lent.")
    
    # Créer le répertoire de cache
    if not create_cache_directory():
        logger.error("Impossible de créer le répertoire de cache. Veuillez vérifier les permissions.")
        return 1
    
    # Installer le modèle dots.ocr
    if not args.skip_dots_ocr:
        if not install_dots_ocr():
            logger.error("Impossible d'installer le modèle dots.ocr. Veuillez vérifier les erreurs ci-dessus.")
            return 1
    else:
        logger.info("Installation du modèle dots.ocr ignorée")
    
    logger.info("Installation terminée avec succès")
    logger.info("\nPour utiliser le modèle dots.ocr, vous pouvez exécuter:")
    logger.info("python dots_ocr_model.py chemin/vers/votre/image.jpg")
    logger.info("\nOu pour plus d'options:")
    logger.info("python exemple_utilisation_dots_ocr.py chemin/vers/votre/image.jpg --prompt \"Extraire le texte de cette image\" --cpu --output resultat.txt")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())