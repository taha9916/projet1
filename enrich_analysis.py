import os
import sys
import json
import pandas as pd
from datetime import datetime

# Importer les fonctions du script d'exportation
from export_api_to_excel import (
    load_api_config,
    get_coordinates,
    get_weather_data,
    get_air_quality_data,
    get_soil_data,
    get_nearby_features,
    get_world_bank_data,
    collect_environmental_data
)

def enrich_dataframe_with_environmental_data(df, location_column=None, lat_column=None, lon_column=None, country_code="MA"):
    """
    Enrichit un DataFrame avec des données environnementales.
    
    Args:
        df (pandas.DataFrame): Le DataFrame à enrichir
        location_column (str, optional): Nom de la colonne contenant les noms de lieux
        lat_column (str, optional): Nom de la colonne contenant les latitudes
        lon_column (str, optional): Nom de la colonne contenant les longitudes
        country_code (str, optional): Code pays pour les données de la Banque mondiale
    
    Returns:
        pandas.DataFrame: Le DataFrame enrichi avec les données environnementales
    """
    # Vérifier qu'au moins une méthode de localisation est fournie
    if location_column is None and (lat_column is None or lon_column is None):
        print("Erreur: Vous devez fournir soit une colonne de lieu, soit des colonnes de latitude et longitude.")
        return df
    
    # Charger la configuration des API
    config = load_api_config()
    
    # Créer une copie du DataFrame pour ne pas modifier l'original
    enriched_df = df.copy()
    
    # Colonnes pour les données environnementales
    env_columns = {
        # Météo
        "temperature": [],
        "humidite": [],
        "pression": [],
        "conditions_meteo": [],
        "vitesse_vent": [],
        
        # Qualité de l'air
        "pm25": [],
        "pm10": [],
        "no2": [],
        "o3": [],
        "indice_qualite_air": [],
        
        # Sol
        "ph_sol": [],
        "carbone_organique": [],
        "argile": [],
        "sable": [],
        
        # Caractéristiques environnementales
        "points_eau_proximite": [],
        "espaces_verts_proximite": [],
        "habitations_proximite": [],
        "zones_industrielles_proximite": [],
        
        # Données nationales
        "population_pays": [],
        "acces_eau": [],
        "couverture_forestiere": []
    }
    
    # Pour chaque ligne du DataFrame
    for index, row in df.iterrows():
        # Déterminer la localisation
        location = None
        lat, lon = None, None
        
        if location_column is not None:
            location = row[location_column]
        
        if lat_column is not None and lon_column is not None:
            try:
                lat = float(row[lat_column])
                lon = float(row[lon_column])
            except (ValueError, TypeError):
                pass
        
        # Si on a un nom de lieu mais pas de coordonnées, essayer de les obtenir
        if location is not None and (lat is None or lon is None):
            lat, lon = get_coordinates(location, country_code, config)
        
        # Si on a des coordonnées, collecter les données environnementales
        if lat is not None and lon is not None:
            env_data = collect_environmental_data((lat, lon), country_code)
            
            # Remplir les colonnes avec les données environnementales
            env_columns["temperature"].append(env_data.get("Température", (None, ""))[0])
            env_columns["humidite"].append(env_data.get("Humidité", (None, ""))[0])
            env_columns["pression"].append(env_data.get("Pression", (None, ""))[0])
            env_columns["conditions_meteo"].append(env_data.get("Conditions", (None, ""))[0])
            env_columns["vitesse_vent"].append(env_data.get("Vent", (None, ""))[0])
            
            env_columns["pm25"].append(env_data.get("PM2.5", (None, ""))[0])
            env_columns["pm10"].append(env_data.get("PM10", (None, ""))[0])
            env_columns["no2"].append(env_data.get("NO2", (None, ""))[0])
            env_columns["o3"].append(env_data.get("O3", (None, ""))[0])
            env_columns["indice_qualite_air"].append(env_data.get("Indice qualité air", (None, ""))[0])
            
            env_columns["ph_sol"].append(env_data.get("pH sol", (None, ""))[0])
            env_columns["carbone_organique"].append(env_data.get("Carbone organique", (None, ""))[0])
            env_columns["argile"].append(env_data.get("Argile", (None, ""))[0])
            env_columns["sable"].append(env_data.get("Sable", (None, ""))[0])
            
            env_columns["points_eau_proximite"].append(env_data.get("Points d'eau", (None, ""))[0])
            env_columns["espaces_verts_proximite"].append(env_data.get("Espaces verts", (None, ""))[0])
            env_columns["habitations_proximite"].append(env_data.get("Habitations", (None, ""))[0])
            env_columns["zones_industrielles_proximite"].append(env_data.get("Zones industrielles", (None, ""))[0])
            
            env_columns["population_pays"].append(env_data.get("Population", (None, ""))[0])
            env_columns["acces_eau"].append(env_data.get("Accès à l'eau", (None, ""))[0])
            env_columns["couverture_forestiere"].append(env_data.get("Couverture forestière", (None, ""))[0])
        else:
            # Si on n'a pas pu déterminer la localisation, mettre des valeurs nulles
            for column in env_columns:
                env_columns[column].append(None)
    
    # Ajouter les colonnes au DataFrame
    for column_name, values in env_columns.items():
        enriched_df[column_name] = values
    
    return enriched_df

def main():
    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("Usage: python enrich_analysis.py <fichier_excel> [colonne_lieu] [colonne_lat] [colonne_lon] [code_pays] [fichier_sortie]")
        print("Exemple: python enrich_analysis.py resultats.xlsx lieu lat lon MA resultats_enrichis.xlsx")
        return
    
    # Récupérer les arguments
    input_file = sys.argv[1]
    location_column = sys.argv[2] if len(sys.argv) > 2 else None
    lat_column = sys.argv[3] if len(sys.argv) > 3 else None
    lon_column = sys.argv[4] if len(sys.argv) > 4 else None
    country_code = sys.argv[5] if len(sys.argv) > 5 else "MA"
    output_file = sys.argv[6] if len(sys.argv) > 6 else input_file.replace(".xlsx", "_enrichi.xlsx")
    
    # Vérifier que le fichier d'entrée existe
    if not os.path.isfile(input_file):
        print(f"Erreur: Le fichier {input_file} n'existe pas.")
        return
    
    # Lire le fichier Excel
    try:
        df = pd.read_excel(input_file)
        print(f"Fichier {input_file} lu avec succès. {len(df)} lignes trouvées.")
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier Excel: {e}")
        return
    
    # Vérifier que les colonnes spécifiées existent
    if location_column and location_column not in df.columns:
        print(f"Erreur: La colonne {location_column} n'existe pas dans le fichier.")
        return
    
    if lat_column and lat_column not in df.columns:
        print(f"Erreur: La colonne {lat_column} n'existe pas dans le fichier.")
        return
    
    if lon_column and lon_column not in df.columns:
        print(f"Erreur: La colonne {lon_column} n'existe pas dans le fichier.")
        return
    
    # Enrichir le DataFrame avec les données environnementales
    print("Enrichissement des données avec les informations environnementales...")
    enriched_df = enrich_dataframe_with_environmental_data(
        df, location_column, lat_column, lon_column, country_code
    )
    
    # Enregistrer le DataFrame enrichi
    try:
        enriched_df.to_excel(output_file, index=False)
        print(f"Données enrichies enregistrées avec succès dans {output_file}")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement du fichier Excel: {e}")

if __name__ == "__main__":
    main()