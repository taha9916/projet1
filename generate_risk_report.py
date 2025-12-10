import pandas as pd
import sys
import os
import json
import subprocess

def load_risk_data(file_path):
    """Charge les données d'analyse de risque depuis un fichier Excel."""
    try:
        return pd.read_excel(file_path)
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier {file_path}: {e}")
        sys.exit(1)

def generate_markdown_report(df, output_md_file):
    """Génère un rapport en format Markdown à partir des données d'analyse de risque."""
    try:
        # Créer le contenu du rapport en Markdown
        md_content = "# Rapport d'Analyse des Risques Environnementaux\n\n"
        
        # Ajouter une introduction
        md_content += "## Introduction\n\n"
        md_content += "Ce rapport présente une analyse des risques environnementaux pour différents sites. "
        md_content += "L'analyse est basée sur plusieurs facteurs environnementaux, notamment la qualité de l'air, "
        md_content += "les conditions de l'eau, les caractéristiques du sol et les facteurs humains.\n\n"
        
        # Ajouter un résumé des résultats
        md_content += "## Résumé des Résultats\n\n"
        md_content += "Le tableau ci-dessous présente un résumé des scores de risque pour chaque site analysé:\n\n"
        
        # Créer un tableau de résumé
        md_content += "| Site | Score Air | Score Eau | Score Sol | Score Humain | Score Global | Niveau de Risque |\n"
        md_content += "|------|-----------|-----------|-----------|--------------|--------------|-----------------|\n"
        
        for _, row in df.iterrows():
            site_name = row['nom_site'] if 'nom_site' in row else f"Site {_+1}"
            air_score = f"{row['score_air']:.2f}" if pd.notna(row['score_air']) else "N/A"
            water_score = f"{row['score_eau']:.2f}" if pd.notna(row['score_eau']) else "N/A"
            soil_score = f"{row['score_sol']:.2f}" if pd.notna(row['score_sol']) else "N/A"
            human_score = f"{row['score_humain']:.2f}" if pd.notna(row['score_humain']) else "N/A"
            global_score = f"{row['score_global']:.2f}" if pd.notna(row['score_global']) else "N/A"
            risk_level = row['niveau_risque']
            
            md_content += f"| {site_name} | {air_score} | {water_score} | {soil_score} | {human_score} | {global_score} | {risk_level} |\n"
        
        md_content += "\n"
        
        # Ajouter une analyse détaillée pour chaque site
        md_content += "## Analyse Détaillée par Site\n\n"
        
        for _, row in df.iterrows():
            site_name = row['nom_site'] if 'nom_site' in row else f"Site {_+1}"
            md_content += f"### {site_name}\n\n"
            
            # Informations générales sur le site
            md_content += "#### Informations Générales\n\n"
            if 'type' in row:
                md_content += f"- **Type de site**: {row['type']}\n"
            if 'risque_initial' in row:
                md_content += f"- **Risque initial évalué**: {row['risque_initial']}\n"
            if 'latitude' in row and 'longitude' in row:
                md_content += f"- **Coordonnées**: {row['latitude']}, {row['longitude']}\n"
            md_content += "\n"
            
            # Analyse de la qualité de l'air
            md_content += "#### Qualité de l'Air\n\n"
            md_content += f"- **Score de risque air**: {row['score_air']:.2f} sur 10\n" if pd.notna(row['score_air']) else "- **Score de risque air**: Non disponible\n"
            
            air_factors = []
            if 'temperature' in row and pd.notna(row['temperature']):
                air_factors.append(f"Température: {row['temperature']} °C")
            if 'humidite' in row and pd.notna(row['humidite']):
                air_factors.append(f"Humidité: {row['humidite']} %")
            if 'pression' in row and pd.notna(row['pression']):
                air_factors.append(f"Pression: {row['pression']} hPa")
            if 'conditions_meteo' in row and pd.notna(row['conditions_meteo']):
                air_factors.append(f"Conditions météo: {row['conditions_meteo']}")
            if 'vitesse_vent' in row and pd.notna(row['vitesse_vent']):
                air_factors.append(f"Vitesse du vent: {row['vitesse_vent']} m/s")
            if 'pm25' in row and pd.notna(row['pm25']):
                air_factors.append(f"PM2.5: {row['pm25']} μg/m³")
            if 'pm10' in row and pd.notna(row['pm10']):
                air_factors.append(f"PM10: {row['pm10']} μg/m³")
            if 'no2' in row and pd.notna(row['no2']):
                air_factors.append(f"NO2: {row['no2']} μg/m³")
            if 'o3' in row and pd.notna(row['o3']):
                air_factors.append(f"O3: {row['o3']} μg/m³")
            if 'indice_qualite_air' in row and pd.notna(row['indice_qualite_air']):
                air_factors.append(f"Indice qualité air: {row['indice_qualite_air']} sur 5")
            
            if air_factors:
                md_content += "- **Facteurs analysés**:\n"
                for factor in air_factors:
                    md_content += f"  - {factor}\n"
            md_content += "\n"
            
            # Analyse de l'eau
            md_content += "#### Conditions de l'Eau\n\n"
            md_content += f"- **Score de risque eau**: {row['score_eau']:.2f} sur 10\n" if pd.notna(row['score_eau']) else "- **Score de risque eau**: Non disponible\n"
            
            water_factors = []
            if 'points_eau_proximite' in row and pd.notna(row['points_eau_proximite']):
                water_factors.append(f"Points d'eau à proximité: {row['points_eau_proximite']}")
            if 'acces_eau' in row and pd.notna(row['acces_eau']):
                water_factors.append(f"Accès à l'eau: {row['acces_eau']} %")
            
            if water_factors:
                md_content += "- **Facteurs analysés**:\n"
                for factor in water_factors:
                    md_content += f"  - {factor}\n"
            md_content += "\n"
            
            # Analyse du sol
            md_content += "#### Caractéristiques du Sol\n\n"
            md_content += f"- **Score de risque sol**: {row['score_sol']:.2f} sur 10\n" if pd.notna(row['score_sol']) else "- **Score de risque sol**: Non disponible\n"
            
            soil_factors = []
            if 'ph_sol' in row and pd.notna(row['ph_sol']):
                soil_factors.append(f"pH du sol: {row['ph_sol']}")
            if 'carbone_organique' in row and pd.notna(row['carbone_organique']):
                soil_factors.append(f"Carbone organique: {row['carbone_organique']} g/kg")
            if 'argile' in row and pd.notna(row['argile']):
                soil_factors.append(f"Argile: {row['argile']} %")
            if 'sable' in row and pd.notna(row['sable']):
                soil_factors.append(f"Sable: {row['sable']} %")
            
            if soil_factors:
                md_content += "- **Facteurs analysés**:\n"
                for factor in soil_factors:
                    md_content += f"  - {factor}\n"
            md_content += "\n"
            
            # Analyse des facteurs humains
            md_content += "#### Facteurs Humains\n\n"
            md_content += f"- **Score de risque humain**: {row['score_humain']:.2f} sur 10\n" if pd.notna(row['score_humain']) else "- **Score de risque humain**: Non disponible\n"
            
            human_factors = []
            if 'habitations_proximite' in row and pd.notna(row['habitations_proximite']):
                human_factors.append(f"Habitations à proximité: {row['habitations_proximite']}")
            if 'zones_industrielles_proximite' in row and pd.notna(row['zones_industrielles_proximite']):
                human_factors.append(f"Zones industrielles à proximité: {row['zones_industrielles_proximite']}")
            if 'population_pays' in row and pd.notna(row['population_pays']):
                human_factors.append(f"Population du pays: {row['population_pays']}")
            if 'couverture_forestiere' in row and pd.notna(row['couverture_forestiere']):
                human_factors.append(f"Couverture forestière: {row['couverture_forestiere']} %")
            
            if human_factors:
                md_content += "- **Facteurs analysés**:\n"
                for factor in human_factors:
                    md_content += f"  - {factor}\n"
            md_content += "\n"
            
            # Conclusion pour ce site
            md_content += "#### Conclusion\n\n"
            md_content += f"Le site **{site_name}** présente un niveau de risque environnemental **{row['niveau_risque'].lower()}** "
            md_content += f"avec un score global de **{row['score_global']:.2f}** sur 10. "
            
            if row['niveau_risque'] == 'Élevé':
                md_content += "Des mesures d'atténuation significatives sont recommandées pour réduire les risques environnementaux.\n\n"
            elif row['niveau_risque'] == 'Moyen':
                md_content += "Une surveillance régulière et certaines mesures d'atténuation sont recommandées.\n\n"
            else:  # Faible
                md_content += "Le site présente un risque environnemental relativement faible, mais une surveillance de routine est recommandée.\n\n"
        
        # Ajouter une conclusion générale
        md_content += "## Conclusion Générale\n\n"
        
        high_risk_sites = df[df['niveau_risque'] == 'Élevé']['nom_site'].tolist() if 'nom_site' in df else []
        medium_risk_sites = df[df['niveau_risque'] == 'Moyen']['nom_site'].tolist() if 'nom_site' in df else []
        low_risk_sites = df[df['niveau_risque'] == 'Faible']['nom_site'].tolist() if 'nom_site' in df else []
        
        md_content += f"Sur les {len(df)} sites analysés:\n\n"
        md_content += f"- **{len(high_risk_sites)}** sites présentent un risque élevé\n"
        md_content += f"- **{len(medium_risk_sites)}** sites présentent un risque moyen\n"
        md_content += f"- **{len(low_risk_sites)}** sites présentent un risque faible\n\n"
        
        md_content += "Les recommandations générales sont les suivantes:\n\n"
        
        if high_risk_sites:
            md_content += "- Pour les sites à risque élevé, mettre en place des mesures d'atténuation immédiates et un plan de surveillance renforcé\n"
        if medium_risk_sites:
            md_content += "- Pour les sites à risque moyen, établir un plan de surveillance régulier et identifier les facteurs de risque spécifiques à améliorer\n"
        if low_risk_sites:
            md_content += "- Pour les sites à risque faible, maintenir une surveillance de routine et documenter tout changement significatif\n"
        
        # Écrire le contenu dans un fichier Markdown
        with open(output_md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"Rapport Markdown généré avec succès: {output_md_file}")
        return True
    except Exception as e:
        print(f"Erreur lors de la génération du rapport Markdown: {e}")
        import traceback
        traceback.print_exc()
        return False

