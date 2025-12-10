import os
import json
import logging
from diskcache import Cache
from functools import wraps
import hashlib

# Initialiser le logging pour ce module
logger = logging.getLogger(__name__)

# Chemin vers le dossier de cache
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diskcache')

# Créer le dossier de cache s'il n'existe pas
os.makedirs(CACHE_DIR, exist_ok=True)

# Initialiser le cache
cache = Cache(CACHE_DIR)

# Durée de vie par défaut du cache en secondes (1 jour)
DEFAULT_CACHE_EXPIRY = 86400

def get_cache_key(func_name, *args, **kwargs):
    """
    Génère une clé de cache unique basée sur le nom de la fonction et ses arguments.
    """
    # Créer une représentation des arguments
    key_parts = [func_name]
    
    # Ajouter les arguments positionnels
    for arg in args:
        key_parts.append(str(arg))
    
    # Ajouter les arguments nommés, triés par nom
    for k in sorted(kwargs.keys()):
        key_parts.append(f"{k}={kwargs[k]}")
    
    # Joindre toutes les parties et créer un hash
    key_str = "|".join(key_parts)
    return hashlib.md5(key_str.encode()).hexdigest()

def cached(expiry=DEFAULT_CACHE_EXPIRY):
    """
    Décorateur pour mettre en cache le résultat d'une fonction.
    
    Args:
        expiry: Durée de vie du cache en secondes
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Générer la clé de cache
            cache_key = get_cache_key(func.__name__, *args, **kwargs)
            
            # Vérifier si le résultat est dans le cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__} with key {cache_key}")
                return cached_result
            
            # Exécuter la fonction et mettre en cache le résultat
            logger.debug(f"Cache miss for {func.__name__} with key {cache_key}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, expire=expiry)
            
            return result
        return wrapper
    return decorator

def clear_cache():
    """
    Vide complètement le cache.
    """
    cache.clear()
    logger.info("Cache cleared")

def get_cache_stats():
    """
    Retourne des statistiques sur l'utilisation du cache.
    """
    # La méthode stats() retourne un tuple (hits, misses) et non un dictionnaire
    hits, misses = cache.stats(enable=True)
    return {
        "size": len(cache),
        "directory": CACHE_DIR,
        "hit_count": hits,
        "miss_count": misses
    }

def get_cached_value(key):
    """
    Récupère une valeur du cache par sa clé.
    """
    return cache.get(key)

def set_cached_value(key, value, expiry=DEFAULT_CACHE_EXPIRY):
    """
    Définit une valeur dans le cache avec une clé spécifique.
    """
    cache.set(key, value, expire=expiry)
    return True

def delete_cached_value(key):
    """
    Supprime une valeur du cache par sa clé.
    """
    return cache.delete(key)