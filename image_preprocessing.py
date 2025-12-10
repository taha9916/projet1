import os
import logging
import concurrent.futures
from PIL import Image
import pytesseract
import torch
from config import MODEL_CONFIG

# Configuration du logger
logger = logging.getLogger(__name__)

def extract_text_from_image(image_path):
    """
    Extrait le texte d'une image en utilisant OCR (pytesseract).
    
    Args:
        image_path: Chemin vers l'image à analyser
        
    Returns:
        str: Texte extrait de l'image
    """
    try:
        # Ouvrir l'image
        image = Image.open(image_path)
        
        # Extraire le texte avec OCR
        text = pytesseract.image_to_string(image)
        
        logger.info(f"Texte extrait de l'image {image_path} avec OCR")
        return text
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction de texte de l'image: {str(e)}")
        return ""

def preprocess_image(image_path, max_dimension=1024):
    """
    Prétraite une image en la redimensionnant et en optimisant sa qualité.
    
    Args:
        image_path: Chemin vers l'image à prétraiter
        max_dimension: Dimension maximale (largeur ou hauteur) de l'image
        
    Returns:
        PIL.Image: Image prétraitée
    """
    try:
        # Ouvrir l'image
        image = Image.open(image_path)
        
        # Redimensionner l'image si nécessaire
        width, height = image.size
        if width > max_dimension or height > max_dimension:
            # Calculer le ratio pour préserver les proportions
            ratio = min(max_dimension / width, max_dimension / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            image = image.resize((new_width, new_height), Image.LANCZOS)
            logger.info(f"Image redimensionnée de {width}x{height} à {new_width}x{new_height}")
        
        return image
    except Exception as e:
        logger.error(f"Erreur lors du prétraitement de l'image: {str(e)}")
        return None

def process_image_batch(image_paths, model, processor, max_workers=2):
    """
    Traite un lot d'images en parallèle en utilisant une file d'attente.
    
    Args:
        image_paths: Liste des chemins d'images à traiter
        model: Modèle IA à utiliser pour l'analyse
        processor: Processeur du modèle
        max_workers: Nombre maximum de workers pour le traitement parallèle
        
    Returns:
        dict: Dictionnaire des résultats par chemin d'image
    """
    results = {}
    
    def process_single_image(image_path):
        try:
            # Extraire le texte avec OCR
            extracted_text = extract_text_from_image(image_path)
            
            # Prétraiter l'image
            image = preprocess_image(image_path)
            if image is None:
                return f"Erreur: Impossible de prétraiter l'image {image_path}"
            
            # Préparer le prompt avec le texte extrait
            prompt = f"Analyse cette image et le texte associé extrait par OCR: {extracted_text}\n\nExtrais les paramètres liés à la qualité de l'environnement avec leurs valeurs et unités."
            
            # Utiliser le format de conversation pour SmolVLM
            if MODEL_CONFIG["model_type"] == "smolvlm":
                conversation = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "image": image},
                            {"type": "text", "text": prompt}
                        ]
                    }
                ]
                # Utiliser apply_chat_template pour formater correctement la conversation
                prompt_text = processor.apply_chat_template(conversation, add_generation_prompt=True)
                # Passer l'image directement sans utiliser le paramètre 'image' dans le dictionnaire
                inputs = processor(text=prompt_text, images=image, return_tensors="pt")
            else:
                # Format standard pour les autres modèles
                inputs = processor(text=prompt, images=image, return_tensors="pt")
            
            # Déplacer les entrées sur le même appareil que le modèle
            if hasattr(model, 'device'):
                for key in inputs:
                    if torch.is_tensor(inputs[key]):
                        inputs[key] = inputs[key].to(model.device)
            
            # Générer la réponse avec un nombre limité de tokens
            max_tokens = MODEL_CONFIG.get("max_new_tokens", 250)
            output = model.generate(**inputs, max_new_tokens=max_tokens)
            
            # Décoder la réponse
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(MODEL_CONFIG["model_path"], trust_remote_code=True)
            response = tokenizer.decode(output[0], skip_special_tokens=True)
            
            # Extraire la partie de la réponse après le prompt si nécessaire
            if prompt_text in response:
                response = response[len(prompt_text):].strip()
            
            logger.info(f"Analyse de l'image {image_path} terminée avec succès")
            return response
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'image {image_path}: {str(e)}")
            return f"Erreur: {str(e)}"
    
    # Utiliser ThreadPoolExecutor pour traiter les images en parallèle
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Soumettre les tâches et stocker les futures
        future_to_path = {executor.submit(process_single_image, path): path for path in image_paths}
        
        # Récupérer les résultats au fur et à mesure qu'ils sont disponibles
        for future in concurrent.futures.as_completed(future_to_path):
            path = future_to_path[future]
            try:
                results[path] = future.result()
            except Exception as e:
                logger.error(f"Exception lors du traitement de {path}: {str(e)}")
                results[path] = f"Erreur: {str(e)}"
    
    return results