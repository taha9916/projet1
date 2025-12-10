import pandas as pd
import sys
import os
import webbrowser

def load_risk_data(file_path):
    """Charge les données d'analyse de risque depuis un fichier Excel."""
    try:
        return pd.read_excel(file_path)
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier {file_path}: {e}")
        sys.exit(1)

def generate_html_report(df, output_html_file):
    """Génère un rapport en format HTML à partir des données d'analyse de risque."""
    try:
        # Créer le contenu du rapport en HTML
        html_content = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport d'Analyse des Risques Environnementaux</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }
        h2 {
            color: #2980b9;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }
        h3 {
            color: #3498db;
        }
        h4 {
            color: #16a085;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px 15px;
            border: 1px solid #ddd;
            text-align: left;
        }
        th {
            background-color: #3498db;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        .risk-high {
            color: #e74c3c;
            font-weight: bold;
        }
        .risk-medium {
            color: #f39c12;
            font-weight: bold;
        }
        .risk-low {
            color: #27ae60;
            font-weight: bold;
        }
        .score-container {
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            margin: 20px 0;
        }
        .score-box {
            width: 22%;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .score-air {
            background-color: #d6eaf8;
            border-left: 5px solid #3498db;
        }
        .score-water {
            background-color: #d1f2eb;
            border-left: 5px solid #1abc9c;
        }
        .score-soil {
            background-color: #fdebd0;
            border-left: 5px solid #f39c12;
        }
        .score-human {
            background-color: #f5eef8;
            border-left: 5px solid #9b59b6;
        }
        .score-global {
            width: 100%;
            background-color: #eaeded;
            border-left: 5px solid #2c3e50;
            text-align: center;
        }
        .factor-list {
            list-style-type: none;
            padding-left: 0;
        }
        .factor-list li {
            padding: 5px 0;
            border-bottom: 1px dotted #ddd;
        }
        .conclusion {
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
            border-left: 5px solid #7f8c8d;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <h1>Rapport d'Analyse des Risques Environnementaux</h1>
    
    <h2>Introduction</h2>
    <p>
        Ce rapport présente une analyse des risques environnementaux pour différents sites. 
        L'analyse est basée sur plusieurs facteurs environnementaux, notamment la qualité de l'air, 
        les conditions de l'eau, les caractéristiques du sol et les facteurs humains.
    </p>
    
    <h2>Résumé des Résultats</h2>
    <p>Le tableau ci-dessous présente un résumé des scores de risque pour chaque site analysé:</p>
    
    <table>
        <thead>
            <tr>
                <th>Site</th>
                <th>Score Air</th>
                <th>Score Eau</th>
                <th>Score Sol</th>
                <th>Score Humain</th>
                <th>Score Global</th>
                <th>Niveau de Risque</th>
            </tr>
        </thead>
        <tbody>
"""
        
        for _, row in df.iterrows():
            site_name = row['nom_site'] if 'nom_site' in row else f"Site {_+1}"
            air_score = f"{row['score_air']:.2f}" if pd.notna(row['score_air']) else "N/A"
            water_score = f"{row['score_eau']:.2f}" if pd.notna(row['score_eau']) else "N/A"
            soil_score = f"{row['score_sol']:.2f}" if pd.notna(row['score_sol']) else "N/A"
            human_score = f"{row['score_humain']:.2f}" if pd.notna(row['score_humain']) else "N/A"
            global_score = f"{row['score_global']:.2f}" if pd.notna(row['score_global']) else "N/A"
            risk_level = row['niveau_risque']
            
            risk_class = ""
            if risk_level == "Élevé":
                risk_class = "risk-high"
            elif risk_level == "Moyen":
                risk_class = "risk-medium"
            else:  # Faible
                risk_class = "risk-low"
            
            html_content += f"""            <tr>
                <td>{site_name}</td>
                <td>{air_score}</td>
                <td>{water_score}</td>
                <td>{soil_score}</td>
                <td>{human_score}</td>
                <td>{global_score}</td>
                <td class="{risk_class}">{risk_level}</td>
            </tr>
"""
        
        html_content += """        </tbody>
    </table>
    
    <h2>Analyse Détaillée par Site</h2>
"""
        
        for _, row in df.iterrows():
            site_name = row['nom_site'] if 'nom_site' in row else f"Site {_+1}"
            html_content += f"""    <h3>{site_name}</h3>
    
    <h4>Informations Générales</h4>
    <ul class="factor-list">
"""
            
            # Informations générales sur le site
            if 'type' in row and pd.notna(row['type']):
                html_content += f"        <li><strong>Type de site</strong>: {row['type']}</li>\n"
            if 'risque_initial' in row and pd.notna(row['risque_initial']):
                html_content += f"        <li><strong>Risque initial évalué</strong>: {row['risque_initial']}</li>\n"
            if 'latitude' in row and 'longitude' in row and pd.notna(row['latitude']) and pd.notna(row['longitude']):
                html_content += f"        <li><strong>Coordonnées</strong>: {row['latitude']}, {row['longitude']}</li>\n"
            
            html_content += """    </ul>
    
    <div class="score-container">
"""
            
            # Score qualité de l'air
            air_score_display = f"{row['score_air']:.2f}" if pd.notna(row['score_air']) else "N/A"
            html_content += f"""        <div class="score-box score-air">
            <h4>Qualité de l'Air</h4>
            <p><strong>Score</strong>: {air_score_display} / 10</p>
            <ul class="factor-list">
"""
            
            air_factors = []
            if 'temperature' in row and pd.notna(row['temperature']):
                html_content += f"                <li><strong>Température</strong>: {row['temperature']} °C</li>\n"
            if 'humidite' in row and pd.notna(row['humidite']):
                html_content += f"                <li><strong>Humidité</strong>: {row['humidite']} %</li>\n"
            if 'pression' in row and pd.notna(row['pression']):
                html_content += f"                <li><strong>Pression</strong>: {row['pression']} hPa</li>\n"
            if 'conditions_meteo' in row and pd.notna(row['conditions_meteo']):
                html_content += f"                <li><strong>Conditions météo</strong>: {row['conditions_meteo']}</li>\n"
            if 'vitesse_vent' in row and pd.notna(row['vitesse_vent']):
                html_content += f"                <li><strong>Vitesse du vent</strong>: {row['vitesse_vent']} m/s</li>\n"
            if 'pm25' in row and pd.notna(row['pm25']):
                html_content += f"                <li><strong>PM2.5</strong>: {row['pm25']} μg/m³</li>\n"
            if 'pm10' in row and pd.notna(row['pm10']):
                html_content += f"                <li><strong>PM10</strong>: {row['pm10']} μg/m³</li>\n"
            if 'no2' in row and pd.notna(row['no2']):
                html_content += f"                <li><strong>NO2</strong>: {row['no2']} μg/m³</li>\n"
            if 'o3' in row and pd.notna(row['o3']):
                html_content += f"                <li><strong>O3</strong>: {row['o3']} μg/m³</li>\n"
            if 'indice_qualite_air' in row and pd.notna(row['indice_qualite_air']):
                html_content += f"                <li><strong>Indice qualité air</strong>: {row['indice_qualite_air']} sur 5</li>\n"
            
            html_content += """            </ul>
        </div>
"""
            
            # Score eau
            water_score_display = f"{row['score_eau']:.2f}" if pd.notna(row['score_eau']) else "N/A"
            html_content += f"""        <div class="score-box score-water">
            <h4>Conditions de l'Eau</h4>
            <p><strong>Score</strong>: {water_score_display} / 10</p>
            <ul class="factor-list">
"""
            
            water_factors = []
            if 'points_eau_proximite' in row and pd.notna(row['points_eau_proximite']):
                html_content += f"                <li><strong>Points d'eau à proximité</strong>: {row['points_eau_proximite']}</li>\n"
            if 'acces_eau' in row and pd.notna(row['acces_eau']):
                html_content += f"                <li><strong>Accès à l'eau</strong>: {row['acces_eau']} %</li>\n"
            
            html_content += """            </ul>
        </div>
"""
            
            # Score sol
            soil_score_display = f"{row['score_sol']:.2f}" if pd.notna(row['score_sol']) else "N/A"
            html_content += f"""        <div class="score-box score-soil">
            <h4>Caractéristiques du Sol</h4>
            <p><strong>Score</strong>: {soil_score_display} / 10</p>
            <ul class="factor-list">
"""
            
            soil_factors = []
            if 'ph_sol' in row and pd.notna(row['ph_sol']):
                html_content += f"                <li><strong>pH du sol</strong>: {row['ph_sol']}</li>\n"
            if 'carbone_organique' in row and pd.notna(row['carbone_organique']):
                html_content += f"                <li><strong>Carbone organique</strong>: {row['carbone_organique']} g/kg</li>\n"
            if 'argile' in row and pd.notna(row['argile']):
                html_content += f"                <li><strong>Argile</strong>: {row['argile']} %</li>\n"
            if 'sable' in row and pd.notna(row['sable']):
                html_content += f"                <li><strong>Sable</strong>: {row['sable']} %</li>\n"
            
            html_content += """            </ul>
        </div>
"""
            
            # Score milieu humain
            human_score_display = f"{row['score_humain']:.2f}" if pd.notna(row['score_humain']) else "N/A"
            html_content += f"""        <div class="score-box score-human">
            <h4>Facteurs Humains</h4>
            <p><strong>Score</strong>: {human_score_display} / 10</p>
            <ul class="factor-list">
"""
            
            human_factors = []
            if 'habitations_proximite' in row and pd.notna(row['habitations_proximite']):
                html_content += f"                <li><strong>Habitations à proximité</strong>: {row['habitations_proximite']}</li>\n"
            if 'zones_industrielles_proximite' in row and pd.notna(row['zones_industrielles_proximite']):
                html_content += f"                <li><strong>Zones industrielles à proximité</strong>: {row['zones_industrielles_proximite']}</li>\n"
            if 'population_pays' in row and pd.notna(row['population_pays']):
                html_content += f"                <li><strong>Population du pays</strong>: {row['population_pays']}</li>\n"
            if 'couverture_forestiere' in row and pd.notna(row['couverture_forestiere']):
                html_content += f"                <li><strong>Couverture forestière</strong>: {row['couverture_forestiere']} %</li>\n"
            
            html_content += """            </ul>
        </div>
"""
            
            # Score global
            global_score_display = f"{row['score_global']:.2f}" if pd.notna(row['score_global']) else "N/A"
            risk_class = ""
            if row['niveau_risque'] == "Élevé":
                risk_class = "risk-high"
            elif row['niveau_risque'] == "Moyen":
                risk_class = "risk-medium"
            else:  # Faible
                risk_class = "risk-low"
            
            html_content += f"""        <div class="score-box score-global">
            <h4>Score Global</h4>
            <p><strong>Score</strong>: {global_score_display} / 10</p>
            <p><strong>Niveau de Risque</strong>: <span class="{risk_class}">{row['niveau_risque']}</span></p>
        </div>
    </div>
    
    <div class="conclusion">
        <h4>Conclusion pour {site_name}</h4>
        <p>
            Le site <strong>{site_name}</strong> présente un niveau de risque environnemental <span class="{risk_class}">{row['niveau_risque'].lower()}</span> 
            avec un score global de <strong>{global_score_display}</strong> sur 10. 
"""
            
            if row['niveau_risque'] == 'Élevé':
                html_content += "Des mesures d'atténuation significatives sont recommandées pour réduire les risques environnementaux."
            elif row['niveau_risque'] == 'Moyen':
                html_content += "Une surveillance régulière et certaines mesures d'atténuation sont recommandées."
            else:  # Faible
                html_content += "Le site présente un risque environnemental relativement faible, mais une surveillance de routine est recommandée."
            
            html_content += """        </p>
    </div>
"""
        
        # Ajouter une conclusion générale
        high_risk_sites = df[df['niveau_risque'] == 'Élevé']['nom_site'].tolist() if 'nom_site' in df else []
        medium_risk_sites = df[df['niveau_risque'] == 'Moyen']['nom_site'].tolist() if 'nom_site' in df else []
        low_risk_sites = df[df['niveau_risque'] == 'Faible']['nom_site'].tolist() if 'nom_site' in df else []
        
        html_content += f"""    <h2>Conclusion Générale</h2>
    
    <p>Sur les {len(df)} sites analysés:</p>
    <ul>
        <li><strong>{len(high_risk_sites)}</strong> sites présentent un risque élevé</li>
        <li><strong>{len(medium_risk_sites)}</strong> sites présentent un risque moyen</li>
        <li><strong>{len(low_risk_sites)}</strong> sites présentent un risque faible</li>
    </ul>
    
    <p>Les recommandations générales sont les suivantes:</p>
    <ul>
"""
        
        if high_risk_sites:
            html_content += "        <li>Pour les sites à risque élevé, mettre en place des mesures d'atténuation immédiates et un plan de surveillance renforcé</li>\n"
        if medium_risk_sites:
            html_content += "        <li>Pour les sites à risque moyen, établir un plan de surveillance régulier et identifier les facteurs de risque spécifiques à améliorer</li>\n"
        if low_risk_sites:
            html_content += "        <li>Pour les sites à risque faible, maintenir une surveillance de routine et documenter tout changement significatif</li>\n"
        
        html_content += """    </ul>
</body>
</html>
"""
        
        # Écrire le contenu dans un fichier HTML
        with open(output_html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Rapport HTML généré avec succès: {output_html_file}")
        return True
    except Exception as e:
        print(f"Erreur lors de la génération du rapport HTML: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("Usage: python generate_html_report.py <fichier_excel> [dossier_sortie]")
        print("Exemple: python generate_html_report.py resultats/analyse_risques.xlsx rapports")
        sys.exit(1)
    
    # Récupérer les arguments
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "rapports"
    
    # Créer le répertoire de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Charger les données
        print(f"Chargement des données depuis {input_file}...")
        df = load_risk_data(input_file)
        print(f"Données chargées avec succès. {len(df)} lignes trouvées.")
        
        # Générer le rapport HTML
        html_file = os.path.join(output_dir, "rapport_risques.html")
        if generate_html_report(df, html_file):
            print(f"\nRapport d'analyse de risque généré avec succès en format HTML: {html_file}")
            
            # Ouvrir le rapport dans le navigateur par défaut
            try:
                print("Ouverture du rapport dans le navigateur...")
                webbrowser.open('file://' + os.path.abspath(html_file))
            except Exception as e:
                print(f"Impossible d'ouvrir le rapport dans le navigateur: {e}")
                print(f"Vous pouvez ouvrir manuellement le fichier: {os.path.abspath(html_file)}")
        else:
            print("\nLa génération du rapport a échoué.")
    except Exception as e:
        print(f"Erreur lors de l'exécution du script: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()