import pandas as pd
import os
import sys

# Forcer la sortie à être affichée immédiatement
sys.stdout.reconfigure(line_buffering=True)

print("Début de la vérification...")

# Utiliser le fichier passé en argument ou trouver le plus récent
if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
    file_to_check = sys.argv[1]
    print(f'Fichier: {file_to_check}')
    
    # Lire le fichier Excel
    df = pd.read_excel(file_to_check)
    
    # Afficher les colonnes
    print('\nColonnes du fichier généré:')
    print(df.columns.tolist())
    
    # Afficher le nombre de lignes
    print(f'\nNombre de lignes: {len(df)}')
    
    # Vérifier la présence de toutes les colonnes attendues
    expected_columns = ['Milieu', 'Paramètre', 'Unité', 'Intervalle acceptable', 'Valeur mesurée', 
                        'Résultat conformité', 'Score', 'Observations', 'Description', 'Évaluation']
    
    missing_columns = [col for col in expected_columns if col not in df.columns]
    if missing_columns:
        print(f"\nColonnes manquantes: {missing_columns}")
    else:
        print("\nToutes les colonnes attendues sont présentes!")
    
    # Afficher les types et valeurs des colonnes présentes
    print("\nDétails des colonnes:")
    for col in df.columns:
        print(f"- {col}: type={df[col].dtype}, valeur1={df[col].iloc[0] if len(df) > 0 else 'Aucune ligne'}")
    
    # Afficher un résumé
    print("\nRésumé:")
    print(f"- Nombre total de colonnes: {len(df.columns)}")
    print(f"- Colonnes attendues: {len(expected_columns)}")
    print(f"- Colonnes présentes: {len(df.columns)}")
    print(f"- Colonnes manquantes: {len(missing_columns)}")
elif os.path.exists('output'):
    # Trouver le fichier Excel le plus récent
    output_files = [f for f in os.listdir('output') if f.endswith('.xlsx') and f.startswith('resultat_analyse_risque')]
    if output_files:
        latest_file = max([os.path.join('output', f) for f in output_files], key=os.path.getmtime)
        print(f'Fichier: {latest_file}')
        
        # Lire le fichier Excel
        df = pd.read_excel(latest_file)
    
    # Afficher les colonnes
    print('\nColonnes du fichier généré:')
    print(df.columns.tolist())
    
    # Afficher le nombre de lignes
    print(f'\nNombre de lignes: {len(df)}')
    
    # Vérifier la présence de toutes les colonnes attendues
    expected_columns = ['Milieu', 'Paramètre', 'Unité', 'Intervalle acceptable', 'Valeur mesurée', 
                        'Résultat conformité', 'Score', 'Observations', 'Description', 'Évaluation']
    
    missing_columns = [col for col in expected_columns if col not in df.columns]
    if missing_columns:
        print(f"\nColonnes manquantes: {missing_columns}")
    else:
        print("\nToutes les colonnes attendues sont présentes!")
    
    # Afficher les types et valeurs des colonnes présentes
    print("\nDétails des colonnes:")
    for col in df.columns:
        print(f"- {col}: type={df[col].dtype}, valeur1={df[col].iloc[0] if len(df) > 0 else 'Aucune ligne'}")
    
    # Afficher un résumé
    print("\nRésumé:")
    print(f"- Nombre total de colonnes: {len(df.columns)}")
    print(f"- Colonnes attendues: {len(expected_columns)}")
    print(f"- Colonnes présentes: {len(df.columns)}")
    print(f"- Colonnes manquantes: {len(missing_columns)}")
else:
    print("Aucun fichier d'analyse de risque trouvé dans le dossier output.")

print("\nVérification terminée.")