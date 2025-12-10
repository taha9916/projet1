import pandas as pd
import numpy as np
import sys
import os

def load_data(file_path):
    """Charge les données depuis un fichier Excel."""
    try:
        return pd.read_excel(file_path)
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier {file_path}: {e}")
        sys.exit(1)

def calculate_environmental_risk_score(df):
    """Calcule un score de risque environnemental basé sur les données disponibles."""
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
        
        # PM2.5 (0-35+ μg/m³)
        if pd.notna(row.get('pm25')):
            pm25 = row['pm25']
            if pm25 < 12:
                air_score += 2
            elif pm25 < 35:
                air_score += 5
            else:
                air_score += 10
            air_factors += 1
        
        # PM10 (0-50+ μg/m³)
        if pd.notna(row.get('pm10')):
            pm10 = row['pm10']
            if pm10 < 20:
                air_score += 2
            elif pm10 < 50:
                air_score += 5
            else:
                air_score += 10
            air_factors += 1
        
        # NO2 (0-200+ μg/m³)
        if pd.notna(row.get('no2')):
            no2 = row['no2']
            if no2 < 40:
                air_score += 2
            elif no2 < 200:
                air_score += 5
            else:
                air_score += 10
            air_factors += 1
        
        # O3 (0-100+ μg/m³)
        if pd.notna(row.get('o3')):
            o3 = row['o3']
            if o3 < 100:
                air_score += 2
            elif o3 < 180:
                air_score += 5
            else:
                air_score += 10
            air_factors += 1
        
        # Indice qualité air (1-5)
        if pd.notna(row.get('indice_qualite_air')):
            aqi = row['indice_qualite_air']
            air_score += aqi * 2  # Échelle 1-5 → 2-10
            air_factors += 1
        
        # Calculer le score moyen pour l'air
        air_score = air_score / air_factors if air_factors > 0 else np.nan
        air_scores.append(air_score)
        
        # Score eau (basé sur les données météo comme proxy)
        water_score = 0
        water_factors = 0
        
        # Humidité (0-100%)
        if pd.notna(row.get('humidite')):
            humidity = row['humidite']
            if humidity < 30:
                water_score += 8  # Très sec = risque élevé
            elif humidity > 80:
                water_score += 6  # Très humide = risque modéré
            else:
                water_score += 3  # Normal = risque faible
            water_factors += 1
        
        # Conditions météo
        if pd.notna(row.get('conditions_meteo')):
            conditions = str(row['conditions_meteo']).lower()
            if 'pluie' in conditions or 'averse' in conditions:
                water_score += 7  # Risque d'inondation
            elif 'orage' in conditions:
                water_score += 9  # Risque d'inondation sévère
            elif 'neige' in conditions:
                water_score += 5  # Risque modéré
            elif 'brouillard' in conditions:
                water_score += 4  # Risque faible à modéré
            else:
                water_score += 2  # Risque faible
            water_factors += 1
        
        # Points d'eau à proximité
        if pd.notna(row.get('points_eau_proximite')):
            water_points = row['points_eau_proximite']
            if water_points > 5:
                water_score += 8  # Nombreux points d'eau = risque élevé
            elif water_points > 0:
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
        
        # pH sol (0-14)
        if pd.notna(row.get('ph_sol')):
            ph = row['ph_sol']
            if ph < 5.5 or ph > 8.5:
                soil_score += 8  # pH extrême = risque élevé
            elif ph < 6.0 or ph > 8.0:
                soil_score += 5  # pH modérément extrême = risque modéré
            else:
                soil_score += 2  # pH normal = risque faible
            soil_factors += 1
        
        # Carbone organique
        if pd.notna(row.get('carbone_organique')):
            organic_carbon = row['carbone_organique']
            if organic_carbon < 1:
                soil_score += 8  # Très peu de carbone = sol pauvre
            elif organic_carbon < 2:
                soil_score += 5  # Peu de carbone = sol modérément fertile
            else:
                soil_score += 2  # Beaucoup de carbone = sol fertile
            soil_factors += 1
        
        # Argile
        if pd.notna(row.get('argile')):
            clay = row['argile']
            if clay > 40:
                soil_score += 7  # Beaucoup d'argile = drainage faible
            elif clay > 20:
                soil_score += 4  # Quantité moyenne d'argile
            else:
                soil_score += 2  # Peu d'argile
            soil_factors += 1
        
        # Sable
        if pd.notna(row.get('sable')):
            sand = row['sable']
            if sand > 70:
                soil_score += 6  # Beaucoup de sable = faible rétention d'eau
            elif sand > 40:
                soil_score += 3  # Quantité moyenne de sable
            else:
                soil_score += 2  # Peu de sable
            soil_factors += 1
        
        # Calculer le score moyen pour le sol
        soil_score = soil_score / soil_factors if soil_factors > 0 else np.nan
        soil_scores.append(soil_score)
        
        # Score milieu humain
        human_score = 0
        human_factors = 0
        
        # Habitations à proximité
        if pd.notna(row.get('habitations_proximite')):
            habitations = row['habitations_proximite']
            if habitations > 100:
                human_score += 9  # Nombreuses habitations = risque élevé
            elif habitations > 10:
                human_score += 6  # Quelques habitations = risque modéré
            else:
                human_score += 3  # Peu d'habitations = risque faible
            human_factors += 1
        
        # Zones industrielles à proximité
        if pd.notna(row.get('zones_industrielles_proximite')):
            industrial = row['zones_industrielles_proximite']
            if industrial > 5:
                human_score += 10  # Nombreuses zones industrielles = risque très élevé
            elif industrial > 0:
                human_score += 7  # Quelques zones industrielles = risque élevé
            else:
                human_score += 2  # Pas de zone industrielle = risque faible
            human_factors += 1
        
        # Population du pays
        if pd.notna(row.get('population_pays')):
            population = row['population_pays']
            if population > 50000000:
                human_score += 7  # Population très élevée
            elif population > 10000000:
                human_score += 5  # Population élevée
            else:
                human_score += 3  # Population modérée
            human_factors += 1
        
        # Accès à l'eau
        if pd.notna(row.get('acces_eau')):
            water_access = row['acces_eau']
            if water_access < 50:
                human_score += 9  # Faible accès = risque élevé
            elif water_access < 80:
                human_score += 6  # Accès modéré = risque modéré
            else:
                human_score += 3  # Bon accès = risque faible
            human_factors += 1
        
        # Couverture forestière
        if pd.notna(row.get('couverture_forestiere')):
            forest = row['couverture_forestiere']
            if forest < 10:
                human_score += 8  # Faible couverture = risque élevé
            elif forest < 30:
                human_score += 5  # Couverture modérée = risque modéré
            else:
                human_score += 2  # Bonne couverture = risque faible
            human_factors += 1
        
        # Calculer le score moyen pour le milieu humain
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
    risk_levels = []
    for score in df_with_score['score_global']:
        if pd.isna(score):
            risk_levels.append('Inconnu')
        elif score < 3.5:
            risk_levels.append('Faible')
        elif score < 6.5:
            risk_levels.append('Moyen')
        else:
            risk_levels.append('Élevé')
    
    df_with_score['niveau_risque'] = risk_levels
    
    return df_with_score

