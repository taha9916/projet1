import pandas as pd
import numpy as np
import json
import os
import logging
from cache_manager import cached

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@cached(expiry=86400)  # Cache valide pendant 24 heures
def load_thresholds(country="morocco"):
    """Charge les seuils spécifiques à un pays à partir d'un fichier JSON.
    
    Args:
        country (str): Le pays pour lequel charger les seuils (par défaut: morocco)
        
    Returns:
        dict: Dictionnaire contenant les seuils pour différents paramètres environnementaux
    """
    try:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"thresholds_{country}.json")
        logger.info(f"Chargement des seuils depuis {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            thresholds = json.load(f)
            
        logger.info(f"Seuils chargés avec succès: {len(thresholds)} catégories trouvées")
        return thresholds
    except Exception as e:
        logger.error(f"Erreur lors du chargement des seuils: {e}")
        return None

def calculate_environmental_risk_score_morocco(df, country="morocco"):
    """Calcule un score de risque environnemental basé sur les données disponibles et les seuils spécifiques au pays.
    
    Args:
        df (pandas.DataFrame): DataFrame contenant les données environnementales
        country (str): Le pays pour lequel calculer les scores (par défaut: morocco)
        
    Returns:
        pandas.DataFrame: DataFrame avec les scores de risque calculés
    """
    # Charger les seuils spécifiques au pays
    thresholds = load_thresholds(country)
    if not thresholds:
        logger.warning(f"Impossible de charger les seuils pour {country}, utilisation des seuils par défaut")
        return calculate_environmental_risk_score_default(df)
    
    # Créer une copie du DataFrame
    df_with_score = df.copy()
    
    # Initialiser les scores pour chaque catégorie
    air_scores = []
    water_scores = []
    soil_scores = []
    human_scores = []
    
    # Pour chaque ligne du DataFrame
    for _, row in df.iterrows():
        # Score qualité de l'air (0-10, 10 étant le plus risqué)
        air_score = 0
        air_factors = 0
        
        # PM2.5
        if pd.notna(row.get('pm25')):
            pm25 = row['pm25']
            pm25_thresholds = thresholds['air']['pm25']
            
            if pm25 < pm25_thresholds['low']:
                air_score += 2  # Risque faible
            elif pm25 < pm25_thresholds['medium']:
                air_score += 5  # Risque moyen
            else:
                air_score += 10  # Risque élevé
            air_factors += 1
        
        # PM10
        if pd.notna(row.get('pm10')):
            pm10 = row['pm10']
            pm10_thresholds = thresholds['air']['pm10']
            
            if pm10 < pm10_thresholds['low']:
                air_score += 2  # Risque faible
            elif pm10 < pm10_thresholds['medium']:
                air_score += 5  # Risque moyen
            else:
                air_score += 10  # Risque élevé
            air_factors += 1
        
        # NO2
        if pd.notna(row.get('no2')):
            no2 = row['no2']
            no2_thresholds = thresholds['air']['no2']
            
            if no2 < no2_thresholds['low']:
                air_score += 2  # Risque faible
            elif no2 < no2_thresholds['medium']:
                air_score += 5  # Risque moyen
            else:
                air_score += 10  # Risque élevé
            air_factors += 1
        
        # O3
        if pd.notna(row.get('o3')):
            o3 = row['o3']
            o3_thresholds = thresholds['air']['o3']
            
            if o3 < o3_thresholds['low']:
                air_score += 2  # Risque faible
            elif o3 < o3_thresholds['medium']:
                air_score += 5  # Risque moyen
            else:
                air_score += 10  # Risque élevé
            air_factors += 1
        
        # Indice qualité air
        if pd.notna(row.get('indice_qualite_air')):
            aqi = row['indice_qualite_air']
            air_score += aqi * 2  # Échelle 1-5 → 2-10
            air_factors += 1
        
        # Calculer le score moyen pour l'air
        air_score = air_score / air_factors if air_factors > 0 else np.nan
        air_scores.append(air_score)
        
        # Score eau
        water_score = 0
        water_factors = 0
        
        # Humidité
        if pd.notna(row.get('humidite')):
            humidity = row['humidite']
            humidity_thresholds = thresholds['water']['humidite']
            
            if humidity < humidity_thresholds['low']:
                water_score += 8  # Très sec = risque élevé
            elif humidity > humidity_thresholds['medium']:
                water_score += 6  # Très humide = risque modéré
            else:
                water_score += 3  # Normal = risque faible
            water_factors += 1
        
        # Points d'eau à proximité
        if pd.notna(row.get('points_eau_proximite')):
            water_points = row['points_eau_proximite']
            water_points_thresholds = thresholds['water']['points_eau_proximite']
            
            if water_points > water_points_thresholds['medium']:
                water_score += 8  # Nombreux points d'eau = risque élevé
            elif water_points > water_points_thresholds['low']:
                water_score += 5  # Quelques points d'eau = risque modéré
            else:
                water_score += 2  # Pas de point d'eau = risque faible
            water_factors += 1
        
        # Calculer le score moyen pour l'eau
        water_score = water_score / water_factors if water_factors > 0 else np.nan
        water_scores.append(water_score)
        
        # Score sol
        soil_score = 0
        soil_factors = 0
        
        # pH sol
        if pd.notna(row.get('ph_sol')):
            ph = row['ph_sol']
            ph_thresholds = thresholds['soil']['ph_sol']
            
            if ph < ph_thresholds['medium_min'] or ph > ph_thresholds['medium_max']:
                soil_score += 8  # pH extrême = risque élevé
            elif ph < ph_thresholds['low_min'] or ph > ph_thresholds['low_max']:
                soil_score += 5  # pH modérément extrême = risque modéré
            else:
                soil_score += 2  # pH normal = risque faible
            soil_factors += 1
        
        # Carbone organique
        if pd.notna(row.get('carbone_organique')):
            organic_carbon = row['carbone_organique']
            organic_carbon_thresholds = thresholds['soil']['carbone_organique']
            
            if organic_carbon < organic_carbon_thresholds['high']:
                soil_score += 8  # Très peu de carbone = sol pauvre
            elif organic_carbon < organic_carbon_thresholds['medium']:
                soil_score += 5  # Peu de carbone = sol modérément fertile
            else:
                soil_score += 2  # Beaucoup de carbone = sol fertile
            soil_factors += 1
        
        # Argile
        if pd.notna(row.get('argile')):
            clay = row['argile']
            clay_thresholds = thresholds['soil']['argile']
            
            if clay > clay_thresholds['medium']:
                soil_score += 7  # Sol très argileux = drainage faible
            elif clay > clay_thresholds['low']:
                soil_score += 4  # Sol modérément argileux
            else:
                soil_score += 2  # Sol peu argileux = bon drainage
            soil_factors += 1
        
        # Sable
        if pd.notna(row.get('sable')):
            sand = row['sable']
            sand_thresholds = thresholds['soil']['sable']
            
            if sand > sand_thresholds['medium']:
                soil_score += 6  # Sol très sableux = faible rétention d'eau
            elif sand > sand_thresholds['low']:
                soil_score += 4  # Sol modérément sableux
            else:
                soil_score += 2  # Sol peu sableux = bonne rétention d'eau
            soil_factors += 1
        
        # Calculer le score moyen pour le sol
        soil_score = soil_score / soil_factors if soil_factors > 0 else np.nan
        soil_scores.append(soil_score)
        
        # Score facteurs humains
        human_score = 0
        human_factors = 0
        
        # Habitations à proximité
        if pd.notna(row.get('habitations_proximite')):
            habitations = row['habitations_proximite']
            habitations_thresholds = thresholds['human']['habitations_proximite']
            
            if habitations > habitations_thresholds['medium']:
                human_score += 9  # Nombreuses habitations = risque élevé
            elif habitations > habitations_thresholds['low']:
                human_score += 6  # Quelques habitations = risque modéré
            else:
                human_score += 3  # Peu d'habitations = risque faible
            human_factors += 1
        
        # Zones industrielles à proximité
        if pd.notna(row.get('zones_industrielles_proximite')):
            industrial_zones = row['zones_industrielles_proximite']
            industrial_zones_thresholds = thresholds['human']['zones_industrielles_proximite']
            
            if industrial_zones > industrial_zones_thresholds['medium']:
                human_score += 10  # Nombreuses zones industrielles = risque très élevé
            elif industrial_zones > industrial_zones_thresholds['low']:
                human_score += 7  # Quelques zones industrielles = risque élevé
            else:
                human_score += 3  # Pas de zone industrielle = risque faible
            human_factors += 1
        
        # Calculer le score moyen pour les facteurs humains
        human_score = human_score / human_factors if human_factors > 0 else np.nan
        human_scores.append(human_score)
    
    # Ajouter les scores au DataFrame
    df_with_score['score_air'] = air_scores
    df_with_score['score_eau'] = water_scores
    df_with_score['score_sol'] = soil_scores
    df_with_score['score_humain'] = human_scores
    
    # Calculer le score global (moyenne des scores disponibles)
    df_with_score['score_global'] = df_with_score[['score_air', 'score_eau', 'score_sol', 'score_humain']].mean(axis=1)
    
    # Déterminer le niveau de risque global
    risk_levels = thresholds['risk_levels']['global']
    
    def get_risk_level(score):
        if pd.isna(score):
            return "Indéterminé"
        elif score < risk_levels['low']:
            return "Faible"
        elif score < risk_levels['medium']:
            return "Moyen"
        else:
            return "Élevé"
    
    df_with_score['niveau_risque'] = df_with_score['score_global'].apply(get_risk_level)
    
    return df_with_score

# Fonction de repli utilisant les seuils par défaut
def calculate_environmental_risk_score_default(df):
    """Calcule un score de risque environnemental basé sur les données disponibles et des seuils par défaut."""
    # Cette fonction est identique à la fonction originale calculate_environmental_risk_score
    # Elle est utilisée comme repli si les seuils spécifiques au pays ne peuvent pas être chargés
    # ...
    logger.warning("Utilisation des seuils par défaut pour le calcul des scores de risque")
    return df  # À remplacer par l'implémentation réelle

def test_risk_scores_morocco():
    """Teste le calcul des scores de risque avec les seuils spécifiques au Maroc."""
    # Créer un DataFrame de test
    data = {
        'pm25': [10, 25, 40],
        'pm10': [15, 40, 60],
        'no2': [30, 150, 250],
        'o3': [90, 150, 200],
        'indice_qualite_air': [1, 3, 5],
        'humidite': [20, 50, 90],
        'points_eau_proximite': [0, 3, 8],
        'ph_sol': [7.0, 5.8, 9.0],
        'carbone_organique': [3, 1.5, 0.5],
        'argile': [15, 30, 50],
        'sable': [30, 60, 80],
        'habitations_proximite': [5, 50, 200],
        'zones_industrielles_proximite': [0, 3, 10]
    }
    
    df = pd.DataFrame(data)
    
    # Calculer les scores de risque
    df_with_score = calculate_environmental_risk_score_morocco(df)
    
    # Afficher les résultats
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 200)
    
    print("\nDataFrame avec scores de risque:")
    print(df_with_score)
    
    print("\nRésumé des scores de risque:")
    for i, row in df_with_score.iterrows():
        print(f"Site {i+1}:")
        print(f"  Score air: {row['score_air']:.2f}/10")
        print(f"  Score eau: {row['score_eau']:.2f}/10")
        print(f"  Score sol: {row['score_sol']:.2f}/10")
        print(f"  Score facteurs humains: {row['score_humain']:.2f}/10")
        print(f"  Score global: {row['score_global']:.2f}/10")
        print(f"  Niveau de risque: {row['niveau_risque']}")

if __name__ == "__main__":
    test_risk_scores_morocco()