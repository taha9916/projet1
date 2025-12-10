from transformers import AutoProcessor, AutoTokenizer, AutoModelForCausalLM
from PIL import Image
import pandas as pd
import os
import logging
import torch
from config import MODEL_CONFIG
import gc
from cloud_api import CloudVisionAPI

logger = logging.getLogger(__name__)

def analyze_environmental_image(image_path, prompt=None):
    """Fonction utilitaire pour analyser une image environnementale.
    
    Cette fonction est un wrapper autour de CloudVisionAPI pour faciliter
    l'analyse d'images environnementales.
    
    Args:
        image_path: Chemin vers l'image à analyser
        prompt: Instructions spécifiques pour l'analyse (optionnel)
        
    Returns:
        str: Résultat de l'analyse
    """
    try:
        # Utiliser un prompt par défaut si aucun n'est fourni
        if not prompt:
            prompt = "Analysez cette image et identifiez les risques environnementaux potentiels."
        
        # Créer une instance de CloudVisionAPI et analyser l'image
        cloud_api = CloudVisionAPI()
        result = cloud_api.analyze_image(image_path, prompt)
        return result
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse environnementale de l'image: {str(e)}")
        return f"Erreur: {str(e)}"

class VLModel:
    def __init__(self, model_path=None):
        """Initialise le modèle Vision-Language."""
        self.model_path = model_path or MODEL_CONFIG["model_path"]
        self.model = None
        self.processor = None
        self.tokenizer = None
        self.model_type = MODEL_CONFIG.get("model_type", "qwen2-vl")
        logger.info(f"Initialisation du modèle {self.model_type} depuis {self.model_path}")


