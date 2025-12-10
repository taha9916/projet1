import pandas as pd
import sys
import os
from datetime import datetime, timedelta

def load_recommendations(file_path):
    """Charge les données de recommandations depuis un fichier Excel."""
    try:
        return pd.read_excel(file_path)
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier {file_path}: {e}")
        sys.exit(1)

def generate_action_plan(recommendations_df):
    """Génère un plan d'action basé sur les recommandations."""
    # Créer un nouveau DataFrame pour le plan d'action
    action_plan_df = pd.DataFrame(columns=[
        'site', 'action', 'categorie', 'priorite', 'responsable', 
        'date_debut', 'date_fin', 'budget_estime', 'statut'
    ])
    
    # Date actuelle pour planifier les actions
    today = datetime.now().date()
    
    # Compteur pour les actions
    action_id = 1
    
    # Pour chaque site dans le DataFrame de recommandations
    for idx, row in recommendations_df.iterrows():
        site_name = row['nom_site']
        priority = row.get('priorite_action', 'Moyenne')  # Par défaut, priorité moyenne
        
        # Définir les délais en fonction de la priorité
        if priority == 'Haute':
            start_delay = timedelta(days=7)  # Commencer dans 1 semaine
            duration = timedelta(days=30)    # Durée de 1 mois
        elif priority == 'Moyenne':
            start_delay = timedelta(days=14)  # Commencer dans 2 semaines
            duration = timedelta(days=60)     # Durée de 2 mois
        else:  # Basse
            start_delay = timedelta(days=30)  # Commencer dans 1 mois
            duration = timedelta(days=90)     # Durée de 3 mois
        
        # Dates de début et de fin
        start_date = today + start_delay
        end_date = start_date + duration
        
        # Catégories de recommandations
        categories = [
            ('Air', 'recommandations_air'),
            ('Eau', 'recommandations_eau'),
            ('Sol', 'recommandations_sol'),
            ('Humain', 'recommandations_humain'),
            ('Général', 'recommandations_generales')
        ]
        
        # Pour chaque catégorie de recommandations
        for cat_name, cat_field in categories:
            if cat_field in row and pd.notna(row[cat_field]):
                # Diviser les recommandations en actions individuelles
                recommendations = row[cat_field].split('\n')
                
                for rec in recommendations:
                    if rec.strip():
                        # Déterminer le budget estimé en fonction de la priorité et de la catégorie
                        if priority == 'Haute':
                            budget = 15000 + (5000 * (action_id % 3))  # Entre 15000 et 25000
                        elif priority == 'Moyenne':
                            budget = 5000 + (3000 * (action_id % 3))   # Entre 5000 et 11000
                        else:  # Basse
                            budget = 2000 + (1000 * (action_id % 3))   # Entre 2000 et 4000
                        
                        # Déterminer le responsable en fonction de la catégorie
                        if cat_name == 'Air':
                            responsable = 'Équipe Qualité de l\'Air'
                        elif cat_name == 'Eau':
                            responsable = 'Équipe Gestion des Eaux'
                        elif cat_name == 'Sol':
                            responsable = 'Équipe Géologie'
                        elif cat_name == 'Humain':
                            responsable = 'Équipe Relations Communautaires'
                        else:  # Général
                            responsable = 'Direction Environnementale'
                        
                        # Ajouter l'action au plan
                        action_plan_df = pd.concat([action_plan_df, pd.DataFrame([{
                            'site': site_name,
                            'action': rec,
                            'categorie': cat_name,
                            'priorite': priority,
                            'responsable': responsable,
                            'date_debut': start_date,
                            'date_fin': end_date,
                            'budget_estime': budget,
                            'statut': 'À faire'
                        }])], ignore_index=True)
                        
                        # Incrémenter le compteur d'actions
                        action_id += 1
                        
                        # Décaler légèrement les dates pour les actions suivantes
                        start_date = start_date + timedelta(days=3)
                        end_date = start_date + duration
    
    return action_plan_df

