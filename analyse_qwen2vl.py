import os
import logging
import pandas as pd
from PIL import Image

# Import des modules du projet
from model_interface import QwenVLModel, analyze_environmental_image
from utils import save_dataframe_to_excel
from config import MODEL_CONFIG, OUTPUT_DIR

logger = logging.getLogger(__name__)

def analyser_image_environnementale(image_path, prompt=None, output_excel=None):
    """Analyse une image environnementale et retourne les résultats."""
    logger.info(f"Analyse de l'image environnementale: {image_path}")
    
    # Vérifier que le fichier existe
    if not os.path.exists(image_path):
        logger.error(f"Le fichier image n'existe pas: {image_path}")
        return None, f"Erreur: Le fichier {image_path} n'existe pas."
    
    # Définir le prompt par défaut si non spécifié
    if prompt is None:
        prompt = "Extrais les paramètres liés à la qualité de l'environnement avec leurs valeurs et unités."
    
    try:
        # Utiliser l'interface du modèle pour analyser l'image
        df, response = analyze_environmental_image(image_path, prompt)
        
        # Sauvegarder les résultats si un DataFrame a été généré
        if df is not None and not df.empty:
            if output_excel is None:
                # Générer un nom de fichier basé sur le nom de l'image
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                output_excel = os.path.join(OUTPUT_DIR, f"{base_name}_resultats.xlsx")
            
            # Sauvegarder le DataFrame
            os.makedirs(os.path.dirname(output_excel), exist_ok=True)
            df.to_excel(output_excel, index=False)
            logger.info(f"Résultats sauvegardés dans {output_excel}")
        
        return df, response
    
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de l'image: {str(e)}")
        return None, f"Erreur: {str(e)}"

def extraire_parametres_batch(dossier_images, prompt=None, dossier_sortie=None):
    """Traite un lot d'images et extrait les paramètres environnementaux."""
    if dossier_sortie is None:
        dossier_sortie = OUTPUT_DIR
    
    os.makedirs(dossier_sortie, exist_ok=True)
    logger.info(f"Traitement par lot des images dans {dossier_images}")
    
    resultats = []
    extensions_images = [".jpg", ".jpeg", ".png"]
    
    # Charger le modèle une seule fois pour toutes les images
    model = QwenVLModel()
    model.load_model()
    
    for filename in os.listdir(dossier_images):
        ext = os.path.splitext(filename)[1].lower()
        if ext in extensions_images:
            image_path = os.path.join(dossier_images, filename)
            logger.info(f"Traitement de l'image: {filename}")
            
            try:
                # Analyser l'image
                image = Image.open(image_path)
                inputs = model.processor(text=prompt or "Extrais les paramètres environnementaux avec leurs valeurs et unités.", 
                                        images=image, return_tensors="pt")
                output = model.model.generate(**inputs, max_new_tokens=MODEL_CONFIG["max_new_tokens"])
                response = model.processor.decode(output[0], skip_special_tokens=True)
                
                # Extraire les paramètres
                df = model.extract_parameters(response)
                
                if not df.empty:
                    # Sauvegarder les résultats individuels
                    output_excel = os.path.join(dossier_sortie, f"{os.path.splitext(filename)[0]}_resultats.xlsx")
                    df.to_excel(output_excel, index=False)
                    
                    # Ajouter aux résultats globaux
                    resultats.append({
                        "fichier": filename,
                        "parametres_extraits": len(df),
                        "resultat": output_excel
                    })
                    logger.info(f"Extraction réussie pour {filename}: {len(df)} paramètres")
                else:
                    logger.warning(f"Aucun paramètre extrait de {filename}")
            
            except Exception as e:
                logger.error(f"Erreur lors du traitement de {filename}: {str(e)}")
    
    # Créer un rapport de synthèse
    if resultats:
        rapport_df = pd.DataFrame(resultats)
        rapport_path = os.path.join(dossier_sortie, "rapport_extraction_images.xlsx")
        rapport_df.to_excel(rapport_path, index=False)
        logger.info(f"Rapport de synthèse sauvegardé dans {rapport_path}")
    
    return resultats

if __name__ == "__main__":
    # Exemple d'utilisation du script
    import sys
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        prompt = sys.argv[2] if len(sys.argv) > 2 else None
        
        print(f"Analyse de l'image: {image_path}")
        df, response = analyser_image_environnementale(image_path, prompt)
        
        if df is not None:
            print("\nParamètres extraits:")
            print(df)
        
        print("\nRéponse complète du modèle:")
        print(response)
    else:
        print("Usage: python analyse_qwen2vl.py <chemin_image> [prompt]")