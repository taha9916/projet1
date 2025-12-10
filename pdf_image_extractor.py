import os
import logging
import tempfile
import pdfplumber
from PIL import Image
import pytesseract
from utils import extract_text_from_file
from image_preprocessing import extract_text_from_image, preprocess_image
from model_interface import analyze_environmental_image

# Configuration du logger
logger = logging.getLogger(__name__)

def extract_images_from_pdf(pdf_path, output_dir=None):
    """
    Extrait toutes les images d'un fichier PDF et les sauvegarde dans un répertoire temporaire.
    
    Args:
        pdf_path (str): Chemin vers le fichier PDF
        output_dir (str, optional): Répertoire de sortie pour les images. Si None, un répertoire temporaire est créé.
        
    Returns:
        tuple: (liste des chemins des images extraites, répertoire de sortie)
    """
    logger.info(f"Extraction des images depuis le PDF: {pdf_path}")
    
    # Vérifier que le fichier existe
    if not os.path.exists(pdf_path):
        logger.error(f"Le fichier PDF {pdf_path} n'existe pas")
        return [], None
    
    # Créer un répertoire temporaire si nécessaire
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="pdf_images_")
    else:
        os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Les images extraites seront sauvegardées dans: {output_dir}")
    
    extracted_images = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                # Extraire les images de la page
                for j, img in enumerate(page.images):
                    # Obtenir les données de l'image
                    image_data = img["stream"].get_data()
                    
                    # Créer un nom de fichier pour l'image
                    image_filename = f"page_{i+1}_image_{j+1}.png"
                    image_path = os.path.join(output_dir, image_filename)
                    
                    # Sauvegarder l'image
                    with open(image_path, "wb") as f:
                        f.write(image_data)
                    
                    extracted_images.append(image_path)
                    logger.info(f"Image extraite: {image_path}")
        
        logger.info(f"Extraction terminée: {len(extracted_images)} images extraites")
        return extracted_images, output_dir
    
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des images: {str(e)}")
        return [], output_dir

def analyze_pdf_with_images(pdf_path, model=None):
    """
    Analyse un fichier PDF en extrayant à la fois le texte et les images.
    
    Args:
        pdf_path (str): Chemin vers le fichier PDF à analyser
        model: Modèle d'analyse à utiliser (si None, un modèle par défaut sera utilisé)
        
    Returns:
        dict: Résultats de l'analyse combinée
    """
    logger.info(f"Analyse complète du PDF avec texte et images: {pdf_path}")
    
    results = {
        "text_analysis": None,
        "image_analysis": [],
        "combined_parameters": []
    }
    
    # 1. Extraire et analyser le texte
    text_content = extract_text_from_file(pdf_path)
    if text_content:
        logger.info(f"Texte extrait du PDF: {len(text_content)} caractères")
        # Analyser le texte (à implémenter selon le modèle utilisé)
        # results["text_analysis"] = analyze_text_content(text_content)
    else:
        logger.warning("Aucun texte extrait du PDF")
    
    # 2. Extraire et analyser les images
    extracted_images, temp_dir = extract_images_from_pdf(pdf_path)
    
    if extracted_images:
        logger.info(f"{len(extracted_images)} images extraites pour analyse")
        
        for image_path in extracted_images:
            try:
                # Extraire le texte de l'image avec OCR
                image_text = extract_text_from_image(image_path)
                
                # Prétraiter l'image
                processed_image = preprocess_image(image_path)
                
                # Analyser l'image
                image_analysis = analyze_environmental_image(
                    image_path, 
                    model, 
                    use_ocr=True,
                    base_prompt="Extrais les paramètres environnementaux avec leurs valeurs et unités."
                )
                
                if image_analysis:
                    results["image_analysis"].append({
                        "image_path": image_path,
                        "extracted_text": image_text,
                        "analysis_results": image_analysis
                    })
                    
                    # Ajouter les paramètres trouvés à la liste combinée
                    if isinstance(image_analysis, list):
                        results["combined_parameters"].extend(image_analysis)
            
            except Exception as e:
                logger.error(f"Erreur lors de l'analyse de l'image {image_path}: {str(e)}")
    else:
        logger.warning("Aucune image extraite du PDF")
    
    # 3. Combiner et dédupliquer les résultats
    # TODO: Implémenter la déduplication des paramètres trouvés
    
    return results

def process_pdf_batch(pdf_dir, output_dir=None, model=None):
    """
    Traite un lot de fichiers PDF en extrayant et analysant le texte et les images.
    
    Args:
        pdf_dir (str): Répertoire contenant les fichiers PDF à analyser
        output_dir (str, optional): Répertoire de sortie pour les résultats
        model: Modèle d'analyse à utiliser
        
    Returns:
        dict: Résultats de l'analyse pour chaque fichier PDF
    """
    logger.info(f"Traitement par lot des PDF dans {pdf_dir}")
    
    if output_dir is None:
        output_dir = os.path.join(pdf_dir, "resultats_analyse")
    
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    
    # Parcourir tous les fichiers PDF du répertoire
    for filename in os.listdir(pdf_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, filename)
            logger.info(f"Traitement du PDF: {filename}")
            
            # Analyser le PDF
            pdf_results = analyze_pdf_with_images(pdf_path, model)
            
            # Stocker les résultats
            results[filename] = pdf_results
            
            # TODO: Sauvegarder les résultats dans un format approprié (Excel, JSON, etc.)
    
    return results