def export_action_plan(action_plan_df, output_file):
    """Exporte le plan d'action dans un fichier Excel."""
    try:
        # Créer un writer Excel avec xlsxwriter comme moteur
        writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
        
        # Écrire le DataFrame dans la feuille 'Plan d'action'
        action_plan_df.to_excel(writer, sheet_name='Plan d\'action', index=False)
        
        # Accéder au classeur et à la feuille
        workbook = writer.book
        worksheet = writer.sheets['Plan d\'action']
        
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
        
        date_format = workbook.add_format({
            'num_format': 'dd/mm/yyyy',
            'valign': 'top'
        })
        
        currency_format = workbook.add_format({
            'num_format': '#,##0 €',
            'valign': 'top'
        })
        
        # Formats pour les priorités
        high_priority_format = workbook.add_format({
            'bg_color': '#FFC7CE',
            'font_color': '#9C0006',
            'bold': True,
            'valign': 'top'
        })
        
        medium_priority_format = workbook.add_format({
            'bg_color': '#FFEB9C',
            'font_color': '#9C6500',
            'valign': 'top'
        })
        
        low_priority_format = workbook.add_format({
            'bg_color': '#C6EFCE',
            'font_color': '#006100',
            'valign': 'top'
        })
        
        # Appliquer le format d'en-tête
        for col_num, value in enumerate(action_plan_df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Définir la largeur des colonnes
        worksheet.set_column('A:A', 15)  # Site
        worksheet.set_column('B:B', 40)  # Action
        worksheet.set_column('C:C', 10)  # Catégorie
        worksheet.set_column('D:D', 10)  # Priorité
        worksheet.set_column('E:E', 25)  # Responsable
        worksheet.set_column('F:G', 12)  # Dates
        worksheet.set_column('H:H', 15)  # Budget
        worksheet.set_column('I:I', 10)  # Statut
        
        # Appliquer les formats conditionnels
        for row_num in range(1, len(action_plan_df) + 1):
            # Format pour les dates
            worksheet.write(row_num, action_plan_df.columns.get_loc('date_debut'), 
                          action_plan_df.iloc[row_num-1]['date_debut'], date_format)
            worksheet.write(row_num, action_plan_df.columns.get_loc('date_fin'), 
                          action_plan_df.iloc[row_num-1]['date_fin'], date_format)
            
            # Format pour le budget
            worksheet.write(row_num, action_plan_df.columns.get_loc('budget_estime'), 
                          action_plan_df.iloc[row_num-1]['budget_estime'], currency_format)
            
            # Format pour la priorité
            priority = action_plan_df.iloc[row_num-1]['priorite']
            priority_col = action_plan_df.columns.get_loc('priorite')
            
            if priority == 'Haute':
                worksheet.write(row_num, priority_col, priority, high_priority_format)
            elif priority == 'Moyenne':
                worksheet.write(row_num, priority_col, priority, medium_priority_format)
            else:  # Basse
                worksheet.write(row_num, priority_col, priority, low_priority_format)
            
            # Format pour l'action (texte enveloppé)
            worksheet.write(row_num, action_plan_df.columns.get_loc('action'), 
                          action_plan_df.iloc[row_num-1]['action'], wrap_format)
        
        # Ajouter un filtre automatique
        worksheet.autofilter(0, 0, len(action_plan_df), len(action_plan_df.columns) - 1)
        
        # Enregistrer le fichier Excel
        writer.close()
        
        print(f"Plan d'action exporté avec succès dans {output_file}")
        return True
    except Exception as e:
        print(f"Erreur lors de l'exportation du plan d'action: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("Usage: python generate_action_plan.py <fichier_recommandations> [dossier_sortie]")
        print("Exemple: python generate_action_plan.py resultats/recommandations.xlsx resultats")
        sys.exit(1)
    
    # Récupérer les arguments
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "resultats"
    
    # Créer le répertoire de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Charger les données
        print(f"Chargement des recommandations depuis {input_file}...")
        recommendations_df = load_recommendations(input_file)
        print(f"Recommandations chargées avec succès. {len(recommendations_df)} sites trouvés.")
        
        # Générer le plan d'action
        print("Génération du plan d'action...")
        action_plan_df = generate_action_plan(recommendations_df)
        print(f"Plan d'action généré avec succès. {len(action_plan_df)} actions planifiées.")
        
        # Exporter le plan d'action
        output_file = os.path.join(output_dir, "plan_action.xlsx")
        if export_action_plan(action_plan_df, output_file):
            print(f"\nPlan d'action exporté avec succès dans {output_file}")
        else:
            print("\nL'exportation du plan d'action a échoué.")
    except Exception as e:
        print(f"Erreur lors de l'exécution du script: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()