import os
import sys
import logging
import torch
from PIL import Image

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def tester_dots_ocr_cpu():
    """
    Teste si le modèle dots.ocr peut être chargé en mode CPU sans flash_attn.
    """
    try:
        logger.info("Importation des bibliothèques nécessaires...")
        from transformers import AutoModelForCausalLM, AutoProcessor
        
        logger.info("Vérification des versions des bibliothèques...")
        import transformers
        logger.info(f"Version de transformers: {transformers.__version__}")
        logger.info(f"Version de torch: {torch.__version__}")
        
        logger.info("Tentative de chargement du processeur dots.ocr...")
        model_name = "rednote-hilab/dots.ocr"
        
        # Création du répertoire de cache si nécessaire
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "dots_ocr")
        os.makedirs(cache_dir, exist_ok=True)
        
        # Charger uniquement le processeur pour tester
        processor = AutoProcessor.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            trust_remote_code=True
        )
        logger.info("Processeur chargé avec succès!")
        
        # Tenter de charger le modèle avec différentes configurations
        logger.info("Tentative 1: Chargement du modèle en mode CPU avec attn_implementation='eager'...")
        try:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="cpu",
                torch_dtype=torch.float32,
                load_in_4bit=False,
                cache_dir=cache_dir,
                trust_remote_code=True,
                attn_implementation="eager",
                low_cpu_mem_usage=True
            )
            logger.info("Modèle chargé avec succès en mode CPU avec attn_implementation='eager'!")
            return True, "CPU avec attn_implementation='eager'"
        except Exception as e:
            logger.warning(f"Échec de la tentative 1: {str(e)}")
        
        logger.info("Tentative 2: Chargement du modèle en mode CPU sans trust_remote_code...")
        try:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="cpu",
                torch_dtype=torch.float32,
                load_in_4bit=False,
                cache_dir=cache_dir,
                trust_remote_code=False,
                low_cpu_mem_usage=True
            )
            logger.info("Modèle chargé avec succès en mode CPU sans trust_remote_code!")
            return True, "CPU sans trust_remote_code"
        except Exception as e:
            logger.warning(f"Échec de la tentative 2: {str(e)}")
        
        logger.info("Tentative 3: Chargement du modèle avec use_flash_attention_2=False...")
        try:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="cpu",
                torch_dtype=torch.float32,
                load_in_4bit=False,
                cache_dir=cache_dir,
                trust_remote_code=True,
                use_flash_attention_2=False,
                low_cpu_mem_usage=True
            )
            logger.info("Modèle chargé avec succès avec use_flash_attention_2=False!")
            return True, "CPU avec use_flash_attention_2=False"
        except Exception as e:
            logger.warning(f"Échec de la tentative 3: {str(e)}")
        
        logger.error("Toutes les tentatives de chargement du modèle ont échoué.")
        return False, "Échec de toutes les tentatives"
    
    except Exception as e:
        logger.error(f"Erreur lors du test: {str(e)}")
        return False, str(e)

def main():
    logger.info("=== Test de chargement du modèle dots.ocr en mode CPU ===")
    
    # Vérifier si CUDA est disponible
    if torch.cuda.is_available():
        logger.info("CUDA est disponible, mais le test sera effectué en mode CPU.")
    else:
        logger.info("CUDA n'est pas disponible. Le test sera effectué en mode CPU.")
    
    # Tester le chargement du modèle
    succes, message = tester_dots_ocr_cpu()
    
    # Afficher le résultat
    if succes:
        logger.info(f"Test réussi! Le modèle peut être chargé en mode: {message}")
        print("\n=== SUCCÈS ===\n")
        print(f"Le modèle dots.ocr peut être chargé en mode: {message}")
        print("\nVous pouvez maintenant utiliser les scripts fournis pour analyser des images.")
    else:
        logger.error(f"Test échoué! Raison: {message}")
        print("\n=== ÉCHEC ===\n")
        print("Le modèle dots.ocr ne peut pas être chargé en mode CPU.")
        print(f"Raison: {message}")
        print("\nVeuillez consulter le README_DOTS_OCR.md pour des alternatives.")

if __name__ == "__main__":
    main()