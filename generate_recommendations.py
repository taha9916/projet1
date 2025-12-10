import pandas as pd
import sys
import os

def load_risk_data(file_path):
    """Charge les données d'analyse de risque depuis un fichier Excel."""
    try:
        return pd.read_excel(file_path)
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier {file_path}: {e}")
        sys.exit(1)

def generate_recommendations(df):
    """Génère des recommandations spécifiques basées sur les scores de risque."""
    # Créer une copie du DataFrame
    df_with_recommendations = df.copy()
    
    # Initialiser les colonnes de recommandations
    df_with_recommendations['recommandations_air'] = ''
    df_with_recommendations['recommandations_eau'] = ''
    df_with_recommendations['recommandations_sol'] = ''
    df_with_recommendations['recommandations_humain'] = ''
    df_with_recommendations['recommandations_generales'] = ''
    df_with_recommendations['priorite_action'] = ''
    
    # Pour chaque ligne du DataFrame
    for idx, row in df_with_recommendations.iterrows():
        # Recommandations pour l'air
        air_recommendations = []
        if pd.notna(row.get('score_air')):
            air_score = row['score_air']
            if air_score > 6.5:
                air_recommendations.append("Mettre en place un système de surveillance continue de la qualité de l'air")
                air_recommendations.append("Réduire les émissions de particules fines et de polluants atmosphériques")
                air_recommendations.append("Envisager des mesures de filtration de l'air pour les bâtiments à proximité")
            elif air_score > 3.5:
                air_recommendations.append("Surveiller régulièrement les niveaux de pollution atmosphérique")
                air_recommendations.append("Identifier les sources locales de pollution de l'air")
            else:
                air_recommendations.append("Maintenir une surveillance de routine de la qualité de l'air")
        
        # Recommandations pour l'eau
        water_recommendations = []
        if pd.notna(row.get('score_eau')):
            water_score = row['score_eau']
            if water_score > 6.5:
                water_recommendations.append("Mettre en place un plan de gestion des risques d'inondation")
                water_recommendations.append("Améliorer les systèmes de drainage et d'évacuation des eaux")
                water_recommendations.append("Surveiller la qualité des eaux de surface et souterraines")
            elif water_score > 3.5:
                water_recommendations.append("Évaluer les risques liés aux précipitations extrêmes")
                water_recommendations.append("Vérifier l'état des infrastructures de gestion des eaux")
            else:
                water_recommendations.append("Maintenir une surveillance de routine des conditions hydriques")
        
        # Recommandations pour le sol
        soil_recommendations = []
        if pd.notna(row.get('score_sol')):
            soil_score = row['score_sol']
            if soil_score > 6.5:
                soil_recommendations.append("Réaliser une analyse approfondie de la contamination des sols")
                soil_recommendations.append("Mettre en œuvre des mesures de remédiation des sols si nécessaire")
                soil_recommendations.append("Limiter l'érosion et améliorer la structure du sol")
            elif soil_score > 3.5:
                soil_recommendations.append("Surveiller les changements dans la composition du sol")
                soil_recommendations.append("Évaluer les risques d'érosion et de dégradation")
            else:
                soil_recommendations.append("Maintenir des pratiques de gestion durable des sols")
        
        # Recommandations pour le milieu humain
        human_recommendations = []
        if pd.notna(row.get('score_humain')):
            human_score = row['score_humain']
            if human_score > 6.5:
                human_recommendations.append("Élaborer un plan d'urgence pour la protection des populations")
                human_recommendations.append("Renforcer la sensibilisation aux risques environnementaux")
                human_recommendations.append("Mettre en place des zones tampons entre les activités à risque et les habitations")
            elif human_score > 3.5:
                human_recommendations.append("Informer les populations locales des risques potentiels")
                human_recommendations.append("Surveiller l'impact des activités sur les communautés environnantes")
            else:
                human_recommendations.append("Maintenir une communication transparente avec les parties prenantes locales")
        
        # Recommandations générales basées sur le score global
        general_recommendations = []
        if pd.notna(row.get('score_global')):
            global_score = row['score_global']
            if global_score > 6.5:
                general_recommendations.append("Élaborer un plan d'action environnemental complet et urgent")
                general_recommendations.append("Réaliser des audits environnementaux réguliers")
                general_recommendations.append("Envisager des modifications significatives des pratiques actuelles")
                df_with_recommendations.loc[idx, 'priorite_action'] = 'Haute'
            elif global_score > 3.5:
                general_recommendations.append("Développer un programme de surveillance environnementale")
                general_recommendations.append("Identifier et traiter les facteurs de risque les plus importants")
                general_recommendations.append("Revoir les procédures opérationnelles pour minimiser les impacts")
                df_with_recommendations.loc[idx, 'priorite_action'] = 'Moyenne'
            else:
                general_recommendations.append("Maintenir les bonnes pratiques environnementales actuelles")
                general_recommendations.append("Documenter les changements environnementaux")
                general_recommendations.append("Rester informé des nouvelles réglementations et meilleures pratiques")
                df_with_recommendations.loc[idx, 'priorite_action'] = 'Basse'
        
        # Ajouter des recommandations spécifiques basées sur les facteurs de risque
        
        # Facteurs de l'air
        if 'pm25' in row and pd.notna(row['pm25']) and row['pm25'] > 25:
            air_recommendations.append("Réduire l'exposition aux particules fines PM2.5")
        if 'pm10' in row and pd.notna(row['pm10']) and row['pm10'] > 50:
            air_recommendations.append("Mettre en place des mesures pour réduire les niveaux de PM10")
        if 'no2' in row and pd.notna(row['no2']) and row['no2'] > 40:
            air_recommendations.append("Surveiller et réduire les émissions d'oxydes d'azote")
        if 'o3' in row and pd.notna(row['o3']) and row['o3'] > 100:
            air_recommendations.append("Limiter les activités extérieures lors des pics d'ozone")
        
        # Facteurs de l'eau
        if 'humidite' in row and pd.notna(row['humidite']):
            if row['humidite'] < 30:
                water_recommendations.append("Mettre en place des mesures de conservation de l'eau")
            elif row['humidite'] > 80:
                water_recommendations.append("Améliorer la ventilation pour réduire les problèmes liés à l'humidité")
        
        if 'conditions_meteo' in row and pd.notna(row['conditions_meteo']):
            conditions = str(row['conditions_meteo']).lower()
            if 'pluie' in conditions or 'averse' in conditions or 'orage' in conditions:
                water_recommendations.append("Renforcer les systèmes de drainage pour gérer les précipitations")
        
        # Facteurs du sol
        if 'ph_sol' in row and pd.notna(row['ph_sol']):
            if row['ph_sol'] < 5.5:
                soil_recommendations.append("Corriger l'acidité du sol pour améliorer sa qualité")
            elif row['ph_sol'] > 8.5:
                soil_recommendations.append("Traiter l'alcalinité excessive du sol")
        
        if 'carbone_organique' in row and pd.notna(row['carbone_organique']) and row['carbone_organique'] < 1:
            soil_recommendations.append("Augmenter la teneur en matière organique du sol")
        
        # Facteurs humains
        if 'habitations_proximite' in row and pd.notna(row['habitations_proximite']) and row['habitations_proximite'] > 50:
            human_recommendations.append("Évaluer l'impact des activités sur les zones résidentielles à proximité")
        
        if 'zones_industrielles_proximite' in row and pd.notna(row['zones_industrielles_proximite']) and row['zones_industrielles_proximite'] > 0:
            human_recommendations.append("Coordonner les efforts de gestion environnementale avec les zones industrielles voisines")
        
        if 'couverture_forestiere' in row and pd.notna(row['couverture_forestiere']) and row['couverture_forestiere'] < 20:
            human_recommendations.append("Promouvoir la reforestation et la protection des espaces verts")
        
        # Ajouter les recommandations au DataFrame
        df_with_recommendations.loc[idx, 'recommandations_air'] = '\n'.join(air_recommendations)
        df_with_recommendations.loc[idx, 'recommandations_eau'] = '\n'.join(water_recommendations)
        df_with_recommendations.loc[idx, 'recommandations_sol'] = '\n'.join(soil_recommendations)
        df_with_recommendations.loc[idx, 'recommandations_humain'] = '\n'.join(human_recommendations)
        df_with_recommendations.loc[idx, 'recommandations_generales'] = '\n'.join(general_recommendations)
    
    return df_with_recommendations

