#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module d'intégration de l'API Gemini pour l'analyse environnementale.

Ce module fournit des fonctions pour utiliser l'API Gemini de Google
pour l'analyse d'images et de textes liés à l'environnement.
"""

import os
import logging
import requests
import json
from typing import Dict, Any, Optional, List, Union
from PIL import Image
import base64
import io

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeminiAPI:
    """
    Classe pour interagir avec l'API Gemini de Google.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise la classe GeminiAPI.
        
        Args:
            api_key (str, optional): Clé API Gemini. Si non fournie, la fonction essaiera
                                     de la récupérer depuis le fichier de configuration ou
                                     la variable d'environnement GEMINI_API_KEY.
        """
        # Essayer d'abord avec la clé fournie en paramètre
        self.api_key = api_key
        
        # Si aucune clé n'est fournie, essayer de la charger depuis le fichier de configuration
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gemini_api_config.json")
        self.default_model = "gemini-1.5-pro-latest"  # Modèle par défaut pour l'analyse d'images
        self.text_model = "gemini-pro"  # Modèle par défaut pour la génération de texte
        
        if not self.api_key:
            try:
                if os.path.exists(self.config_path):
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                        self.api_key = config.get("api_key")
                        self.default_model = config.get("default_model", self.default_model)
                        self.text_model = config.get("text_model", self.text_model)
                        logger.info("Configuration Gemini chargée depuis le fichier de configuration.")
            except Exception as e:
                logger.error(f"Erreur lors du chargement de la configuration: {str(e)}")
        
        # Si toujours pas de clé, essayer avec la variable d'environnement
        if not self.api_key:
            self.api_key = os.environ.get("GEMINI_API_KEY")
            
        if not self.api_key:
            logger.warning("Aucune clé API Gemini trouvée. Utilisez set_api_key() pour définir la clé.")
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def set_api_key(self, api_key: str) -> None:
        """
        Définit la clé API Gemini.
        
        Args:
            api_key (str): Clé API Gemini.
        """
        self.api_key = api_key
        logger.info("Clé API Gemini définie avec succès.")
    
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Effectue une requête à l'API Gemini.
        
        Args:
            endpoint (str): Point de terminaison de l'API.
            data (Dict[str, Any]): Données à envoyer dans la requête.
            
        Returns:
            Dict[str, Any]: Réponse de l'API ou dictionnaire contenant des informations d'erreur.
            
        Raises:
            ValueError: Si la clé API n'est pas définie.
        """
        if not self.api_key:
            raise ValueError("Clé API Gemini non définie. Utilisez set_api_key() pour définir la clé.")
        
        url = f"{self.base_url}/{endpoint}?key={self.api_key}"
        response = None
        
        try:
            logger.info(f"Envoi d'une requête à l'API Gemini: {endpoint}")
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            # Vérifier si la requête a réussi
            if response.status_code == 200:
                logger.info("Requête à l'API Gemini réussie")
                return response.json()
            else:
                error_message = f"Erreur API Gemini: {response.status_code} - {response.reason}"
                error_detail = ""
                
                # Essayer d'extraire plus de détails sur l'erreur
                try:
                    error_json = response.json()
                    if 'error' in error_json:
                        error_detail = error_json['error'].get('message', '')
                except Exception:
                    pass
                
                logger.error(f"{error_message}. Détails: {error_detail}")
                
                # Retourner un dictionnaire d'erreur structuré
                return {
                    "erreur": True,
                    "code": response.status_code,
                    "message": error_message,
                    "details": error_detail
                }
                
        except requests.exceptions.RequestException as e:
            error_message = f"Erreur lors de la requête à l'API Gemini: {str(e)}"
            logger.error(error_message)
            
            # Extraire plus d'informations si disponibles
            error_detail = ""
            if response and hasattr(response, 'text'):
                error_detail = response.text
                logger.error(f"Détails de l'erreur: {error_detail}")
            
            # Retourner un dictionnaire d'erreur structuré au lieu de lever une exception
            return {
                "erreur": True,
                "code": "REQUEST_ERROR",
                "message": error_message,
                "details": error_detail
            }
    
    def _encode_image(self, image_path: str) -> str:
        """
        Encode une image en base64 pour l'API Gemini.
        
        Args:
            image_path (str): Chemin vers l'image à encoder.
            
        Returns:
            str: Image encodée en base64.
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    def list_models(self) -> Dict[str, Any]:
        """
        Liste les modèles disponibles dans l'API Gemini.
        
        Cette méthode est utile pour vérifier si la clé API est valide.
        
        Returns:
            Dict[str, Any]: Liste des modèles disponibles ou message d'erreur.
        """
        try:
            url = f"{self.base_url}/models?key={self.api_key}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la requête pour lister les modèles: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                error_text = e.response.text
                logger.error(f"Statut HTTP: {status_code}, Détails: {error_text}")
                return {"error": {"code": status_code, "message": error_text}}
            return {"error": {"message": str(e)}}
    
    def generate_content(self, prompt: str, model: str = None) -> Union[str, Dict[str, Any]]:
        """
        Génère du contenu textuel avec l'API Gemini.
        
        Args:
            prompt (str): Prompt textuel à envoyer à l'API.
            model (str, optional): Modèle Gemini à utiliser. Par défaut utilise le modèle de texte configuré.
            
        Returns:
            Union[str, Dict[str, Any]]: Réponse générée par l'API ou dictionnaire d'erreur.
        """
        # Utiliser le modèle de texte par défaut si aucun n'est spécifié
        if model is None:
            model = self.text_model
            
        logger.info(f"Génération de contenu avec le modèle {model}")
        
        # Vérifier que le prompt n'est pas vide
        if not prompt or not prompt.strip():
            error_message = "Le prompt ne peut pas être vide"
            logger.error(error_message)
            return {"erreur": True, "message": error_message}
            
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        endpoint = f"models/{model}:generateContent"
        response = self._make_request(endpoint, data)
        
        # Vérifier si la réponse contient une erreur
        if isinstance(response, dict) and response.get("erreur"):
            logger.error(f"Erreur lors de la génération de contenu: {response.get('message')}")
            return response
        
        # Extraire le texte de la réponse
        try:
            return response["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            error_message = f"Erreur lors de l'extraction du texte de la réponse: {str(e)}"
            logger.error(error_message)
            logger.debug(f"Réponse complète: {response}")
            return {
                "erreur": True,
                "message": error_message,
                "details": "Format de réponse inattendu",
                "response_data": str(response)
            }
    
    def analyze_image(self, image_path: str, prompt: str, model: str = None) -> Union[str, Dict[str, Any]]:
        """
        Analyse une image avec l'API Gemini.
        
        Args:
            image_path (str): Chemin vers l'image à analyser.
            prompt (str): Prompt textuel pour guider l'analyse de l'image.
            model (str, optional): Modèle Gemini à utiliser. Si None, utilise le modèle par défaut configuré.
            
        Returns:
            Union[str, Dict[str, Any]]: Résultat de l'analyse de l'image ou dictionnaire d'erreur.
        """
        
        # Utiliser le modèle par défaut si aucun n'est spécifié
        if model is None:
            model = self.default_model
        logger.info(f"Analyse d'image avec le modèle {model}: {image_path}")
        
        # Vérifier que le prompt n'est pas vide
        if not prompt or not prompt.strip():
            error_message = "Le prompt ne peut pas être vide"
            logger.error(error_message)
            return {"erreur": True, "message": error_message}
        
        try:
            # Vérifier que le fichier image existe
            if not os.path.exists(image_path):
                error_msg = f"Le fichier image n'existe pas: {image_path}"
                logger.error(error_msg)
                return {"erreur": True, "message": error_msg}
            
            # Vérifier que le fichier est une image valide
            try:
                Image.open(image_path).verify()
                logger.info(f"Image validée: {image_path}")
            except Exception as img_error:
                error_msg = f"Fichier image invalide ou corrompu: {str(img_error)}"
                logger.error(error_msg)
                return {"erreur": True, "message": error_msg}
            
            # Encoder l'image en base64
            try:
                logger.info(f"Encodage de l'image: {image_path}")
                image_data = self._encode_image(image_path)
            except Exception as encode_error:
                error_msg = f"Erreur lors de l'encodage de l'image: {str(encode_error)}"
                logger.error(error_msg)
                return {"erreur": True, "message": error_msg}
            
            # Préparer les données pour l'API
            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            },
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": image_data
                                }
                            }
                        ]
                    }
                ]
            }
            
            # Faire la requête à l'API
            logger.info(f"Envoi de la requête à l'API Gemini avec le modèle {model}")
            endpoint = f"models/{model}:generateContent"
            response = self._make_request(endpoint, data)
            
            # Vérifier si la réponse contient une erreur
            if isinstance(response, dict) and response.get("erreur"):
                logger.error(f"Erreur lors de l'appel à l'API Gemini: {response.get('message')}")
                return response
            
            # Extraire le texte de la réponse
            try:
                result = response["candidates"][0]["content"]["parts"][0]["text"]
                logger.info("Réponse de l'API Gemini reçue avec succès")
                return result
            except (KeyError, IndexError) as e:
                error_msg = f"Erreur lors de l'extraction du texte de la réponse: {str(e)}"
                logger.error(error_msg)
                logger.debug(f"Réponse complète: {response}")
                return {"erreur": True, "message": error_msg, "details": str(response)}
        except Exception as e:
            error_msg = f"Erreur inattendue lors de l'analyse de l'image: {str(e)}"
            logger.error(error_msg)
            return {"erreur": True, "message": error_msg}
    
    def analyze_environmental_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyse une image environnementale avec l'API Gemini.
        
        Args:
            image_path (str): Chemin vers l'image environnementale à analyser.
            
        Returns:
            Dict[str, Any]: Résultat de l'analyse avec des informations structurées.
        """
        logger.info(f"Début de l'analyse environnementale de l'image: {image_path}")
        
        # Vérifier que le fichier image existe
        if not os.path.exists(image_path):
            error_msg = f"Le fichier image n'existe pas: {image_path}"
            logger.error(error_msg)
            return {
                "erreur": error_msg,
                "type_environnement": "Non déterminé",
                "polluants": [],
                "risques": [],
                "recommandations": []
            }
        
        # Vérifier que le fichier est une image valide
        try:
            from PIL import Image
            Image.open(image_path).verify()
            logger.info(f"Image validée: {image_path}")
        except Exception as img_error:
            error_msg = f"Fichier image invalide ou corrompu: {str(img_error)}"
            logger.error(error_msg)
            return {
                "erreur": error_msg,
                "type_environnement": "Non déterminé",
                "polluants": [],
                "risques": [],
                "recommandations": []
            }
            
        prompt = """
        Analyse cette image environnementale et fournit les informations suivantes au format JSON:
        1. Type d'environnement (urbain, industriel, naturel, etc.)
        2. Polluants visibles ou potentiels
        3. Risques environnementaux identifiés
        4. Recommandations pour améliorer la situation
        
        Format de réponse attendu:
        {
            "type_environnement": "...",
            "polluants": ["...", "..."],
            "risques": ["...", "..."],
            "recommandations": ["...", "..."]
        }
        """
        
        try:
            logger.info("Envoi de l'image à l'API Gemini pour analyse environnementale")
            response = self.analyze_image(image_path, prompt, model=self.default_model)
            
            # Vérifier si la réponse contient une erreur
            if isinstance(response, dict) and response.get("erreur"):
                logger.error(f"Erreur retournée par analyze_image: {response.get('message', 'Erreur inconnue')}")
                return {
                    "erreur": response.get('message', 'Erreur inconnue'),
                    "type_environnement": "Non déterminé",
                    "polluants": [],
                    "risques": [],
                    "recommandations": []
                }
                
            # Convertir la réponse en texte si ce n'est pas déjà le cas
            response_text = response if isinstance(response, str) else str(response)
            
            # Si la réponse est vide ou trop courte
            if not response_text or len(response_text) < 10:
                logger.warning(f"Réponse trop courte ou vide: '{response_text}'")
                return {
                    "erreur": "Réponse vide ou insuffisante de l'API",
                    "type_environnement": "Non déterminé",
                    "polluants": [],
                    "risques": [],
                    "recommandations": [],
                    "texte_brut": response_text
                }
            
            # Extraire le JSON de la réponse
            try:
                # Chercher un objet JSON dans la réponse
                import re
                logger.info("Recherche du bloc JSON dans la réponse")
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                
                if json_match:
                    json_str = json_match.group(0)
                    logger.info(f"Bloc JSON trouvé, longueur: {len(json_str)} caractères")
                    result = json.loads(json_str)
                    
                    # Vérifier que tous les champs requis sont présents
                    required_fields = ["type_environnement", "polluants", "risques", "recommandations"]
                    for field in required_fields:
                        if field not in result:
                            result[field] = [] if field != "type_environnement" else "Non déterminé"
                    
                    # Ajouter le texte brut
                    result["texte_brut"] = response_text
                    
                    logger.info("Analyse environnementale réussie")
                    return result
                else:
                    logger.warning("Aucun JSON trouvé dans la réponse")
                    return {
                        "erreur": "Format de réponse invalide - aucun JSON trouvé",
                        "type_environnement": "Non déterminé",
                        "polluants": [],
                        "risques": [],
                        "recommandations": [],
                        "texte_brut": response_text
                    }
            except json.JSONDecodeError as json_error:
                error_msg = f"Erreur lors du décodage JSON: {str(json_error)}"
                logger.error(error_msg)
                return {
                    "erreur": error_msg,
                    "type_environnement": "Non déterminé",
                    "polluants": [],
                    "risques": [],
                    "recommandations": [],
                    "texte_brut": response_text
                }
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'analyse environnementale: {str(e)}")
            return {
                "erreur": f"Erreur inattendue: {str(e)}",
                "type_environnement": "Non déterminé",
                "polluants": [],
                "risques": [],
                "recommandations": [],
                "texte_brut": ""
            }

# Exemple d'utilisation
if __name__ == "__main__":
    # Initialiser l'API Gemini avec la clé API
    gemini_api = GeminiAPI("AIzaSyA7QfEziIgen9FNoJHb4G6imoBKeySQauE")
    
    # Générer du contenu textuel
    response = gemini_api.generate_content("Expliquez comment l'IA fonctionne en quelques mots")
    print("Réponse textuelle:")
    print(response)
    print("\n" + "-"*50 + "\n")
    
    # Analyser une image (si disponible)
    try:
        image_path = "test_image.jpg"  # Remplacer par le chemin d'une image réelle
        if os.path.exists(image_path):
            response = gemini_api.analyze_environmental_image(image_path)
            print("Analyse d'image environnementale:")
            print(json.dumps(response, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Erreur lors de l'analyse de l'image: {str(e)}")