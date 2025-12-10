import json
import re
import logging
import pandas as pd
from cloud_api import normalize_text

logger = logging.getLogger(__name__)

def _extract_from_json(response_text):
    """Extrait les paramètres d'une réponse au format JSON.
    
    Args:
        response_text (str): Texte de la réponse au format JSON
        
    Returns:
        pandas.DataFrame: DataFrame contenant les paramètres extraits
    """
    try:
        # Tenter de charger le JSON
        data = json.loads(response_text)
        
        # Vérifier si le JSON contient une liste de paramètres
        if isinstance(data, list):
            # Cas où le JSON est une liste d'objets
            parameters = []
            for item in data:
                # Vérifier si l'objet contient les clés attendues
                if isinstance(item, dict):
                    param = {}
                    # Mapper les clés possibles aux noms de colonnes attendus
                    key_mapping = {
                        "parameter": "Paramètre",
                        "parametre": "Paramètre",
                        "paramètre": "Paramètre",
                        "param": "Paramètre",
                        "name": "Paramètre",
                        "nom": "Paramètre",
                        
                        "value": "Valeur mesurée",
                        "valeur": "Valeur mesurée",
                        "measured_value": "Valeur mesurée",
                        "valeur_mesuree": "Valeur mesurée",
                        "valeur_mesurée": "Valeur mesurée",
                        
                        "unit": "Unité",
                        "unite": "Unité",
                        "unité": "Unité",
                        "units": "Unité",
                        "unites": "Unité",
                        "unités": "Unité"
                    }
                    
                    # Parcourir les clés de l'objet et les mapper aux noms de colonnes attendus
                    for key, value in item.items():
                        key_lower = key.lower()
                        for possible_key, column_name in key_mapping.items():
                            if normalize_text(key_lower) == normalize_text(possible_key):
                                param[column_name] = str(value)
                                break
                    
                    # Ajouter le paramètre à la liste si au moins une clé a été mappée
                    if param:
                        parameters.append(param)
            
            # Créer un DataFrame à partir de la liste de paramètres
            if parameters:
                return pd.DataFrame(parameters)
        
        # Cas où le JSON est un objet avec des clés pour chaque paramètre
        elif isinstance(data, dict):
            parameters = []
            # Cas 1: {"param1": {"value": "...", "unit": "..."}, "param2": {...}}
            for param_name, param_data in data.items():
                if isinstance(param_data, dict):
                    param = {"Paramètre": param_name}
                    
                    # Mapper les clés possibles aux noms de colonnes attendus
                    value_keys = ["value", "valeur", "measured_value", "valeur_mesuree", "valeur_mesurée"]
                    unit_keys = ["unit", "unite", "unité", "units", "unites", "unités"]
                    
                    # Chercher la valeur
                    for key in value_keys:
                        if key in param_data:
                            param["Valeur mesurée"] = str(param_data[key])
                            break
                    
                    # Chercher l'unité
                    for key in unit_keys:
                        if key in param_data:
                            param["Unité"] = str(param_data[key])
                            break
                    
                    parameters.append(param)
                else:
                    # Cas 2: {"param1": "value1", "param2": "value2"}
                    # Dans ce cas, on considère que la clé est le nom du paramètre et la valeur est la valeur mesurée
                    parameters.append({
                        "Paramètre": param_name,
                        "Valeur mesurée": str(param_data),
                        "Unité": ""  # Unité inconnue
                    })
            
            # Créer un DataFrame à partir de la liste de paramètres
            if parameters:
                return pd.DataFrame(parameters)
        
        # Si on arrive ici, le format JSON n'est pas reconnu
        logger.warning("Format JSON non reconnu")
        return pd.DataFrame()
    
    except json.JSONDecodeError as e:
        logger.warning(f"Erreur de décodage JSON: {str(e)}")
        return pd.DataFrame()

def _extract_from_bullets(response_text):
    """Extrait les paramètres d'une réponse au format liste à puces.
    
    Args:
        response_text (str): Texte de la réponse au format liste à puces
        
    Returns:
        pandas.DataFrame: DataFrame contenant les paramètres extraits
    """
    # Rechercher les lignes qui commencent par - ou *
    bullet_pattern = r"^\s*[-*]\s+(.+)$"
    bullet_lines = re.findall(bullet_pattern, response_text, re.MULTILINE)
    
    if not bullet_lines:
        logger.warning("Aucune ligne à puces trouvée")
        return pd.DataFrame()
    
    parameters = []
    for line in bullet_lines:
        # Rechercher un format "Paramètre: Valeur Unité" ou "Paramètre - Valeur Unité"
        param_pattern = r"([^:]+)[:\-]\s*([\d.,]+)\s*([^\d\s].*)?"
        match = re.match(param_pattern, line.strip())
        
        if match:
            param_name = match.group(1).strip()
            param_value = match.group(2).strip()
            param_unit = match.group(3).strip() if match.group(3) else ""
            
            parameters.append({
                "Paramètre": param_name,
                "Valeur mesurée": param_value,
                "Unité": param_unit
            })
        else:
            # Essayer un autre format: "Paramètre = Valeur Unité"
            alt_pattern = r"([^=]+)=\s*([\d.,]+)\s*([^\d\s].*)?"
            match = re.match(alt_pattern, line.strip())
            
            if match:
                param_name = match.group(1).strip()
                param_value = match.group(2).strip()
                param_unit = match.group(3).strip() if match.group(3) else ""
                
                parameters.append({
                    "Paramètre": param_name,
                    "Valeur mesurée": param_value,
                    "Unité": param_unit
                })
    
    if parameters:
        return pd.DataFrame(parameters)
    else:
        logger.warning("Aucun paramètre extrait des lignes à puces")
        return pd.DataFrame()

def _extract_from_text(response_text):
    """Extrait les paramètres d'une réponse en texte libre structuré.
    
    Args:
        response_text (str): Texte de la réponse en format libre
        
    Returns:
        pandas.DataFrame: DataFrame contenant les paramètres extraits
    """
    # Rechercher des patterns comme "Paramètre: Valeur Unité" ou "Paramètre = Valeur Unité"
    patterns = [
        r"([\w\s]+)\s*:\s*([\d.,]+)\s*([^\d\s].+?)(?=[\n\r]|$)",  # Paramètre: Valeur Unité
        r"([\w\s]+)\s*=\s*([\d.,]+)\s*([^\d\s].+?)(?=[\n\r]|$)",  # Paramètre = Valeur Unité
        r"([\w\s]+)\s+est\s+de\s+([\d.,]+)\s*([^\d\s].+?)(?=[\n\r]|$)",  # Paramètre est de Valeur Unité
        r"([\w\s]+)\s+:\s+([\d.,]+)\s*([^\d\s].+?)(?=[\n\r]|$)"  # Paramètre : Valeur Unité
    ]
    
    parameters = []
    for pattern in patterns:
        matches = re.findall(pattern, response_text)
        for match in matches:
            param_name = match[0].strip()
            param_value = match[1].strip()
            param_unit = match[2].strip() if len(match) > 2 else ""
            
            parameters.append({
                "Paramètre": param_name,
                "Valeur mesurée": param_value,
                "Unité": param_unit
            })
    
    if parameters:
        return pd.DataFrame(parameters)
    else:
        logger.warning("Aucun paramètre extrait du texte libre")
        return pd.DataFrame()