import os
import logging
from huggingface_hub import snapshot_download

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Définir le modèle à télécharger et le répertoire de destination
MODEL_ID = "rednote-hilab/dots.ocr"
LOCAL_DIR = os.path.join("models", "dots_ocr")

def download_model_files():
    """
    Télécharge les fichiers du modèle et du processeur depuis Hugging Face Hub
    vers un répertoire local.
    """
    logger.info(f"Début du téléchargement du modèle {MODEL_ID} vers {LOCAL_DIR}")

    # Créer le répertoire de destination s'il n'existe pas
    os.makedirs(LOCAL_DIR, exist_ok=True)

    try:
        # Utiliser snapshot_download pour télécharger tous les fichiers du repo
        snapshot_download(
            repo_id=MODEL_ID,
            local_dir=LOCAL_DIR,
            local_dir_use_symlinks=False,  # Important pour Windows
            force_download=True  # Forcer le re-téléchargement pour garantir l'intégrité
        )
        logger.info(f"Modèle {MODEL_ID} téléchargé avec succès dans {LOCAL_DIR}")
        
        # Vérifier que les fichiers essentiels sont présents
        required_files = ['config.json', 'pytorch_model.bin', 'processor_config.json']
        missing_files = [f for f in required_files if not os.path.exists(os.path.join(LOCAL_DIR, f))]
        if missing_files:
            logger.error(f"Fichiers manquants après le téléchargement : {missing_files}")
            return False
        return True

    except Exception as e:
        logger.error(f"Une erreur est survenue lors du téléchargement du modèle : {e}")
        return False

if __name__ == "__main__":
    download_model_files()
