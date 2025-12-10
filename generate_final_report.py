import pandas as pd
import sys
import os
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Utiliser le backend non-interactif
import numpy as np
from datetime import datetime

def load_data(risk_file, recommendations_file):
    """Charge les données d'analyse de risque et de recommandations."""
    try:
        risk_df = pd.read_excel(risk_file)
        recommendations_df = pd.read_excel(recommendations_file)
        return risk_df, recommendations_df
    except Exception as e:
        print(f"Erreur lors de la lecture des fichiers: {e}")
        sys.exit(1)

def generate_risk_summary(risk_df):
    """Génère un résumé des niveaux de risque."""
    risk_counts = risk_df['niveau_risque'].value_counts().to_dict()
    high_risk = risk_counts.get('Élevé', 0)
    medium_risk = risk_counts.get('Moyen', 0)
    low_risk = risk_counts.get('Faible', 0)
    
    return {
        'high_risk': high_risk,
        'medium_risk': medium_risk,
        'low_risk': low_risk,
        'total_sites': len(risk_df)
    }

def try_generate_chart(risk_df, output_dir):
    """Tente de générer un graphique des scores de risque."""
    try:
        # Créer un graphique à barres des scores de risque
        plt.figure(figsize=(10, 6))
        
        # Préparer les données
        sites = risk_df['nom_site'].tolist()
        air_scores = risk_df['score_air'].tolist()
        water_scores = risk_df['score_eau'].tolist()
        soil_scores = risk_df['score_sol'].tolist()
        human_scores = risk_df['score_humain'].tolist()
        global_scores = risk_df['score_global'].tolist()
        
        # Positions des barres
        x = np.arange(len(sites))
        width = 0.15
        
        # Créer les barres
        plt.bar(x - 2*width, air_scores, width, label='Air')
        plt.bar(x - width, water_scores, width, label='Eau')
        plt.bar(x, soil_scores, width, label='Sol')
        plt.bar(x + width, human_scores, width, label='Humain')
        plt.bar(x + 2*width, global_scores, width, label='Global')
        
        # Ajouter les étiquettes et le titre
        plt.xlabel('Sites')
        plt.ylabel('Scores de risque')
        plt.title('Scores de risque par catégorie et par site')
        plt.xticks(x, sites, rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        
        # Enregistrer le graphique
        chart_path = os.path.join(output_dir, 'risk_scores_chart.png')
        plt.savefig(chart_path)
        plt.close()
        
        return chart_path
    except Exception as e:
        print(f"Avertissement: Impossible de générer le graphique: {e}")
        return None

def generate_html_report(risk_df, recommendations_df, risk_summary, chart_path, output_file):
    """Génère un rapport HTML complet."""
    # Fusionner les DataFrames sur la colonne 'nom_site'
    merged_df = pd.merge(risk_df, recommendations_df, on='nom_site', how='left', suffixes=('', '_rec'))
    
    # Créer le contenu HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Rapport d'Analyse Environnementale</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            h1 {{ border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            h2 {{ border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; margin-top: 30px; }}
            .summary-box {{ background-color: #f8f9fa; border-left: 4px solid #3498db; padding: 15px; margin: 20px 0; }}
            .high-risk {{ color: #e74c3c; font-weight: bold; }}
            .medium-risk {{ color: #f39c12; font-weight: bold; }}
            .low-risk {{ color: #27ae60; font-weight: bold; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .site-card {{ background-color: #fff; border: 1px solid #ddd; border-radius: 5px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .site-header {{ display: flex; justify-content: space-between; align-items: center; }}
            .risk-badge {{ padding: 5px 10px; border-radius: 3px; color: white; font-weight: bold; }}
            .risk-high {{ background-color: #e74c3c; }}
            .risk-medium {{ background-color: #f39c12; }}
            .risk-low {{ background-color: #27ae60; }}
            .recommendation-section {{ background-color: #f8f9fa; padding: 15px; margin-top: 15px; border-radius: 5px; }}
            .chart-container {{ text-align: center; margin: 30px 0; }}
            .chart-container img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; }}
            .footer {{ margin-top: 50px; border-top: 1px solid #ddd; padding-top: 20px; text-align: center; color: #7f8c8d; }}
            .priority {{ display: inline-block; padding: 3px 8px; border-radius: 3px; color: white; font-size: 0.8em; margin-left: 10px; }}
            .priority-high {{ background-color: #e74c3c; }}
            .priority-medium {{ background-color: #f39c12; }}
            .priority-low {{ background-color: #27ae60; }}
        </style>
    </head>
    <body>
        <h1>Rapport d'Analyse Environnementale</h1>
        <p>Date du rapport: {datetime.now().strftime('%d/%m/%Y')}</p>
        
        <div class="summary-box">
            <h2>Résumé des Risques</h2>
            <p>Ce rapport présente l'analyse environnementale de <strong>{risk_summary['total_sites']} sites</strong>.</p>
            <p>Distribution des niveaux de risque:</p>
            <ul>
                <li><span class="high-risk">Risque élevé:</span> {risk_summary['high_risk']} sites</li>
                <li><span class="medium-risk">Risque moyen:</span> {risk_summary['medium_risk']} sites</li>
                <li><span class="low-risk">Risque faible:</span> {risk_summary['low_risk']} sites</li>
            </ul>
        </div>
    """
    
    # Ajouter le graphique s'il a été généré
    if chart_path:
        html_content += f"""
        <div class="chart-container">
            <h2>Visualisation des Scores de Risque</h2>
            <img src="{os.path.basename(chart_path)}" alt="Graphique des scores de risque">
        </div>
        """
    
    # Tableau récapitulatif des sites
    html_content += f"""
        <h2>Tableau Récapitulatif des Sites</h2>
        <table>
            <tr>
                <th>Site</th>
                <th>Type</th>
                <th>Score Air</th>
                <th>Score Eau</th>
                <th>Score Sol</th>
                <th>Score Humain</th>
                <th>Score Global</th>
                <th>Niveau de Risque</th>
                <th>Priorité d'Action</th>
            </tr>
    """
    
    for _, row in merged_df.iterrows():
        risk_class = ""
        if row['niveau_risque'] == 'Élevé':
            risk_class = "risk-high"
        elif row['niveau_risque'] == 'Moyen':
            risk_class = "risk-medium"
        else:
            risk_class = "risk-low"
            
        priority_class = ""
        if 'priorite_action' in row and pd.notna(row['priorite_action']):
            if row['priorite_action'] == 'Haute':
                priority_class = "priority-high"
            elif row['priorite_action'] == 'Moyenne':
                priority_class = "priority-medium"
            else:
                priority_class = "priority-low"
        
        html_content += f"""
            <tr>
                <td>{row['nom_site']}</td>
                <td>{row['type']}</td>
                <td>{row['score_air']:.2f}</td>
                <td>{row['score_eau']:.2f}</td>
                <td>{row['score_sol']:.2f}</td>
                <td>{row['score_humain']:.2f}</td>
                <td>{row['score_global']:.2f}</td>
                <td><span class="risk-badge {risk_class}">{row['niveau_risque']}</span></td>
                <td>{f'<span class="priority {priority_class}">{row["priorite_action"]}</span>' if 'priorite_action' in row and pd.notna(row['priorite_action']) else 'Non définie'}</td>
            </tr>
        """
    
    html_content += "</table>"
    
    # Détails par site
    html_content += "<h2>Analyse Détaillée par Site</h2>"
    
    for _, row in merged_df.iterrows():
        risk_class = ""
        if row['niveau_risque'] == 'Élevé':
            risk_class = "risk-high"
        elif row['niveau_risque'] == 'Moyen':
            risk_class = "risk-medium"
        else:
            risk_class = "risk-low"
        
        html_content += f"""
        <div class="site-card">
            <div class="site-header">
                <h3>{row['nom_site']} ({row['type']})</h3>
                <span class="risk-badge {risk_class}">{row['niveau_risque']}</span>
            </div>
            <p><strong>Coordonnées:</strong> {row['latitude']}, {row['longitude']}</p>
            <p><strong>Score global:</strong> {row['score_global']:.2f}</p>
            
            <h4>Scores par catégorie</h4>
            <table>
                <tr>
                    <th>Air</th>
                    <th>Eau</th>
                    <th>Sol</th>
                    <th>Humain</th>
                </tr>
                <tr>
                    <td>{row['score_air']:.2f}</td>
                    <td>{row['score_eau']:.2f}</td>
                    <td>{row['score_sol']:.2f}</td>
                    <td>{row['score_humain']:.2f}</td>
                </tr>
            </table>
        """
        
        # Ajouter les recommandations si disponibles
        if 'recommandations_generales' in row and pd.notna(row['recommandations_generales']):
            priority_class = ""
            if 'priorite_action' in row and pd.notna(row['priorite_action']):
                if row['priorite_action'] == 'Haute':
                    priority_class = "priority-high"
                elif row['priorite_action'] == 'Moyenne':
                    priority_class = "priority-medium"
                else:
                    priority_class = "priority-low"
            
            html_content += f"""
            <div class="recommendation-section">
                <h4>Recommandations {f'<span class="priority {priority_class}">{row["priorite_action"]}</span>' if 'priorite_action' in row and pd.notna(row['priorite_action']) else ''}</h4>
                
                <h5>Recommandations générales</h5>
                <ul>
            """
            
            for rec in row['recommandations_generales'].split('\n'):
                if rec.strip():
                    html_content += f"<li>{rec}</li>\n"
            
            html_content += "</ul>"
            
            # Recommandations par catégorie
            categories = [
                ('Air', 'recommandations_air'),
                ('Eau', 'recommandations_eau'),
                ('Sol', 'recommandations_sol'),
                ('Humain', 'recommandations_humain')
            ]
            
            for cat_name, cat_field in categories:
                if cat_field in row and pd.notna(row[cat_field]) and row[cat_field].strip():
                    html_content += f"<h5>Recommandations pour {cat_name}</h5>\n<ul>\n"
                    
                    for rec in row[cat_field].split('\n'):
                        if rec.strip():
                            html_content += f"<li>{rec}</li>\n"
                    
                    html_content += "</ul>\n"
            
            html_content += "</div>\n"
        
        html_content += "</div>\n"
    
    # Pied de page
    html_content += f"""
        <div class="footer">
            <p>Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>
            <p>Système d'Analyse Environnementale - Version 1.0</p>
        </div>
    </body>
    </html>
    """
    
    # Écrire le contenu HTML dans un fichier
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Rapport HTML généré avec succès: {output_file}")
        return True
    except Exception as e:
        print(f"Erreur lors de la génération du rapport HTML: {e}")
        return False

def try_open_html(html_file):
    """Tente d'ouvrir le fichier HTML dans un navigateur."""
    try:
        import webbrowser
        webbrowser.open('file://' + os.path.abspath(html_file))
        print(f"Ouverture du rapport dans le navigateur: {html_file}")
    except Exception as e:
        print(f"Impossible d'ouvrir le navigateur: {e}")
        print(f"Veuillez ouvrir manuellement le fichier: {html_file}")

def main():
    # Vérifier les arguments
    if len(sys.argv) < 3:
        print("Usage: python generate_final_report.py <fichier_risques> <fichier_recommandations> [dossier_sortie]")
        print("Exemple: python generate_final_report.py resultats/analyse_risques.xlsx resultats/recommandations.xlsx rapports")
        sys.exit(1)
    
    # Récupérer les arguments
    risk_file = sys.argv[1]
    recommendations_file = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "rapports"
    
    # Créer le répertoire de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Charger les données
        print(f"Chargement des données...")
        risk_df, recommendations_df = load_data(risk_file, recommendations_file)
        print(f"Données chargées avec succès.")
        
        # Générer le résumé des risques
        risk_summary = generate_risk_summary(risk_df)
        print(f"Résumé des risques généré.")
        
        # Tenter de générer un graphique
        chart_path = try_generate_chart(risk_df, output_dir)
        if chart_path:
            print(f"Graphique généré: {chart_path}")
        
        # Générer le rapport HTML
        output_file = os.path.join(output_dir, "rapport_final.html")
        if generate_html_report(risk_df, recommendations_df, risk_summary, chart_path, output_file):
            print(f"\nRapport final généré avec succès: {output_file}")
            try_open_html(output_file)
        else:
            print("\nLa génération du rapport final a échoué.")
    except Exception as e:
        print(f"Erreur lors de l'exécution du script: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()