import requests
import json
import logging
import os
import math
import pandas as pd
from config import OUTPUT_DIR
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from cache_manager import cached, clear_cache, get_cache_stats

# Initialiser le logging pour ce module
logger = logging.getLogger(__name__)

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


# Configuration par défaut des API externes
DEFAULT_EXTERNAL_API_CONFIG = {
    # OpenWeatherMap API
    "openweathermap": {
        "api_key": "",  # À remplir avec votre clé API
        "api_url": "https://api.openweathermap.org/data/2.5/",
        "units": "metric",  # Unités métriques (Celsius, m/s, etc.)
        "lang": "fr",  # Langue française
        "enabled": True,  # Activer/désactiver cette API
        "air_quality": {
            "enabled": True,
            "standard": "EPA"  # Valeurs possibles: "EPA", "EU", "Morocco"
        }
    },
    # OpenWeatherMap Air Pollution API
    "openweathermap_air_pollution": {
        "api_key": "",  # À remplir avec votre clé API
        "api_url": "https://api.openweathermap.org/data/2.5/air_pollution",
        "enabled": True  # Activer/désactiver cette API
    },
    # AQICN (World Air Quality Index)
    "aqicn": {
        "token": "",  # À remplir avec votre token AQICN
        "api_url": "https://api.waqi.info/feed/geo:{lat};{lon}/?token={token}",
        "enabled": True
    },
    # SoilGrids API
    "soilgrids": {
        "api_url": "https://rest.isric.org/soilgrids/v2.0/",
        "enabled": True  # Activer/désactiver cette API
    },
    # INSEE API
    "insee": {
        "api_key": "",  # À remplir avec votre clé API
        "api_secret": "",  # À remplir avec votre secret API
        "api_url": "https://api.insee.fr/",
        "enabled": True  # Activer/désactiver cette API
    },
    # Banque Mondiale API
    "worldbank": {
        "api_url": "https://api.worldbank.org/v2/",
        "format": "json",
        "country": "MA",  # Code pays pour le Maroc
        "enabled": True  # Activer/désactiver cette API
    },
    # OpenStreetMap / Overpass API
    "openstreetmap": {
        "api_url": "https://overpass-api.de/api/interpreter",
        "enabled": True  # Activer/désactiver cette API
    },
    # Copernicus Climate Data Store API
    "copernicus": {
        "api_key": "",  # À remplir avec votre clé API
        "api_url": "https://cds.climate.copernicus.eu/api/v2/",
        "enabled": True  # Activer/désactiver cette API
    },
    # Global Biodiversity Information Facility (GBIF) API
    "gbif": {
        "api_url": "https://api.gbif.org/v1/",
        "enabled": True  # Activer/désactiver cette API
    },
    # NASA Earth Data API
    "nasa": {
        "api_key": "",  # À remplir avec votre clé API NASA
        "api_url": "https://api.nasa.gov/",
        "enabled": True  # Activer/désactiver cette API
    },
    # FAO AquaStat API
    "fao_aquastat": {
        "api_url": "https://fenixservices.fao.org/faostat/api/v1/en/data/",
        "web_url": "https://data.apps.fao.org/aquastat/",
        "country_code": "MA",  # Code pays pour le Maroc
        "enabled": True  # Activer/désactiver cette API
    }
}

# Charger les configurations depuis le fichier external_api_config.json
def _apply_runtime_defaults(config: dict) -> dict:
    """Complète les clés manquantes depuis les variables d'environnement ou des valeurs fournies.
    - OWM_API_KEY pour OpenWeatherMap
    - AQICN_TOKEN pour AQICN
    """
    try:
        # OpenWeatherMap
        owm_key = config.get("openweathermap", {}).get("api_key")
        if not owm_key:
            owm_key = os.environ.get("OWM_API_KEY") or "4d6683b49a192822ceb510d6f65844f1"
            config.setdefault("openweathermap", {})["api_key"] = owm_key
        # Associer aussi à la section air_pollution si besoin
        if not config.get("openweathermap_air_pollution", {}).get("api_key"):
            config.setdefault("openweathermap_air_pollution", {})["api_key"] = owm_key

        # AQICN
        aqicn_token = config.get("aqicn", {}).get("token")
        if not aqicn_token:
            aqicn_token = os.environ.get("AQICN_TOKEN") or "2a29806f-7f37-41aa-9c33-f95a22963b73"
            config.setdefault("aqicn", {})["token"] = aqicn_token
            config.setdefault("aqicn", {})["enabled"] = True
    except Exception:
        pass
    return config

def load_external_api_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "external_api_config.json")
    config = DEFAULT_EXTERNAL_API_CONFIG.copy()
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
                
                # Mettre à jour la configuration avec les valeurs sauvegardées
                for provider in config.keys():
                    if provider in saved_config:
                        for key, value in saved_config[provider].items():
                            if key in config[provider]:
                                config[provider][key] = value
                                
            logger.info("Configurations des API externes chargées avec succès depuis external_api_config.json")
        except Exception as e:
            if isinstance(e, requests.exceptions.RequestException):
                if 'WinError 10013' in str(e):
                    logger.error(f"Erreur d'autorisation réseau: {e}. Essayez d'exécuter l'application en tant qu'administrateur.")
                else:
                    logger.error(f"Erreur lors du chargement des configurations API externes: {str(e)}")
    else:
        logger.warning("Fichier external_api_config.json non trouvé, utilisation des configurations par défaut")
    
    return _apply_runtime_defaults(config)

# Charger les configurations au démarrage
EXTERNAL_API_CONFIG = load_external_api_config()

