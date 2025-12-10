import os
import sys
import json
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_file(file_path):
    """Crée une sauvegarde du fichier spécifié."""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.bak"
        try:
            with open(file_path, 'r', encoding='utf-8') as src_file:
                content = src_file.read()
            
            with open(backup_path, 'w', encoding='utf-8') as backup_file:
                backup_file.write(content)
            
            logger.info(f"Sauvegarde créée: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la création de la sauvegarde: {e}")
            return False
    else:
        logger.warning(f"Le fichier {file_path} n'existe pas, aucune sauvegarde créée")
        return False

def fix_external_apis_file():
    """Corrige les problèmes d'autorisation réseau dans le fichier external_apis.py."""
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "external_apis.py")
    
    if not os.path.exists(file_path):
        logger.error(f"Le fichier {file_path} n'existe pas")
        return False
    
    # Créer une sauvegarde avant modification
    if not backup_file(file_path):
        logger.warning("Impossible de créer une sauvegarde, annulation des modifications")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Modifications à apporter
        
        # 1. Ajouter des en-têtes User-Agent aux requêtes HTTP
        user_agent_header = "{'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}"
        
        # Remplacer les appels requests.get sans en-tête
        content = content.replace(
            "response = requests.get(url, params=params, timeout=10)", 
            f"headers = {user_agent_header}\n            response = requests.get(url, params=params, headers=headers, timeout=10)"
        )
        
        content = content.replace(
            "response = requests.get(url, timeout=10)", 
            f"headers = {user_agent_header}\n            response = requests.get(url, headers=headers, timeout=10)"
        )
        
        # Remplacer les appels requests.post sans en-tête
        content = content.replace(
            "response = requests.post(url, data={\"data\": query}, timeout=10)", 
            f"headers = {user_agent_header}\n            response = requests.post(url, data={{\"data\": query}}, headers=headers, timeout=10)"
        )
        
        # 2. Améliorer la gestion des erreurs réseau
        error_handling = """
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Erreur de connexion: {e}")
            if 'WinError 10013' in str(e):
                logger.error("Erreur d'autorisation réseau. Essayez d'exécuter l'application en tant qu'administrateur.")
            return {"error": f"Erreur de connexion: {str(e)}"}
        except requests.exceptions.Timeout as e:
            logger.error(f"Délai d'attente dépassé: {e}")
            return {"error": f"Délai d'attente dépassé: {str(e)}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de requête: {e}")
            return {"error": f"Erreur de requête: {str(e)}"}
        """
        
        # Remplacer les blocs except génériques par une gestion d'erreur plus précise
        content = content.replace(
            "except Exception as e:\n            logger.error", 
            "except Exception as e:\n            if isinstance(e, requests.exceptions.RequestException):\n                if 'WinError 10013' in str(e):\n                    logger.error(f\"Erreur d'autorisation réseau: {e}. Essayez d'exécuter l'application en tant qu'administrateur.\")\n                else:\n                    logger.error"
        )
        
        # 3. Ajouter un mécanisme de retry pour les requêtes HTTP
        retry_import = "from requests.adapters import HTTPAdapter\nfrom urllib3.util.retry import Retry\n"
        
        # Ajouter l'import au début du fichier, après les imports existants
        import_section_end = "from config import OUTPUT_DIR\n"
        content = content.replace(import_section_end, import_section_end + retry_import)
        
        # Ajouter une fonction pour créer une session avec retry
        create_session_function = """
# Fonction pour créer une session HTTP avec retry
def create_session_with_retry(retries=3, backoff_factor=0.3):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

"""
        
        # Ajouter la fonction après la section d'initialisation du logger
        logger_section_end = "logger = logging.getLogger(__name__)\n"
        content = content.replace(logger_section_end, logger_section_end + create_session_function)
        
        # 4. Utiliser la session avec retry dans les méthodes get_*_data
        # Remplacer requests.get par session.get
        content = content.replace(
            "response = requests.get(", 
            "session = create_session_with_retry()\n            response = session.get("
        )
        
        # Remplacer requests.post par session.post
        content = content.replace(
            "response = requests.post(", 
            "session = create_session_with_retry()\n            response = session.post("
        )
        
        # Écrire le contenu modifié dans le fichier
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        logger.info(f"Le fichier {file_path} a été modifié avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la modification du fichier: {e}")
        return False