def export_risk_analysis(df_with_score, output_file):
    """Exporte les résultats de l'analyse de risque dans un fichier Excel."""
    try:
        # Enregistrer le DataFrame dans un fichier Excel
        df_with_score.to_excel(output_file, index=False)
        print(f"Analyse de risque exportée avec succès dans {output_file}")
        return True
    except Exception as e:
        print(f"Erreur lors de l'exportation de l'analyse de risque: {e}")
        return False

def main():
    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("Usage: python calculate_risk_scores.py <fichier_excel> [dossier_sortie]")
        print("Exemple: python calculate_risk_scores.py sites_enrichis.xlsx resultats")
        sys.exit(1)
    
    # Récupérer les arguments
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "resultats"
    
    # Créer le répertoire de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Charger les données
        print(f"Chargement des données depuis {input_file}...")
        df = load_data(input_file)
        print(f"Données chargées avec succès. {len(df)} lignes trouvées.")
        
        # Calculer les scores de risque
        print("Calcul des scores de risque environnemental...")
        df_with_score = calculate_environmental_risk_score(df)
        print("Scores calculés avec succès.")
        
        # Afficher un résumé des scores
        print("\nRésumé des scores de risque:")
        for i, row in df_with_score.iterrows():
            site_name = row['nom_site'] if 'nom_site' in row else f"Site {i+1}"
            risk_level = row['niveau_risque']
            global_score = row['score_global']
            print(f"- {site_name}: Niveau de risque {risk_level} (Score: {global_score:.2f})")
        
        # Exporter les résultats
        output_file = os.path.join(output_dir, "analyse_risques.xlsx")
        export_risk_analysis(df_with_score, output_file)
        
        print(f"\nAnalyse de risque environnemental terminée. Résultats enregistrés dans {output_file}")
    except Exception as e:
        print(f"Erreur lors de l'exécution du script: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()