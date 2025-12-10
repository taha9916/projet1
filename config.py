import os

# Chemins de base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "Qwen2-VL-7B-Instruct")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Créer le dossier de sortie s'il n'existe pas
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configuration du modèle IA
MODEL_CONFIG = {
    # Modèle par défaut
    "model_name": "dots.ocr",  # Utiliser dots.ocr comme modèle par défaut
    "model_type": "dots_ocr",  # Type de modèle (qwen2-vl, smolvlm, moondream, dots_ocr)
    "model_path": "models/dots_ocr",  # Chemin local
    "max_new_tokens": 500,
    "temperature": 0.7,
    "device_map": "cpu",      # Forcer l'utilisation du CPU
    "torch_dtype": "float32",  # Utiliser float32
    
    # Alternatives disponibles
    "available_models": {
        "SmolVLM-2B": {
            "type": "smolvlm",
            "path": "HuggingFaceTB/SmolVLM-Instruct",
            "description": "Modèle léger (2B paramètres) avec bonne performance et faible consommation mémoire"
        },
        "Moondream-2B": {
            "type": "moondream",
            "path": "vikhyatk/moondream2",
            "description": "Modèle compact (2B paramètres) optimisé pour les appareils à ressources limitées"
        },
        "Qwen2-VL-7B-Instruct": {
            "type": "qwen",
            "path": MODEL_DIR,  # Installation locale
            "description": "Modèle original plus grand (7B paramètres) avec haute précision mais consommation mémoire élevée"
        },
        "dots.ocr": {
            "type": "dots_ocr",
            "path": "models/dots_ocr",
            "description": "Modèle spécialisé pour l'OCR et l'analyse d'images avec texte"
        }
    },
    
    # Paramètres de traitement par lots (optimisés pour la performance)
    "batch_processing": {
        "text_chunk_size": 1000,   # Taille des morceaux de texte
        "text_overlap": 100,       # Chevauchement entre morceaux de texte
        "image_tile_size": 512,    # Taille des tuiles d'image (réduite pour accélérer le traitement)
        "image_overlap": 50        # Chevauchement entre tuiles d'image (réduit pour limiter le nombre de tuiles)
    }
}

# Configuration de l'interface utilisateur
UI_CONFIG = {
    "window_title": "Analyse de Risque Environnemental - Maroc",
    "window_width": 800,
    "window_height": 600,
    "padding": 10,
}

# Types de fichiers supportés
SUPPORTED_FILE_TYPES = {
    "Tous les fichiers supportés": "*.xlsx *.csv *.txt *.pdf *.docx *.png *.jpg *.jpeg",
    "Fichiers Excel": "*.xlsx",
    "Fichiers CSV": "*.csv",
    "Fichiers texte": "*.txt",
    "Fichiers PDF": "*.pdf",
    "Fichiers Word": "*.docx",
    "Images": "*.png *.jpg *.jpeg"
}

# Requêtes web
WEB_CONFIG = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "search_url": "https://www.google.com/search?q={query}",
}

# Configuration des API Cloud pour l'analyse d'images
CLOUD_API_CONFIG = {
    # OpenAI API
    "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),  # Clé API OpenAI
    "OPENAI_MODEL": "gpt-4-vision-preview",  # Modèle OpenAI pour la vision
    
    # Azure Computer Vision API
    "AZURE_API_KEY": os.environ.get("AZURE_API_KEY", ""),  # Clé API Azure
    "AZURE_ENDPOINT": os.environ.get("AZURE_ENDPOINT", "https://your-resource.cognitiveservices.azure.com/"),
    
    # Google Cloud Vision API
    "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY", ""),  # Clé API Google
    
    # Qwen API
    "QWEN_API_KEY": os.environ.get("QWEN_API_KEY", ""),  # Clé API Qwen
    "QWEN_ENDPOINT": os.environ.get("QWEN_ENDPOINT", "https://dashscope.aliyuncs.com/api/v1/services/vision/multimodal-generation"),
    "QWEN_MODEL": "qwen-vl-plus",  # Modèle Qwen pour la vision
    
    # OpenRouter API
    "OPENROUTER_API_KEY": os.environ.get("OPENROUTER_API_KEY", ""),  # Clé API OpenRouter
    "OPENROUTER_MODEL": "anthropic/claude-3-opus-20240229-vision",  # Modèle OpenRouter pour la vision
    
    # Paramètres généraux
    "MAX_TOKENS": 4000,  # Nombre maximum de tokens pour les réponses
    "TEMPERATURE": 0.7,  # Température pour la génération de texte
    "DEFAULT_PROVIDER": "openai"  # Fournisseur par défaut
}

# Paramètres de logging
LOG_CONFIG = {
    # Fichier de log principal
    "log_file": os.path.join(BASE_DIR, "app.log"),
    "log_level": "INFO",
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "encoding": "utf-8",
    
    # Rotation des fichiers de log
    "max_bytes": 10 * 1024 * 1024,  # 10 Mo par fichier
    "backup_count": 5,             # Conserver 5 fichiers de backup
    
    # Sortie console
    "console_output": True,        # Afficher les logs dans la console
    
    # Fichiers de log spécifiques
    "error_log_file": os.path.join(BASE_DIR, "logs", "error.log"),  # Log des erreurs uniquement
    "audit_log_file": os.path.join(BASE_DIR, "logs", "audit.log"),  # Log d'audit (actions importantes)
    
    # Configuration des loggers tiers
    "third_party_loggers": {
        "PIL": "WARNING",
        "matplotlib": "WARNING",
        "requests": "WARNING",
        "urllib3": "WARNING",
        "transformers": "WARNING",
        "torch": "WARNING"
    },
    
    # Niveaux de log par module
    "module_levels": {
        "data_processing": "INFO",
        "model_interface": "INFO",
        "cloud_api": "DEBUG",      # Plus détaillé pour les API cloud
        "image_preprocessing": "INFO"
    }
}