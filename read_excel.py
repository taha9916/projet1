import pandas as pd
import sys
import glob
import os

def read_excel_file(file_path):
    """Lit et affiche le contenu d'un fichier Excel."""
    try:
        # Lire le fichier Excel
        df = pd.read_excel(file_path)
        
        # Afficher les informations sur le DataFrame
        print(f"\nInformations sur le fichier: {file_path}")
        print(f"Nombre de lignes: {len(df)}")
        print(f"Colonnes: {', '.join(df.columns)}")
        
        # Afficher les données
        print("\nContenu du fichier:")
        print(df.to_string())
        
        return True
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier Excel: {e}")
        return False

def main():
    # Si un fichier est spécifié en argument, l'utiliser
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        read_excel_file(file_path)
    else:
        # Sinon, trouver le fichier Excel le plus récent
        excel_files = glob.glob("*.xlsx")
        if excel_files:
            # Trier par date de modification (le plus récent en premier)
            latest_file = max(excel_files, key=lambda x: os.path.getmtime(x))
            print(f"Lecture du fichier Excel le plus récent: {latest_file}")
            read_excel_file(latest_file)
        else:
            print("Aucun fichier Excel trouvé dans le répertoire courant.")

if __name__ == "__main__":
    main()