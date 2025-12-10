import pandas as pd
import requests
from bs4 import BeautifulSoup
import logging
from config import WEB_CONFIG

logger = logging.getLogger(__name__)

def load_data(file_path):
    """Charge les données depuis un fichier Excel."""
    try:
        logger.info(f"Chargement des données depuis {file_path}")
        df = pd.read_excel(file_path)
        logger.info(f"Données chargées avec succès. Colonnes: {df.columns.tolist()}")
        return df
    except FileNotFoundError:
        logger.error(f"Erreur: Le fichier {file_path} n'a pas été trouvé.")
        return None
    except Exception as e:
        logger.error(f"Erreur lors du chargement des données: {str(e)}")
        return None

def search_web_for_info(query):
    """Recherche sur le web pour des informations manquantes."""
    # Normaliser la requête pour éviter les problèmes d'encodage
    normalized_query = query.replace('₃', '3').replace('₂', '2')
    logger.info(f"Recherche d'informations pour: {normalized_query}")
    try:
        search_url = WEB_CONFIG["search_url"].format(query=normalized_query)
        headers = {"User-Agent": WEB_CONFIG["user_agent"]}
        
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Essayer différentes classes pour les extraits de résultats
        search_snippets = soup.find_all('div', class_='BNeawe vvjwJb AP7Wnd')
        if search_snippets:
            return search_snippets[0].get_text()
        
        search_snippets = soup.find_all('div', class_='VwiC3b yXK7lf lVm3ye r025kc hJNv6b')
        if search_snippets:
            return search_snippets[0].get_text()

        logger.warning("Pas d'information pertinente trouvée.")
        return "Pas d'information pertinente trouvée."
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur de réseau lors de la recherche: {str(e)}")
        return None

def enrich_data(df, search_column="Paramètre", target_column="Description", query_prefix="risque environnemental", query_suffix="Maroc"):
    """Enrichit les données avec des informations provenant du web."""
    logger.info(f"Enrichissement des données pour {len(df)} entrées")
    
    # Ajouter la colonne cible si elle n'existe pas
    if target_column not in df.columns:
        df[target_column] = pd.NA
    
    # Compter les entrées à enrichir
    missing_count = df[target_column].isna().sum()
    logger.info(f"{missing_count} entrées à enrichir")
    
    # Enrichir les entrées manquantes
    enriched_count = 0
    for index, row in df.iterrows():
        if pd.isna(row[target_column]):
            value = row.get(search_column)
            if pd.notna(value):
                query = f"{query_prefix} {value} {query_suffix}"
                web_info = search_web_for_info(query)
                if web_info and web_info != "Pas d'information pertinente trouvée.":
                    df.at[index, target_column] = web_info
                    enriched_count += 1
    
    logger.info(f"{enriched_count} entrées enrichies avec succès")
    return df

def clean_data(df):
    """Nettoie les données en supprimant les doublons et les valeurs manquantes."""
    logger.info("Nettoyage des données")
    
    # Enregistrer la taille initiale
    initial_size = len(df)
    
    # Supprimer les doublons
    df = df.drop_duplicates()
    
    # Supprimer les lignes où toutes les valeurs sont manquantes
    df = df.dropna(how='all')
    
    # Remplacer les valeurs manquantes par des valeurs par défaut selon le type de colonne
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].fillna('')
        else:
            df[col] = df[col].fillna(0)
    
    # Enregistrer la taille finale
    final_size = len(df)
    logger.info(f"Nettoyage terminé: {initial_size - final_size} lignes supprimées")
    
    return df

