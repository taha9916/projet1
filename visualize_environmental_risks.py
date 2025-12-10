import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
from matplotlib.colors import LinearSegmentedColormap

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

def plot_risk_radar(df_with_score, output_dir):
    """Crée des graphiques radar pour visualiser les risques environnementaux."""
    # Créer le répertoire de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)
    
    # Pour chaque site
    for i, row in df_with_score.iterrows():
        site_name = row['nom_site'] if 'nom_site' in row else f"Site {i+1}"
        
        # Données pour le radar
        categories = ['Air', 'Eau', 'Sol', 'Humain']
        values = [row['score_air'], row['score_eau'], row['score_sol'], row['score_humain']]
        
        # Remplacer les valeurs NaN par 0
        values = [0 if pd.isna(v) else v for v in values]
        
        # Nombre de variables
        N = len(categories)
        
        # Répéter le premier élément pour fermer le polygone
        values += values[:1]
        categories += categories[:1]
        
        # Calculer les angles pour chaque catégorie
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]
        
        # Créer la figure
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        
        # Dessiner le polygone
        ax.plot(angles, values, linewidth=2, linestyle='solid')
        ax.fill(angles, values, alpha=0.25)
        
        # Ajouter les catégories
        plt.xticks(angles[:-1], categories[:-1], size=12)
        
        # Ajouter les niveaux de risque (1-10)
        ax.set_rlabel_position(0)
        plt.yticks([2, 4, 6, 8, 10], ["2 (Très faible)", "4 (Faible)", "6 (Moyen)", "8 (Élevé)", "10 (Très élevé)"], color="grey", size=10)
        plt.ylim(0, 10)
        
        # Ajouter un titre
        risk_level = row['niveau_risque']
        plt.title(f"Profil de risque environnemental - {site_name}\nNiveau de risque global: {risk_level}", size=15, y=1.1)
        
        # Enregistrer la figure
        output_file = os.path.join(output_dir, f"risque_{site_name.replace(' ', '_')}.png")
        plt.savefig(output_file, bbox_inches='tight')
        plt.close()
        
        print(f"Graphique radar créé pour {site_name} et enregistré dans {output_file}")

def plot_risk_map(df_with_score, output_dir):
    """Crée une carte des sites avec leur niveau de risque."""
    # Vérifier que les colonnes nécessaires existent
    if 'latitude' not in df_with_score.columns or 'longitude' not in df_with_score.columns:
        print("Impossible de créer la carte: colonnes latitude/longitude manquantes")
        return
    
    # Créer le répertoire de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)
    
    # Créer la figure
    plt.figure(figsize=(12, 10))
    
    # Définir une palette de couleurs pour les niveaux de risque
    colors = {'Faible': 'green', 'Moyen': 'orange', 'Élevé': 'red', 'Inconnu': 'gray'}
    
    # Tracer chaque site
    for i, row in df_with_score.iterrows():
        site_name = row['nom_site'] if 'nom_site' in row else f"Site {i+1}"
        risk_level = row['niveau_risque']
        color = colors.get(risk_level, 'gray')
        
        # Tracer le point
        plt.scatter(row['longitude'], row['latitude'], c=color, s=100, alpha=0.7, edgecolors='black')
        
        # Ajouter une étiquette
        plt.annotate(site_name, (row['longitude'], row['latitude']), xytext=(5, 5), 
                     textcoords='offset points', fontsize=10)
    
    # Ajouter une légende
    for level, color in colors.items():
        if level in df_with_score['niveau_risque'].values:
            plt.scatter([], [], c=color, s=100, alpha=0.7, edgecolors='black', label=f"Risque {level}")
    plt.legend()
    
    # Ajouter un titre et des étiquettes d'axes
    plt.title("Carte des sites et leur niveau de risque environnemental", fontsize=15)
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Ajuster les limites de la carte pour inclure tous les sites avec une marge
    x_min, x_max = df_with_score['longitude'].min(), df_with_score['longitude'].max()
    y_min, y_max = df_with_score['latitude'].min(), df_with_score['latitude'].max()
    x_margin = (x_max - x_min) * 0.1
    y_margin = (y_max - y_min) * 0.1
    plt.xlim(x_min - x_margin, x_max + x_margin)
    plt.ylim(y_min - y_margin, y_max + y_margin)
    
    # Enregistrer la figure
    output_file = os.path.join(output_dir, "carte_risques.png")
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()
    
    print(f"Carte des risques créée et enregistrée dans {output_file}")

