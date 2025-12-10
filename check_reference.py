import pandas as pd
import os

# Vérifier le fichier de référence (le plus ancien fichier d'analyse de risque)
reference_file = os.path.join('output', 'resultat_analyse_risque_20250716_134950.xlsx')
if os.path.exists(reference_file):
    print('Fichier de référence:', reference_file)
    
    # Lire le fichier Excel
    df = pd.read_excel(reference_file)
    
    # Afficher les colonnes
    print('\nColonnes du fichier de référence:')
    print(df.columns.tolist())
    
    # Afficher les types de données
    print('\nTypes de données:')
    for col in df.columns:
        print(f'{col}: {df[col].dtype}')
    
    # Afficher le nombre de lignes
    print(f'\nNombre de lignes: {len(df)}')
else:
    print(f"Le fichier de référence '{reference_file}' n'existe pas.")