def convert_markdown_to_pdf(md_file, pdf_file):
    """Convertit un fichier Markdown en PDF en utilisant le MCP Pandoc."""
    try:
        # Préparer les arguments pour le MCP Pandoc
        args = {
            "server_name": "mcp.config.usrlocalmcp.Pandoc",
            "tool_name": "convert-contents",
            "args": {
                "input_file": md_file,
                "input_format": "markdown",
                "output_format": "pdf",
                "output_file": pdf_file
            }
        }
        
        # Exécuter la commande Python pour appeler le MCP
        cmd = f"python -c \"import json, subprocess; result = subprocess.run(['run_mcp', json.dumps({json.dumps(args)})], capture_output=True, text=True); print(result.stdout); print(result.stderr) if result.returncode != 0 else None\""
        
        print("Conversion du rapport Markdown en PDF...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Rapport PDF généré avec succès: {pdf_file}")
            return True
        else:
            print(f"Erreur lors de la conversion en PDF: {result.stderr}")
            print("Tentative de conversion alternative...")
            
            # Méthode alternative: utiliser pandoc directement si disponible
            try:
                pandoc_cmd = f"pandoc {md_file} -o {pdf_file}"
                alt_result = subprocess.run(pandoc_cmd, shell=True, capture_output=True, text=True)
                
                if alt_result.returncode == 0:
                    print(f"Rapport PDF généré avec succès (méthode alternative): {pdf_file}")
                    return True
                else:
                    print(f"Échec de la méthode alternative: {alt_result.stderr}")
                    return False
            except Exception as e:
                print(f"Erreur lors de la tentative alternative: {e}")
                return False
    except Exception as e:
        print(f"Erreur lors de la conversion en PDF: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("Usage: python generate_risk_report.py <fichier_excel> [dossier_sortie]")
        print("Exemple: python generate_risk_report.py resultats/analyse_risques.xlsx rapports")
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
        
        # Générer le rapport Markdown
        md_file = os.path.join(output_dir, "rapport_risques.md")
        if generate_markdown_report(df, md_file):
            # Convertir en PDF
            pdf_file = os.path.join(output_dir, "rapport_risques.pdf")
            if convert_markdown_to_pdf(md_file, pdf_file):
                print(f"\nRapport d'analyse de risque généré avec succès en format PDF: {pdf_file}")
            else:
                print(f"\nLe rapport Markdown a été généré, mais la conversion en PDF a échoué: {md_file}")
        else:
            print("\nLa génération du rapport a échoué.")
    except Exception as e:
        print(f"Erreur lors de l'exécution du script: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()