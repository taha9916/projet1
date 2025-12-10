import os
import sys
import argparse
import logging
from extraire_donnees_rapports import extraire_donnees_rapport, extraire_tableaux_markdown, convertir_tableaux_en_dataframes

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_extraction(fichier_path, type_rapport="environnement", format_sortie="markdown", sauvegarder=True):
    """
    Démontre l'extraction de données de rapports avec dots.ocr.
    
    Args:
        fichier_path (str): Chemin vers le fichier rapport (image ou PDF)
        type_rapport (str): Type de rapport ('environnement', 'pollution', 'biodiversite')
        format_sortie (str): Format de sortie ('dataframe', 'json', 'dict', 'markdown')
        sauvegarder (bool): Si True, sauvegarde les résultats dans un fichier
    """
    logger.info(f"Démonstration d'extraction de données avec dots.ocr")
    logger.info(f"Fichier: {fichier_path}")
    logger.info(f"Type de rapport: {type_rapport}")
    logger.info(f"Format de sortie: {format_sortie}")
    
    # Vérifier que le fichier existe
    if not os.path.exists(fichier_path):
        logger.error(f"Le fichier {fichier_path} n'existe pas.")
        return
    
    # Extraire les données du rapport
    logger.info("Extraction des données...")
    resultat = extraire_donnees_rapport(fichier_path, type_rapport, format_sortie)
    
    if resultat is None:
        logger.error("L'extraction a échoué.")
        return
    
    # Afficher les résultats selon le format
    logger.info("Extraction terminée. Résultats:")
    
    if format_sortie == "markdown":
        print("\n" + "=" * 80)
        print("RÉSULTATS DE L'EXTRACTION (FORMAT MARKDOWN)")
        print("=" * 80)
        print(resultat)
        print("=" * 80)
        
        # Extraire et convertir les tableaux en DataFrames
        tableaux = extraire_tableaux_markdown(resultat)
        logger.info(f"{len(tableaux)} tableaux extraits du texte Markdown.")
        
        dataframes = convertir_tableaux_en_dataframes(tableaux)
        logger.info(f"{len(dataframes)} tableaux convertis en DataFrames.")
        
        # Afficher les DataFrames
        for i, df in enumerate(dataframes, 1):
            print(f"\nTableau {i}:")
            print(df.to_string(index=False))
            
            # Sauvegarder les DataFrames individuels
            if sauvegarder:
                nom_base = os.path.splitext(os.path.basename(fichier_path))[0]
                fichier_sortie = f"{nom_base}_tableau_{i}.xlsx"
                df.to_excel(fichier_sortie, index=False)
                logger.info(f"Tableau {i} sauvegardé dans {fichier_sortie}")
    
    elif format_sortie == "dataframe":
        print("\n" + "=" * 80)
        print("RÉSULTATS DE L'EXTRACTION (FORMAT DATAFRAME)")
        print("=" * 80)
        print(resultat.to_string(index=False))
        print("=" * 80)
        
        # Sauvegarder le DataFrame
        if sauvegarder:
            nom_base = os.path.splitext(os.path.basename(fichier_path))[0]
            fichier_sortie = f"{nom_base}_resultats.xlsx"
            resultat.to_excel(fichier_sortie, index=False)
            logger.info(f"Résultats sauvegardés dans {fichier_sortie}")
    
    elif format_sortie == "json":
        print("\n" + "=" * 80)
        print("RÉSULTATS DE L'EXTRACTION (FORMAT JSON)")
        print("=" * 80)
        print(resultat)
        print("=" * 80)
        
        # Sauvegarder le JSON
        if sauvegarder:
            nom_base = os.path.splitext(os.path.basename(fichier_path))[0]
            fichier_sortie = f"{nom_base}_resultats.json"
            with open(fichier_sortie, 'w', encoding='utf-8') as f:
                f.write(resultat)
            logger.info(f"Résultats sauvegardés dans {fichier_sortie}")
    
    elif format_sortie == "dict":
        print("\n" + "=" * 80)
        print("RÉSULTATS DE L'EXTRACTION (FORMAT DICT)")
        print("=" * 80)
        for key, value in resultat.items():
            print(f"{key}: {value}")
        print("=" * 80)
    
    logger.info("Démonstration terminée.")

def main():
    # Configurer l'analyseur d'arguments
    parser = argparse.ArgumentParser(description="Démonstrateur d'extraction de données de rapports avec dots.ocr")
    parser.add_argument("fichier", help="Chemin vers le fichier rapport (image ou PDF)")
    parser.add_argument("-t", "--type", choices=["environnement", "pollution", "biodiversite"], 
                        default="environnement", help="Type de rapport (défaut: environnement)")
    parser.add_argument("-f", "--format", choices=["dataframe", "json", "dict", "markdown"], 
                        default="markdown", help="Format de sortie (défaut: markdown)")
    parser.add_argument("-n", "--no-save", action="store_true", help="Ne pas sauvegarder les résultats")
    
    # Analyser les arguments
    args = parser.parse_args()
    
    # Exécuter la démonstration
    demo_extraction(args.fichier, args.type, args.format, not args.no_save)

if __name__ == "__main__":
    main()