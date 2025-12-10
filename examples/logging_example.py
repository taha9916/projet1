#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exemple d'utilisation du système de logging centralisé et configurable.

Ce script montre comment utiliser les différentes fonctionnalités du module logger.py
pour implémenter un système de logging avancé dans l'application.
"""

import os
import sys
import time
import random

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer le module de logging centralisé
from logger import setup_logging, get_logger, set_log_level, add_file_handler, AuditLogger, ModuleFilter

# Configurer le logging principal
logger = setup_logging()

# Créer des loggers pour différents modules
data_logger = get_logger("data_processing")
model_logger = get_logger("model_interface")
api_logger = get_logger("cloud_api")

# Créer un logger d'audit
audit_logger = AuditLogger()

def simulate_data_processing():
    """Simule le traitement de données avec différents niveaux de log."""
    data_logger.info("Début du traitement des données")
    
    # Simuler différentes étapes avec différents niveaux de log
    for i in range(5):
        data_logger.debug(f"Étape de prétraitement {i+1}: Normalisation des données")
        time.sleep(0.5)
    
    # Simuler un avertissement
    if random.random() < 0.3:
        data_logger.warning("Certaines données sont manquantes ou incomplètes")
    
    # Simuler une erreur (mais continuer l'exécution)
    if random.random() < 0.2:
        data_logger.error("Erreur lors du traitement d'un segment de données")
    
    data_logger.info("Traitement des données terminé")

def simulate_model_operations():
    """Simule les opérations du modèle avec différents niveaux de log."""
    model_logger.info("Initialisation du modèle")
    
    # Simuler le chargement du modèle
    model_logger.debug("Chargement des poids du modèle")
    time.sleep(1)
    
    # Simuler une inférence
    model_logger.info("Exécution de l'inférence sur les données")
    time.sleep(0.5)
    
    # Simuler une erreur critique (qui arrête l'exécution)
    if random.random() < 0.1:
        model_logger.critical("Erreur critique: Mémoire insuffisante pour exécuter le modèle")
        return False
    
    model_logger.info("Opérations du modèle terminées avec succès")
    return True

def simulate_api_calls():
    """Simule des appels API avec différents niveaux de log."""
    api_logger.info("Préparation des appels API")
    
    # Simuler différents appels API
    apis = ["Google Vision", "OpenAI", "Azure Computer Vision"]
    
    for api in apis:
        api_logger.debug(f"Configuration de l'API {api}")
        api_logger.info(f"Envoi de la requête à {api}")
        
        # Simuler une réponse API
        time.sleep(0.7)
        
        # Simuler différents résultats
        result = random.choice(["success", "error", "timeout"])
        
        if result == "success":
            api_logger.info(f"Réponse reçue de {api} avec succès")
            # Enregistrer dans le log d'audit
            audit_logger.log_action(
                action=f"Appel API {api}",
                user="system",
                ip="localhost",
                resultat="success",
                temps_reponse=f"{random.uniform(0.1, 2.0):.2f}s"
            )
        elif result == "error":
            api_logger.error(f"Erreur lors de l'appel à {api}: Code 403 Forbidden")
            # Enregistrer dans le log d'audit
            audit_logger.log_action(
                action=f"Appel API {api}",
                user="system",
                ip="localhost",
                resultat="error",
                code_erreur=403,
                message="Forbidden",
                level="ERROR"
            )
        else:  # timeout
            api_logger.warning(f"Timeout lors de l'appel à {api}")
            # Enregistrer dans le log d'audit
            audit_logger.log_action(
                action=f"Appel API {api}",
                user="system",
                ip="localhost",
                resultat="timeout",
                temps_attente="5s",
                level="WARNING"
            )
    
    api_logger.info("Tous les appels API sont terminés")

def demonstrate_dynamic_log_levels():
    """Démontre comment changer dynamiquement les niveaux de log."""
    print("\n=== Démonstration des niveaux de log dynamiques ===")
    
    # Logger initial (INFO par défaut)
    logger.debug("Ce message DEBUG ne devrait pas s'afficher")
    logger.info("Ce message INFO devrait s'afficher")
    
    # Changer le niveau de log à DEBUG
    print("\nChangement du niveau de log à DEBUG:")
    set_log_level("DEBUG")
    logger.debug("Ce message DEBUG devrait maintenant s'afficher")
    logger.info("Ce message INFO devrait toujours s'afficher")
    
    # Changer le niveau de log à WARNING
    print("\nChangement du niveau de log à WARNING:")
    set_log_level("WARNING")
    logger.debug("Ce message DEBUG ne devrait pas s'afficher")
    logger.info("Ce message INFO ne devrait pas s'afficher")
    logger.warning("Ce message WARNING devrait s'afficher")
    
    # Restaurer le niveau de log à INFO
    set_log_level("INFO")

def demonstrate_module_specific_logging():
    """Démontre comment configurer des niveaux de log spécifiques par module."""
    print("\n=== Démonstration des niveaux de log par module ===")
    
    # Configurer des niveaux différents pour chaque module
    set_log_level("DEBUG", "data_processing")
    set_log_level("INFO", "model_interface")
    set_log_level("WARNING", "cloud_api")
    
    # Tester les différents niveaux
    data_logger.debug("Message DEBUG de data_processing (devrait s'afficher)")
    model_logger.debug("Message DEBUG de model_interface (ne devrait pas s'afficher)")
    api_logger.debug("Message DEBUG de cloud_api (ne devrait pas s'afficher)")
    
    data_logger.info("Message INFO de data_processing (devrait s'afficher)")
    model_logger.info("Message INFO de model_interface (devrait s'afficher)")
    api_logger.info("Message INFO de cloud_api (ne devrait pas s'afficher)")
    
    # Restaurer les niveaux par défaut
    set_log_level("INFO", "data_processing")
    set_log_level("INFO", "model_interface")
    set_log_level("INFO", "cloud_api")

def demonstrate_separate_log_files():
    """Démontre comment utiliser des fichiers de log séparés."""
    print("\n=== Démonstration des fichiers de log séparés ===")
    
    # Créer un handler pour les erreurs uniquement
    error_handler = add_file_handler("logs/errors_only.log", "ERROR")
    
    # Créer un handler pour un module spécifique
    data_handler = add_file_handler("logs/data_processing.log", "DEBUG")
    data_handler.addFilter(ModuleFilter("data_processing"))
    
    # Générer quelques logs pour tester
    logger.info("Message INFO général (devrait aller dans app.log uniquement)")
    logger.error("Message ERROR général (devrait aller dans app.log ET errors_only.log)")
    
    data_logger.debug("Message DEBUG de data_processing (devrait aller dans app.log ET data_processing.log)")
    data_logger.error("Message ERROR de data_processing (devrait aller dans les trois fichiers de log)")
    
    print("Logs écrits dans les fichiers suivants:")
    print("- app.log (tous les messages)")
    print("- logs/errors_only.log (erreurs uniquement)")
    print("- logs/data_processing.log (messages du module data_processing uniquement)")

def main():
    """Fonction principale qui exécute les démonstrations."""
    print("=== Démonstration du système de logging centralisé et configurable ===")
    
    # Simuler les opérations normales
    print("\n1. Simulation du traitement de données...")
    simulate_data_processing()
    
    print("\n2. Simulation des opérations du modèle...")
    model_success = simulate_model_operations()
    
    if model_success:
        print("\n3. Simulation des appels API...")
        simulate_api_calls()
    
    # Démontrer les fonctionnalités avancées
    demonstrate_dynamic_log_levels()
    demonstrate_module_specific_logging()
    demonstrate_separate_log_files()
    
    print("\n=== Démonstration terminée ===")
    print("Consultez les fichiers de log pour voir les résultats.")

if __name__ == "__main__":
    # Créer le répertoire logs s'il n'existe pas
    os.makedirs("logs", exist_ok=True)
    
    # Exécuter la démonstration
    main()