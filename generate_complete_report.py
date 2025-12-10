import pandas as pd
import sys
import os
import matplotlib
matplotlib.use('Agg')  # Utiliser un backend non-interactif
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
from datetime import datetime
import subprocess

def load_data(risk_file, recommendations_file, action_plan_file):
    """Charge les données depuis les fichiers Excel."""
    try:
        risk_df = pd.read_excel(risk_file)
        recommendations_df = pd.read_excel(recommendations_file)
        action_plan_df = pd.read_excel(action_plan_file)
        return risk_df, recommendations_df, action_plan_df
    except Exception as e:
        print(f"Erreur lors de la lecture des fichiers: {e}")
        sys.exit(1)

def create_risk_chart(risk_df, output_dir):
    """Crée un graphique des scores de risque et le sauvegarde."""
    # Créer une figure avec une taille spécifique
    plt.figure(figsize=(10, 6))
    
    # Définir les couleurs pour chaque catégorie
    colors = ['#3498db', '#2ecc71', '#e67e22', '#9b59b6', '#34495e']
    
    # Créer les positions des barres
    sites = risk_df['nom_site']
    x = np.arange(len(sites))
    width = 0.15  # Largeur des barres
    
    # Créer les barres pour chaque catégorie
    categories = ['score_air', 'score_eau', 'score_sol', 'score_humain', 'score_global']
    labels = ['Air', 'Eau', 'Sol', 'Humain', 'Global']
    
    for i, (category, color) in enumerate(zip(categories, colors)):
        plt.bar(x + (i - 2) * width, risk_df[category], width, label=labels[i], color=color)
    
    # Ajouter les étiquettes, le titre et la légende
    plt.xlabel('Sites')
    plt.ylabel('Scores de risque')
    plt.title('Scores de risque environnemental par site et par catégorie')
    plt.xticks(x, sites, rotation=45, ha='right')
    plt.legend()
    
    # Ajuster la mise en page
    plt.tight_layout()
    
    # Sauvegarder le graphique
    chart_path = os.path.join(output_dir, 'risk_scores_chart.png')
    plt.savefig(chart_path, dpi=300)
    plt.close()
    
    return chart_path

def create_priority_chart(action_plan_df, output_dir):
    """Crée un graphique de la distribution des priorités et le sauvegarde."""
    # Compter les actions par priorité
    priority_counts = action_plan_df['priorite'].value_counts()
    
    # Définir les couleurs pour chaque priorité
    colors = {'Haute': '#e74c3c', 'Moyenne': '#f39c12', 'Basse': '#27ae60'}
    
    # Créer une figure avec une taille spécifique
    plt.figure(figsize=(8, 8))
    
    # Créer le graphique en camembert
    plt.pie(
        priority_counts,
        labels=priority_counts.index,
        autopct='%1.1f%%',
        startangle=90,
        colors=[colors.get(p, '#95a5a6') for p in priority_counts.index]
    )
    
    # Ajouter un titre
    plt.title('Distribution des priorités d\'action')
    
    # Ajuster la mise en page
    plt.axis('equal')  # Pour que le camembert soit circulaire
    
    # Sauvegarder le graphique
    chart_path = os.path.join(output_dir, 'priority_distribution_chart.png')
    plt.savefig(chart_path, dpi=300)
    plt.close()
    
    return chart_path

def create_category_chart(action_plan_df, output_dir):
    """Crée un graphique des actions par catégorie et le sauvegarde."""
    # Compter les actions par catégorie
    category_counts = action_plan_df['categorie'].value_counts()
    
    # Créer une figure avec une taille spécifique
    plt.figure(figsize=(10, 6))
    
    # Créer le graphique à barres
    bars = plt.bar(
        category_counts.index,
        category_counts.values,
        color=cm.tab10.colors[:len(category_counts)]
    )
    
    # Ajouter les valeurs au-dessus des barres
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2.,
            height + 0.1,
            str(int(height)),
            ha='center',
            va='bottom'
        )
    
    # Ajouter les étiquettes, le titre et la légende
    plt.xlabel('Catégorie')
    plt.ylabel('Nombre d\'actions')
    plt.title('Nombre d\'actions par catégorie')
    plt.xticks(rotation=45, ha='right')
    
    # Ajuster la mise en page
    plt.tight_layout()
    
    # Sauvegarder le graphique
    chart_path = os.path.join(output_dir, 'category_distribution_chart.png')
    plt.savefig(chart_path, dpi=300)
    plt.close()
    
    return chart_path

