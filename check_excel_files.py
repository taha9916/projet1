import pandas as pd
import os
import glob

# Trouver le fichier modèle
model_file = 'table-6381b721-60f9-4997-bfdc-34634c92fe8b-11 (1).xlsx'
print(f"\nExamen du fichier modèle: {model_file}")

try:
    model_df = pd.read_excel(model_file)
    print("\nColonnes du fichier modèle:")
    print(model_df.columns.tolist())
    print("\nAperçu des premières lignes du modèle:")
    print(model_df.head(3).to_string())
    print("\nInformations sur le DataFrame modèle:")
    print(model_df.info())
except Exception as e:
    print(f"Erreur lors de la lecture du fichier modèle: {e}")

# Trouver le fichier Excel le plus récent dans le dossier output
output_dir = 'output'
print(f"\n\nRecherche des fichiers générés dans le dossier: {output_dir}")

try:
    excel_files = glob.glob(os.path.join(output_dir, 'resultat_analyse_risque_*.xlsx'))
    
    if not excel_files:
        print("Aucun fichier Excel trouvé dans le dossier output.")
    else:
        # Trier par date de modification (le plus récent en premier)
        latest_file = max(excel_files, key=os.path.getmtime)
        print(f"\nFichier généré le plus récent: {latest_file}")
        
        generated_df = pd.read_excel(latest_file)
        print("\nColonnes du fichier généré:")
        print(generated_df.columns.tolist())
        print("\nAperçu des premières lignes du fichier généré:")
        print(generated_df.head(3).to_string())
        print("\nInformations sur le DataFrame généré:")
        print(generated_df.info())
except Exception as e:
    print(f"Erreur lors de la lecture du fichier généré: {e}")