import os
import sys
import logging
import time
from PIL import Image

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importer CloudVisionAPI
try:
    from cloud_api import CloudVisionAPI
    logger.info("Module CloudVisionAPI importé avec succès.")
except ImportError as e:
    logger.error(f"Impossible d'importer CloudVisionAPI: {e}")
    logger.error("Assurez-vous que le fichier cloud_api.py est présent dans le répertoire.")
    sys.exit(1)

def analyser_image_avec_dots_ocr(image_path, prompt=None):
    """
    Analyse une image avec dots.ocr via CloudVisionAPI.
    """
    if not os.path.exists(image_path):
        logger.error(f"L'image {image_path} n'existe pas.")
        return None
    
    try:
        # Créer une instance de CloudVisionAPI avec dots_ocr comme fournisseur
        api = CloudVisionAPI(provider="dots_ocr")
        
        # Charger l'image
        img = Image.open(image_path)
        
        # Mesurer le temps d'exécution
        start_time = time.time()
        
        # Analyser l'image
        if prompt:
            logger.info(f"Analyse de l'image avec le prompt: {prompt}")
            response = api.analyze_image(img, prompt=prompt)
        else:
            logger.info("Analyse de l'image sans prompt spécifique.")
            response = api.analyze_image(img)
        
        # Calculer le temps d'exécution
        execution_time = time.time() - start_time
        logger.info(f"Analyse terminée en {execution_time:.2f} secondes.")
        
        # Libérer la mémoire
        api.cleanup()
        
        return response
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de l'image: {e}")
        return None

def extraire_tableaux(response):
    """
    Extrait les tableaux Markdown de la réponse.
    """
    if not response:
        return []
    
    tableaux = []
    lignes = response.split('\n')
    tableau_en_cours = []
    dans_tableau = False
    
    for ligne in lignes:
        if ligne.startswith('|') and '-|-' in ligne.replace(' ', ''):
            # Début d'un tableau ou ligne de séparation
            dans_tableau = True
            tableau_en_cours.append(ligne)
        elif dans_tableau and ligne.startswith('|'):
            # Ligne de tableau
            tableau_en_cours.append(ligne)
        elif dans_tableau:
            # Fin du tableau
            dans_tableau = False
            if tableau_en_cours:
                tableaux.append('\n'.join(tableau_en_cours))
                tableau_en_cours = []
    
    # Ajouter le dernier tableau s'il existe
    if dans_tableau and tableau_en_cours:
        tableaux.append('\n'.join(tableau_en_cours))
    
    return tableaux

def main():
    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("Usage: python utiliser_dots_ocr_api.py <chemin_image> [prompt]")
        return
    
    # Récupérer les arguments
    image_path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Analyser l'image
    resultat = analyser_image_avec_dots_ocr(image_path, prompt)
    
    # Afficher le résultat
    if resultat:
        print("\nRésultat de l'analyse:")
        print("=======================")
        print(resultat)
        print("=======================")
        
        # Extraire et afficher les tableaux
        tableaux = extraire_tableaux(resultat)
        if tableaux:
            print("\nTableaux extraits:")
            for i, tableau in enumerate(tableaux, 1):
                print(f"\nTableau {i}:")
                print(tableau)
    else:
        logger.error("Échec de l'analyse de l'image.")

if __name__ == "__main__":
    main()