class QwenVLModel(VLModel):
    def __init__(self, model_path=None):
        """Initialise le modèle Qwen Vision-Language via l'API Cloud.
        
        Cette classe est un wrapper autour de CloudVisionAPI pour maintenir
        la compatibilité avec le code existant.
        
        Args:
            model_path: Ignoré, conservé pour compatibilité avec l'interface existante
        """
        super().__init__(model_path)
        self.cloud_api = CloudVisionAPI()
        logger.info("Initialisation du modèle QwenVLModel via l'API Cloud")
    
    def analyze_image(self, image_path, prompt, max_new_tokens=None, **kwargs):
        """Analyse une image avec l'API Cloud.
        
        Args:
            image_path: Chemin vers l'image à analyser
            prompt: Instruction textuelle pour l'analyse
            max_new_tokens: Ignoré, conservé pour compatibilité
            **kwargs: Arguments supplémentaires ignorés
        """
        try:
            logger.info(f"Analyse de l'image via l'API Cloud: {image_path}")
            
            # Utiliser l'API Cloud pour analyser l'image
            result = self.cloud_api.analyze_image(image_path, prompt)
            return result
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de l'image via l'API Cloud: {str(e)}")
            return f"Erreur: {str(e)}"
    
    def load_model(self):
        """Charge le modèle et le processeur."""
        try:
            logger.info(f"Chargement du modèle {self.model_type}...")
            
            # Libérer la mémoire avant de charger le modèle
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
            
            # Chargement du modèle en fonction du type
            if self.model_type == "qwen2-vl":
                # Utiliser AutoModelForCausalLM pour Qwen2-VL avec trust_remote_code
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.float16,  # Utiliser la précision réduite
                    device_map="auto",  # Répartir sur les GPU disponibles
                    trust_remote_code=True
                )
            elif self.model_type == "smolvlm":
                # Utiliser AutoModelForVision2Seq pour SmolVLM
                from transformers import AutoModelForVision2Seq
                self.model = AutoModelForVision2Seq.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True
                )
            elif self.model_type == "moondream":
                # Utiliser AutoModelForCausalLM pour Moondream avec trust_remote_code
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True
                )
            else:
                logger.error(f"Type de modèle non supporté: {self.model_type}")
                return False
                
            self.processor = AutoProcessor.from_pretrained(self.model_path, trust_remote_code=True)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
            logger.info("Modèle chargé avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {str(e)}")
            return False
    
    def analyze_image(self, image_path, prompt, max_new_tokens=None, tile_size=512, overlap=50):
        """Analyse une image avec le modèle Vision-Language.
        
        Args:
            image_path: Chemin vers l'image à analyser
            prompt: Instruction textuelle pour l'analyse
            max_new_tokens: Nombre maximum de tokens à générer
            tile_size: Taille des tuiles pour le traitement par lots des grandes images (réduit à 512)
            overlap: Chevauchement entre les tuiles pour maintenir le contexte (réduit à 50)
        """
        if not self.model or not self.processor:
            if not self.load_model():
                return "Erreur: Impossible de charger le modèle."
        
        try:
            logger.info(f"Analyse de l'image: {image_path}")
            
            # S'assurer que le prompt n'est jamais vide
            if not prompt:
                prompt = "Extrais les paramètres liés à la qualité de l'environnement avec leurs valeurs et unités."
                logger.info("Prompt vide détecté, utilisation du prompt par défaut")
            
            # Charger l'image et la redimensionner pour accélérer le traitement
            image = Image.open(image_path)
            
            # Redimensionner l'image si elle est trop grande (max 1024px)
            max_dimension = 1024
            width, height = image.size
            if width > max_dimension or height > max_dimension:
                # Calculer le ratio pour préserver les proportions
                ratio = min(max_dimension / width, max_dimension / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                image = image.resize((new_width, new_height), Image.LANCZOS)
                width, height = new_width, new_height
                logger.info(f"Image redimensionnée à {width}x{height} pour optimiser les performances")
            
            # Si l'image est très grande, la diviser en tuiles
            if width > tile_size or height > tile_size:
                logger.info(f"Image de grande taille détectée ({width}x{height}), traitement par tuiles")
                
                # Diviser l'image en tuiles avec chevauchement
                tiles = []
                tile_positions = []
                
                # Réduire le nombre de tuiles en augmentant l'écart entre elles
                for y in range(0, height, tile_size - overlap):
                    for x in range(0, width, tile_size - overlap):
                        # Définir les limites de la tuile
                        right = min(x + tile_size, width)
                        bottom = min(y + tile_size, height)
                        
                        # Extraire la tuile
                        tile = image.crop((x, y, right, bottom))
                        tiles.append(tile)
                        tile_positions.append((x, y, right, bottom))
                
                # Analyser chaque tuile et combiner les résultats
                all_responses = []
                
                # Limiter le nombre de tuiles à analyser (max 4)
                max_tiles = min(4, len(tiles))
                logger.info(f"Limitation à {max_tiles} tuiles pour optimiser les performances")
                
                for idx, (tile, position) in enumerate(zip(tiles[:max_tiles], tile_positions[:max_tiles])):
                    logger.info(f"Traitement de la tuile {idx+1}/{max_tiles} - Position: {position}")
                    
                    # Libérer la mémoire entre les traitements
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    
                    # Préparer l'entrée pour cette tuile
                    tile_prompt = f"{prompt} (Section {idx+1}/{len(tiles)} de l'image)"
                    
                    # Utiliser le format de conversation pour SmolVLM
                    if self.model_type == "smolvlm":
                        # Format de conversation pour SmolVLM
                        conversation = [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "image", "image": tile},
                                    {"type": "text", "text": tile_prompt}
                                ]
                            }
                        ]
                        # Utiliser apply_chat_template pour formater correctement la conversation
                        prompt_text = self.processor.apply_chat_template(conversation, add_generation_prompt=True)
                        # Passer l'image directement sans utiliser le paramètre 'image' dans le dictionnaire
                        inputs = self.processor(text=prompt_text, images=tile, return_tensors="pt")
                    else:
                        # Format standard pour les autres modèles
                        inputs = self.processor(text=tile_prompt, images=tile, return_tensors="pt")
                    
                    # Déplacer les entrées sur le même appareil que le modèle
                    if hasattr(self.model, 'device'):
                        for key in inputs:
                            if torch.is_tensor(inputs[key]):
                                inputs[key] = inputs[key].to(self.model.device)
                    
                    max_tokens = max_new_tokens or MODEL_CONFIG["max_new_tokens"]
                    output = self.model.generate(**inputs, max_new_tokens=max_tokens)
                    tile_response = self.tokenizer.decode(output[0], skip_special_tokens=True)
                    
                    # Extraire la partie de la réponse après le prompt si nécessaire
                    if tile_prompt in tile_response:
                        tile_response = tile_response[len(tile_prompt):].strip()
                    
                    all_responses.append(f"Section {idx+1}/{len(tiles)} - Position {position}:\n{tile_response}")
                
                # Combiner toutes les réponses
                combined_response = "\n\n".join(all_responses)
                combined_response = f"Analyse par tuiles de l'image {image_path}:\n\n{combined_response}"
                response = combined_response
            else:
                # Traitement normal pour les images de taille standard
                # Utiliser le format de conversation pour SmolVLM
                if self.model_type == "smolvlm":
                    # Format de conversation pour SmolVLM
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
                    prompt_text = self.processor.apply_chat_template(conversation, add_generation_prompt=True)
                    # Passer l'image directement sans utiliser le paramètre 'image' dans le dictionnaire
                    inputs = self.processor(text=prompt_text, images=image, return_tensors="pt")
                else:
                    # Format standard pour les autres modèles
                    inputs = self.processor(text=prompt, images=image, return_tensors="pt")
                
                # Déplacer les entrées sur le même appareil que le modèle
                if hasattr(self.model, 'device'):
                    for key in inputs:
                        if torch.is_tensor(inputs[key]):
                            inputs[key] = inputs[key].to(self.model.device)
                
                max_tokens = max_new_tokens or MODEL_CONFIG["max_new_tokens"]
                output = self.model.generate(**inputs, max_new_tokens=max_tokens)
                # Utiliser self.tokenizer.decode au lieu de self.processor.decode pour être cohérent
                response = self.tokenizer.decode(output[0], skip_special_tokens=True)
            
            logger.info("Analyse d'image terminée avec succès")
            return response
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de l'image: {str(e)}")
            return f"Erreur: {str(e)}"
    
    def analyze_text(self, text, prompt=None, max_new_tokens=None, chunk_size=1000, overlap=100):
        """Analyse un texte avec le modèle Vision-Language.
        
        Args:
            text: Texte à analyser
            prompt: Instruction textuelle pour l'analyse
            max_new_tokens: Nombre maximum de tokens à générer
            chunk_size: Taille des morceaux de texte pour le traitement par lots
            overlap: Chevauchement entre les morceaux pour maintenir le contexte
        """
        if not self.model or not self.tokenizer:
            if not self.load_model():
                return pd.DataFrame()
        
        try:
            logger.info("Analyse de texte en cours...")
            default_prompt = "Extrais tous les paramètres environnementaux avec leurs valeurs et unités à partir du texte suivant. Assure-toi d'analyser l'intégralité du texte et de fournir une liste complète et structurée de tous les paramètres trouvés. Pour chaque paramètre, indique clairement sa valeur et son unité au format 'Paramètre: Valeur Unité'. Voici le texte: "
            prompt_text = prompt or default_prompt
            
            # Vérifier si le texte est très long et doit être traité par lots
            if len(text) > chunk_size:
                logger.info(f"Texte de grande taille détecté ({len(text)} caractères), traitement par lots")
                
                # Diviser le texte en morceaux avec chevauchement
                chunks = []
                start = 0
                while start < len(text):
                    end = min(start + chunk_size, len(text))
                    # Ajuster la fin pour éviter de couper au milieu d'un mot
                    if end < len(text):
                        # Chercher le dernier espace avant la fin du morceau
                        while end > start and text[end] != ' ':
                            end -= 1
                        if end == start:  # Si aucun espace n'est trouvé, utiliser la fin originale
                            end = min(start + chunk_size, len(text))
                    
                    chunks.append(text[start:end])
                    start = end - overlap  # Chevauchement pour maintenir le contexte
                
                # Analyser chaque morceau et combiner les résultats
                all_parameters = []
                all_values = []
                all_units = []
                
                for idx, chunk in enumerate(chunks):
                    logger.info(f"Traitement du morceau {idx+1}/{len(chunks)}")
                    
                    # Libérer la mémoire entre les traitements
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    
                    # Ajouter des instructions spécifiques pour ce morceau
                    chunk_prompt = f"{prompt_text}\n\nCeci est le morceau {idx+1} sur {len(chunks)} du texte complet. Analyse-le en détail et extrait tous les paramètres environnementaux:\n\n{chunk}"
                    inputs = self.tokenizer(chunk_prompt, return_tensors="pt")
                    
                    # Déplacer les entrées sur le même appareil que le modèle
                    if hasattr(self.model, 'device'):
                        for key in inputs:
                            if torch.is_tensor(inputs[key]):
                                inputs[key] = inputs[key].to(self.model.device)
                    
                    # Augmenter le nombre de tokens générés pour les textes longs
                    max_tokens = max_new_tokens or MODEL_CONFIG["max_new_tokens"]
                    output = self.model.generate(**inputs, max_new_tokens=max_tokens)
                    chunk_response = self.tokenizer.decode(output[0], skip_special_tokens=True)
                    
                    # Extraire la partie de la réponse après le prompt
                    if chunk_prompt in chunk_response:
                        chunk_response = chunk_response[len(chunk_prompt):].strip()
                    
                    # Extraire les paramètres du morceau
                    chunk_df = self.extract_parameters(chunk_response)
                    
                    if not chunk_df.empty:
                        all_parameters.extend(chunk_df["Paramètre"].tolist())
                        all_values.extend(chunk_df["Valeur mesurée"].tolist())
                        all_units.extend(chunk_df["Unité"].tolist())
                
                # Créer un DataFrame avec tous les paramètres extraits
                result_df = pd.DataFrame({
                    "Paramètre": all_parameters,
                    "Valeur mesurée": all_values,
                    "Unité": all_units
                })
                
                # Supprimer les doublons potentiels dus au chevauchement
                result_df = result_df.drop_duplicates(subset=["Paramètre"])
                
                logger.info(f"Analyse de texte terminée avec succès, {len(result_df)} paramètres extraits")
                return result_df
            else:
                # Traitement normal pour les textes de taille standard
                # Améliorer le prompt pour une meilleure extraction
                full_prompt = f"{prompt_text}\n\n{text}\n\nAssure-toi d'extraire TOUS les paramètres environnementaux présents dans le texte ci-dessus, avec leurs valeurs et unités. Présente les résultats sous forme de liste structurée au format 'Paramètre: Valeur Unité'."
                inputs = self.tokenizer(full_prompt, return_tensors="pt")
                
                # Déplacer les entrées sur le même appareil que le modèle
                if hasattr(self.model, 'device'):
                    for key in inputs:
                        if torch.is_tensor(inputs[key]):
                            inputs[key] = inputs[key].to(self.model.device)
                
                # Augmenter le nombre de tokens générés pour une réponse plus complète
                max_tokens = max_new_tokens or MODEL_CONFIG["max_new_tokens"]
                if max_tokens < 1000:  # Assurer un minimum de tokens pour les réponses complètes
                    max_tokens = 1000
                output = self.model.generate(**inputs, max_new_tokens=max_tokens)
                response = self.tokenizer.decode(output[0], skip_special_tokens=True)
                
                # Extraire la partie de la réponse après le prompt
                if full_prompt in response:
                    response = response[len(full_prompt):].strip()
                
                logger.info("Analyse de texte terminée avec succès")
                return self.extract_parameters(response)
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du texte: {str(e)}")
            return pd.DataFrame()
    
    def extract_parameters(self, response):
        """Extrait les paramètres structurés à partir de la réponse du modèle."""
        try:
            logger.info(f"Extraction des paramètres à partir d'une réponse de {len(response)} caractères")
            
            # Journaliser un extrait de la réponse pour le débogage
            preview = response[:200] + "..." if len(response) > 200 else response
            logger.debug(f"Aperçu de la réponse: {preview}")
            
            # Analyse la réponse pour extraire les paramètres, valeurs et unités
            # Rechercher différents formats de liste (-, *, 1., etc.)
            lines = []
            for line in response.split('\n'):
                line = line.strip()
                # Ignorer les lignes vides ou trop courtes
                if not line or len(line) < 3:
                    continue
                    
                # Supprimer les marqueurs de liste courants
                line = re.sub(r'^[-*•⦁◦▪▫●○➢➤➥➔→♦⬧⚫⚪⬤▸▹►▻▼▽◆◇★☆✓✔✗✘]\s*', '', line)
                line = re.sub(r'^\d+[.)]\s*', '', line)
                
                # Vérifier si la ligne contient un séparateur clé-valeur
                if ':' in line:
                    lines.append(line)
                elif '=' in line and ':' not in line:  # Format alternatif avec =
                    lines.append(line.replace('=', ':', 1))
            
            logger.debug(f"Nombre de lignes extraites: {len(lines)}")
            
            parameters, values, units = [], [], []
            
            for line in lines:
                try:
                    # Diviser la ligne en clé et valeur
                    key, val = line.split(':', 1)
                    key = key.strip()
                    val = val.strip()
                    
                    # Ignorer les clés vides ou trop courtes
                    if not key or len(key) < 2:
                        continue
                        
                    # Traiter les valeurs et unités
                    # Cas 1: Valeur et unité séparées par un espace (ex: "25 mg/L")
                    val_parts = val.split()
                    
                    # Cas spécial: valeur numérique avec unité attachée (ex: "25mg/L")
                    if len(val_parts) == 1 and val_parts[0]:
                        # Rechercher un motif où un nombre est suivi directement par des lettres
                        match = re.match(r'^([\d.,]+)([^\d.,].*)$', val_parts[0])
                        if match:
                            value = match.group(1)
                            unit = match.group(2)
                        else:
                            # Si pas de correspondance, considérer tout comme valeur
                            value = val_parts[0]
                            unit = ""
                    else:
                        # Cas standard: premier élément est la valeur, le reste est l'unité
                        value = val_parts[0] if val_parts else ""
                        unit = ' '.join(val_parts[1:]) if len(val_parts) > 1 else ""
                    
                    # Nettoyer la valeur (supprimer les caractères non numériques sauf point et virgule)
                    value = re.sub(r'[^\d.,]', '', value) if value else ""
                    
                    # Ajouter aux listes
                    parameters.append(key)
                    values.append(value)
                    units.append(unit)
                    
                    logger.debug(f"Paramètre extrait: {key} = {value} {unit}")
                    
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement de la ligne '{line}': {str(e)}")
                    continue
            
            # Crée un DataFrame avec les données extraites
            df = pd.DataFrame({
                "Paramètre": parameters,
                "Valeur mesurée": values,
                "Unité": units
            })
            
            logger.info(f"Extraction terminée: {len(df)} paramètres extraits")
            return df
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des paramètres: {str(e)}")
            return pd.DataFrame()