def export_recommendations(df_with_recommendations, output_file):
    """Exporte les recommandations dans un fichier Excel."""
    try:
        # Créer un writer Excel avec xlsxwriter comme moteur
        writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
        
        # Écrire le DataFrame dans la feuille 'Analyse de risque'
        df_with_recommendations.to_excel(writer, sheet_name='Analyse de risque', index=False)
        
        # Accéder au classeur et à la feuille
        workbook = writer.book
        worksheet = writer.sheets['Analyse de risque']
        
        # Définir les formats
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        wrap_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top'
        })
        
        # Appliquer le format d'en-tête
        for col_num, value in enumerate(df_with_recommendations.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Définir la largeur des colonnes
        worksheet.set_column('A:Z', 15)  # Largeur par défaut
        
        # Colonnes plus larges pour les recommandations
        recommendation_cols = [
            df_with_recommendations.columns.get_loc(col) 
            for col in df_with_recommendations.columns 
            if 'recommandation' in col
        ]
        for col in recommendation_cols:
            worksheet.set_column(col, col, 40, wrap_format)
        
        # Enregistrer le fichier Excel
        writer.close()
        
        print(f"Recommandations exportées avec succès dans {output_file}")
        return True
    except Exception as e:
        print(f"Erreur lors de l'exportation des recommandations: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("Usage: python generate_recommendations.py <fichier_excel> [dossier_sortie]")
        print("Exemple: python generate_recommendations.py resultats/analyse_risques.xlsx resultats")
        sys.exit(1)
    
    # Récupérer les arguments
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "resultats"
    
    # Créer le répertoire de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Charger les données
        print(f"Chargement des données depuis {input_file}...")
        df = load_risk_data(input_file)
        print(f"Données chargées avec succès. {len(df)} lignes trouvées.")
        
        # Générer les recommandations
        print("Génération des recommandations...")
        df_with_recommendations = generate_recommendations(df)
        print("Recommandations générées avec succès.")
        
        # Exporter les recommandations
        output_file = os.path.join(output_dir, "recommandations.xlsx")
        if export_recommendations(df_with_recommendations, output_file):
            print(f"\nRecommandations exportées avec succès dans {output_file}")
        else:
            print("\nL'exportation des recommandations a échoué.")
    except Exception as e:
        print(f"Erreur lors de l'exécution du script: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()