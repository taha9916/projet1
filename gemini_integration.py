#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module d'intégration de l'API Gemini dans l'application principale.

Ce module permet d'utiliser l'API Gemini comme alternative pour l'analyse d'images
environnementales dans l'application principale.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Tuple
from gemini_api import GeminiAPI

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chemin du fichier de configuration pour l'API Gemini
GEMINI_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gemini_api_config.json")

def load_gemini_config() -> Dict[str, Any]:
    """
    Charge la configuration de l'API Gemini depuis le fichier de configuration.
    
    Returns:
        Dict[str, Any]: Configuration de l'API Gemini.
    """
    default_config = {
        "api_key": "",
        "enabled": False,
        "default_model": "gemini-2.0-pro-vision",
        "text_model": "gemini-2.0-flash",
        "max_tokens": 1024
    }
    
    if os.path.exists(GEMINI_CONFIG_PATH):
        try:
            with open(GEMINI_CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info("Configuration de l'API Gemini chargée avec succès.")
            return {**default_config, **config}  # Fusionner avec les valeurs par défaut
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration de l'API Gemini: {str(e)}")
    else:
        logger.warning(f"Fichier de configuration de l'API Gemini non trouvé: {GEMINI_CONFIG_PATH}")
        # Créer le fichier de configuration avec les valeurs par défaut
        save_gemini_config(default_config)
    
    return default_config

def save_gemini_config(config: Dict[str, Any]) -> bool:
    """
    Sauvegarde la configuration de l'API Gemini dans le fichier de configuration.
    
    Args:
        config (Dict[str, Any]): Configuration de l'API Gemini.
        
    Returns:
        bool: True si la sauvegarde a réussi, False sinon.
        
    Raises:
        TypeError: Si config n'est pas un dictionnaire.
        IOError: Si une erreur se produit lors de l'écriture du fichier.
    """
    try:
        # Vérifier si config est un dictionnaire
        if not isinstance(config, dict):
            error_msg = f"La configuration doit être un dictionnaire, reçu: {type(config)}"
            logger.error(error_msg)
            raise TypeError(error_msg)
            
        # Vérifier que les clés requises sont présentes
        required_keys = ["api_key", "enabled"]
        for key in required_keys:
            if key not in config:
                logger.warning(f"Clé requise '{key}' manquante dans la configuration Gemini")
                # Ajouter des valeurs par défaut si nécessaire
                if key == "enabled":
                    config["enabled"] = True
                    
        # Charger la configuration existante pour conserver les autres paramètres
        existing_config = {}
        if os.path.exists(GEMINI_CONFIG_PATH):
            try:
                with open(GEMINI_CONFIG_PATH, "r", encoding="utf-8") as f:
                    existing_config = json.load(f)
                    if not isinstance(existing_config, dict):
                        logger.warning("Le fichier de configuration existant n'est pas un dictionnaire valide, utilisation d'un dictionnaire vide")
                        existing_config = {}
            except json.JSONDecodeError:
                logger.warning("Fichier de configuration existant non valide, utilisation d'un dictionnaire vide")
            except Exception as e:
                logger.warning(f"Erreur lors de la lecture du fichier de configuration existant: {str(e)}")
        
        # Fusionner avec la nouvelle configuration
        updated_config = {**existing_config, **config}
        
        # Ajouter des valeurs par défaut si nécessaires
        if "default_model" not in updated_config:
            updated_config["default_model"] = "gemini-2.0-pro-vision"
        if "text_model" not in updated_config:
            updated_config["text_model"] = "gemini-2.0-flash"
        if "max_tokens" not in updated_config:
            updated_config["max_tokens"] = 1024
        
        # Sauvegarder la configuration
        with open(GEMINI_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(updated_config, f, indent=2, ensure_ascii=False)
        logger.info("Configuration de l'API Gemini sauvegardée avec succès.")
        return True
    except TypeError as e:
        # Propager l'erreur de type pour qu'elle soit gérée par l'appelant
        logger.error(f"Erreur de type lors de la sauvegarde de la configuration: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de la configuration de l'API Gemini: {str(e)}")
        raise IOError(f"Erreur lors de la sauvegarde de la configuration: {str(e)}")
        return False

def initialize_gemini_api() -> Tuple[Optional[GeminiAPI], Dict[str, Any]]:
    """
    Initialise l'API Gemini avec la configuration chargée.
    
    Returns:
        Tuple[Optional[GeminiAPI], Dict[str, Any]]: Instance de l'API Gemini et configuration.
    """
    config = load_gemini_config()
    
    if not config["enabled"]:
        logger.info("L'API Gemini est désactivée dans la configuration.")
        return None, config
    
    if not config["api_key"]:
        logger.warning("Clé API Gemini non définie dans la configuration.")
        return None, config
    
    try:
        gemini_api = GeminiAPI(config["api_key"])
        logger.info("API Gemini initialisée avec succès.")
        return gemini_api, config
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de l'API Gemini: {str(e)}")
        return None, config

def _gemini_default_error(error_msg: str) -> tuple:
    import pandas as pd
    df = pd.DataFrame([{
        "Milieu": "Erreur",
        "Paramètre": error_msg,
        "Unité": "Non disponible",
        "Intervalle acceptable": "Non disponible",
        "Valeur mesurée": "Non disponible",
        "Résultat conformité": "Non disponible"
    }])
    result_dict = {
        "erreur": error_msg,
        "type_environnement": "Non déterminé",
        "polluants": [],
        "risques": [],
        "recommandations": []
    }
    return df, result_dict

def analyze_environmental_image_with_gemini(image_path: str, ocr_text: Optional[str] = None, use_ocr: bool = False) -> tuple:
    """
    Analyse une image environnementale avec l'API Gemini.
    
    Args:
        image_path (str): Chemin vers l'image à analyser.
        ocr_text (str, optional): Texte extrait de l'image par OCR.
        use_ocr (bool, optional): Indique si l'OCR doit être utilisé. Par défaut à False.
        
    Returns:
        Dict[str, Any]: Résultats de l'analyse.
    """
    logger.info(f"Début de l'analyse d'image avec Gemini: {image_path}")
    
    # Vérifier si le fichier existe
    if not os.path.exists(image_path):
        logger.error(f"Fichier image introuvable: {image_path}")
        return _gemini_default_error(f"Fichier image introuvable: {image_path}")
    
    gemini_api, config = initialize_gemini_api()
    
    if not gemini_api:
        logger.error("API Gemini non disponible ou désactivée.")
        return _gemini_default_error("API Gemini non disponible ou désactivée.")
    
    try:
        # Extraire le texte avec OCR si demandé et qu'aucun texte OCR n'a été fourni
        if use_ocr and not ocr_text:
            try:
                from image_preprocessing import extract_text_from_image
                logger.info(f"Tentative d'extraction de texte avec OCR depuis: {image_path}")
                ocr_text = extract_text_from_image(image_path)
                logger.info(f"Texte extrait avec OCR: {len(ocr_text) if ocr_text else 0} caractères")
            except Exception as ocr_error:
                logger.error(f"Erreur lors de l'extraction OCR: {str(ocr_error)}")
                ocr_text = ""
                logger.info("Poursuite de l'analyse sans OCR")
        
        # Vérifier si l'image est valide
        try:
            from PIL import Image
            Image.open(image_path).verify()  # Vérifier si l'image est valide
            logger.info("Image validée avec succès")
        except Exception as img_error:
            logger.error(f"Erreur lors de la validation de l'image: {str(img_error)}")
            return _gemini_default_error(f"Image invalide ou corrompue: {str(img_error)}")
        
        # Construire un prompt personnalisé si du texte OCR est disponible
        if ocr_text:
            prompt = f"""
            Analyse cette image environnementale et le texte extrait par OCR ci-dessous.
            Fournit les informations suivantes au format JSON:
            1. Type d'environnement (urbain, industriel, naturel, etc.)
            2. Polluants visibles ou potentiels
            3. Risques environnementaux identifiés
            4. Recommandations pour améliorer la situation
            
            Texte OCR extrait de l'image:
            {ocr_text}
            
            Format de réponse attendu:
            {{
                "type_environnement": "...",
                "polluants": ["...", "..."],
                "risques": ["...", "..."],
                "recommandations": ["...", "..."]
            }}
            """
            
            # Utiliser l'analyse d'image avec le prompt personnalisé
            try:
                logger.info(f"Envoi de l'image à l'API Gemini pour analyse: {image_path}")
                response = gemini_api.analyze_image(image_path, prompt)
                logger.info("Réponse reçue de l'API Gemini")
                
                if isinstance(response, dict) and response.get("erreur"):
                    logger.error(f"Erreur API Gemini: {response.get('message', str(response))}")
                    return _gemini_default_error(f"Erreur API Gemini: {response.get('message', str(response))}")
                if not response or (isinstance(response, str) and response.strip() == ""):
                    logger.error("Réponse vide reçue de l'API Gemini")
                    return _gemini_default_error("Réponse vide reçue de l'API Gemini")
            except Exception as api_error:
                logger.error(f"Erreur lors de l'appel à l'API Gemini: {str(api_error)}")
                return _gemini_default_error(f"Erreur lors de l'appel à l'API Gemini: {str(api_error)}")
            
            # Extraire le JSON de la réponse
            try:
                # Chercher le premier bloc JSON dans la réponse
                logger.info("Tentative d'extraction du JSON de la réponse")
                json_start = response.find('{')
                json_end = response.rfind('}')
                
                if json_start != -1 and json_end != -1:
                    json_str = response[json_start:json_end+1]
                    logger.debug(f"JSON extrait: {json_str}")
                    result_dict = json.loads(json_str)
                    logger.info("JSON parsé avec succès")
                else:
                    logger.warning("Aucun JSON trouvé dans la réponse. Utilisation de la réponse brute.")
                    result_dict = {
                        "type_environnement": "Non déterminé",
                        "polluants": [],
                        "risques": [],
                        "recommandations": [response],
                        "texte_brut": response
                    }
                
                # Créer un DataFrame à partir des données
                try:
                    logger.info("Création du DataFrame à partir des données")
                    import pandas as pd
                    df = pd.DataFrame()
                    
                    # Ajouter les paramètres environnementaux au DataFrame
                    if "polluants" in result_dict and result_dict["polluants"]:
                        logger.info(f"Ajout de {len(result_dict['polluants'])} polluants au DataFrame")
                        for polluant in result_dict["polluants"]:
                            # Utiliser pd.concat au lieu de append qui est déprécié
                            new_row = pd.DataFrame([{
                                "Milieu": result_dict.get("type_environnement", "Non déterminé"),
                                "Paramètre": polluant,
                                "Unité": "Non disponible",
                                "Intervalle acceptable": "Non disponible",
                                "Valeur mesurée": "Non disponible",
                                "Résultat conformité": "Non disponible"
                            }])
                            df = pd.concat([df, new_row], ignore_index=True)
                    
                    # Si aucun polluant n'est identifié, ajouter une ligne par défaut
                    if df.empty:
                        logger.info("Aucun polluant identifié, ajout d'une ligne par défaut")
                        new_row = pd.DataFrame([{
                            "Milieu": result_dict.get("type_environnement", "Non déterminé"),
                            "Paramètre": "Non identifié",
                            "Unité": "Non disponible",
                            "Intervalle acceptable": "Non disponible",
                            "Valeur mesurée": "Non disponible",
                            "Résultat conformité": "Non disponible"
                        }])
                        df = pd.concat([df, new_row], ignore_index=True)
                    
                    logger.info(f"DataFrame créé avec succès: {df.shape[0]} lignes")
                except Exception as df_error:
                    logger.error(f"Erreur lors de la création du DataFrame: {str(df_error)}")
                    # Créer un DataFrame minimal en cas d'erreur
                    df = pd.DataFrame([{
                        "Milieu": "Erreur",
                        "Paramètre": f"Erreur de traitement: {str(df_error)}",
                        "Unité": "Non disponible",
                        "Intervalle acceptable": "Non disponible",
                        "Valeur mesurée": "Non disponible",
                        "Résultat conformité": "Non disponible"
                    }])
                
                return df, result_dict
            except json.JSONDecodeError as e:
                logger.error(f"Erreur lors du décodage JSON: {str(e)}")
                result_dict = {
                    "type_environnement": "Non déterminé",
                    "polluants": [],
                    "risques": [],
                    "recommandations": [],
                    "texte_brut": response,
                    "erreur": "Impossible de parser la réponse en JSON"
                }
                
                # Créer un DataFrame vide avec message d'erreur
                import pandas as pd
                df = pd.DataFrame([{
                    "Milieu": "Erreur",
                    "Paramètre": "Erreur de format JSON",
                    "Unité": "Non disponible",
                    "Intervalle acceptable": "Non disponible",
                    "Valeur mesurée": "Non disponible",
                    "Résultat conformité": "Non disponible"
                }])
                
                return df, result_dict
        else:
            # Utiliser la fonction d'analyse environnementale standard
            result_dict = gemini_api.analyze_environmental_image(image_path)
            
            # Créer un DataFrame à partir des données
            import pandas as pd
            df = pd.DataFrame()
            
            # Ajouter les paramètres environnementaux au DataFrame
            if "polluants" in result_dict and result_dict["polluants"]:
                for polluant in result_dict["polluants"]:
                    df = df._append({
                        "Milieu": result_dict.get("type_environnement", "Non déterminé"),
                        "Paramètre": polluant,
                        "Unité": "Non disponible",
                        "Intervalle acceptable": "Non disponible",
                        "Valeur mesurée": "Non disponible",
                        "Résultat conformité": "Non disponible"
                    }, ignore_index=True)
            
            # Si aucun polluant n'est identifié, ajouter une ligne par défaut
            if df.empty:
                df = df._append({
                    "Milieu": result_dict.get("type_environnement", "Non déterminé"),
                    "Paramètre": "Non identifié",
                    "Unité": "Non disponible",
                    "Intervalle acceptable": "Non disponible",
                    "Valeur mesurée": "Non disponible",
                    "Résultat conformité": "Non disponible"
                }, ignore_index=True)
            
            return df, result_dict
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de l'image avec Gemini: {str(e)}")
        return _gemini_default_error(f"Erreur lors de l'analyse de l'image: {str(e)}")

# Exemple d'utilisation
if __name__ == "__main__":
    # Créer une configuration par défaut avec la clé API fournie
    config = {
        "api_key": "AIzaSyA7QfEziIgen9FNoJHb4G6imoBKeySQauE",
        "enabled": True,
        "default_model": "gemini-2.0-pro-vision",
        "text_model": "gemini-2.0-flash",
        "max_tokens": 1024
    }
    
    # Sauvegarder la configuration
    save_gemini_config(config)
    
    # Tester l'analyse d'une image (si disponible)
    try:
        image_path = "test_image.jpg"  # Remplacer par le chemin d'une image réelle
        
        # Analyser l'image avec OCR activé
        df, results = analyze_environmental_image_with_gemini(image_path, use_ocr=True)
        if os.path.exists(image_path):
            print(f"Analyse de l'image {image_path}...")
            print(f"DataFrame généré: {df.shape[0]} lignes")
            print("Résultats:", results)
        else:
            print(f"L'image {image_path} n'existe pas.")
        
        # Afficher les résultats de manière formatée
        print("Analyse d'image environnementale avec Gemini:")
        print(json.dumps(results, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Erreur lors du test: {str(e)}")