#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script d'intégration pour la fonction d'extraction améliorée des paramètres environnementaux.

Ce script permet d'intégrer la fonction _extract_parameters_improved du module
improved_cloud_api_extraction.py dans le système existant en remplaçant la fonction
_extract_parameters du module cloud_api.py.
"""

import os
import sys
import logging
import importlib.util
import shutil
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('integration.log')
    ]
)

logger = logging.getLogger(__name__)

def backup_original_file(file_path):
    """Crée une sauvegarde du fichier original.
    
    Args:
        file_path (str): Chemin du fichier à sauvegarder
        
    Returns:
        str: Chemin du fichier de sauvegarde
    """
    if not os.path.exists(file_path):
        logger.error(f"Le fichier {file_path} n'existe pas")
        return None
    
    # Créer un nom de fichier de sauvegarde avec la date et l'heure
    backup_dir = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    file_base, file_ext = os.path.splitext(file_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"{file_base}_backup_{timestamp}{file_ext}")
    
    # Copier le fichier original vers le fichier de sauvegarde
    try:
        shutil.copy2(file_path, backup_file)
        logger.info(f"Sauvegarde créée: {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"Erreur lors de la création de la sauvegarde: {str(e)}")
        return None

def find_cloud_api_file():
    """Retourne le chemin du fichier de test d'API cloud existant.
    
    Returns:
        str: Chemin du fichier cloud_api_tester.py
    """
    # Utiliser directement le fichier existant
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloud_api_tester.py")
    logger.info(f"Utilisation du fichier API testeur: {file_path}")
    return file
            logger.info(f"Fichier cloud_api.py trouvé: {file_path}")
            return file_path
    
    logger.error("Fichier cloud_api.py non trouvé dans le projet")
    return None

def extract_function_from_file(file_path, function_name):
    """Extrait une fonction d'un fichier Python.
    
    Args:
        file_path (str): Chemin du fichier Python
        function_name (str): Nom de la fonction à extraire
        
    Returns:
        tuple: (début de la fonction, corps de la fonction, fin de la fonction)
    """
    if not os.path.exists(file_path):
        logger.error(f"Le fichier {file_path} n'existe pas")
        return None, None, None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Rechercher la définition de la fonction
        import re
        pattern = rf"def\s+{function_name}\s*\([^)]*\)\s*:\s*"
        match = re.search(pattern, content)
        
        if not match:
            logger.error(f"Fonction {function_name} non trouvée dans {file_path}")
            return None, None, None
        
        # Trouver le début de la fonction
        start_pos = match.start()
        
        # Trouver la fin de la fonction en cherchant la prochaine définition de fonction ou de classe
        next_def = re.search(r"\ndef\s+", content[start_pos + 1:])
        next_class = re.search(r"\nclass\s+", content[start_pos + 1:])
        
        if next_def and next_class:
            end_pos = start_pos + 1 + min(next_def.start(), next_class.start())
        elif next_def:
            end_pos = start_pos + 1 + next_def.start()
        elif next_class:
            end_pos = start_pos + 1 + next_class.start()
        else:
            end_pos = len(content)
        
        # Extraire le contenu avant, pendant et après la fonction
        before_function = content[:start_pos]
        function_body = content[start_pos:end_pos]
        after_function = content[end_pos:]
        
        return before_function, function_body, after_function
    
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction de la fonction: {str(e)}")
        return None, None, None

def integrate_improved_extraction():
    """Intègre la fonction d'extraction améliorée dans le fichier cloud_api.py.
    
    Returns:
        bool: True si l'intégration a réussi, False sinon
    """
    # Trouver le fichier cloud_api.py
    cloud_api_path = find_cloud_api_file()
    if not cloud_api_path:
        return False
    
    # Créer une sauvegarde du fichier original
    backup_path = backup_original_file(cloud_api_path)
    if not backup_path:
        return False
    
    # Charger la fonction améliorée
    improved_extraction_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "improved_cloud_api_extraction.py")
    if not os.path.exists(improved_extraction_path):
        logger.error(f"Le fichier {improved_extraction_path} n'existe pas")
        return False
    
    # Extraire la fonction _extract_parameters du fichier cloud_api.py
    before_function, old_function, after_function = extract_function_from_file(cloud_api_path, "_extract_parameters")
    if not before_function or not old_function or not after_function:
        return False
    
    # Extraire la fonction _extract_parameters_improved du fichier improved_cloud_api_extraction.py
    _, improved_function, _ = extract_function_from_file(improved_extraction_path, "_extract_parameters_improved")
    if not improved_function:
        return False
    
    # Remplacer la fonction _extract_parameters par la fonction _extract_parameters_improved
    # en renommant la fonction améliorée
    improved_function = improved_function.replace("_extract_parameters_improved", "_extract_parameters")
    
    # Ajouter l'import pour unicodedata si nécessaire
    if "import unicodedata" not in before_function:
        import_pos = before_function.rfind("import")
        if import_pos != -1:
            # Trouver la fin de la section d'importation
            import_end = before_function.find("\n\n", import_pos)
            if import_end != -1:
                before_function = before_function[:import_end] + "\nimport unicodedata" + before_function[import_end:]
            else:
                before_function += "\nimport unicodedata\n"
    
    # Ajouter la fonction normalize_text si elle n'est pas déjà présente
    if "def normalize_text(" not in before_function:
        normalize_text_func = """

def normalize_text(text):
    # Normalise le texte en supprimant les accents et en convertissant en minuscules.
    # 
    # Args:
    #     text (str): Texte à normaliser
    #     
    # Returns:
    #     str: Texte normalisé
    if not text or not isinstance(text, str):
        return ""
    
    # Normaliser les caractères Unicode (NFD décompose les caractères accentués)
    normalized = unicodedata.normalize('NFD', text)
    # Supprimer les caractères diacritiques (accents)
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    # Convertir en minuscules
    return normalized.lower()
"""
        # Ajouter la fonction après les imports
        import_end = before_function.rfind("\n\n", 0, len(before_function) - 1)
        if import_end != -1:
            before_function = before_function[:import_end] + normalize_text_func + before_function[import_end:]
        else:
            before_function += normalize_text_func
    
    # Créer le nouveau contenu du fichier
    new_content = before_function + improved_function + after_function
    
    # Écrire le nouveau contenu dans le fichier
    try:
        with open(cloud_api_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        logger.info(f"Fonction d'extraction améliorée intégrée dans {cloud_api_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'écriture du fichier: {str(e)}")
        # Restaurer la sauvegarde en cas d'erreur
        try:
            shutil.copy2(backup_path, cloud_api_path)
            logger.info(f"Restauration de la sauvegarde: {backup_path} -> {cloud_api_path}")
        except Exception as e2:
            logger.error(f"Erreur lors de la restauration de la sauvegarde: {str(e2)}")
        return False

def main():
    """Fonction principale."""
    logger.info("=== Début de l'intégration ===")
    
    # Intégrer la fonction d'extraction améliorée
    success = integrate_improved_extraction()
    
    if success:
        logger.info("=== Intégration réussie ===")
    else:
        logger.error("=== Échec de l'intégration ===")
    
    return success

if __name__ == "__main__":
    main()