def generate_markdown_report(risk_df, recommendations_df, action_plan_df, output_dir, charts):
    """Génère un rapport Markdown complet."""
    # Fusionner les DataFrames pour l'analyse
    merged_df = pd.merge(risk_df, recommendations_df, on='nom_site', how='left', suffixes=('', '_rec'))
    
    # Créer le contenu du rapport
    today = datetime.now().strftime("%d/%m/%Y")
    
    report = f"""# Rapport d'Analyse Environnementale Complet

Date: {today}

## Résumé Exécutif

Ce rapport présente une analyse complète des risques environnementaux pour {len(risk_df)} sites, ainsi que des recommandations et un plan d'action pour atténuer ces risques.

### Distribution des niveaux de risque

"""
    
    # Ajouter les statistiques de risque
    risk_counts = risk_df['niveau_risque'].value_counts()
    total_sites = len(risk_df)
    
    report += "| Niveau de risque | Nombre de sites | Pourcentage |\n"
    report += "|----------------|----------------|--------------|\n"
    
    for level, count in risk_counts.items():
        percentage = (count / total_sites) * 100
        report += f"| {level} | {count} | {percentage:.1f}% |\n"
    
    report += "\n"
    
    # Ajouter le graphique des scores de risque
    report += f"""### Scores de risque par site et par catégorie

![Scores de risque](risk_scores_chart.png)

## Plan d'action

Un total de {len(action_plan_df)} actions ont été identifiées pour atténuer les risques environnementaux.

### Distribution des priorités

![Distribution des priorités](priority_distribution_chart.png)

### Actions par catégorie

![Actions par catégorie](category_distribution_chart.png)

## Analyse détaillée par site

"""
    
    # Ajouter une section pour chaque site
    for _, site_data in merged_df.iterrows():
        site_name = site_data['nom_site']
        site_type = site_data['type']
        risk_level = site_data['niveau_risque']
        global_score = site_data['score_global']
        
        report += f"""### {site_name} ({site_type})

**Niveau de risque**: {risk_level}  
**Score global**: {global_score:.2f}

#### Scores par catégorie

| Air | Eau | Sol | Humain |
|-----|-----|-----|--------|
| {site_data['score_air']:.2f} | {site_data['score_eau']:.2f} | {site_data['score_sol']:.2f} | {site_data['score_humain']:.2f} |

"""
        
        # Ajouter les recommandations pour ce site
        categories = [
            ('Recommandations générales', 'recommandations_generales'),
            ('Recommandations pour l\'air', 'recommandations_air'),
            ('Recommandations pour l\'eau', 'recommandations_eau'),
            ('Recommandations pour le sol', 'recommandations_sol'),
            ('Recommandations pour le milieu humain', 'recommandations_humain')
        ]
        
        for cat_title, cat_field in categories:
            if cat_field in site_data and pd.notna(site_data[cat_field]) and site_data[cat_field].strip():
                report += f"#### {cat_title}\n\n"
                
                recommendations = site_data[cat_field].split('\n')
                for rec in recommendations:
                    if rec.strip():
                        report += f"- {rec.strip()}\n"
                
                report += "\n"
        
        # Ajouter les actions planifiées pour ce site
        site_actions = action_plan_df[action_plan_df['site'] == site_name]
        
        if not site_actions.empty:
            report += f"#### Actions planifiées ({len(site_actions)} actions)\n\n"
            report += "| Action | Catégorie | Priorité | Responsable | Date de début | Date de fin | Budget estimé | Statut |\n"
            report += "|--------|-----------|----------|-------------|--------------|------------|---------------|-----------|\n"
            
            for _, action in site_actions.iterrows():
                start_date = action['date_debut'].strftime('%d/%m/%Y') if pd.notna(action['date_debut']) else "-"
                end_date = action['date_fin'].strftime('%d/%m/%Y') if pd.notna(action['date_fin']) else "-"
                budget = f"{action['budget_estime']:,.0f} €" if pd.notna(action['budget_estime']) else "-"
                
                report += f"| {action['action']} | {action['categorie']} | {action['priorite']} | {action['responsable']} | {start_date} | {end_date} | {budget} | {action['statut']} |\n"
            
            report += "\n"
    
    # Ajouter une conclusion
    report += f"""## Conclusion

Cette analyse environnementale a identifié des risques variés sur les {len(risk_df)} sites étudiés. Le plan d'action proposé comprend {len(action_plan_df)} actions concrètes pour atténuer ces risques, avec une attention particulière aux {len(action_plan_df[action_plan_df['priorite'] == 'Haute'])} actions de haute priorité.

La mise en œuvre de ces recommandations permettra d'améliorer significativement l'impact environnemental des sites et de réduire les risques associés.

## Prochaines étapes

1. Valider le plan d'action avec les parties prenantes
2. Allouer les ressources nécessaires pour les actions prioritaires
3. Mettre en place un suivi régulier de l'avancement des actions
4. Réévaluer les risques après la mise en œuvre des actions principales
"""
    
    # Écrire le rapport dans un fichier Markdown
    md_path = os.path.join(output_dir, 'rapport_complet.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    return md_path

def convert_to_pdf(md_path, output_dir):
    """Convertit le rapport Markdown en PDF en utilisant Pandoc."""
    try:
        # Construire le chemin de sortie PDF
        pdf_path = os.path.join(output_dir, 'rapport_complet.pdf')
        
        # Essayer d'utiliser le MCP Pandoc si disponible
        try:
            from run_mcp import run_mcp
            print("Conversion du rapport en PDF avec MCP Pandoc...")
            result = run_mcp({
                "server_name": "mcp.config.usrlocalmcp.Pandoc",
                "tool_name": "convert-contents",
                "args": {
                    "input_file": md_path,
                    "input_format": "markdown",
                    "output_format": "pdf",
                    "output_file": pdf_path
                }
            })
            print("Conversion réussie avec MCP Pandoc.")
            return pdf_path
        except Exception as e:
            print(f"Erreur lors de l'utilisation de MCP Pandoc: {e}")
            print("Tentative de conversion avec Pandoc en ligne de commande...")
            
            # Utiliser Pandoc en ligne de commande
            cmd = ["pandoc", md_path, "-o", pdf_path, "--pdf-engine=xelatex"]
            subprocess.run(cmd, check=True)
            print("Conversion réussie avec Pandoc en ligne de commande.")
            return pdf_path
    except Exception as e:
        print(f"Erreur lors de la conversion en PDF: {e}")
        print("La conversion en PDF a échoué. Le rapport est disponible au format Markdown.")
        return md_path

def convert_to_html(md_path, output_dir, charts):
    """Convertit le rapport Markdown en HTML avec les images intégrées."""
    try:
        # Construire le chemin de sortie HTML
        html_path = os.path.join(output_dir, 'rapport_complet.html')
        
        # Lire le contenu Markdown
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Créer le contenu HTML avec un style CSS intégré
        html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport d'Analyse Environnementale Complet</title>
    <style>
        body {{  
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3, h4 {{  
            color: #2c3e50;
        }}
        h1 {{  
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{  
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 5px;
            margin-top: 30px;
        }}
        table {{  
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{  
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{  
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        tr:nth-child(even) {{  
            background-color: #f9f9f9;
        }}
        img {{  
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 5px;
        }}
        ul {{  
            margin-bottom: 20px;
        }}
        .site-header {{  
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .risk-high {{  
            color: #e74c3c;
            font-weight: bold;
        }}
        .risk-medium {{  
            color: #f39c12;
            font-weight: bold;
        }}
        .risk-low {{  
            color: #27ae60;
            font-weight: bold;
        }}
        .priority-high {{  
            background-color: #ffcccc;
            color: #990000;
            padding: 2px 5px;
            border-radius: 3px;
        }}
        .priority-medium {{  
            background-color: #ffffcc;
            color: #999900;
            padding: 2px 5px;
            border-radius: 3px;
        }}
        .priority-low {{  
            background-color: #ccffcc;
            color: #009900;
            padding: 2px 5px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
"""
        
        # Convertir le Markdown en HTML
        try:
            import markdown
            html_body = markdown.markdown(md_content, extensions=['tables'])
        except ImportError:
            # Si markdown n'est pas disponible, utiliser une conversion basique
            html_body = md_content.replace('\n\n', '<br><br>').replace('\n', '<br>')
            html_body = html_body.replace('# ', '<h1>').replace(' #', '</h1>')
            html_body = html_body.replace('## ', '<h2>').replace(' ##', '</h2>')
            html_body = html_body.replace('### ', '<h3>').replace(' ###', '</h3>')
            html_body = html_body.replace('#### ', '<h4>').replace(' ####', '</h4>')
            html_body = html_body.replace('- ', '<li>').replace('\n<li>', '\n<ul><li>').replace('\n\n', '</ul>\n\n')
        
        # Ajouter le contenu HTML converti
        html_content += html_body
        
        # Fermer les balises HTML
        html_content += "\n</body>\n</html>"
        
        # Écrire le contenu HTML dans un fichier
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Rapport HTML généré avec succès: {html_path}")
        return html_path
    except Exception as e:
        print(f"Erreur lors de la conversion en HTML: {e}")
        print("La conversion en HTML a échoué. Le rapport est disponible au format Markdown.")
        return md_path

def main():
    # Vérifier les arguments
    if len(sys.argv) < 4:
        print("Usage: python generate_complete_report.py <fichier_risques> <fichier_recommandations> <fichier_plan_action> [dossier_sortie]")
        print("Exemple: python generate_complete_report.py resultats/analyse_risques.xlsx resultats/recommandations.xlsx resultats/plan_action.xlsx rapports")
        sys.exit(1)
    
    # Récupérer les arguments
    risk_file = sys.argv[1]
    recommendations_file = sys.argv[2]
    action_plan_file = sys.argv[3]
    output_dir = sys.argv[4] if len(sys.argv) > 4 else 'rapports'
    
    # Créer le dossier de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Charger les données
        print(f"Chargement des données...")
        risk_df, recommendations_df, action_plan_df = load_data(risk_file, recommendations_file, action_plan_file)
        print(f"Données chargées avec succès.")
        
        # Créer les graphiques
        print("Création des graphiques...")
        charts = {
            'risk': create_risk_chart(risk_df, output_dir),
            'priority': create_priority_chart(action_plan_df, output_dir),
            'category': create_category_chart(action_plan_df, output_dir)
        }
        print(f"Graphiques créés avec succès.")
        
        # Générer le rapport Markdown
        print("Génération du rapport Markdown...")
        md_path = generate_markdown_report(risk_df, recommendations_df, action_plan_df, output_dir, charts)
        print(f"Rapport Markdown généré avec succès: {md_path}")
        
        # Convertir en PDF
        print("Conversion du rapport en PDF...")
        pdf_path = convert_to_pdf(md_path, output_dir)
        
        # Convertir en HTML (comme alternative au PDF)
        print("Conversion du rapport en HTML...")
        html_path = convert_to_html(md_path, output_dir, charts)
        
        # Afficher un résumé
        print("\nRapport généré avec succès!")
        print(f"Rapport Markdown: {md_path}")
        if pdf_path != md_path:
            print(f"Rapport PDF: {pdf_path}")
        if html_path != md_path:
            print(f"Rapport HTML: {html_path}")
            print(f"Vous pouvez ouvrir le rapport HTML dans votre navigateur.")
        
        # Tenter d'ouvrir le rapport HTML dans le navigateur
        try:
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(html_path)}")
        except Exception as e:
            print(f"Impossible d'ouvrir automatiquement le rapport dans le navigateur: {e}")
    
    except Exception as e:
        print(f"Erreur lors de l'exécution du script: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()