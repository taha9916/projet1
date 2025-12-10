#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de logging centralisé et configurable pour l'application d'analyse de risque environnemental.

Ce module fournit des fonctionnalités avancées de logging avec:
- Configuration centralisée
- Rotation des fichiers de log
- Niveaux de log différenciés
- Formatage personnalisable
- Gestion des encodages
- Filtres personnalisables
"""

import os
import logging
import logging.handlers
import json
from datetime import datetime
from config import LOG_CONFIG

# Constantes par défaut
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_ENCODING = "utf-8"

# Mapping des niveaux de log
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

class LoggerManager:
    """Gestionnaire centralisé des loggers de l'application."""
    
    _instance = None
    _initialized = False
    _loggers = {}
    
    def __new__(cls):
        """Implémentation du pattern Singleton."""
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialise le gestionnaire de loggers."""
        if not self._initialized:
            self._config = self._load_config()
            self._setup_root_logger()
            self._initialized = True
    
    def _load_config(self):
        """Charge la configuration de logging depuis config.py ou utilise les valeurs par défaut."""
        config = {
            "log_file": LOG_CONFIG.get("log_file", "app.log"),
            "log_level": LOG_CONFIG.get("log_level", DEFAULT_LOG_LEVEL),
            "log_format": LOG_CONFIG.get("log_format", DEFAULT_LOG_FORMAT),
            "date_format": LOG_CONFIG.get("date_format", DEFAULT_DATE_FORMAT),
            "encoding": LOG_CONFIG.get("encoding", DEFAULT_ENCODING),
            "max_bytes": LOG_CONFIG.get("max_bytes", 10 * 1024 * 1024),  # 10 Mo par défaut
            "backup_count": LOG_CONFIG.get("backup_count", 5),  # 5 fichiers de backup par défaut
            "console_output": LOG_CONFIG.get("console_output", True),
            "third_party_loggers": LOG_CONFIG.get("third_party_loggers", {
                "PIL": "WARNING",
                "matplotlib": "WARNING",
                "requests": "WARNING",
                "urllib3": "WARNING",
                "transformers": "WARNING"
            })
        }
        
        # Créer le répertoire du fichier de log si nécessaire
        log_dir = os.path.dirname(config["log_file"])
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        return config
    
    def _setup_root_logger(self):
        """Configure le logger racine avec les paramètres de base."""
        # Réinitialiser les handlers existants
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:  # Copie de la liste pour éviter les problèmes de modification pendant l'itération
            root_logger.removeHandler(handler)
        
        # Définir le niveau de log global
        root_logger.setLevel(LOG_LEVELS.get(self._config["log_level"], logging.INFO))
        
        # Créer le formateur
        formatter = logging.Formatter(
            fmt=self._config["log_format"],
            datefmt=self._config["date_format"]
        )
        
        # Ajouter le handler de fichier avec rotation
        file_handler = logging.handlers.RotatingFileHandler(
            filename=self._config["log_file"],
            maxBytes=self._config["max_bytes"],
            backupCount=self._config["backup_count"],
            encoding=self._config["encoding"]
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Ajouter le handler de console si activé
        if self._config["console_output"]:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # Configurer les loggers tiers
        for logger_name, level in self._config["third_party_loggers"].items():
            third_party_logger = logging.getLogger(logger_name)
            third_party_logger.setLevel(LOG_LEVELS.get(level, logging.WARNING))
    
    def get_logger(self, name):
        """Obtient un logger configuré pour le module spécifié.
        
        Args:
            name: Nom du module (généralement __name__)
            
        Returns:
            Un objet logger configuré
        """
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        return self._loggers[name]
    
    def set_level(self, level, logger_name=None):
        """Change dynamiquement le niveau de log.
        
        Args:
            level: Niveau de log ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
            logger_name: Nom du logger spécifique (None pour le logger racine)
        """
        log_level = LOG_LEVELS.get(level.upper(), logging.INFO)
        
        if logger_name:
            logger = logging.getLogger(logger_name)
            logger.setLevel(log_level)
        else:
            logging.getLogger().setLevel(log_level)
    
    def add_file_handler(self, filename, level="INFO", format_str=None):
        """Ajoute un handler de fichier supplémentaire.
        
        Utile pour enregistrer certains types de logs dans des fichiers séparés.
        
        Args:
            filename: Chemin du fichier de log
            level: Niveau de log pour ce handler
            format_str: Format personnalisé (utilise le format par défaut si None)
        """
        log_level = LOG_LEVELS.get(level.upper(), logging.INFO)
        
        # Créer le répertoire si nécessaire
        log_dir = os.path.dirname(filename)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Créer le handler
        handler = logging.handlers.RotatingFileHandler(
            filename=filename,
            maxBytes=self._config["max_bytes"],
            backupCount=self._config["backup_count"],
            encoding=self._config["encoding"]
        )
        
        # Définir le niveau et le format
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            fmt=format_str or self._config["log_format"],
            datefmt=self._config["date_format"]
        )
        handler.setFormatter(formatter)
        
        # Ajouter au logger racine
        logging.getLogger().addHandler(handler)
        
        return handler
    
    def create_module_logger(self, module_name, level=None):
        """Crée un logger spécifique pour un module avec un niveau personnalisé.
        
        Args:
            module_name: Nom du module
            level: Niveau de log spécifique pour ce module
            
        Returns:
            Un objet logger configuré
        """
        logger = logging.getLogger(module_name)
        
        if level:
            log_level = LOG_LEVELS.get(level.upper(), None)
            if log_level:
                logger.setLevel(log_level)
        
        return logger

# Fonction d'initialisation globale
def setup_logging():
    """Configure le système de logging et retourne le logger principal.
    
    Returns:
        Le logger principal de l'application
    """
    manager = LoggerManager()
    return manager.get_logger("app")

# Fonction pour obtenir un logger pour un module spécifique
def get_logger(name):
    """Obtient un logger configuré pour le module spécifié.
    
    Args:
        name: Nom du module (généralement __name__)
        
    Returns:
        Un objet logger configuré
    """
    manager = LoggerManager()
    return manager.get_logger(name)

# Fonction pour changer dynamiquement le niveau de log
def set_log_level(level, logger_name=None):
    """Change dynamiquement le niveau de log.
    
    Args:
        level: Niveau de log ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        logger_name: Nom du logger spécifique (None pour le logger racine)
    """
    manager = LoggerManager()
    manager.set_level(level, logger_name)

# Fonction pour ajouter un handler de fichier séparé
def add_file_handler(filename, level="INFO", format_str=None):
    """Ajoute un handler de fichier supplémentaire.
    
    Args:
        filename: Chemin du fichier de log
        level: Niveau de log pour ce handler
        format_str: Format personnalisé
        
    Returns:
        Le handler créé
    """
    manager = LoggerManager()
    return manager.add_file_handler(filename, level, format_str)

# Classe de filtre personnalisable
class ModuleFilter(logging.Filter):
    """Filtre les messages de log en fonction du module source."""
    
    def __init__(self, module_prefix):
        """Initialise le filtre avec un préfixe de module.
        
        Args:
            module_prefix: Préfixe du module à filtrer (ex: 'data_processing')
        """
        super().__init__()
        self.module_prefix = module_prefix
    
    def filter(self, record):
        """Filtre les enregistrements de log.
        
        Args:
            record: Enregistrement de log à filtrer
            
        Returns:
            True si l'enregistrement doit être inclus, False sinon
        """
        return record.name.startswith(self.module_prefix)

# Classe pour les logs d'audit (actions importantes)
class AuditLogger:
    """Logger spécialisé pour les actions d'audit importantes."""
    
    def __init__(self, audit_file="audit.log"):
        """Initialise le logger d'audit.
        
        Args:
            audit_file: Chemin du fichier d'audit
        """
        self.logger = logging.getLogger("audit")
        
        # Créer le répertoire si nécessaire
        log_dir = os.path.dirname(audit_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Format spécial pour l'audit avec plus de détails
        audit_format = "%(asctime)s - AUDIT - %(levelname)s - %(message)s - [%(user)s] [%(ip)s]"
        formatter = logging.Formatter(audit_format)
        
        # Handler spécifique pour l'audit
        handler = logging.handlers.RotatingFileHandler(
            filename=audit_file,
            maxBytes=10 * 1024 * 1024,  # 10 Mo
            backupCount=10,  # 10 fichiers de backup
            encoding="utf-8"
        )
        handler.setFormatter(formatter)
        
        # Configurer le logger d'audit
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_action(self, action, user="system", ip="localhost", level="INFO", **kwargs):
        """Enregistre une action d'audit.
        
        Args:
            action: Description de l'action
            user: Utilisateur ayant effectué l'action
            ip: Adresse IP de l'utilisateur
            level: Niveau de log
            **kwargs: Données supplémentaires à enregistrer
        """
        # Créer un dictionnaire avec les informations d'audit
        audit_data = {
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "ip": ip,
            **kwargs
        }
        
        # Créer un message formaté
        message = f"{action} - {json.dumps(kwargs)}"
        
        # Ajouter des informations supplémentaires au record
        extra = {"user": user, "ip": ip}
        
        # Enregistrer selon le niveau spécifié
        log_level = LOG_LEVELS.get(level.upper(), logging.INFO)
        self.logger.log(log_level, message, extra=extra)
        
        return audit_data

# Si exécuté directement, configurer le logging et afficher un message de test
if __name__ == "__main__":
    logger = setup_logging()
    logger.debug("Message de test (DEBUG)")
    logger.info("Message de test (INFO)")
    logger.warning("Message de test (WARNING)")
    logger.error("Message de test (ERROR)")
    logger.critical("Message de test (CRITICAL)")
    
    # Tester le logger d'audit
    audit = AuditLogger()
    audit.log_action("Test d'audit", user="test_user", ip="127.0.0.1", fichier="test.txt")
    
    print("Tests de logging terminés. Vérifiez les fichiers de log.")