class ExternalAPIs:
    """Classe pour interagir avec différentes API externes pour collecter des données environnementales."""
    
    def __init__(self):
        """Initialise les API externes."""
        self.config = EXTERNAL_API_CONFIG

    def get_detailed_water_data(self, lat, lon):
        """
        Récupère les paramètres d'eau détaillés via le collecteur local.
        """
        try:
            from water_parameters_collector import create_water_parameters_collector
            collector = create_water_parameters_collector()
            if not collector:
                logger.error("Impossible de créer le collecteur de paramètres d'eau.")
                return {"Erreur": "Collecteur de paramètres d'eau non disponible"}
            
            data = collector.collect_detailed_water_parameters((lat, lon))
            if not data:
                logger.warning("Aucune donnée d'eau détaillée n'a été collectée.")
                return {"Avertissement": "Aucune donnée détaillée collectée"}

            # Formatter les données pour l'affichage
            flat_data = {}
            for category, params in data.items():
                if category == 'contexte' or not isinstance(params, dict):
                    continue
                for param_name, details in params.items():
                    value = details.get('valeur_mesuree', 'N/A')
                    unit = details.get('unite', '')
                    conformity = details.get('conforme')
                    indicator = " ✓" if conformity is True else (" ✗" if conformity is False else " ?")
                    
                    # Clé unique pour l'affichage
                    display_key = f"{param_name} ({category.replace('_', ' ').title()})"
                    flat_data[display_key] = f"{value} {unit}{indicator}"
            
            # Ajouter un résumé de la qualité
            summary = collector.get_water_quality_summary(data)
            if summary:
                flat_data["Qualité Globale de l'Eau"] = f"{summary['qualite_globale']} ({summary['score_qualite']}%)"

            logger.info(f"{len(flat_data)} paramètres d'eau détaillés formatés pour l'affichage.")
            return flat_data

        except ImportError:
            logger.error("Le module 'water_parameters_collector' est introuvable.")
            return {"Erreur": "Module de collecte d'eau manquant."}
        except Exception as e:
            logger.error(f"Erreur inattendue dans get_detailed_water_data: {e}")
            return {"Erreur": str(e)}
    
    @cached(expiry=3600)  # Cache valide pendant 1 heure (les données météo changent plus fréquemment)
    def get_weather_data(self, lat, lon):
        """Récupère les données météorologiques pour des coordonnées données via OpenWeatherMap.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            dict: Données météorologiques ou None en cas d'erreur
        """
        try:
            api_key = self.config["openweathermap"]["api_key"]
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": api_key,
                "units": "metric",
                "lang": "fr"
            }
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            session = create_session_with_retry()
            response = session.get(url, params=params, headers=headers, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Météo: {response.status_code} - {response.text}")
                return None
            data = response.json()
            return {
                "Température": (data["main"]["temp"], "°C"),
                "Humidité": (data["main"]["humidity"], "%"),
                "Pression": (data["main"]["pressure"], "hPa"),
                "Vent": (data["wind"]["speed"], "m/s"),
                "Ciel": (data["weather"][0]["description"], "")
            }
        except Exception as e:
            if isinstance(e, requests.exceptions.RequestException):
                if 'WinError 10013' in str(e):
                    logger.error(f"Erreur d'autorisation réseau: {e}. Essayez d'exécuter l'application en tant qu'administrateur.")
                else:
                    logger.error(f"Erreur météo: {e}")
            return None
    def get_air_quality_data_aqicn(self, lat, lon):
        """Récupère les données de qualité d'air via AQICN (World Air Quality Index)."""
        try:
            conf = self.config.get("aqicn", {})
            token = conf.get("token")
            if not token:
                return None
            url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={token}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            session = create_session_with_retry()
            response = session.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                logger.warning(f"AQICN: {response.status_code} - {response.text}")
                return None
            payload = response.json()
            if payload.get("status") != "ok":
                logger.warning(f"AQICN: statut {payload.get('status')}")
                return None
            data = payload.get("data", {})
            iaqi = data.get("iaqi", {})
            def gv(key):
                val = iaqi.get(key)
                return val.get("v") if isinstance(val, dict) else None
            aqi_val = data.get("aqi")
            return {
                "AQI": (aqi_val, "index"),
                "PM2.5": (gv("pm25"), "µg/m³"),
                "PM10": (gv("pm10"), "µg/m³"),
                "NO₂": (gv("no2"), "µg/m³"),
                "SO₂": (gv("so2"), "µg/m³"),
                "O₃": (gv("o3"), "µg/m³"),
                "CO": (gv("co"), "µg/m³")
            }
        except Exception as e:
            logger.error(f"Erreur AQICN: {e}")
            return None

    @cached(expiry=3600)  # Cache valide pendant 1 heure (les données de qualité d'air changent plus fréquemment)
    def get_air_quality_data(self, lat, lon, standard=None):
        """Récupère les données de qualité de l'air pour des coordonnées données.
        Préférence AQICN si configuré, sinon OpenWeatherMap Air Pollution.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            standard (str, optional): Norme AQI (pour OpenWeatherMap): "EPA", "EU", "Morocco".
            
        Returns:
            dict: Données de qualité de l'air ou None en cas d'erreur
        """
        # 1) Essayer AQICN si activé et token présent
        try:
            aq_conf = self.config.get("aqicn", {})
            if aq_conf.get("enabled") and aq_conf.get("token"):
                aq_data = self.get_air_quality_data_aqicn(lat, lon)
                if aq_data:
                    return aq_data
        except Exception:
            pass

        # 2) Fallback OpenWeatherMap
        try:
            api_key = self.config["openweathermap"]["api_key"]
            
            # Déterminer le standard AQI à utiliser
            if standard is None:
                # Utiliser le standard défini dans la configuration OpenWeatherMap, ou EPA par défaut
                aq_conf = self.config.get("openweathermap", {}).get("air_quality", {})
                standard = aq_conf.get("standard", "EPA")
            
            url = "https://api.openweathermap.org/data/2.5/air_pollution"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": api_key
            }
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            session = create_session_with_retry()
            response = session.get(url, params=params, headers=headers, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Air: {response.status_code} - {response.text}")
                return None

            data = response.json()["list"][0]["components"]

            aqi = response.json()["list"][0]["main"]["aqi"]
            
            # Utiliser la fonction _interpret_aqi avec le standard spécifié
            aqi_description, aqi_score = self._interpret_aqi(aqi, standard)
            
            return {
                "AQI": (aqi, aqi_description),
                "AQI Score": (aqi_score, "/100"),
                "Standard AQI": (standard, ""),
                "PM2.5": (data["pm2_5"], "µg/m³"),
                "PM10": (data["pm10"], "µg/m³"),
                "NO₂": (data["no2"], "µg/m³"),
                "SO₂": (data["so2"], "µg/m³"),
                "O₃": (data["o3"], "µg/m³"),
                "CO": (data["co"], "µg/m³")
            }
        except Exception as e:
            if isinstance(e, requests.exceptions.RequestException):
                if 'WinError 10013' in str(e):
                    logger.error(f"Erreur d'autorisation réseau: {e}. Essayez d'exécuter l'application en tant qu'administrateur.")
                else:
                    logger.error(f"Erreur air: {e}")
            return None

    
    def _interpret_aqi(self, aqi, standard="EPA"):
        """Interprète l'indice de qualité de l'air selon différentes normes.
        
        Args:
            aqi (int): Indice de qualité de l'air
            standard (str): Norme à utiliser ("EPA", "EU", "Morocco")
            
        Returns:
            tuple: (Description de l'AQI, Score normalisé de 0 à 100)
        """
        if standard == "EPA":
            # Normes US EPA
            if aqi <= 50:
                return "Bon - La qualité de l'air est satisfaisante et la pollution présente peu ou pas de risque", 100
            elif aqi <= 100:
                return "Modéré - La qualité de l'air est acceptable, mais peut présenter un risque pour certaines personnes sensibles", 80
            elif aqi <= 150:
                return "Malsain pour les groupes sensibles - Les personnes sensibles peuvent subir des effets sur la santé", 60
            elif aqi <= 200:
                return "Malsain - Tout le monde peut commencer à ressentir des effets sur la santé", 40
            elif aqi <= 300:
                return "Très malsain - Avertissements sanitaires, tout le monde peut subir des effets plus graves", 20
            else:
                return "Dangereux - Alerte sanitaire: tout le monde peut subir des effets graves sur la santé", 0
        elif standard == "EU":
            # Normes européennes (échelle différente)
            if aqi <= 25:
                return "Très bon - Qualité de l'air excellente", 100
            elif aqi <= 50:
                return "Bon - Qualité de l'air bonne", 80
            elif aqi <= 75:
                return "Moyen - Qualité de l'air moyenne", 60
            elif aqi <= 100:
                return "Médiocre - Qualité de l'air médiocre", 40
            else:
                return "Mauvais - Qualité de l'air mauvaise", 20
        elif standard == "Morocco":
            # Normes marocaines (adaptées aux conditions locales)
            if aqi <= 30:
                return "Excellent - Qualité de l'air optimale pour le Maroc", 100
            elif aqi <= 60:
                return "Bon - Qualité de l'air bonne selon les normes marocaines", 80
            elif aqi <= 90:
                return "Acceptable - Qualité de l'air acceptable pour le Maroc", 60
            elif aqi <= 120:
                return "Médiocre - Qualité de l'air médiocre selon les normes marocaines", 40
            else:
                return "Mauvais - Qualité de l'air mauvaise selon les normes marocaines", 20
        else:
            # Par défaut, utiliser les normes US EPA
            return self._interpret_aqi(aqi, "EPA")
    
    def _describe_pollutant(self, pollutant):
        """Fournit une description du polluant principal.
        
        Args:
            pollutant (str): Code du polluant principal
            
        Returns:
            str: Description du polluant
        """
        descriptions = {
            # Anciens codes AirVisual
            "p2": "PM2.5 - Particules fines de diamètre inférieur à 2,5 micromètres, dangereuses car elles pénètrent profondément dans les poumons",
            "p1": "PM10 - Particules de diamètre inférieur à 10 micromètres, pouvant causer des problèmes respiratoires",
            "o3": "Ozone (O3) - Polluant secondaire formé par réaction photochimique, irritant pour les voies respiratoires",
            "n2": "Dioxyde d'azote (NO2) - Gaz irritant produit principalement par la combustion, affecte le système respiratoire",
            "s2": "Dioxyde de soufre (SO2) - Gaz irritant produit par la combustion de combustibles fossiles, cause des problèmes respiratoires",
            "co": "Monoxyde de carbone (CO) - Gaz toxique inodore produit par combustion incomplète, réduit la capacité du sang à transporter l'oxygène",
            
            # Nouveaux codes OpenWeatherMap
            "PM2.5": "PM2.5 - Particules fines de diamètre inférieur à 2,5 micromètres, dangereuses car elles pénètrent profondément dans les poumons",
            "PM10": "PM10 - Particules de diamètre inférieur à 10 micromètres, pouvant causer des problèmes respiratoires",
            "O3": "Ozone (O3) - Polluant secondaire formé par réaction photochimique, irritant pour les voies respiratoires",
            "NO2": "Dioxyde d'azote (NO2) - Gaz irritant produit principalement par la combustion, affecte le système respiratoire",
            "SO2": "Dioxyde de soufre (SO2) - Gaz irritant produit par la combustion de combustibles fossiles, cause des problèmes respiratoires",
            "CO": "Monoxyde de carbone (CO) - Gaz toxique inodore produit par combustion incomplète, réduit la capacité du sang à transporter l'oxygène"
        }
        
        return descriptions.get(pollutant, f"Polluant inconnu: {pollutant}")
    
    @cached(expiry=604800)  # Cache valide pendant 7 jours (les données de sol changent très lentement)
    def get_soil_data(self, lat, lon, properties=None, depth="0-5cm"):
        """
        Récupère plusieurs propriétés du sol via SoilGrids en utilisant l'endpoint properties/query.
        Si cet endpoint échoue, essaie l'endpoint classification/query comme solution de secours.

        Args:
            lat (float): Latitude.
            lon (float): Longitude.
            properties (list, optional): Liste des propriétés SoilGrids à récupérer. 
                                     Par défaut: ["phh2o", "clay", "sand", "soc", "bdod"].
            depth (str, optional): Profondeur d'analyse. Par défaut: "0-5cm".

        Returns:
            dict: Dictionnaire avec les noms de paramètres normalisés et leurs valeurs.
        """
        if properties is None:
            properties = ["phh2o", "clay", "sand", "soc", "bdod"]

        # 🔧 Arrondir les coordonnées pour éviter les erreurs
        try:
            lat = round(float(lat), 6)
            lon = round(float(lon), 6)
        except (TypeError, ValueError) as e:
            logger.error(f"SoilGrids: Erreur de conversion des coordonnées - {str(e)}")
            return {}

        # Normalisation des noms de paramètres et unités
        PROPERTY_MAP = {
            "phh2o": ("pH du sol", "pH"),
            "clay": ("Teneur en argile", "%"),
            "sand": ("Teneur en sable", "%"),
            "soc": ("Carbone organique du sol", "g/kg"),
            "bdod": ("Densité apparente", "kg/dm³")
        }

        # Initialiser le dictionnaire de résultats
        soil_data = {}
        for prop_code in properties:
            norm_name, unit = PROPERTY_MAP.get(prop_code, (prop_code, ""))
            soil_data[norm_name] = ("N/A", unit)

        try:
            # 🛑 Ajouter un délai pour ne pas surcharger le serveur
            import time
            time.sleep(1)
            
            # Essayer d'abord l'endpoint properties/query pour obtenir les valeurs exactes
            base_url = "https://rest.isric.org/soilgrids/v2.0/"
            properties_url = f"{base_url}properties/query"
            properties_params = {
                'lon': lon,
                'lat': lat,
                'property': properties,
                'depth': depth,
                'value': 'mean,Q0.05,Q0.95'  # Demander plus de valeurs au cas où mean serait null
            }
            
            logger.info(f"SoilGrids: Tentative d'utilisation de l'endpoint properties/query avec {properties_params}")
            properties_session = create_session_with_retry()
            properties_response = properties_session.get(properties_url, params=properties_params, timeout=15)
            
            # Si l'endpoint properties/query fonctionne, utiliser les valeurs exactes
            if properties_response.status_code == 200:
                logger.info("SoilGrids: Endpoint properties/query a réussi, utilisation des valeurs exactes")
                data = properties_response.json()
                
                # Debug: afficher la structure de la réponse
                logger.info(f"SoilGrids: Structure de réponse: {json.dumps(data, indent=2)[:500]}...")
                
                # Vérifier la structure de réponse SoilGrids v2.0
                if "properties" in data and "layers" in data["properties"]:
                    logger.info(f"SoilGrids: Nombre de couches trouvées: {len(data['properties']['layers'])}")
                    for layer in data["properties"]["layers"]:
                        prop_name = layer["name"]
                        logger.info(f"SoilGrids: Traitement de la propriété: {prop_name}")
                        logger.info(f"SoilGrids: Structure layer pour {prop_name}: {json.dumps(layer, indent=2)[:200]}...")
                        if prop_name in properties and "depths" in layer and len(layer["depths"]) > 0:
                            depth_data = layer["depths"][0]
                            logger.info(f"SoilGrids: Structure depth[0]: {json.dumps(depth_data, indent=2)[:300]}...")
                            
                            # Rechercher les valeurs dans différents endroits possibles
                            final_value = None
                            
                            if "values" in depth_data and isinstance(depth_data["values"], dict):
                                values_dict = depth_data["values"]
                                logger.info(f"SoilGrids: Valeurs disponibles pour {prop_name}: {list(values_dict.keys())}")
                                
                                # Essayer mean en premier
                                mean_value = values_dict.get("mean")
                                if mean_value is not None:
                                    final_value = mean_value
                                    logger.info(f"SoilGrids: Utilisé mean pour {prop_name}: {mean_value}")
                                else:
                                    logger.warning(f"SoilGrids: Mean est null pour {prop_name}, tentative des quantiles")
                                    
                                    # Si mean est null, essayer les quantiles
                                    q05 = values_dict.get("Q0.05")
                                    q95 = values_dict.get("Q0.95")
                                    
                                    if q05 is not None and q95 is not None:
                                        # Calculer la moyenne des quantiles comme approximation
                                        final_value = (q05 + q95) / 2
                                        logger.info(f"SoilGrids: Utilisé moyenne des quantiles pour {prop_name}: (Q0.05:{q05} + Q0.95:{q95})/2 = {final_value}")
                                    elif q05 is not None:
                                        final_value = q05
                                        logger.info(f"SoilGrids: Utilisé Q0.05 pour {prop_name}: {q05}")
                                    elif q95 is not None:
                                        final_value = q95
                                        logger.info(f"SoilGrids: Utilisé Q0.95 pour {prop_name}: {q95}")
                            
                            # Option fallback: chercher dans toute la structure depth
                            if final_value is None:
                                for key, value in depth_data.items():
                                    if isinstance(value, dict) and "mean" in value:
                                        final_value = value["mean"]
                                        logger.info(f"SoilGrids: Trouvé mean dans {key} pour {prop_name}: {final_value}")
                                        break
                                    elif key == "mean" and value is not None:
                                        final_value = value
                                        logger.info(f"SoilGrids: Trouvé mean key pour {prop_name}: {final_value}")
                                        break
                            
                            logger.info(f"SoilGrids: Valeur finale pour {prop_name}: {final_value}")
                            
                            if final_value is not None:
                                # Appliquer les facteurs de conversion si nécessaire
                                if prop_name == "phh2o":
                                    final_value = final_value / 10  # Convertir en pH réel
                                
                                norm_name, unit = PROPERTY_MAP.get(prop_name, (prop_name, ""))
                                soil_data[norm_name] = (str(round(final_value, 2)), unit)
                                logger.info(f"SoilGrids: Valeur exacte pour {prop_name}: {final_value} {unit}")
                            else:
                                logger.warning(f"SoilGrids: Aucune valeur trouvée pour {prop_name}")
                        else:
                            logger.warning(f"SoilGrids: Propriété {prop_name} non demandée ou pas de données de profondeur")
                
                # Vérification alternative pour la structure SoilGrids v1.0 
                elif "layers" in data:
                    logger.info("SoilGrids: Utilisation structure v1.0")
                    for layer in data["layers"]:
                        prop_name = layer["name"]
                        if prop_name in properties and "depths" in layer and len(layer["depths"]) > 0:
                            mean_value = layer["depths"][0]["values"].get("mean")
                            if mean_value is not None:
                                if prop_name == "phh2o":
                                    mean_value = mean_value / 10
                                norm_name, unit = PROPERTY_MAP.get(prop_name, (prop_name, ""))
                                soil_data[norm_name] = (str(round(mean_value, 2)), unit)
                                logger.info(f"SoilGrids: Valeur v1.0 pour {prop_name}: {mean_value} {unit}")
                
                else:
                    logger.warning(f"SoilGrids: Structure de réponse inattendue: {list(data.keys())}")
                    # Essayer de parser toute structure qui contient des valeurs
                    for key, value in data.items():
                        if isinstance(value, dict) and "mean" in str(value):
                            logger.info(f"SoilGrids: Structure alternative détectée dans '{key}': {value}")
                
                return soil_data
            else:
                logger.warning(f"SoilGrids: L'endpoint properties/query a échoué avec le code {properties_response.status_code}. Utilisation de l'endpoint classification/query comme solution de secours.")
            
            # Si l'endpoint properties/query échoue, utiliser l'endpoint classification/query comme solution de secours
            url = "https://rest.isric.org/soilgrids/v2.0/classification/query"
            params = {
                "lon": lon,
                "lat": lat,
                "number_classes": 5  # Obtenir les 5 classes de sol les plus probables
            }
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            session = create_session_with_retry()
            response = session.get(url, params=params, headers=headers, timeout=10)
            
            # 🔍 Vérifier le code de statut
            if response.status_code != 200:
                logger.error(f"SoilGrids: {response.status_code} - {response.text}")
                return soil_data

            data = response.json()
            
            # Déboguer la structure de la réponse
            logger.info(f"SoilGrids: Structure de la réponse: {json.dumps(data, indent=2)[:500]}...")

            # Extraire la classification du sol et les probabilités
            soil_class = None
            soil_class_probability = 0
            soil_classes_info = []

            if "wrb_class_name" in data:
                soil_class = data.get("wrb_class_name")
                soil_class_probability = data.get("wrb_class_probability", 0)
                logger.info(f"SoilGrids: Classe de sol principale: {soil_class} (probabilité: {soil_class_probability})")
                
                # Collecter les informations sur la classe principale
                soil_classes_info.append({
                    "class": soil_class,
                    "probability": soil_class_probability
                })
                
                # Collecter les informations sur les classes alternatives
                if "wrb_class_name_other" in data and "wrb_class_probability_other" in data:
                    other_classes = data.get("wrb_class_name_other", [])
                    other_probs = data.get("wrb_class_probability_other", [])
                    
                    for i in range(min(len(other_classes), len(other_probs))):
                        soil_classes_info.append({
                            "class": other_classes[i],
                            "probability": other_probs[i]
                        })
                        logger.info(f"SoilGrids: Classe alternative {i+1}: {other_classes[i]} (probabilité: {other_probs[i]})")
                
                # Estimer les propriétés du sol en fonction de la classification
                estimated_properties = self._estimate_soil_properties(soil_class, soil_classes_info)
                
                # Mettre à jour soil_data avec les estimations, mais indiquer qu'il s'agit d'estimations
                for prop_code in properties:
                    if prop_code in estimated_properties:
                        norm_name, unit = PROPERTY_MAP.get(prop_code, (prop_code, ""))
                        value = estimated_properties[prop_code]
                        soil_data[norm_name] = (f"{value} (estimé)", unit)
                        logger.info(f"SoilGrids: Valeur estimée pour {prop_code}: {value} {unit}")
            else:
                logger.warning("SoilGrids: Classification du sol non trouvée dans la réponse")
            
            return soil_data

        except requests.exceptions.Timeout:
            logger.error("SoilGrids: Timeout après 10 secondes")
        except requests.exceptions.ConnectionError:
            logger.error("SoilGrids: Problème de connexion au serveur")
        except Exception as e:
            if isinstance(e, requests.exceptions.RequestException):
                if 'WinError 10013' in str(e):
                    logger.error(f"Erreur d'autorisation réseau: {e}. Essayez d'exécuter l'application en tant qu'administrateur.")
                else:
                    logger.error(f"SoilGrids: Erreur inattendue - {str(e)}")
        
        return soil_data
        
    def _estimate_soil_properties(self, soil_class, soil_classes_info):
        """
        Estime les propriétés du sol en fonction de la classification WRB.
        
        Args:
            soil_class (str): Classe de sol principale selon WRB.
            soil_classes_info (list): Liste des classes de sol avec leurs probabilités.
            
        Returns:
            dict: Propriétés estimées du sol.
        """
        # Valeurs par défaut pour les différentes classes de sol
        # Ces valeurs sont des estimations basées sur la littérature scientifique
        soil_properties_by_class = {
            "Acrisols": {"phh2o": 5.2, "clay": 35, "sand": 40, "soc": 15, "bdod": 1.3},
            "Alisols": {"phh2o": 4.8, "clay": 40, "sand": 30, "soc": 20, "bdod": 1.2},
            "Andosols": {"phh2o": 6.0, "clay": 15, "sand": 45, "soc": 80, "bdod": 0.8},
            "Arenosols": {"phh2o": 6.5, "clay": 5, "sand": 90, "soc": 5, "bdod": 1.5},
            "Calcisols": {"phh2o": 8.0, "clay": 25, "sand": 50, "soc": 10, "bdod": 1.4},
            "Cambisols": {"phh2o": 6.5, "clay": 25, "sand": 40, "soc": 20, "bdod": 1.3},
            "Chernozems": {"phh2o": 7.0, "clay": 30, "sand": 35, "soc": 60, "bdod": 1.2},
            "Cryosols": {"phh2o": 6.0, "clay": 20, "sand": 45, "soc": 40, "bdod": 1.1},
            "Durisols": {"phh2o": 7.5, "clay": 30, "sand": 45, "soc": 8, "bdod": 1.5},
            "Ferralsols": {"phh2o": 5.5, "clay": 60, "sand": 20, "soc": 25, "bdod": 1.2},
            "Fluvisols": {"phh2o": 6.8, "clay": 25, "sand": 40, "soc": 30, "bdod": 1.3},
            "Gleysols": {"phh2o": 6.0, "clay": 35, "sand": 30, "soc": 40, "bdod": 1.2},
            "Gypsisols": {"phh2o": 7.8, "clay": 20, "sand": 60, "soc": 5, "bdod": 1.4},
            "Histosols": {"phh2o": 5.5, "clay": 10, "sand": 20, "soc": 200, "bdod": 0.3},
            "Kastanozems": {"phh2o": 7.2, "clay": 30, "sand": 40, "soc": 40, "bdod": 1.3},
            "Leptosols": {"phh2o": 6.5, "clay": 20, "sand": 50, "soc": 15, "bdod": 1.4},
            "Lixisols": {"phh2o": 6.0, "clay": 30, "sand": 45, "soc": 10, "bdod": 1.4},
            "Luvisols": {"phh2o": 6.5, "clay": 35, "sand": 30, "soc": 20, "bdod": 1.3},
            "Nitisols": {"phh2o": 5.8, "clay": 50, "sand": 20, "soc": 25, "bdod": 1.2},
            "Phaeozems": {"phh2o": 6.8, "clay": 30, "sand": 35, "soc": 50, "bdod": 1.2},
            "Planosols": {"phh2o": 6.0, "clay": 40, "sand": 30, "soc": 15, "bdod": 1.4},
            "Plinthosols": {"phh2o": 5.5, "clay": 45, "sand": 30, "soc": 15, "bdod": 1.3},
            "Podzols": {"phh2o": 4.5, "clay": 10, "sand": 80, "soc": 30, "bdod": 1.3},
            "Regosols": {"phh2o": 6.5, "clay": 15, "sand": 60, "soc": 10, "bdod": 1.4},
            "Solonchaks": {"phh2o": 8.5, "clay": 30, "sand": 45, "soc": 10, "bdod": 1.4},
            "Solonetz": {"phh2o": 8.0, "clay": 35, "sand": 40, "soc": 15, "bdod": 1.4},
            "Stagnosols": {"phh2o": 6.0, "clay": 40, "sand": 25, "soc": 30, "bdod": 1.3},
            "Technosols": {"phh2o": 7.0, "clay": 20, "sand": 50, "soc": 20, "bdod": 1.3},
            "Umbrisols": {"phh2o": 5.5, "clay": 25, "sand": 45, "soc": 50, "bdod": 1.1},
            "Vertisols": {"phh2o": 7.0, "clay": 60, "sand": 15, "soc": 25, "bdod": 1.3}
        }
        
        # Valeurs par défaut si la classe de sol n'est pas reconnue
        default_properties = {"phh2o": 6.5, "clay": 25, "sand": 40, "soc": 20, "bdod": 1.3}
        
        # Si la classe de sol principale est reconnue, utiliser ses valeurs
        if soil_class in soil_properties_by_class:
            return soil_properties_by_class[soil_class]
        
        # Si la classe principale n'est pas reconnue mais qu'il y a des classes alternatives
        if soil_classes_info and len(soil_classes_info) > 0:
            # Calculer une moyenne pondérée des propriétés en fonction des probabilités
            weighted_properties = {"phh2o": 0, "clay": 0, "sand": 0, "soc": 0, "bdod": 0}
            total_probability = 0
            
            for class_info in soil_classes_info:
                class_name = class_info.get("class")
                probability = class_info.get("probability", 0)
                
                if class_name in soil_properties_by_class and probability > 0:
                    for prop, value in soil_properties_by_class[class_name].items():
                        weighted_properties[prop] += value * probability
                    total_probability += probability
            
            # Si au moins une classe reconnue a été trouvée
            if total_probability > 0:
                for prop in weighted_properties:
                    weighted_properties[prop] = round(weighted_properties[prop] / total_probability, 2)
                return weighted_properties
        
        # Si aucune classe reconnue n'a été trouvée, utiliser les valeurs par défaut
        logger.warning(f"SoilGrids: Classe de sol '{soil_class}' non reconnue, utilisation des valeurs par défaut")
        return default_properties

    def _interpret_clay_content(self, clay_percentage):
        """Interprète la teneur en argile du sol.
        
        Args:
            clay_percentage (float): Pourcentage d'argile
            
        Returns:
            str: Interprétation de la teneur en argile
        """
        # Vérifier si clay_percentage est None avant de faire des comparaisons
        if clay_percentage is None:
            return "Teneur moyenne en argile (estimé)"
            
        if clay_percentage < 10:
            return "Sol sableux - Drainage rapide, faible rétention d'eau et de nutriments"
        elif clay_percentage < 25:
            return "Sol limoneux - Bon équilibre entre drainage et rétention"
        elif clay_percentage < 40:
            return "Sol argileux - Bonne rétention d'eau et de nutriments, mais drainage lent"
        else:
            return "Sol très argileux - Forte rétention d'eau, risque de compaction et drainage très lent"
    
    def _interpret_organic_carbon(self, soc):
        """Interprète la teneur en carbone organique du sol.
        
        Args:
            soc (float): Teneur en carbone organique (g/kg)
            
        Returns:
            str: Interprétation de la teneur en carbone organique
        """
        # Vérifier si soc est None avant de faire des comparaisons
        if soc is None:
            return "Teneur moyenne en carbone organique (estimé)"
            
        if soc < 10:
            return "Très faible - Sol pauvre en matière organique, fertilité réduite"
        elif soc < 20:
            return "Faible - Teneur limitée en matière organique"
        elif soc < 40:
            return "Moyen - Teneur acceptable en matière organique"
        elif soc < 60:
            return "Élevé - Bonne teneur en matière organique, sol fertile"
        else:
            return "Très élevé - Sol très riche en matière organique, excellente fertilité"
    
    def _interpret_ph(self, ph):
        """Interprète le pH du sol.
        
        Args:
            ph (float): Valeur du pH
            
        Returns:
            str: Interprétation du pH
        """
        # Vérifier si ph est None avant de faire des comparaisons
        if ph is None:
            return "pH neutre (estimé)"
            
        if ph < 4.5:
            return "Extrêmement acide - Problèmes de toxicité, disponibilité limitée des nutriments"
        elif ph < 5.5:
            return "Très acide - Conditions défavorables pour de nombreuses cultures"
        elif ph < 6.5:
            return "Modérément acide - Convient à de nombreuses cultures, surveiller le calcium"
        elif ph < 7.5:
            return "Neutre - Conditions optimales pour la plupart des cultures"
        elif ph < 8.5:
            return "Modérément alcalin - Peut limiter la disponibilité de certains nutriments"
        else:
            return "Très alcalin - Problèmes de disponibilité des nutriments, notamment le phosphore et les micronutriments"
    
    @cached(expiry=2592000)  # Cache valide pendant 30 jours (les données statistiques changent lentement)
    def get_insee_data(self, region_code):
        """Récupère les données statistiques pour une région donnée via l'API INSEE.
        
        Args:
            region_code (str): Code de la région
            
        Returns:
            dict: Données statistiques
        """
        try:
            api_key = self.config["insee"]["api_key"]
            api_secret = self.config["insee"]["api_secret"]
            
            if not api_key or not api_secret:
                logger.warning("Identifiants API INSEE non configurés")
                return None
                
            base_url = self.config["insee"]["api_url"]
            
            # Obtenir un token d'accès
            token_url = f"{base_url}token"
            auth = (api_key, api_secret)
            token_data = {"grant_type": "client_credentials"}
            
            token_session = create_session_with_retry()
            token_response = token_session.post(token_url, auth=auth, data=token_data, timeout=10)
            token_response.raise_for_status()
            
            access_token = token_response.json().get("access_token")
            if not access_token:
                logger.error("INSEE: Aucun token d'accès reçu")
                return None
            
            # Construire l'URL de l'API pour les données régionales
            url = f"{base_url}donnees-locales/v1/regions/{region_code}/statistiques"
            
            # Définir les en-têtes avec le token d'accès
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Effectuer la requête
            session = create_session_with_retry()
            response = session.get(url, headers=headers)
            response.raise_for_status()
            
            # Convertir la réponse en JSON
            data = response.json()
            
            # Extraire les données pertinentes
            insee_data = {}
            
            for stat in data["statistiques"]:
                name = stat["libelle"]
                value = stat["valeur"]
                unit = stat["unite"] if "unite" in stat else ""
                insee_data[name] = (value, unit)
            
            return insee_data
        except requests.exceptions.HTTPError as e:
            logger.error(f"INSEE: Erreur HTTP {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"INSEE: Erreur inattendue - {str(e)}")
            return None

    @cached(expiry=86400)  # Cache valide pendant 24 heures
    def get_fao_aquastat_data(self, indicator_codes=None, years=None):
        """Récupère les données de FAO AquaStat pour des indicateurs et années spécifiques.

        Args:
            indicator_codes (dict, optional): Dictionnaire des indicateurs à récupérer. 
                                              Format: {"code": ("item_code", "element_code")}.
                                              Par défaut: Ressources en eau renouvelables totales.
            years (list, optional): Liste des années à interroger. Par défaut, les 5 dernières années.

        Returns:
            dict: Données formatées de FAO AquaStat ou None en cas d'erreur.
        """
        fao_config = self.config.get("fao_aquastat", {})
        if not fao_config.get("enabled"):
            logger.info("L'API FAO AquaStat est désactivée dans la configuration.")
            return None

        # --- Configuration par défaut ---
        if indicator_codes is None:
            indicator_codes = {
                "ressources_eau_renouvelables_per_capita": ("4001", "6021") # Item, Element
            }
        
        if years is None:
            from datetime import datetime
            current_year = datetime.now().year
            years = [str(y) for y in range(current_year - 5, current_year + 1)]

        # --- Construction de la requête ---
        base_url = fao_config.get("api_url", "")
        if not base_url.endswith("/"):
            base_url += "/"
        
        # Le code pays pour le Maroc dans FAOSTAT est 143
        # Note: La config utilise 'MA', mais l'API nécessite le code numérique M49.
        country_code_m49 = "143" # Maroc

        all_items = [v[0] for v in indicator_codes.values()]
        all_elements = [v[1] for v in indicator_codes.values()]

        params = {
            "area": country_code_m49,
            "item": all_items,
            "element": all_elements,
            "year": years,
            "show_codes": "true",
            "show_flags": "true"
        }

        try:
            session = create_session_with_retry()
            # L'API FAOSTAT utilise un endpoint spécifique pour le domaine 'QW' (Water resources)
            request_url = f"{base_url}QW"
            logger.info(f"FAO AquaStat: Appel à {request_url} avec les paramètres {params}")
            
            response = session.get(request_url, params=params, timeout=20)
            response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP

            data = response.json()
            if not data or 'data' not in data:
                logger.warning("FAO AquaStat: Aucune donnée retournée par l'API.")
                return None

            # --- Traitement des données ---
            fao_data = {}
            for record in data['data']:
                item_code = record.get('Item Code')
                element_code = record.get('Element Code')
                year = record.get('Year')
                value = record.get('Value')
                unit = record.get('Unit')
                flag = record.get('Flag') # E=Estimated, I=Imputed, etc.

                # Retrouver le nom de l'indicateur
                indicator_name = "Inconnu"
                for name, codes in indicator_codes.items():
                    if codes == (item_code, element_code):
                        indicator_name = name.replace("_", " ").title()
                        break
                
                if indicator_name not in fao_data:
                    fao_data[indicator_name] = {}
                
                # Formater la valeur
                formatted_value = f"{value} ({flag})" if flag else str(value)
                fao_data[indicator_name][year] = (formatted_value, unit)

            logger.info(f"Données FAO AquaStat récupérées avec succès pour {len(fao_data)} indicateurs.")
            return fao_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Échec de l'API FAO AquaStat: {e}. Utilisation du fallback World Bank.")
            return self.get_water_data_fallback()
        except Exception as e:
            logger.error(f"FAO AquaStat: Erreur inattendue - {e}")
            return None

    def get_water_data(self, lat, lon):
        """Récupère les données sur l'eau pour des coordonnées données.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            dict: Données sur l'eau formatées
        """
        try:
            # Utiliser FAO AquaStat pour les données d'eau
            water_data = self.get_fao_aquastat_data()
            
            if water_data:
                return water_data
            else:
                # Fallback vers World Bank si FAO échoue
                return self.get_water_data_fallback()
                
        except Exception as e:
            logger.error(f"Erreur récupération données eau: {e}")
            return None

    def get_air_quality_data(self, lat, lon):
        """Récupère les données de qualité de l'air pour des coordonnées données.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            dict: Données de qualité de l'air formatées
        """
        try:
            # Utiliser la méthode existante get_air_pollution_data
            air_data = self.get_air_pollution_data(lat, lon)
            
            if air_data:
                return air_data
            else:
                logger.warning("Aucune donnée de qualité de l'air disponible")
                return None
                
        except Exception as e:
            logger.error(f"Erreur récupération données qualité air: {e}")
            return None

    def get_soil_data(self, lat, lon):
        """Récupère les données de sol pour des coordonnées données.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            dict: Données de sol formatées
        """
        try:
            # Utiliser la méthode existante get_soilgrids_data
            soil_data = self.get_soilgrids_data(lat, lon)
            
            if soil_data:
                return soil_data
            else:
                logger.warning("Aucune donnée de sol disponible")
                return None
                
        except Exception as e:
            logger.error(f"Erreur récupération données sol: {e}")
            return None

    @cached(expiry=2592000)  # Cache valide pendant 30 jours (les données de la Banque Mondiale sont mises à jour lentement)
    def get_water_data_fallback(self):
        """Récupère les données sur l'eau via des sources alternatives quand FAO échoue.
        
        Returns:
            dict: Données sur l'eau formatées comme FAO AquaStat
        """
        logger.info("Utilisation du fallback World Bank pour les données d'eau")
        
        # Indicateurs de la Banque Mondiale liés aux ressources en eau
        water_indicators = [
            "ER.H2O.FWRN.K3",  # Ressources en eau douce renouvelables (km³/an)
            "ER.H2O.FWTL.K3",  # Ressources en eau douce totales (km³/an)
            "ER.H2O.FWRN.PC.K3",  # Ressources en eau douce renouvelables par habitant (m³/habitant/an)
        ]
        
        try:
            worldbank_data = self.get_worldbank_data(water_indicators)
            
            if not worldbank_data:
                logger.warning("Fallback World Bank: Aucune donnée récupérée")
                return None
            
            # Convertir les données World Bank au format FAO AquaStat
            fao_format_data = {}
            
            for indicator_name, (value, year) in worldbank_data.items():
                if value and value != "None":
                    # Mapper les noms d'indicateurs vers des noms plus lisibles
                    if "per capita" in indicator_name.lower() or "habitant" in indicator_name.lower():
                        readable_name = "Ressources Eau Renouvelables Per Capita"
                        unit = "m³/habitant/an"
                    elif "renouvelables" in indicator_name.lower() or "renewable" in indicator_name.lower():
                        readable_name = "Ressources Eau Renouvelables Totales"
                        unit = "km³/an"
                    elif "totales" in indicator_name.lower() or "total" in indicator_name.lower():
                        readable_name = "Ressources Eau Totales"
                        unit = "km³/an"
                    else:
                        readable_name = indicator_name
                        unit = ""
                    
                    if readable_name not in fao_format_data:
                        fao_format_data[readable_name] = {}
                    
                    # Formater comme FAO avec indication de la source
                    formatted_value = f"{value} (World Bank)"
                    fao_format_data[readable_name][year] = (formatted_value, unit)
                    
                    logger.info(f"Fallback World Bank: {readable_name} = {value} {unit} ({year})")
            
            if fao_format_data:
                logger.info(f"Fallback World Bank: {len(fao_format_data)} indicateurs récupérés avec succès")
                return fao_format_data
            else:
                logger.warning("Fallback World Bank: Aucune donnée valide trouvée")
                return None
                
        except Exception as e:
            logger.error(f"Erreur dans le fallback World Bank: {e}")
            return None

    @cached(expiry=2592000)  # Cache valide pendant 30 jours (les données de la Banque Mondiale sont mises à jour lentement)
    def get_worldbank_data(self, indicators):
        """Récupère les données de la Banque Mondiale pour le Maroc.
        
        Args:
            indicators (list): Liste des codes d'indicateurs à récupérer
            
        Returns:
            dict: Données de la Banque Mondiale
        """
        logger.info(f"World Bank: Récupération de {len(indicators)} indicateurs: {indicators}")
        
        try:
            base_url = self.config["worldbank"]["api_url"]
            format_type = self.config["worldbank"]["format"]
            country = self.config["worldbank"]["country"]
            
            logger.info(f"World Bank: Configuration - URL: {base_url}, Format: {format_type}, Pays: {country}")
            
            worldbank_data = {}
            
            # Récupérer les données pour chaque indicateur
            for indicator in indicators:
                logger.info(f"World Bank: Traitement de l'indicateur {indicator}")
                
                # Construire l'URL de l'API
                url = f"{base_url}country/{country}/indicator/{indicator}?format={format_type}"
                logger.info(f"World Bank: Requête vers {url}")
                
                try:
                    # Effectuer la requête
                    session = create_session_with_retry()
                    response = session.get(url, timeout=15)
                    response.raise_for_status()
                    
                    # Convertir la réponse en JSON
                    data = response.json()
                    logger.info(f"World Bank: Réponse reçue pour {indicator}, structure: {type(data)}, longueur: {len(data) if isinstance(data, list) else 'N/A'}")
                    
                    # Extraire les données les plus récentes
                    if isinstance(data, list) and len(data) > 1:
                        records = data[1]
                        logger.info(f"World Bank: {len(records)} enregistrements trouvés pour {indicator}")
                        
                        if len(records) > 0:
                            # Chercher le premier enregistrement avec une valeur non-null
                            for record in records:
                                if record.get("value") is not None:
                                    indicator_name = record["indicator"]["value"]
                                    value = record["value"]
                                    year = record["date"]
                                    
                                    worldbank_data[indicator_name] = (str(value), year)
                                    logger.info(f"World Bank: Données trouvées pour {indicator}: {value} ({year})")
                                    break
                            else:
                                logger.warning(f"World Bank: Aucune valeur non-null trouvée pour {indicator}")
                        else:
                            logger.warning(f"World Bank: Aucun enregistrement pour {indicator}")
                    else:
                        logger.warning(f"World Bank: Structure de réponse inattendue pour {indicator}: {data}")
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"World Bank: Erreur de requête pour {indicator}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"World Bank: Erreur lors du traitement de {indicator}: {e}")
                    continue
            
            if worldbank_data:
                logger.info(f"World Bank: {len(worldbank_data)} indicateurs récupérés avec succès")
                return worldbank_data
            else:
                logger.warning("World Bank: Aucune donnée récupérée")
                return None
            
        except Exception as e:
            logger.error(f"World Bank: Erreur générale: {e}")
            return None
    
    def parse_osm_response(self, data):
        """Parse la réponse de l'API Overpass pour extraire les informations pertinentes.
        
        Args:
            data (dict): Données JSON de la réponse Overpass
            
        Returns:
            dict: Données structurées avec les comptages par catégorie
        """
        try:
            # Initialiser les compteurs pour les différentes catégories
            water_bodies = 0
            green_spaces = 0
            industrial = 0
            residential = 0
            
            # Parcourir tous les éléments de la réponse
            for element in data.get("elements", []):
                # Récupérer les tags de l'élément
                tags = element.get("tags", {})
                
                # Vérifier le type d'élément et incrémenter le compteur approprié
                if "natural" in tags and tags["natural"] in ["water", "wetland"]:
                    water_bodies += 1
                elif "waterway" in tags:
                    water_bodies += 1
                elif "leisure" in tags and tags["leisure"] == "park":
                    green_spaces += 1
                elif "landuse" in tags:
                    if tags["landuse"] == "forest":
                        green_spaces += 1
                    elif tags["landuse"] == "industrial":
                        industrial += 1
                    elif tags["landuse"] == "residential":
                        residential += 1
            
            # Créer le dictionnaire de résultats
            result = {
                "water_bodies": str(water_bodies),
                "green_spaces": str(green_spaces),
                "industrial": str(industrial),
                "residential": str(residential)
            }
            
            return result
            
        except Exception as e:
            if isinstance(e, requests.exceptions.RequestException):
                if 'WinError 10013' in str(e):
                    logger.error(f"Erreur d'autorisation réseau: {e}. Essayez d'exécuter l'application en tant qu'administrateur.")
                else:
                    logger.error(f"Erreur lors du parsing des données OpenStreetMap: {str(e)}")
            return {}
    
    @cached(expiry=86400)  # Cache valide pendant 24 heures
    def get_osm_data(self, lat, lon, radius=5000, tags=None):
        """Récupère les données OpenStreetMap autour d'un point donné.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            radius (int): Rayon de recherche en mètres (par défaut 5000m)
            tags (list): Liste des tags à rechercher (optionnel)
            
        Returns:
            dict: Données OpenStreetMap structurées
        """
        try:
            url = self.config["openstreetmap"]["api_url"]
            
            # Requête Overpass optimisée
            query = f"""
            [out:json];
            (
              way(around:{radius},{lat},{lon})["natural"="water"];
              way(around:{radius},{lat},{lon})["waterway"];
              way(around:{radius},{lat},{lon})["landuse"="forest"];
              node(around:{radius},{lat},{lon})["leisure"="park"];
              way(around:{radius},{lat},{lon})["leisure"="park"];
              way(around:{radius},{lat},{lon})["landuse"="industrial"];
              way(around:{radius},{lat},{lon})["landuse"="residential"];
            );
            out center;
            """
            
            # Effectuer la requête
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            session = create_session_with_retry()
            response = session.post(url, data={"data": query}, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parser la réponse avec la nouvelle fonction
            return self.parse_osm_response(data)
            
        except Exception as e:
            if isinstance(e, requests.exceptions.RequestException):
                if 'WinError 10013' in str(e):
                    logger.error(f"Erreur d'autorisation réseau: {e}. Essayez d'exécuter l'application en tant qu'administrateur.")
                else:
                    logger.error(f"Erreur lors de la récupération des données OpenStreetMap: {str(e)}")
            return None

    @cached(expiry=2592000)  # Cache valide pendant 30 jours (les données climatiques changent très lentement)
    def get_copernicus_data(self, lat, lon):
        """Récupère les données climatiques via l'API Copernicus Climate Data Store.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            dict: Données climatiques
        """
        try:
            api_key = self.config["copernicus"]["api_key"]
            if not api_key or not self.config["copernicus"]["enabled"]:
                logger.warning("Clé API Copernicus non configurée ou API désactivée")
                return None
                
            base_url = self.config["copernicus"]["api_url"]
            
            # Construire l'URL de l'API pour les données climatiques
            # Note: Copernicus CDS nécessite généralement une authentification plus complexe
            # et l'utilisation de leur client Python (cdsapi)
            # Ceci est une implémentation simplifiée
            url = f"{base_url}data?latitude={lat}&longitude={lon}&key={api_key}"
            
            # Effectuer la requête
            session = create_session_with_retry()
            response = session.get(url)
            response.raise_for_status()
            
            # Convertir la réponse en JSON
            data = response.json()
            
            # Extraire les données pertinentes
            climate_data = {
                "Température moyenne annuelle": (data.get("annual_temperature", 0), "°C"),
                "Précipitations annuelles": (data.get("annual_precipitation", 0), "mm"),
                "Jours de chaleur extrême": (data.get("extreme_heat_days", 0), "jours"),
                "Risque de sécheresse": (data.get("drought_risk", "Moyen"), ""),
                "Tendance climatique": (data.get("climate_trend", "Stable"), "")
            }
            
            return climate_data
            
        except Exception as e:
            if isinstance(e, requests.exceptions.RequestException):
                if 'WinError 10013' in str(e):
                    logger.error(f"Erreur d'autorisation réseau: {e}. Essayez d'exécuter l'application en tant qu'administrateur.")
                else:
                    logger.error(f"Erreur lors de la récupération des données Copernicus: {str(e)}")
            return None
    
    @cached(expiry=2592000)  # Cache valide pendant 30 jours (les données de biodiversité changent lentement)
    def get_gbif_data(self, lat, lon, radius=1000):
        """Récupère les données de biodiversité via l'API GBIF.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            radius (int): Rayon de recherche en mètres
            
        Returns:
            dict: Données de biodiversité
        """
        try:
            if not self.config["gbif"]["enabled"]:
                logger.warning("API GBIF désactivée")
                return None
                
            base_url = self.config["gbif"]["api_url"]
            
            # Convertir le rayon en degrés (approximation)
            radius_degrees = radius / 111000  # ~111km par degré à l'équateur
            
            # Construire l'URL de l'API pour les occurrences d'espèces
            url = f"{base_url}occurrence/search?decimalLatitude={lat-radius_degrees},{lat+radius_degrees}&decimalLongitude={lon-radius_degrees},{lon+radius_degrees}&limit=300"
            
            # Effectuer la requête
            session = create_session_with_retry()
            response = session.get(url)
            response.raise_for_status()
            
            # Convertir la réponse en JSON
            data = response.json()
            
            # Compter les espèces par groupe taxonomique
            species_count = {}
            endangered_count = 0
            
            if "results" in data:
                for occurrence in data["results"]:
                    kingdom = occurrence.get("kingdom", "Inconnu")
                    if kingdom not in species_count:
                        species_count[kingdom] = 0
                    species_count[kingdom] += 1
                    
                    # Vérifier si l'espèce est menacée (statut IUCN)
                    if occurrence.get("iucnRedListCategory") in ["VULNERABLE", "ENDANGERED", "CRITICALLY_ENDANGERED"]:
                        endangered_count += 1
            
            # Préparer les données de biodiversité
            # Calculer la densité faunistique (nombre d'espèces par km²)
            area_km2 = math.pi * (radius/1000)**2  # Convertir le rayon en km et calculer l'aire du cercle
            species_density = round(data.get("count", 0) / area_km2, 2) if area_km2 > 0 else 0
            
            biodiversity_data = {
                "Nombre total d'espèces": (data.get("count", 0), "espèces"),
                "Espèces menacées": (endangered_count, "espèces"),
                "Densité faunistique": (species_density, "Individus/km²"),
                "Richesse en biodiversité": (self._interpret_biodiversity_richness(data.get("count", 0)), "")
            }
            
            # Ajouter les comptages par groupe taxonomique
            for kingdom, count in species_count.items():
                biodiversity_data[f"Espèces - {kingdom}"] = (count, "espèces")
            
            return biodiversity_data
            
        except Exception as e:
            if isinstance(e, requests.exceptions.RequestException):
                if 'WinError 10013' in str(e):
                    logger.error(f"Erreur d'autorisation réseau: {e}. Essayez d'exécuter l'application en tant qu'administrateur.")
                else:
                    logger.error(f"Erreur lors de la récupération des données GBIF: {str(e)}")
            return None
    
    def _interpret_biodiversity_richness(self, species_count):
        """Interprète la richesse en biodiversité en fonction du nombre d'espèces.
        
        Args:
            species_count (int): Nombre d'espèces
            
        Returns:
            str: Interprétation de la richesse en biodiversité
        """
        if species_count < 10:
            return "Très faible - Zone potentiellement dégradée ou à faible diversité naturelle"
        elif species_count < 50:
            return "Faible - Biodiversité limitée"
        elif species_count < 100:
            return "Moyenne - Biodiversité modérée"
        elif species_count < 200:
            return "Élevée - Zone riche en biodiversité"
        else:
            return "Très élevée - Zone exceptionnellement riche en biodiversité, potentiellement sensible"
    
    @cached(expiry=2592000)  # Cache valide pendant 30 jours (les données satellitaires changent lentement)
    def get_nasa_data(self, lat, lon):
        """Récupère les données environnementales via les API NASA.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            dict: Données environnementales de la NASA
        """
        try:
            api_key = self.config["nasa"]["api_key"]
            if not api_key or not self.config["nasa"]["enabled"]:
                logger.warning("Clé API NASA non configurée ou API désactivée")
                return None
                
            base_url = self.config["nasa"]["api_url"]
            
            # Construire l'URL de l'API pour les données de couverture terrestre (MODIS)
            url = f"{base_url}planetary/earth/assets?lon={lon}&lat={lat}&api_key={api_key}"
            
            # Effectuer la requête
            session = create_session_with_retry()
            response = session.get(url)
            response.raise_for_status()
            
            # Convertir la réponse en JSON
            data = response.json()
            
            # Extraire les données pertinentes avec des valeurs estimées au lieu de "Non disponible"
            nasa_data = {
                "Dernière image satellite": (data.get("date", "Date estimée (récente)"), "date"),
                "Indice de végétation": (data.get("vegetation_index", 0.5), "NDVI"),
                "Changement de couverture terrestre": (data.get("land_cover_change", "Stable (estimé)"), ""),
                "Risque d'incendie": (data.get("fire_risk", "Faible à modéré (estimé)"), ""),
                "Anomalie de température": (data.get("temperature_anomaly", 0.2), "°C")
            }
            
            return nasa_data
            
        except Exception as e:
            if isinstance(e, requests.exceptions.RequestException):
                if 'WinError 10013' in str(e):
                    logger.error(f"Erreur d'autorisation réseau: {e}. Essayez d'exécuter l'application en tant qu'administrateur.")
                else:
                    logger.error(f"Erreur lors de la récupération des données NASA: {str(e)}")
            return None

    def collect_all_data(self, location, lat=None, lon=None, api_options=None):
        """Collecte toutes les données disponibles pour une localisation donnée.
        
        Args:
            location (str): Nom de la localisation (ville, région)
            lat (float, optional): Latitude (si disponible)
            lon (float, optional): Longitude (si disponible)
            api_options (dict, optional): Dictionnaire des API à utiliser
            
        Returns:
            pandas.DataFrame: DataFrame contenant toutes les données collectées
        """
        all_data = {}
        
        # Utiliser les options d'API si fournies, sinon utiliser la configuration par défaut
        if api_options is None:
            api_options = {
                "weather": self.config["openweathermap"]["enabled"],
                "air_quality": self.config["openweathermap_air_pollution"]["enabled"],
                "soil": self.config["soilgrids"]["enabled"],
                "worldbank": self.config["worldbank"]["enabled"],
                "osm": self.config["openstreetmap"]["enabled"],
                "copernicus": self.config["copernicus"]["enabled"],
                "gbif": self.config["gbif"]["enabled"],
                "nasa": self.config["nasa"]["enabled"],
                "eau": True  # Activer les paramètres d'eau détaillés par défaut
            }
        
        # Récupérer les données météorologiques
        if api_options.get("weather", True):
            # Si les coordonnées sont disponibles, les utiliser directement
            if lat is not None and lon is not None:
                weather_data = self.get_weather_data(lat, lon)
                if weather_data:
                    all_data.update({f"Météo - {k}": (v, "") for k, v in weather_data.items()})
        
        # Récupérer les données de qualité de l'air
        if api_options.get("air_quality", True):
            # Si les coordonnées sont disponibles, les utiliser directement
            if lat is not None and lon is not None:
                # Appeler l'API avec lat et lon séparés
                air_quality_data = self.get_air_quality_data(lat, lon)
            else:
                # Si les coordonnées ne sont pas disponibles, on ne peut pas appeler cette API
                logger.warning("Coordonnées non disponibles pour get_air_quality_data")
                air_quality_data = None
            
            if air_quality_data:
                # Pour l'AQI, conserver l'unité qui est le niveau textuel
                for k, v in air_quality_data.items():
                    if k == "AQI":
                        all_data.update({f"Air - {k}": v})
                    else:
                        all_data.update({f"Air - {k}": (v[0], v[1])})
        
        # Si les coordonnées sont disponibles, récupérer les données supplémentaires
        if lat is not None and lon is not None:
            # Récupérer les données sur le sol
            if api_options.get("soil", True):
                soil_properties = ["phh2o", "clay", "sand", "soc", "bdod"]
                soil_data = self.get_soil_data(lat, lon, properties=soil_properties)
                if isinstance(soil_data, dict):
                    all_data.update({f"Sol - {k}": v for k, v in soil_data.items()})
            
            # Récupérer les données OpenStreetMap
            if api_options.get("osm", True):
                osm_data = self.get_osm_data(lat, lon)
                if osm_data:
                    all_data.update({f"OSM - {k}": (v, "count") for k, v in osm_data.items()})
            
            # Récupérer les données Copernicus
            if api_options.get("copernicus", True):
                copernicus_data = self.get_copernicus_data(lat, lon)
                if copernicus_data:
                    all_data.update({f"Climat - {k}": v for k, v in copernicus_data.items()})
            
            # Récupérer les données GBIF
            if api_options.get("gbif", True):
                gbif_data = self.get_gbif_data(lat, lon)
                if gbif_data:
                    all_data.update({f"Biologique - {k}": v for k, v in gbif_data.items()})
            
            # Récupérer les données NASA
            if api_options.get("nasa", True):
                nasa_data = self.get_nasa_data(lat, lon)
                if nasa_data:
                    all_data.update({f"Satellite - {k}": v for k, v in nasa_data.items()})
        
        # Récupérer les données d'eau détaillées
        if api_options.get("eau", True) and lat is not None and lon is not None:
            logger.info("Récupération des paramètres d'eau détaillés...")
            # Priorité au collecteur détaillé
            detailed_water_data = self.get_detailed_water_data(lat, lon)
            
            if detailed_water_data and "Erreur" not in detailed_water_data:
                logger.info(f"{len(detailed_water_data)} paramètres d'eau détaillés récupérés.")
                all_data.update({f"Eau - {k}": (v, "") for k, v in detailed_water_data.items()})
            else:
                logger.warning("Échec de la récupération des données détaillées, utilisation du fallback World Bank.")
                fallback_water_data = self.get_water_data_fallback()
                if fallback_water_data:
                    all_data.update({f"Eau - {k}": v for k, v in fallback_water_data.items()})

        # Récupérer les données de la Banque Mondiale pour le Maroc
        if api_options.get("worldbank", True):
            worldbank_indicators = [
                "EN.ATM.CO2E.PC",  # Émissions de CO2 (tonnes métriques par habitant)
                "EN.ATM.PM25.MC.M3",  # Exposition aux PM2.5 (microgrammes par mètre cube)
                "ER.H2O.FWTL.ZS",  # Prélèvements annuels d'eau douce (% des ressources internes)
                "AG.LND.FRST.ZS",  # Superficie forestière (% du territoire)
                "EG.USE.PCAP.KG.OE",  # Consommation d'énergie (kg d'équivalent pétrole par habitant)
                "EN.CLC.GHGR.MT.CE",  # Émissions totales de gaz à effet de serre
                "ER.PTD.TOTL.ZS"  # Aires protégées (% du territoire)
            ]
            worldbank_data = self.get_worldbank_data(worldbank_indicators)
            if isinstance(worldbank_data, dict):
                all_data.update({f"BM - {k}": v for k, v in worldbank_data.items()})
        
        # Convertir les données en DataFrame
        df_data = []
        for param, value_tuple in all_data.items():
            # S'assurer que la valeur est un tuple de taille 2 (valeur, unité)
            if isinstance(value_tuple, tuple) and len(value_tuple) == 2:
                value, unit = value_tuple
            else:
                # Si ce n'est pas le cas, utiliser une valeur par défaut et logger un avertissement
                value, unit = (value_tuple, "N/A") # Utiliser la valeur telle quelle et une unité par défaut
                logger.warning(f"Format de données inattendu pour le paramètre '{param}'. Attendu (valeur, unité), reçu: {value_tuple}")

            parts = param.split(' - ', 1)
            milieu = parts[0] if len(parts) > 1 else "Général"
            parametre = parts[1] if len(parts) > 1 else param
            
            # Définir des intervalles acceptables et descriptions pour les paramètres connus
            intervalle_acceptable = "À déterminer"
            description = "Données collectées via API externe"
            
            # Paramètres connus avec leurs intervalles acceptables
            if parametre == "pH" or parametre.lower() == "ph sol":
                intervalle_acceptable = "6.5 - 8.5"
                description = "Mesure de l'acidité ou de l'alcalinité de l'eau ou du sol"
            elif parametre == "Température" or parametre == "Température de l'air":
                intervalle_acceptable = "15 - 25"
                description = "Température ambiante en degrés Celsius"
            elif parametre == "Humidité":
                intervalle_acceptable = "30 - 70"
                description = "Pourcentage d'humidité dans l'air"
            elif parametre == "Turbidité":
                intervalle_acceptable = "≤ 5"
                description = "Mesure de la clarté de l'eau"
            elif parametre == "Conductivité":
                intervalle_acceptable = "200 - 1000"
                description = "Capacité de l'eau à conduire l'électricité"
            elif parametre == "Oxygène dissous":
                intervalle_acceptable = "≥ 5"
                description = "Quantité d'oxygène disponible dans l'eau"
            elif "PM2.5" in parametre:
                intervalle_acceptable = "≤ 10"
                description = "Particules fines dans l'air de diamètre inférieur à 2.5 microns"
            elif "PM10" in parametre:
                intervalle_acceptable = "≤ 20"
                description = "Particules fines dans l'air de diamètre inférieur à 10 microns"
            elif "NO2" in parametre:
                intervalle_acceptable = "≤ 40"
                description = "Dioxyde d'azote, polluant atmosphérique"
            elif "O3" in parametre:
                intervalle_acceptable = "≤ 100"
                description = "Ozone, polluant atmosphérique"
            elif "CO" in parametre:
                intervalle_acceptable = "≤ 4000"
                description = "Monoxyde de carbone, polluant atmosphérique"
            elif "SO2" in parametre:
                intervalle_acceptable = "≤ 40"
                description = "Dioxyde de soufre, polluant atmosphérique"
            elif parametre == "Espèces menacées":
                intervalle_acceptable = "Liste rouge UICN"
                description = "Espèces en danger selon la classification de l'Union Internationale pour la Conservation de la Nature"
            elif parametre == "Densité faunistique":
                intervalle_acceptable = "Selon inventaire régional"
                description = "Nombre d'individus par kilomètre carré dans la zone étudiée"
            
            df_data.append({
                "Milieu": milieu,
                "Paramètre": parametre,
                "Valeur": value,
                "Unité": unit,
                "Intervalle acceptable": intervalle_acceptable,
                "Description": description
            })
        
        # Créer le DataFrame
        df = pd.DataFrame(df_data)
        
        # Réorganiser les colonnes
        columns = ["Milieu", "Paramètre", "Valeur", "Unité", "Intervalle acceptable", "Description"]
        df = df[columns]
        
        return df

# Fonction pour extraire les coordonnées géographiques à partir d'un nom de lieu
def get_coordinates(location):
    """Récupère les coordonnées géographiques (latitude, longitude) pour un lieu donné.
    
    Args:
        location (str): Nom du lieu (ville, adresse, etc.) ou coordonnées directes au format "lat,lon"
        
    Returns:
        tuple: (latitude, longitude) ou (None, None) en cas d'erreur
    """
    try:
        # Vérifier si la localisation est déjà au format de coordonnées "lat,lon"
        if ',' in location:
            try:
                parts = location.split(',')
                if len(parts) == 2:  # Exactement 2 parties pour les coordonnées lat,lon
                    # Nettoyer les parties pour s'assurer qu'elles peuvent être converties en float
                    lat_str = parts[0].strip()
                    lon_str = parts[1].strip()
                    
                    # Vérification plus stricte pour s'assurer qu'il s'agit bien de coordonnées
                    # et non d'un nom de lieu contenant une virgule
                    # Vérifier que les chaînes contiennent principalement des chiffres et des caractères de nombre
                    # et qu'elles ont un format de nombre décimal valide
                    lat_is_numeric = all(c.isdigit() or c in '.-' for c in lat_str) and lat_str.replace('-', '', 1).replace('.', '', 1).isdigit()
                    lon_is_numeric = all(c.isdigit() or c in '.-' for c in lon_str) and lon_str.replace('-', '', 1).replace('.', '', 1).isdigit()
                    
                    if lat_is_numeric and lon_is_numeric:
                        try:
                            lat = float(lat_str)
                            lon = float(lon_str)
                            # Vérifier que les valeurs sont dans des plages valides pour des coordonnées géographiques
                            if -90 <= lat <= 90 and -180 <= lon <= 180:
                                logger.info(f"Coordonnées extraites directement: {lat}, {lon}")
                                return lat, lon
                            else:
                                logger.warning(f"Valeurs de coordonnées hors limites: {lat}, {lon}")
                                # Continuer avec la méthode de géocodage standard
                        except ValueError as e:
                            logger.warning(f"Impossible de convertir en coordonnées: {str(e)}")
                            # Continuer avec la méthode de géocodage standard
                    else:
                        logger.info(f"La chaîne '{location}' contient une virgule mais n'est pas au format de coordonnées valides")
                else:
                    logger.info(f"La chaîne '{location}' contient {len(parts)} parties, pas exactement 2 comme attendu pour des coordonnées")
            except Exception as e:
                logger.warning(f"Erreur lors de l'analyse des coordonnées: {str(e)}")
        else:
            logger.info(f"La chaîne '{location}' ne contient pas de virgule, ce n'est pas un format de coordonnées")
        
        # Utiliser l'API de géocodage Nominatim (OpenStreetMap)
        url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1"
        
        # Ajouter un User-Agent pour respecter les conditions d'utilisation de Nominatim
        headers = {"User-Agent": "EnvironmentalRiskAnalysis/1.0"}
        
        session = create_session_with_retry()
        response = session.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if data and len(data) > 0:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
        else:
            logger.warning(f"Aucune coordonnée trouvée pour {location}")
            return None, None
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des coordonnées: {str(e)}")
        return None, None

# Fonction principale pour collecter les données environnementales via les API externes
def collect_environmental_data_from_apis(location, project_type=None, api_options=None):
    """Collecte les données environnementales pour une localisation donnée en utilisant diverses API externes.
    
    Args:
        location (str): Localisation du projet (ville, région)
        project_type (str, optional): Type de projet (pour filtrer les données pertinentes)
        api_options (dict, optional): Dictionnaire des API à utiliser
        
    Returns:
        pandas.DataFrame: DataFrame contenant les données environnementales collectées
    """
    try:
        # Récupérer les coordonnées géographiques
        lat, lon = get_coordinates(location)
        
        # Vérifier si les coordonnées ont été obtenues avec succès
        if lat is None or lon is None:
            logger.warning(f"Impossible d'obtenir les coordonnées pour la localisation: {location}")
            # Continuer avec les API qui ne nécessitent pas de coordonnées
        
        # Initialiser les API externes
        apis = ExternalAPIs()
        
        # Collecter toutes les données disponibles
        df = apis.collect_all_data(location, lat, lon, api_options)
        
        # Filtrer les données en fonction du type de projet si spécifié
        if project_type and not df.empty:
            # Définir les paramètres pertinents pour chaque type de projet
            project_filters = {
                "Industriel": ["Air", "Eau", "Sol", "Météo"],
                "Agricole": ["Sol", "Eau", "Météo"],
                "Urbain": ["Air", "Bruit", "OSM"],
                "Infrastructure": ["Sol", "Eau", "OSM"],
                "Touristique": ["Air", "Eau", "Météo", "OSM"],
                "Minier": ["Sol", "Eau", "Air"],
                "Énergétique": ["Air", "Eau", "Météo"],
                "Autre": ["Air", "Eau", "Sol", "Météo", "OSM"]
            }
            
            # Obtenir les filtres pour le type de projet spécifié
            filters = project_filters.get(project_type, project_filters["Autre"])
            
            # Filtrer le DataFrame
            df = df[df["Milieu"].isin(filters)]
        
        # Ajouter des colonnes supplémentaires pour la conformité
        for col in ["Valeur mesurée", "Résultat conformité", "Score"]:
            if col not in df.columns:
                df[col] = ""
        
        return df
        
    except Exception as e:
        logger.error(f"Erreur lors de la collecte des données environnementales: {str(e)}")
        # Retourner un DataFrame vide avec les colonnes appropriées
        return pd.DataFrame(columns=["Milieu", "Paramètre", "Unité", "Intervalle acceptable", "Valeur mesurée", "Résultat conformité", "Score", "Description"])

# Fonction pour tester les API externes
def test_apis(location=None):
    """Fonction de test pour vérifier le fonctionnement des API externes.
    
    Args:
        location (str, optional): Localisation à tester. Si non spécifiée, utilise "Casablanca" par défaut.
        
    Returns:
        str: Rapport de test formaté
    """
    # Initialiser les API externes
    apis = ExternalAPIs()
    
    # Utiliser la localisation spécifiée ou la valeur par défaut
    if not location:
        location = "Casablanca"
        
    # Définir un type de projet par défaut pour le test
    default_project_type = "Industriel"
    api_options = {
        "weather": True,
        "air_quality": {
            "enabled": True,
            "standard": "EPA"  # ou "EU", "Morocco"
        },
        "soil": True,
        "worldbank": True,
        "osm": True
    }
    
    # Préparer le rapport de test
    report = f"Test des API externes pour {location}\n"
    report += "=" * 50 + "\n\n"
    
    # Récupérer les coordonnées
    lat, lon = get_coordinates(location)
    report += f"Coordonnées: {lat}, {lon}\n\n"
    
    # Tester l'API OpenWeatherMap
    report += "1. OpenWeatherMap (Données météorologiques)\n"
    report += "-" * 40 + "\n"
    try:
        if lat is not None and lon is not None:
            weather_data = apis.get_weather_data(lat, lon)
            if weather_data:
                report += "Statut: ✅ Succès\n"
                for key, (value, unit) in weather_data.items():
                    report += f"{key}: {value} {unit}\n"
            else:
                report += "Statut: ❌ Échec\n"
                report += "Erreur: Aucune donnée météorologique disponible\n"
        else:
            report += "Statut: ❌ Échec\n"
            report += "Erreur: Coordonnées géographiques non disponibles\n"
    except Exception as e:
        report += "Statut: ❌ Échec\n"
        report += f"Erreur: {str(e)}\n"
    report += "\n"
    
    # Tester l'API OpenWeatherMap Air Pollution
    report += "2. OpenWeatherMap Air Pollution (Qualité de l'air)\n"
    report += "-" * 40 + "\n"
    try:
        if lat is not None and lon is not None:
            air_data = apis.get_air_quality_data(lat, lon)
            if isinstance(air_data, dict) and "error" not in air_data:
                report += "Statut: ✅ Succès\n"
                report += f"AQI: {air_data.get('AQI', 'N/A')}\n"
                report += f"PM2.5: {air_data.get('PM2.5', ('N/A', ''))[0]} {air_data.get('PM2.5', ('', 'µg/m³'))[1]}\n"
                report += f"PM10: {air_data.get('PM10', ('N/A', ''))[0]} {air_data.get('PM10', ('', 'µg/m³'))[1]}\n"
            else:
                report += "Statut: ❌ Échec\n"
                report += f"Erreur: {air_data.get('error', 'Erreur inconnue')}\n"
        else:
            report += "Statut: ❌ Échec\n"
            report += "Erreur: Coordonnées géographiques non disponibles\n"
    except Exception as e:
        report += "Statut: ❌ Échec\n"
        report += f"Erreur: {str(e)}\n"
    report += "\n"
    
    # Tester l'API SoilGrids (si les coordonnées sont disponibles)
    report += "3. SoilGrids (Données sur le sol)\n"
    report += "-" * 40 + "\n"
    if lat and lon:
        try:
            soil_data = apis.get_soil_data(lat, lon)
            if isinstance(soil_data, dict) and "error" not in soil_data:
                report += "Statut: ✅ Succès\n"
                # Utiliser les nouvelles clés normalisées
                ph_value, ph_unit = soil_data.get("pH du sol", ("N/A", ""))
                report += f"pH: {ph_value} {ph_unit}\n"
                
                carbone_value, carbone_unit = soil_data.get("Carbone organique du sol", ("N/A", ""))
                report += f"Carbone organique: {carbone_value} {carbone_unit}\n"
                
                argile_value, argile_unit = soil_data.get("Teneur en argile", ("N/A", ""))
                report += f"Argile: {argile_value} {argile_unit}\n"
                
                sable_value, sable_unit = soil_data.get("Teneur en sable", ("N/A", ""))
                report += f"Sable: {sable_value} {sable_unit}\n"
            else:
                report += "Statut: ❌ Échec\n"
                report += f"Erreur: {soil_data.get('error', 'Erreur inconnue')}\n"
        except Exception as e:
            report += "Statut: ❌ Échec\n"
            report += f"Erreur: {str(e)}\n"
    else:
        report += "Statut: ⚠️ Non testé\n"
        report += "Raison: Coordonnées non disponibles\n"
    report += "\n"
    
    # Tester l'API OpenStreetMap (si les coordonnées sont disponibles)
    report += "4. OpenStreetMap (Données géographiques)\n"
    report += "-" * 40 + "\n"
    if lat and lon:
        try:
            osm_data = apis.get_osm_data(lat, lon)
            if isinstance(osm_data, dict) and "error" not in osm_data:
                report += "Statut: ✅ Succès\n"
                report += f"Points d'eau: {osm_data.get('water_bodies', 'N/A')}\n"
                report += f"Espaces verts: {osm_data.get('green_spaces', 'N/A')}\n"
                report += f"Zones industrielles: {osm_data.get('industrial', 'N/A')}\n"
            else:
                report += "Statut: ❌ Échec\n"
                report += f"Erreur: {osm_data.get('error', 'Erreur inconnue')}\n"
        except Exception as e:
            report += "Statut: ❌ Échec\n"
            report += f"Erreur: {str(e)}\n"
    else:
        report += "Statut: ⚠️ Non testé\n"
        report += "Raison: Coordonnées non disponibles\n"
    report += "\n"
    
    # Tester l'API de la Banque Mondiale
    report += "5. Banque Mondiale (Indicateurs environnementaux)\n"
    report += "-" * 40 + "\n"
    try:
        worldbank_data = apis.get_worldbank_data(["EN.ATM.CO2E.PC", "EN.ATM.PM25.MC.M3"])
        if isinstance(worldbank_data, dict) and "error" not in worldbank_data:
            report += "Statut: ✅ Succès\n"
            for indicator, value in worldbank_data.items():
                if indicator != "error":
                    report += f"{indicator}: {value}\n"
        else:
            report += "Statut: ❌ Échec\n"
            report += f"Erreur: {worldbank_data.get('error', 'Erreur inconnue')}\n"
    except Exception as e:
        report += "Statut: ❌ Échec\n"
        report += f"Erreur: {str(e)}\n"
    report += "\n"
    
    # Résumé de la collecte complète des données
    report += "6. Collecte complète des données\n"
    report += "-" * 40 + "\n"
    try:
        # Utiliser le type de projet et les options d'API définis plus haut
        df = collect_environmental_data_from_apis(location, default_project_type, api_options)
        if not df.empty:
            report += "Statut: ✅ Succès\n"
            report += f"Nombre total de paramètres collectés: {len(df)}\n"
            report += f"Milieux disponibles: {', '.join(df['Milieu'].unique())}\n"
        else:
            report += "Statut: ⚠️ Aucune donnée\n"
            report += "Raison: Aucun paramètre environnemental n'a pu être collecté\n"
    except Exception as e:
        report += "Statut: ❌ Échec\n"
        report += f"Erreur: {str(e)}\n"
    
    report += "\n" + "=" * 50 + "\n"
    report += "Test terminé.\n"
    
    # Si exécuté en mode console, afficher le rapport
    if __name__ == "__main__":
        print(report)
    
    return report

# Exécuter le test si le script est exécuté directement
if __name__ == "__main__":
    # Configurer le logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    test_apis()

@cached(expiry=3600)  # Cache valide pendant 1 heure
def collect_environmental_data_from_apis(location, project_type, api_options=None):
    """Collecte des données environnementales à partir de diverses API externes.
    
    Args:
        location (str): Nom de la localisation (ville, région)
        project_type (str): Type de projet (Industriel, Agricole, Urbain)
        api_options (dict, optional): Dictionnaire des API à utiliser. Par défaut, toutes les API sont utilisées.
            Exemple: {
                "weather": True,
                "air_quality": {
                    "enabled": True,
                    "standard": "EPA"  # ou "EU", "Morocco"
                },
                "soil": True,
                "worldbank": True,
                "osm": True
            }
        
    Returns:
        pandas.DataFrame: DataFrame contenant les données environnementales collectées
    """
    # Si aucune option d'API n'est spécifiée, utiliser toutes les API
    if api_options is None:
        api_options = {
            "weather": True,
            "air_quality": {
                "enabled": True,
                "standard": "EPA"
            },
            "soil": True,
            "worldbank": True,
            "osm": True
        }

    # Initialiser l'objet ExternalAPIs
    apis = ExternalAPIs()

    # Récupérer les coordonnées géographiques
    lat, lon = get_coordinates(location)

    # Collecter les données
    data = {}

    # Récupérer les données météorologiques si l'option est activée
    if api_options.get("weather", True) and lat is not None and lon is not None:
        weather_data = apis.get_weather_data(lat, lon)
        if weather_data:
            data.update(weather_data)

    # Récupérer les données de qualité de l'air si l'option est activée
    air_quality_option = api_options.get("air_quality", {"enabled": True, "standard": "EPA"})
    if lat is not None and lon is not None:
        # Vérifier si air_quality est un dictionnaire ou un booléen
        if isinstance(air_quality_option, dict):
            if air_quality_option.get("enabled", True):
                standard = air_quality_option.get("standard", "EPA")
                air_quality_data = apis.get_air_quality_data(lat, lon, standard)
                if air_quality_data:
                    data.update(air_quality_data)
        elif air_quality_option:  # Si c'est un booléen True
            air_quality_data = apis.get_air_quality_data(lat, lon)
            if air_quality_data:
                data.update(air_quality_data)
    
    # Récupérer les données sur le sol si l'option est activée et si les coordonnées sont disponibles
    if api_options.get("soil", True) and lat is not None and lon is not None:
        soil_data = apis.get_soil_data(lat, lon)
        if soil_data:
            data.update(soil_data)
    
    # Récupérer les données OpenStreetMap si l'option est activée et si les coordonnées sont disponibles
    if api_options.get("osm", True) and lat is not None and lon is not None:
        osm_data = apis.get_osm_data(lat, lon)
        if osm_data:
            data.update(osm_data)
    
    # Récupérer les données de la Banque Mondiale si l'option est activée
    if api_options.get("worldbank", True):
        # Définir les indicateurs de la Banque Mondiale à récupérer
        worldbank_indicators = [
            "EN.ATM.CO2E.PC",  # Émissions de CO2 (tonnes métriques par habitant)
            "EN.ATM.PM25.MC.M3",  # Exposition aux PM2.5 (microgrammes par mètre cube)
            "ER.H2O.FWTL.ZS",  # Prélèvements annuels d'eau douce (% des ressources internes)
            "AG.LND.FRST.ZS",  # Superficie forestière (% du territoire)
            "EG.USE.PCAP.KG.OE",  # Consommation d'énergie (kg d'équivalent pétrole par habitant)
            "EN.CLC.GHGR.MT.CE",  # Émissions totales de gaz à effet de serre
            "ER.PTD.TOTL.ZS"  # Aires protégées (% du territoire)
        ]
        worldbank_data = apis.get_worldbank_data(worldbank_indicators)
        if worldbank_data:
            data.update(worldbank_data)
    
    # Convertir les données en DataFrame
    if not data:
        return pd.DataFrame()
        
    # S'assurer que toutes les valeurs sont des tuples (valeur, unité)
    formatted_data = {}
    for key, value in data.items():
        if isinstance(value, tuple) and len(value) == 2:
            formatted_data[key] = value
        elif isinstance(value, (int, float, str)):
            # Si la valeur est un nombre ou une chaîne, la convertir en tuple avec unité vide
            formatted_data[key] = (value, "")
        else:
            # Ignorer les valeurs qui ne peuvent pas être converties
            logger.warning(f"Valeur ignorée pour {key}: {value} (type non supporté)")
            
    df = pd.DataFrame({
        "Milieu": ["Environnement" for _ in formatted_data],
        "Paramètre": list(formatted_data.keys()),
        "Valeur": [d[0] for d in formatted_data.values()],
        "Unité": [d[1] for d in formatted_data.values()],
        "Source": ["API Externe" for _ in formatted_data]
    })
    
    # Filtrer les données en fonction du type de projet
    filtered_df = filter_data_by_project_type(df, project_type)
    
    # Ajouter des colonnes supplémentaires pour la conformité si elles n'existent pas
    for col in ["Valeur mesurée", "Résultat conformité"]:
        if col not in filtered_df.columns:
            filtered_df[col] = ""
    
    # Remplir les colonnes de conformité pour l'AQI
    aqi_mask = filtered_df['Paramètre'] == 'AQI'
    if any(aqi_mask):
        # Copier la valeur numérique dans 'Valeur mesurée'
        filtered_df.loc[aqi_mask, 'Valeur mesurée'] = filtered_df.loc[aqi_mask, 'Valeur']
        # Utiliser le niveau textuel comme 'Résultat conformité'
        filtered_df.loc[aqi_mask, 'Résultat conformité'] = filtered_df.loc[aqi_mask, 'Unité']
        
        # Attribuer un score en fonction du niveau d'AQI
        aqi_level = filtered_df.loc[aqi_mask, 'Unité'].iloc[0]
        aqi_score_map = {
            'Bon': 100,
            'Acceptable': 80,
            'Modéré': 60,
            'Mauvais': 40,
            'Très mauvais': 20,
            'Dangereux': 0
        }
        filtered_df.loc[aqi_mask, 'Score'] = aqi_score_map.get(aqi_level, 0)

    # Initialiser la colonne Score avec des valeurs numériques
    if "Score" not in filtered_df.columns:
        filtered_df["Score"] = 0

    return filtered_df

def filter_environmental_data_by_project_type(df, project_type="Général"):
    """Filtre les données en fonction du type de projet.

    Args:
        df (pandas.DataFrame): DataFrame contenant les données environnementales
        project_type (str): Type de projet (Industriel, Agricole, etc.)

    Returns:
        pandas.DataFrame: DataFrame filtré
    """
    if df.empty:
        return df
        
    # Définir les paramètres pertinents pour chaque type de projet
    project_params = {
        "Industriel": ["CO2", "PM", "NOx", "SO2", "Température", "Humidité", "Qualité de l'air", "AQI", 
                     "pH", "Métaux lourds", "Bruit", "Émissions"],
        "Agricole": ["Nitrates", "Phosphates", "pH", "Matière organique", "Pesticides", "Irrigation", 
                    "Précipitations", "Température", "Humidité", "Qualité de l'eau", "AQI"],
        "Urbain": ["PM", "NOx", "CO", "Bruit", "Espaces verts", "Température", "Précipitations", 
                  "Qualité de l'air", "Déchets", "AQI"],
        "Infrastructure": ["Bruit", "Vibrations", "Poussière", "Érosion", "Drainage", "Qualité de l'eau", 
                         "Biodiversité", "AQI"],
        "Touristique": ["Qualité de l'eau", "Qualité de l'air", "Biodiversité", "Espaces naturels", 
                       "Température", "Précipitations", "AQI"],
        "Minier": ["Métaux lourds", "pH", "Poussière", "Qualité de l'eau", "Érosion", "Vibrations", 
                   "Bruit", "AQI"],
        "Énergétique": ["CO2", "NOx", "SO2", "Température", "Émissions", "Bruit", "AQI"]
    }
    
    # Si le type de projet n'est pas dans la liste, retourner toutes les données
    if project_type not in project_params:
        return df
    
    # Filtrer les données en fonction des paramètres pertinents
    # Utiliser une approche souple pour la correspondance
    filtered_rows = []
    for _, row in df.iterrows():
        param = row["Paramètre"]
        for keyword in project_params[project_type]:
            if keyword.lower() in param.lower():
                filtered_rows.append(row)
                break
    
    # Si aucun paramètre ne correspond, retourner toutes les données
    if not filtered_rows:
        return df
    
    return pd.DataFrame(filtered_rows)