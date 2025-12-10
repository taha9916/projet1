import os
import sys
import logging
import torch
from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def charger_dots_ocr():
    """
    Charge le modèle dots.ocr directement depuis Hugging Face.
    """
    try:
        logger.info("Chargement du modèle dots.ocr...")
        
        # Définir le nom du modèle
        model_name = "rednote-hilab/dots.ocr"
        
        # Création du répertoire de cache si nécessaire
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "dots_ocr")
        os.makedirs(cache_dir, exist_ok=True)
        logger.info(f"Utilisation du répertoire de cache: {cache_dir}")
        
        # Télécharger d'abord le processeur (plus petit)
        logger.info("Chargement du processeur...")
        processor = AutoProcessor.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            trust_remote_code=True
        )
        
        # Charger le modèle pour CPU uniquement
        logger.info("Chargement du modèle pour CPU (cela peut prendre plusieurs minutes)...")
        try:
            # Forcer l'utilisation du CPU pour éviter les problèmes de flash_attn
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="cpu",  # Forcer l'utilisation du CPU
                torch_dtype=torch.float32,  # Utiliser float32 pour CPU
                load_in_4bit=False,  # Désactiver la quantification 4-bit sur CPU
                cache_dir=cache_dir,
                trust_remote_code=True,
                attn_implementation="eager",
                low_cpu_mem_usage=True  # Optimiser pour CPU avec mémoire limitée
            )
            logger.warning("Modèle chargé en mode CPU. Les performances seront réduites.")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {str(e)}")
            logger.warning("Tentative de chargement avec des paramètres alternatifs...")
            # Essayer avec des paramètres plus simples
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="cpu",
                torch_dtype=torch.float32,
                cache_dir=cache_dir,
                trust_remote_code=False,  # Désactiver le code distant
                low_cpu_mem_usage=True
            )
        
        return model, processor
    except Exception as e:
        logger.error(f"Échec du chargement du modèle: {e}")
        return None, None

def analyser_image(model, processor, image_path, prompt=None):
    """
    Analyse une image avec le modèle dots.ocr.
    """
    if not os.path.exists(image_path):
        logger.error(f"L'image {image_path} n'existe pas.")
        return None
    
    try:
        # Charger l'image
        img = Image.open(image_path)
        
        # Préparer les inputs
        inputs = processor(images=img, return_tensors="pt")
        
        # Déplacer les inputs sur le même device que le modèle
        for k, v in inputs.items():
            if isinstance(v, torch.Tensor):
                inputs[k] = v.to(model.device)
        
        # Si un prompt est fourni, l'ajouter
        if prompt:
            inputs["prompt"] = prompt
        
        # Générer la réponse
        logger.info("Génération de la réponse...")
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=1000,  # Ajuster selon vos besoins
            do_sample=False,
            num_beams=1  # Désactiver beam search pour simplifier
        )
        
        # Décoder la réponse
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        # Libérer la mémoire
        del inputs
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        return generated_text
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de l'image: {e}")
        return None

def main():
    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("Usage: python utiliser_dots_ocr.py <chemin_image> [prompt]")
        return
    
    # Récupérer les arguments
    image_path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Charger le modèle
    model, processor = charger_dots_ocr()
    if model is None or processor is None:
        logger.error("Impossible de charger le modèle. Arrêt du programme.")
        return
    
    # Analyser l'image
    resultat = analyser_image(model, processor, image_path, prompt)
    
    # Afficher le résultat
    if resultat:
        print("\nRésultat de l'analyse:")
        print("=======================")
        print(resultat)
        print("=======================")
    else:
        logger.error("Échec de l'analyse de l'image.")
    
    # Libérer la mémoire
    del model, processor
    torch.cuda.empty_cache() if torch.cuda.is_available() else None

if __name__ == "__main__":
    main()