def analyze_environmental_data(df):
    """Analyse les données environnementales et ajoute des colonnes d'évaluation."""
    logger.info("Analyse des données environnementales")
    
    # Base de connaissances des paramètres environnementaux courants
    parametres_connus = {
        "ph": {
            "milieu": "Eau",
            "intervalle": "6.5 - 8.5",
            "unite": "pH",
            "valeur_defaut": "7.2 (estimé)",
            "description": "Mesure de l'acidité/basicité de l'eau"
        },
        "turbidité": {
            "milieu": "Eau",
            "intervalle": "< 5",
            "unite": "NTU",
            "valeur_defaut": "2.5 (estimé)",
            "description": "Mesure de la clarté de l'eau"
        },
        "température": {
            "milieu": "Eau",
            "intervalle": "10 - 25",
            "unite": "°C",
            "valeur_defaut": "18 (estimé)",
            "description": "Température de l'eau"
        },
        "conductivité": {
            "milieu": "Eau",
            "intervalle": "< 1000",
            "unite": "µS/cm",
            "valeur_defaut": "500 (estimé)",
            "description": "Mesure des ions dissous dans l'eau"
        },
        "oxygène dissous": {
            "milieu": "Eau",
            "intervalle": "> 5",
            "unite": "mg/L",
            "valeur_defaut": "7.5 (estimé)",
            "description": "Quantité d'oxygène disponible pour la vie aquatique"
        },
        "dbo5": {
            "milieu": "Eau",
            "intervalle": "< 5",
            "unite": "mg/L",
            "valeur_defaut": "3 (estimé)",
            "description": "Demande biochimique en oxygène sur 5 jours"
        },
        "dco": {
            "milieu": "Eau",
            "intervalle": "< 30",
            "unite": "mg/L",
            "valeur_defaut": "20 (estimé)",
            "description": "Demande chimique en oxygène"
        },
        "nitrates": {
            "milieu": "Eau",
            "intervalle": "< 50",
            "unite": "mg/L",
            "valeur_defaut": "25 (estimé)",
            "description": "Concentration en nitrates"
        },
        "phosphates": {
            "milieu": "Eau",
            "intervalle": "< 0.5",
            "unite": "mg/L",
            "valeur_defaut": "0.2 (estimé)",
            "description": "Concentration en phosphates"
        }
    }
    
    # Vérifier si les colonnes nécessaires existent et les créer si elles sont manquantes
    required_columns = ["Paramètre", "Valeur mesurée"]
    for col in required_columns:
        if col not in df.columns:
            logger.warning(f"Colonne requise manquante: {col}. Création de la colonne.")
            df[col] = ""
    
    # Assurer que le DataFrame a toutes les colonnes du modèle
    model_columns = ["Milieu", "Paramètre", "Unité", "Intervalle acceptable", "Valeur mesurée", "Résultat conformité", "Score", "Observations", "Description"]
    for col in model_columns:
        if col not in df.columns:
            df[col] = ""
    
    # Analyse des données environnementales
    for index, row in df.iterrows():
        parametre = row["Paramètre"].lower() if isinstance(row["Paramètre"], str) else ""
        valeur = row["Valeur mesurée"]
        
        # Rechercher le paramètre dans notre base de connaissances
        param_info = None
        for known_param, info in parametres_connus.items():
            if known_param in parametre or parametre in known_param:
                param_info = info
                break
        
        # Appliquer les valeurs par défaut si disponibles dans notre base de connaissances
        if param_info:
            # Définir le milieu par défaut si non spécifié
            if not row["Milieu"] or row["Milieu"] == "Non disponible":
                df.at[index, "Milieu"] = param_info["milieu"]
            
            # Définir l'unité par défaut si non spécifiée
            if not row["Unité"] or row["Unité"] == "Non disponible":
                df.at[index, "Unité"] = param_info["unite"]
            
            # Définir l'intervalle acceptable par défaut si non spécifié
            if not row["Intervalle acceptable"] or row["Intervalle acceptable"] == "Non disponible":
                df.at[index, "Intervalle acceptable"] = param_info["intervalle"]
                
            # Définir la valeur mesurée par défaut si non spécifiée
            if not valeur or valeur == "Non disponible":
                df.at[index, "Valeur mesurée"] = param_info["valeur_defaut"]
                valeur = param_info["valeur_defaut"]
                
            # Ajouter une description si disponible
            if not row["Description"] or row["Description"] == "Non disponible":
                df.at[index, "Description"] = param_info["description"]
        else:
            # Valeurs par défaut génériques si le paramètre n'est pas dans notre base de connaissances
            if not row["Milieu"] or row["Milieu"] == "Non disponible":
                df.at[index, "Milieu"] = "Eau"  # Valeur par défaut
            
            if not row["Unité"] or row["Unité"] == "Non disponible":
                df.at[index, "Unité"] = "mg/L"  # Unité par défaut
            
            if not row["Intervalle acceptable"] or row["Intervalle acceptable"] == "Non disponible":
                df.at[index, "Intervalle acceptable"] = "À déterminer"
                
            if not valeur or valeur == "Non disponible":
                df.at[index, "Valeur mesurée"] = "5.0 (estimé)"
                valeur = "5.0 (estimé)"
        
        try:
            # Extraire la valeur numérique, en ignorant le texte "(estimé)" si présent
            valeur_str = str(valeur) if pd.notna(valeur) and valeur != "" else ""
            valeur_num = None
            est_estime = False
            
            if "(estimé)" in valeur_str:
                est_estime = True
                valeur_str = valeur_str.replace("(estimé)", "").strip()
                
            try:
                valeur_num = float(valeur_str) if valeur_str else None
            except ValueError:
                valeur_num = None
            
            # Logique d'évaluation et de conformité
            if valeur_num is None:
                df.at[index, "Résultat conformité"] = "À évaluer"
                df.at[index, "Score"] = "-"
                df.at[index, "Observations"] = "Données manquantes"
            else:
                # Évaluation selon le paramètre
                intervalle = df.at[index, "Intervalle acceptable"]
                
                # Traitement des intervalles avec tiret (min-max)
                if "-" in intervalle or "–" in intervalle:
                    intervalle = intervalle.replace("–", "-")
                    try:
                        min_val, max_val = map(float, intervalle.split("-"))
                        if min_val <= valeur_num <= max_val:
                            df.at[index, "Résultat conformité"] = "Conforme" + (" (estimé)" if est_estime else "")
                            df.at[index, "Score"] = "1" if not est_estime else "0.8"
                            df.at[index, "Observations"] = "Bon" + (" (basé sur estimation)" if est_estime else "")
                        else:
                            df.at[index, "Résultat conformité"] = "Non conforme" + (" (estimé)" if est_estime else "")
                            df.at[index, "Score"] = "0"
                            
                            # Observations spécifiques selon le paramètre
                            if "ph" in parametre:
                                if valeur_num < min_val:
                                    df.at[index, "Observations"] = "Trop acide" + (" (basé sur estimation)" if est_estime else "")
                                else:
                                    df.at[index, "Observations"] = "Trop basique" + (" (basé sur estimation)" if est_estime else "")
                            elif "température" in parametre:
                                if valeur_num < min_val:
                                    df.at[index, "Observations"] = "Température basse" + (" (basé sur estimation)" if est_estime else "")
                                else:
                                    df.at[index, "Observations"] = "Température élevée" + (" (basé sur estimation)" if est_estime else "")
                            else:
                                df.at[index, "Observations"] = "Hors intervalle" + (" (basé sur estimation)" if est_estime else "")
                    except ValueError:
                        df.at[index, "Résultat conformité"] = "À évaluer"
                        df.at[index, "Score"] = "-"
                        df.at[index, "Observations"] = "Format d'intervalle incorrect"
                
                # Traitement des intervalles avec < ou >
                elif "<" in intervalle or "≤" in intervalle:
                    try:
                        max_val = float(intervalle.replace("<", "").replace("≤", "").strip())
                        if valeur_num <= max_val:
                            df.at[index, "Résultat conformité"] = "Conforme" + (" (estimé)" if est_estime else "")
                            df.at[index, "Score"] = "1" if not est_estime else "0.8"
                            df.at[index, "Observations"] = "Bon" + (" (basé sur estimation)" if est_estime else "")
                        else:
                            df.at[index, "Résultat conformité"] = "Non conforme" + (" (estimé)" if est_estime else "")
                            df.at[index, "Score"] = "0"
                            
                            # Observations spécifiques selon le paramètre
                            if "conductivité" in parametre:
                                df.at[index, "Observations"] = "Salinité élevée" + (" (basé sur estimation)" if est_estime else "")
                            elif "turbidité" in parametre:
                                df.at[index, "Observations"] = "Eau troublée" + (" (basé sur estimation)" if est_estime else "")
                            elif "dbo" in parametre or "dco" in parametre:
                                df.at[index, "Observations"] = "Pollution organique élevée" + (" (basé sur estimation)" if est_estime else "")
                            elif "nitrates" in parametre or "phosphates" in parametre:
                                df.at[index, "Observations"] = "Concentration élevée en nutriments" + (" (basé sur estimation)" if est_estime else "")
                            else:
                                df.at[index, "Observations"] = "Valeur élevée" + (" (basé sur estimation)" if est_estime else "")
                    except ValueError:
                        df.at[index, "Résultat conformité"] = "À évaluer"
                        df.at[index, "Score"] = "-"
                        df.at[index, "Observations"] = "Format d'intervalle incorrect"
                
                elif ">" in intervalle or "≥" in intervalle:
                    try:
                        min_val = float(intervalle.replace(">", "").replace("≥", "").strip())
                        if valeur_num >= min_val:
                            df.at[index, "Résultat conformité"] = "Conforme" + (" (estimé)" if est_estime else "")
                            df.at[index, "Score"] = "1" if not est_estime else "0.8"
                            df.at[index, "Observations"] = "Bon" + (" (basé sur estimation)" if est_estime else "")
                        else:
                            df.at[index, "Résultat conformité"] = "Non conforme" + (" (estimé)" if est_estime else "")
                            df.at[index, "Score"] = "0"
                            df.at[index, "Observations"] = "Valeur insuffisante" + (" (basé sur estimation)" if est_estime else "")
                    except ValueError:
                        df.at[index, "Résultat conformité"] = "À évaluer"
                        df.at[index, "Score"] = "-"
                        df.at[index, "Observations"] = "Format d'intervalle incorrect"
                else:
                    df.at[index, "Résultat conformité"] = "À évaluer"
                    df.at[index, "Score"] = "-"
                    df.at[index, "Observations"] = "Intervalle non défini ou format non reconnu"
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du paramètre {parametre}: {str(e)}")
            df.at[index, "Résultat conformité"] = "Non évalué"
            df.at[index, "Score"] = "-"
            df.at[index, "Observations"] = "Erreur d'évaluation: " + str(e)
    
    logger.info("Analyse des données terminée")
    return df