def fix_export_api_to_excel_file():
    """Corrige les problèmes d'autorisation réseau dans le fichier export_api_to_excel.py."""
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "export_api_to_excel.py")
    
    if not os.path.exists(file_path):
        logger.error(f"Le fichier {file_path} n'existe pas")
        return False
    
    # Créer une sauvegarde avant modification
    if not backup_file(file_path):
        logger.warning("Impossible de créer une sauvegarde, annulation des modifications")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Modifications à apporter
        
        # 1. Ajouter des en-têtes User-Agent aux requêtes HTTP
        user_agent_header = "{'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}"
        
        # Remplacer les appels requests.get sans en-tête
        content = content.replace(
            "response = requests.get(url, params=params)", 
            f"headers = {user_agent_header}\n    response = requests.get(url, params=params, headers=headers)"
        )
        
        content = content.replace(
            "response = requests.get(url)", 
            f"headers = {user_agent_header}\n    response = requests.get(url, headers=headers)"
        )
        
        # Remplacer les appels requests.post sans en-tête
        content = content.replace(
            "response = requests.post(url, data=data)", 
            f"headers = {user_agent_header}\n    response = requests.post(url, data=data, headers=headers)"
        )
        
        # 2. Améliorer la gestion des erreurs réseau
        error_handling = """
    except requests.exceptions.ConnectionError as e:
        print(f"Erreur de connexion: {e}")
        if 'WinError 10013' in str(e):
            print("Erreur d'autorisation réseau. Essayez d'exécuter l'application en tant qu'administrateur.")
        return None
    except requests.exceptions.Timeout as e:
        print(f"Délai d'attente dépassé: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Erreur de requête: {e}")
        return None
    """
        
        # Remplacer les blocs except génériques par une gestion d'erreur plus précise
        content = content.replace(
            "except Exception as e:\n        print", 
            "except Exception as e:\n        if isinstance(e, requests.exceptions.RequestException):\n            if 'WinError 10013' in str(e):\n                print(f\"Erreur d'autorisation réseau: {e}. Essayez d'exécuter l'application en tant qu'administrateur.\")\n            else:\n                print"
        )
        
        # 3. Ajouter un mécanisme de retry pour les requêtes HTTP
        retry_import = "from requests.adapters import HTTPAdapter\nfrom urllib3.util.retry import Retry\n"
        
        # Ajouter l'import au début du fichier, après les imports existants
        import_section_end = "import pandas as pd\n"
        content = content.replace(import_section_end, import_section_end + retry_import)
        
        # Ajouter une fonction pour créer une session avec retry
        create_session_function = """
# Fonction pour créer une session HTTP avec retry
def create_session_with_retry(retries=3, backoff_factor=0.3):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

"""
        
        # Ajouter la fonction après les imports
        content = content.replace(import_section_end + retry_import, import_section_end + retry_import + create_session_function)
        
        # 4. Utiliser la session avec retry dans les fonctions get_*_data
        # Remplacer requests.get par session.get
        content = content.replace(
            "response = requests.get(", 
            "session = create_session_with_retry()\n    response = session.get("
        )
        
        # Remplacer requests.post par session.post
        content = content.replace(
            "response = requests.post(", 
            "session = create_session_with_retry()\n    response = session.post("
        )
        
        # Écrire le contenu modifié dans le fichier
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        logger.info(f"Le fichier {file_path} a été modifié avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la modification du fichier: {e}")
        return False

def main():
    """Fonction principale pour exécuter les corrections."""
    logger.info("=== Début des corrections des problèmes d'autorisation réseau ===")
    
    # Corriger le fichier external_apis.py
    logger.info("\n=== Correction du fichier external_apis.py ===")
    if fix_external_apis_file():
        logger.info("✅ Fichier external_apis.py corrigé avec succès")
    else:
        logger.error("❌ Échec de la correction du fichier external_apis.py")
    
    # Corriger le fichier export_api_to_excel.py
    logger.info("\n=== Correction du fichier export_api_to_excel.py ===")
    if fix_export_api_to_excel_file():
        logger.info("✅ Fichier export_api_to_excel.py corrigé avec succès")
    else:
        logger.error("❌ Échec de la correction du fichier export_api_to_excel.py")
    
    logger.info("\n=== Fin des corrections ===")
    logger.info("Pour appliquer les corrections, redémarrez l'application.")

if __name__ == "__main__":
    main()