# Importer le module de prétraitement des images
from image_preprocessing import extract_text_from_image, preprocess_image, process_image_batch

# Fonction utilitaire pour faciliter l'utilisation
def analyze_environmental_image(image_path, prompt=None, model=None, batch_params=None, max_new_tokens=None, use_ocr=False):
    """
    Analyse une image environnementale avec le modèle Vision-Language.
    
    Args:
        image_path: Chemin vers l'image à analyser
        prompt: Instruction textuelle pour l'analyse
        model: Instance de modèle VLModel à utiliser
        batch_params: Paramètres de traitement par lots (taille des tuiles, chevauchement)
        max_new_tokens: Nombre maximum de tokens à générer (pour limiter le temps d'analyse)
        use_ocr: Utiliser l'OCR pour extraire le texte de l'image avant l'analyse
    
    Returns:
        Tuple (DataFrame, str): DataFrame contenant les paramètres extraits et réponse brute du modèle
    """
    default_prompt = "Extrais les paramètres liés à la qualité de l'environnement avec leurs valeurs et unités. Sois bref et concis."
    base_prompt = prompt or default_prompt
    
    # Utiliser les paramètres de traitement par lots par défaut si non spécifiés
    if batch_params is None:
        batch_params = MODEL_CONFIG.get("batch_processing", {
            "image_tile_size": 512,  # Valeur réduite pour accélérer le traitement
            "image_overlap": 50      # Valeur réduite pour limiter le nombre de tuiles
        })
    
    # Limiter le nombre de tokens générés pour accélérer l'analyse
    if max_new_tokens is None:
        max_new_tokens = 250  # Valeur réduite pour accélérer la génération
    
    # Créer une instance du modèle si nécessaire
    if model is None:
        model_path = MODEL_CONFIG["model_path"]
        model = VLModel(model_path)
    
    # Extraire le texte de l'image avec OCR si demandé
    extracted_text = ""
    if use_ocr:
        logger.info("Extraction du texte de l'image avec OCR...")
        extracted_text = extract_text_from_image(image_path)
        if extracted_text:
            logger.info(f"Texte extrait avec OCR: {len(extracted_text)} caractères")
            # Enrichir le prompt avec le texte extrait
            prompt = f"{base_prompt}\n\nTexte extrait de l'image par OCR: {extracted_text}"
        else:
            logger.info("Aucun texte extrait par OCR ou erreur lors de l'extraction")
            prompt = base_prompt
    else:
        prompt = base_prompt
    
    logger.info(f"Analyse de l'image avec paramètres optimisés: tile_size={batch_params.get('image_tile_size')}, overlap={batch_params.get('image_overlap')}, max_new_tokens={max_new_tokens}, OCR={use_ocr}")
    
    # Prétraiter l'image (redimensionnement) avant l'analyse
    preprocessed_image = preprocess_image(image_path)
    if preprocessed_image is None:
        error_msg = "Erreur: Impossible de prétraiter l'image"
        logger.error(error_msg)
        return None, error_msg
    
    # Analyser l'image avec les paramètres de traitement par lots
    # Note: VLModelAdapter.analyze_image n'accepte pas max_new_tokens, tile_size ou overlap
    # Ces paramètres sont ignorés pour la compatibilité avec VLModelAdapter
    response = model.analyze_image(
        image_path, 
        prompt
    )
    
    if isinstance(response, str) and response.startswith("Erreur"):
        logger.error(response)
        return None, response
    
    # Extraire les paramètres de la réponse
    df = model.extract_parameters(response)
    return df, response