def plot_risk_heatmap(df_with_score, output_dir):
    """Crée une heatmap des différents scores de risque pour chaque site."""
    # Créer le répertoire de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)
    
    # Extraire les données pertinentes
    sites = df_with_score['nom_site'] if 'nom_site' in df_with_score.columns else [f"Site {i+1}" for i in range(len(df_with_score))]
    risk_categories = ['score_air', 'score_eau', 'score_sol', 'score_humain', 'score_global']
    risk_names = ['Air', 'Eau', 'Sol', 'Humain', 'Global']
    
    # Créer une matrice de données pour la heatmap
    data = df_with_score[risk_categories].values
    
    # Créer la figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Créer une palette de couleurs personnalisée (vert à rouge)
    cmap = LinearSegmentedColormap.from_list('risk_cmap', ['green', 'yellow', 'orange', 'red'])
    
    # Créer la heatmap
    im = ax.imshow(data, cmap=cmap, vmin=0, vmax=10)
    
    # Ajouter une barre de couleur
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Score de risque", rotation=-90, va="bottom")
    
    # Ajouter les étiquettes
    ax.set_xticks(np.arange(len(risk_names)))
    ax.set_yticks(np.arange(len(sites)))
    ax.set_xticklabels(risk_names)
    ax.set_yticklabels(sites)
    
    # Rotation des étiquettes de l'axe x
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    # Ajouter les valeurs dans chaque cellule
    for i in range(len(sites)):
        for j in range(len(risk_names)):
            value = data[i, j]
            if pd.notna(value):
                text_color = "white" if value > 5 else "black"
                ax.text(j, i, f"{value:.1f}", ha="center", va="center", color=text_color)
            else:
                ax.text(j, i, "N/A", ha="center", va="center", color="black")
    
    # Ajouter un titre
    ax.set_title("Heatmap des scores de risque environnemental par site", fontsize=15)
    
    # Ajuster la mise en page
    fig.tight_layout()
    
    # Enregistrer la figure
    output_file = os.path.join(output_dir, "heatmap_risques.png")
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()
    
    print(f"Heatmap des risques créée et enregistrée dans {output_file}")

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
        print("Usage: python visualize_environmental_risks.py <fichier_excel> [dossier_sortie]")
        print("Exemple: python visualize_environmental_risks.py sites_enrichis.xlsx visualisations")
        sys.exit(1)
    
    # Récupérer les arguments
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "visualisations"
    
    try:
        # Charger les données
        print(f"Chargement des données depuis {input_file}...")
        df = load_data(input_file)
        print(f"Données chargées avec succès. Colonnes disponibles: {df.columns.tolist()}")
        
        # Calculer les scores de risque
        print("Calcul des scores de risque environnemental...")
        df_with_score = calculate_environmental_risk_score(df)
        print("Scores calculés avec succès.")
        
        # Créer les visualisations
        print("Création des visualisations...")
        try:
            plot_risk_radar(df_with_score, output_dir)
            print("Graphiques radar créés avec succès.")
        except Exception as e:
            print(f"Erreur lors de la création des graphiques radar: {e}")
        
        try:
            plot_risk_map(df_with_score, output_dir)
            print("Carte des risques créée avec succès.")
        except Exception as e:
            print(f"Erreur lors de la création de la carte des risques: {e}")
        
        try:
            plot_risk_heatmap(df_with_score, output_dir)
            print("Heatmap des risques créée avec succès.")
        except Exception as e:
            print(f"Erreur lors de la création de la heatmap: {e}")
        
        # Exporter les résultats
        output_file = os.path.join(output_dir, "analyse_risques.xlsx")
        export_risk_analysis(df_with_score, output_file)
        
        print(f"\nAnalyse de risque environnemental terminée. Résultats enregistrés dans le dossier {output_dir}")
    except Exception as e:
        print(f"Erreur lors de l'exécution du script: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERREUR PRINCIPALE: {e}")
        import traceback
        traceback.print_exc()