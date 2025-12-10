import requests
import json
import logging
import os
from bs4 import BeautifulSoup
from config import WEB_CONFIG

# Initialiser le logging pour ce module
logger = logging.getLogger(__name__)

class WebSearchEngine:
    """Classe pour effectuer des recherches web et extraire des informations environnementales."""
    
    def __init__(self, api_key=None):
        """Initialise le moteur de recherche web.
        
        Args:
            api_key (str, optional): Clé API pour les services de recherche (Google, Bing, etc.)
        """
        self.api_key = api_key
        self.user_agent = WEB_CONFIG["user_agent"]
        self.search_url = WEB_CONFIG["search_url"]
        
        # Créer un répertoire de cache si nécessaire
        self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def search(self, query, use_cache=True):
        """Effectue une recherche web et retourne les résultats.
        
        Args:
            query (str): La requête de recherche
            use_cache (bool): Utiliser le cache pour les requêtes déjà effectuées
            
        Returns:
            list: Liste des résultats de recherche
        """
        # Normaliser la requête
        normalized_query = query.replace('₃', '3').replace('₂', '2')
        logger.info(f"Recherche d'informations pour: {normalized_query}")
        
        # Vérifier le cache
        # Utiliser un hash sécurisé pour éviter les erreurs de type
        import hashlib
        query_hash = hashlib.md5(normalized_query.encode()).hexdigest()
        cache_file = os.path.join(self.cache_dir, f"{query_hash}.json")
        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erreur lors de la lecture du cache: {str(e)}")
        
        try:
            # Effectuer la recherche
            headers = {"User-Agent": self.user_agent}
            search_url = self.search_url.format(query=normalized_query)
            
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
            
            # Analyser les résultats
            results = self._parse_search_results(response.text)
            
            # Sauvegarder dans le cache
            if use_cache:
                try:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    logger.warning(f"Erreur lors de l'écriture dans le cache: {str(e)}")
            
            return results
        
        except Exception as e:
            logger.error(f"Erreur lors de la recherche web: {str(e)}")
            return []
    
    def _parse_search_results(self, html_content):
        """Analyse le contenu HTML pour extraire les résultats de recherche.
        
        Args:
            html_content (str): Le contenu HTML de la page de résultats
            
        Returns:
            list: Liste des résultats de recherche
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []
        
        # Essayer différentes classes pour les extraits de résultats
        search_snippets = soup.find_all('div', class_='BNeawe vvjwJb AP7Wnd')
        if not search_snippets:
            search_snippets = soup.find_all('div', class_='VwiC3b yXK7lf lVm3ye r025kc hJNv6b')
        
        for snippet in search_snippets[:5]:  # Limiter aux 5 premiers résultats
            results.append({
                "text": snippet.get_text(),
                "source": "web_search"
            })
        
        return results
    
    def extract_environmental_parameters(self, location, project_type):
        """Extrait les paramètres environnementaux basés sur la localisation et le type de projet.
        
        Args:
            location (str): La localisation du projet (ville, région, etc.)
            project_type (str): Le type de projet (industriel, agricole, etc.)
            
        Returns:
            dict: Dictionnaire des paramètres environnementaux
        """
        # Construire une requête spécifique
        query = f"paramètres environnementaux {project_type} {location} Maroc normes"
        results = self.search(query)
        
        # Extraire les paramètres environnementaux
        parameters = {
            "air": self._extract_air_parameters(results),
            "eau": self._extract_water_parameters(results),
            "sol": self._extract_soil_parameters(results),
            "bruit": self._extract_noise_parameters(results)
        }
        
        return parameters
    
    def _extract_air_parameters(self, search_results):
        """Extrait les paramètres de qualité de l'air à partir des résultats de recherche."""
        air_params = []
        air_keywords = ["PM10", "PM2.5", "CO2", "CO", "NOx", "SO2", "O3", "ozone", "particules", "qualité de l'air"]
        
        for result in search_results:
            text = result["text"]
            for keyword in air_keywords:
                if keyword.lower() in text.lower():
                    # Essayer d'extraire les valeurs et les unités
                    air_params.append(self._extract_parameter_info(text, keyword))
        
        return air_params
    
    def _extract_water_parameters(self, search_results):
        """Extrait les paramètres de qualité de l'eau à partir des résultats de recherche."""
        water_params = []
        water_keywords = ["pH", "turbidité", "DBO", "DCO", "nitrates", "phosphates", "coliformes", "métaux lourds", "qualité de l'eau"]
        
        for result in search_results:
            text = result["text"]
            for keyword in water_keywords:
                if keyword.lower() in text.lower():
                    water_params.append(self._extract_parameter_info(text, keyword))
        
        return water_params
    
    def _extract_soil_parameters(self, search_results):
        """Extrait les paramètres de qualité du sol à partir des résultats de recherche."""
        soil_params = []
        soil_keywords = ["pH du sol", "matière organique", "azote", "phosphore", "potassium", "métaux lourds sol", "contamination sol"]
        
        for result in search_results:
            text = result["text"]
            for keyword in soil_keywords:
                if keyword.lower() in text.lower():
                    soil_params.append(self._extract_parameter_info(text, keyword))
        
        return soil_params
    
    def _extract_noise_parameters(self, search_results):
        """Extrait les paramètres de bruit à partir des résultats de recherche."""
        noise_params = []
        noise_keywords = ["bruit", "décibels", "dB", "nuisance sonore"]
        
        for result in search_results:
            text = result["text"]
            for keyword in noise_keywords:
                if keyword.lower() in text.lower():
                    noise_params.append(self._extract_parameter_info(text, keyword))
        
        return noise_params
    
    def _extract_parameter_info(self, text, keyword):
        """Extrait les informations sur un paramètre à partir d'un texte."""
        # Initialiser le dictionnaire de paramètres
        param_info = {
            "Paramètre": keyword,
            "Unité": "Non disponible",
            "Intervalle acceptable": "Non disponible",
            "Description": "Non disponible"
        }
        
        # Essayer d'extraire l'unité
        units = ["mg/L", "µg/L", "mg/m3", "µg/m3", "dB", "NTU", "%", "ppm"]
        for unit in units:
            if unit in text:
                param_info["Unité"] = unit
                break
        
        # Essayer d'extraire l'intervalle acceptable
        # Rechercher des patterns comme "5-10", "< 5", "> 10"
        import re
        interval_patterns = [
            r"(\d+(?:\.\d+)?)[\s]*-[\s]*(\d+(?:\.\d+)?)",  # 5-10, 5.5-10.5
            r"<[\s]*(\d+(?:\.\d+)?)",  # < 5, < 5.5
            r">[\s]*(\d+(?:\.\d+)?)",  # > 10, > 10.5
            r"(\d+(?:\.\d+)?)[\s]*à[\s]*(\d+(?:\.\d+)?)",  # 5 à 10, 5.5 à 10.5
            r"entre[\s]*(\d+(?:\.\d+)?)[\s]*et[\s]*(\d+(?:\.\d+)?)",  # entre 5 et 10
            r"maximum[\s]*(\d+(?:\.\d+)?)",  # maximum 50
            r"minimum[\s]*(\d+(?:\.\d+)?)",  # minimum 5
            r"max[\s]*[:\.]?[\s]*(\d+(?:\.\d+)?)",  # max: 50, max. 50
            r"min[\s]*[:\.]?[\s]*(\d+(?:\.\d+)?)",  # min: 5, min. 5
        ]
        
        for pattern in interval_patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 2:  # Intervalle avec deux valeurs
                    param_info["Intervalle acceptable"] = f"{match.group(1)}-{match.group(2)}"
                elif "<" in pattern:  # Valeur maximale
                    param_info["Intervalle acceptable"] = f"< {match.group(1)}"
                elif ">" in pattern:  # Valeur minimale
                    param_info["Intervalle acceptable"] = f"> {match.group(1)}"
                elif "maximum" in pattern or "max" in pattern:  # Valeur maximale
                    param_info["Intervalle acceptable"] = f"< {match.group(1)}"
                elif "minimum" in pattern or "min" in pattern:  # Valeur minimale
                    param_info["Intervalle acceptable"] = f"> {match.group(1)}"
                break
        
        # Extraire une description
        # Prendre la phrase contenant le mot-clé
        sentences = text.split('.')
        for sentence in sentences:
            if keyword.lower() in sentence.lower():
                param_info["Description"] = sentence.strip()
                break
        
        return param_info

# Fonction utilitaire pour convertir les paramètres en DataFrame
def parameters_to_dataframe(parameters):
    """Convertit les paramètres environnementaux en DataFrame.
    
    Args:
        parameters (dict): Dictionnaire des paramètres environnementaux
        
    Returns:
        pandas.DataFrame: DataFrame contenant les paramètres environnementaux
    """
    import pandas as pd
    
    # Créer une liste de tous les paramètres
    all_params = []
    
    for milieu, params in parameters.items():
        for param in params:
            param_copy = param.copy()
            param_copy["Milieu"] = milieu.capitalize()
            all_params.append(param_copy)
    
    # Créer un DataFrame
    if all_params:
        df = pd.DataFrame(all_params)
        
        # Réorganiser les colonnes
        columns = ["Milieu", "Paramètre", "Unité", "Intervalle acceptable", "Description"]
        df = df[columns]
        
        return df
    else:
        # Retourner un DataFrame vide avec les colonnes appropriées
        return pd.DataFrame(columns=["Milieu", "Paramètre", "Unité", "Intervalle acceptable", "Description"])