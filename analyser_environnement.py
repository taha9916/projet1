import os
import sys
import logging
import time
from PIL import Image

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importer les fonctions nécessaires
try:
    from cloud_api import CloudVisionAPI, extract_environmental_parameters_cloud
    logger.info("Modules importés avec succès.")
except ImportError as e:
    logger.error(f"Impossible d'importer les modules nécessaires: {e}")
    logger.error("Assurez-vous que le fichier cloud_api.py est présent dans le répertoire.")
    sys.exit(1)

def analyser_image_environnementale(image_path, langue="fr"):
    """
    Analyse une image environnementale avec dots.ocr.
    """
    if not os.path.exists(image_path):
        logger.error(f"L'image {image_path} n'existe pas.")
        return None
    
    try:
        # Charger l'image
        img = Image.open(image_path)
        
        # Mesurer le temps d'exécution
        start_time = time.time()
        
        # Créer une instance de CloudVisionAPI avec dots_ocr comme fournisseur
        api = CloudVisionAPI(provider="dots_ocr")
        
        # Construire le prompt environnemental
        prompt = extract_environmental_parameters_cloud(langue=langue)
        logger.info(f"Prompt environnemental généré: {prompt[:100]}...")
        
        # Analyser l'image
        logger.info("Analyse de l'image environnementale...")
        response = api.analyze_image(img, prompt=prompt)
        
        # Calculer le temps d'exécution
        execution_time = time.time() - start_time
        logger.info(f"Analyse terminée en {execution_time:.2f} secondes.")
        
        # Libérer la mémoire
        api.cleanup()
        
        return response
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de l'image: {e}")
        return None

def extraire_parametres(response):
    """
    Extrait les paramètres environnementaux de la réponse.
    """
    if not response:
        return {}
    
    parametres = {}
    lignes = response.split('\n')
    
    for ligne in lignes:
        if ':' in ligne:
            # Essayer d'extraire les paires clé-valeur
            parties = ligne.split(':', 1)
            if len(parties) == 2:
                cle = parties[0].strip()
                valeur = parties[1].strip()
                parametres[cle] = valeur
    
    return parametres

def main():
    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("Usage: python analyser_environnement.py <chemin_image> [langue]")
        print("  langue: fr (par défaut), en, es, etc.")
        return
    
    # Récupérer les arguments
    image_path = sys.argv[1]
    langue = sys.argv[2] if len(sys.argv) > 2 else "fr"
    
    # Analyser l'image
    resultat = analyser_image_environnementale(image_path, langue)
    
    # Afficher le résultat
    if resultat:
        print("\nRésultat de l'analyse environnementale:")
        print("======================================")
        print(resultat)
        print("======================================")
        
        # Extraire et afficher les paramètres
        parametres = extraire_parametres(resultat)
        if parametres:
            print("\nParamètres environnementaux extraits:")
            for cle, valeur in parametres.items():
                print(f"{cle}: {valeur}")
        else:
            print("\nAucun paramètre environnemental n'a pu être extrait.")
    else:
        logger.error("Échec de l'analyse de l'image.")

if __name__ == "__main__":
    main()