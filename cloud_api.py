import os
import base64
import json
import logging
import requests
import time
import pandas as pd
import json
import os

# Import optionnel de PIL pour fallback de chargement d'image
try:
    from PIL import Image as PILImage
except Exception:
    PILImage = None

# Charger la configuration des API cloud depuis le fichier JSON
def _load_api_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloud_api_config.json")
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Configuration des API cloud
API_CONFIG = _load_api_config()

# Configuration du logger
logger = logging.getLogger(__name__)

def extract_environmental_parameters_cloud(location, project_type, specific_params=None, api_provider="openrouter"):
    """
    Extrait les paramètres environnementaux pour un lieu et un type de projet donnés en utilisant une API cloud.
    
    Args:
        location (str): Localisation du projet (ville, région, pays)
        project_type (str): Type de projet (industriel, agricole, etc.)
        specific_params (list): Liste de paramètres spécifiques à rechercher (optionnel)
        api_provider (str): Fournisseur d'API à utiliser (openrouter, openai, openrouter_deepseek, openrouter_qwen, dots_ocr, etc.)
        
    Returns:
        pandas.DataFrame: DataFrame contenant les paramètres environnementaux extraits
    """
    try:
        logger.info(f"Extraction des paramètres environnementaux pour {location} (projet {project_type}) via {api_provider}")
        
        # Construire le prompt pour l'API cloud (format compatible SLRI: D,E,F,J,K)
        prompt = f"""
        Agis comme un expert en environnement et en analyse de risques SLRI.
        Je travaille sur un projet de type {project_type} à {location}.

        OBJECTIF :
        Extrais uniquement les 5 paramètres SLRI suivants pour chaque paramètre environnemental pertinent :
        - Intervalle acceptable/MIN
        - Intervalle acceptable/MAX
        - Valeur mesurée de milieux initial
        - Rejet de PHASE CONSTRUCTION
        - Valeure Mesure+rejet

        Si ces valeurs ne sont pas explicitement nommées dans le texte ou les tableaux, tu dois :
        - Déduire/calculer la valeur à partir des informations disponibles (autres tableaux, texte, unités, formules implicites, contexte, etc.)
        - Utiliser toutes les informations pertinentes du PDF (même si la donnée est cachée sous une autre forme ou à calculer)
        - Si une valeur est calculée ou estimée, explique brièvement comment tu l’as obtenue (méthode de calcul, hypothèse, etc.)

        FORMAT DE SORTIE :
        Rends UNIQUEMENT un tableau Markdown avec EXACTEMENT ces colonnes (dans cet ordre) :
        | Paramètre | Milieu | Intervalle acceptable/MIN | Intervalle acceptable/MAX | Valeur mesurée de milieux initial | Rejet de PHASE CONSTRUCTION | Valeure Mesure+rejet | Unité | Justification/Calcul |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- |

        RÈGLES :
        - Si l’intervalle acceptable est donné sous forme "6-8", sépare MIN=6 et MAX=8. Si "<5", MIN vide et MAX=5. Si ">=10", MIN=10 et MAX vide.
        - Pour toute valeur calculée ou déduite, indique la méthode dans la colonne "Justification/Calcul" (ex : "somme de X et Y", "valeur extraite du texte page 4", "moyenne des valeurs du tableau 2", etc.).
        - Si une valeur n’est pas trouvée et ne peut être estimée, laisse la cellule vide et explique pourquoi dans "Justification/Calcul".
        - N’inclus aucun texte hors du tableau Markdown.
        """
        
        # Ajouter les paramètres spécifiques s'ils sont fournis
        if specific_params and len(specific_params) > 0:
            specific_params_text = "\n".join([f"- {param}" for param in specific_params])
            prompt += f"""
            
            Incluez spécifiquement les paramètres suivants dans votre analyse:
            {specific_params_text}
            """
        
        # Ajouter des instructions quantitatives
        prompt += """
        
        Incluez au moins 12 paramètres pertinents couvrant les milieux eau/sol/air. 
        Les valeurs peuvent être estimées si nécessaire, mais restent réalistes pour la région.
        """
        
        # Créer une instance de CloudVisionAPI et analyser le texte
        cloud_api = CloudVisionAPI()
        result = cloud_api.analyze_text(prompt, provider=api_provider)
        
        # Extraire le tableau du résultat Markdown et le convertir en DataFrame
        df = extract_markdown_table(result)
        
        if df is not None and not df.empty:
            logger.info(f"Extraction réussie: {len(df)} paramètres environnementaux trouvés")
            return df
        else:
            logger.warning("Aucun paramètre environnemental extrait du résultat de l'API cloud")
            return pd.DataFrame(columns=["Paramètre", "Catégorie", "Valeur", "Unité", "Source", "Impact potentiel"])
            
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des paramètres environnementaux: {str(e)}")
        return pd.DataFrame(columns=["Paramètre", "Catégorie", "Valeur", "Unité", "Source", "Impact potentiel"])

def extract_markdown_table(markdown_text):
    """
    Extrait un tableau Markdown et le convertit en DataFrame pandas, de façon tolérante
    aux décalages de colonnes (padding/troncature des cellules par ligne).
    """
    try:
        import re

        lines = markdown_text.splitlines()
        n = len(lines)

        def is_table_line(l):
            s = l.strip()
            return s.startswith('|') and s.count('|') >= 2

        def is_alignment_line(l):
            s = l.strip().strip('|').replace(':', '').replace('-', '').replace(' ', '')
            return s == '' and '|' in l

        header_idx = -1
        align_idx = -1
        start_idx = -1
        end_idx = -1

        # 1) Trouver un bloc de tableau: en-tête + (optionnel) ligne d'alignement + données
        for i in range(n):
            if is_table_line(lines[i]):
                header_idx = i
                # Chercher ligne d'alignement à i+1
                if i + 1 < n and is_table_line(lines[i + 1]):
                    # Détecter si la ligne suivante est une ligne d'alignement (---, :---, ---:)
                    raw = lines[i + 1].strip().strip('|')
                    parts = [p.strip() for p in raw.split('|')]
                    if all(set(p) <= set('-: ') and len(p.replace('-', '').replace(':', '')) == 0 for p in parts):
                        align_idx = i + 1
                        start_idx = i + 2
                    else:
                        start_idx = i + 1
                else:
                    start_idx = i + 1

                # Étendre jusqu'à la dernière ligne de tableau contiguë
                j = start_idx
                while j < n and is_table_line(lines[j]):
                    j += 1
                end_idx = j
                break

        if header_idx == -1 or end_idx == -1 or start_idx == -1:
            logger.warning("Aucun tableau Markdown trouvé dans le texte")
            return None

        # 2) Parser l'en-tête
        def split_cells(l):
            return [c.strip() for c in l.strip().strip('|').split('|')]

        headers = [h for h in split_cells(lines[header_idx]) if h]
        if not headers:
            logger.warning("Entêtes de tableau introuvables")
            return None

        # 3) Parser les lignes et corriger la longueur
        fixed_rows = []
        for k in range(start_idx, end_idx):
            row_cells = split_cells(lines[k])
            if not any(cell.strip() for cell in row_cells):
                continue
            # Padding/troncature pour correspondre au nombre de colonnes
            if len(row_cells) < len(headers):
                row_cells = row_cells + [''] * (len(headers) - len(row_cells))
            elif len(row_cells) > len(headers):
                keep = row_cells[:len(headers) - 1]
                merged = ' | '.join(row_cells[len(headers) - 1:])
                row_cells = keep + [merged]
            fixed_rows.append(row_cells)

        if not fixed_rows:
            logger.warning("Aucune ligne de données trouvée dans le tableau")
            return pd.DataFrame(columns=headers)

        df = pd.DataFrame(fixed_rows, columns=headers)
        return df

    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du tableau Markdown: {str(e)}")
        return None
logger = logging.getLogger(__name__)

# Fonction principale pour l'analyse d'image environnementale
def analyze_environmental_image_cloud(image_path, api_provider="openai", prompt=None):
    """Analyse une image environnementale a l'aide d'une API cloud.
    
    Args:
        image_path (str): Chemin vers l'image a analyser
        api_provider (str): Fournisseur API a utiliser ('openai', 'azure', 'google', 'qwen', 'openrouter', 'openrouter_deepseek', 'openrouter_qwen', ou 'dots_ocr')
        prompt (str, optional): Instructions specifiques pour l'analyse
        
    Returns:
        tuple: (DataFrame des parametres extraits, reponse brute)
    """
    # Prompt par defaut ameliore pour l'analyse environnementale avec format tabulaire specifique
    if prompt is None:
        prompt = """Analyse cette image de test environnemental et extrait tous les parametres visibles.

Tu dois identifier le milieu (eau, sol, air), les parametres mesures, leurs unites,
les intervalles acceptables, les valeurs mesurees, et les resultats (conforme/non-conforme).

IMPORTANT: Tu DOIS presenter les resultats UNIQUEMENT sous forme de tableau Markdown
avec EXACTEMENT les colonnes suivantes (dans cet ordre precis):
| Milieu | Parametre | Unite | Intervalle acceptable | Valeur mesuree | Resultat conformite | Score | Observations | Description | Evaluation |
| ------ | --------- | ----- | -------------------- | -------------- | ------------------ | ----- | ------------ | ----------- | ---------- |

Si le format tableau n'est pas possible, liste chaque parametre au format suivant:
- Parametre: Valeur Unite

Si certaines informations ne sont pas visibles dans l'image, recherche-les sur internet
pour completer le tableau. Par exemple, recherche les intervalles acceptables pour les parametres identifies.

IMPORTANT: Pour les valeurs mesurees manquantes, tu DOIS faire une estimation basee sur:
1. Les valeurs typiques pour ce parametre dans des contextes similaires
2. Les autres parametres presents dans le document
3. Le contexte environnemental decrit dans le document

Indique clairement que c'est une valeur estimee en ajoutant "(estime)" après la valeur.
Si après recherche, certaines informations restent absolument indisponibles, indique 'Valeur estimee requise' dans les cellules correspondantes.
Ne laisse AUCUNE cellule vide dans le tableau et evite d'utiliser 'Non disponible'.
Ne reponds RIEN d'autre que ce tableau Markdown correctement formate."""
    
    # Journaliser le prompt utilisé pour le débogage
    logger.debug(f"Prompt utilisé pour l'analyse: {prompt}")
    
    # Initialiser l'API cloud
    cloud_api = CloudVisionAPI(api_provider=api_provider)
    
    # Analyser l'image
    logger.info(f"Analyse de l'image {image_path} avec l'API {api_provider}")
    df, response = cloud_api.analyze_image(image_path, prompt)
    
    return df, response

class CloudVisionAPI:
    """Classe pour interagir avec différentes API de vision par ordinateur dans le cloud.
    
    Cette classe fournit une interface unifiée pour interagir avec plusieurs API de vision
    par ordinateur dans le cloud, notamment Google Cloud Vision, Azure Computer Vision,
    OpenAI, Qwen, OpenRouter, OpenRouter DeepSeek et OpenRouter Qwen.
    """
    
    def __init__(self, api_provider="openai"):
        """Initialise l'API de vision par ordinateur.
        
        Args:
            api_provider (str): Fournisseur d'API à utiliser ('openai', 'azure', 'google', 'qwen', ou 'openrouter')
        """
        self.api_provider = api_provider.lower()
        # Mapper l'alias 'gemini' vers 'google' (Gemini Pro pour le texte)
        if self.api_provider == "gemini":
            logger.info("Alias 'gemini' détecté, utilisation du fournisseur 'google'.")
            self.api_provider = "google"
        logger.info(f"Initialisation de CloudVisionAPI avec le fournisseur {self.api_provider}")
        
        # Vérifier que le fournisseur est supporté
        supported_providers = ["openai", "azure", "google", "qwen", "openrouter", "openrouter_deepseek", "openrouter_qwen", "dots_ocr", "huggingface"]
        if self.api_provider not in supported_providers:
            logger.warning(f"Fournisseur {self.api_provider} non supporté. Utilisation d'OpenAI par défaut.")
            self.api_provider = "openai"
        
        # Charger la configuration des API
        self._load_config()
    
    def _load_config(self):
        """Charge la configuration des API depuis le fichier de configuration."""
        try:
            # Charger les clés API et autres paramètres de configuration
            if self.api_provider == "google":
                self.api_key = API_CONFIG.get("google", {}).get("api_key", "")
                # Pour l'analyse d'image, utiliser l'API Vision
                self.api_endpoint = "https://vision.googleapis.com/v1/images:annotate"
                # Pour l'analyse de texte, utiliser l'API Gemini Pro (version v1)
                self.gemini_endpoint = API_CONFIG.get("google", {}).get("gemini_url", "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent")
            elif self.api_provider == "azure":
                self.api_key = API_CONFIG.get("azure", {}).get("api_key", "")
                self.api_endpoint = API_CONFIG.get("azure", {}).get("endpoint", "")
            elif self.api_provider == "openai":
                self.api_key = API_CONFIG.get("openai", {}).get("api_key", "")
                self.api_endpoint = "https://api.openai.com/v1/chat/completions"
                self.model = API_CONFIG.get("openai", {}).get("model", "gpt-4-vision-preview")
            elif self.api_provider == "qwen":
                self.api_key = API_CONFIG.get("qwen", {}).get("api_key", "")
                self.api_endpoint = API_CONFIG.get("qwen", {}).get("endpoint", "")
                self.model = API_CONFIG.get("qwen", {}).get("model", "qwen-vl-plus")
            elif self.api_provider == "openrouter":
                self.api_key = API_CONFIG.get("openrouter", {}).get("api_key", "")
                self.api_endpoint = "https://openrouter.ai/api/v1/chat/completions"
                self.model = API_CONFIG.get("openrouter", {}).get("model", "anthropic/claude-3-opus-20240229-vision")
            elif self.api_provider == "openrouter_deepseek":
                self.api_key = API_CONFIG.get("openrouter_deepseek", {}).get("api_key", "")
                self.api_endpoint = "https://openrouter.ai/api/v1/chat/completions"
                self.model = API_CONFIG.get("openrouter_deepseek", {}).get("model", "deepseek/deepseek-chat-v3-0324:free")
            elif self.api_provider == "openrouter_qwen":
                self.api_key = API_CONFIG.get("openrouter_qwen", {}).get("api_key", "")
                self.api_endpoint = "https://openrouter.ai/api/v1/chat/completions"
                self.model = API_CONFIG.get("openrouter_qwen", {}).get("model", "qwen/qwen3-235b-a22b:free")
            elif self.api_provider == "dots_ocr":
                # Pour dots.ocr, nous n'avons pas besoin d'API key car c'est un modèle local
                self.model_name = API_CONFIG.get("dots_ocr", {}).get("model_name", "rednote-hilab/dots.ocr")
                self.load_in_4bit = API_CONFIG.get("dots_ocr", {}).get("load_in_4bit", True)
                self.device_map = API_CONFIG.get("dots_ocr", {}).get("device_map", "auto")
                self.torch_dtype = API_CONFIG.get("dots_ocr", {}).get("torch_dtype", "float16")
                self.max_tokens = API_CONFIG.get("dots_ocr", {}).get("max_tokens", 1000)
                # Nous initialiserons le modèle à la demande pour économiser la mémoire
                self.model = None
                self.processor = None
            elif self.api_provider == "huggingface":
                self.api_key = API_CONFIG.get("huggingface", {}).get("api_key", "")
                self.api_endpoint = API_CONFIG.get("huggingface", {}).get("api_url", "https://api-inference.huggingface.co/models/")
                self.model = API_CONFIG.get("huggingface", {}).get("model", "microsoft/DialoGPT-medium")
                self.max_tokens = API_CONFIG.get("huggingface", {}).get("max_tokens", 1000)
            
            logger.debug(f"Configuration chargée pour {self.api_provider}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {str(e)}")
            raise
    
    def _initialize_dots_ocr_model(self):
        """Initialise le modèle dots.ocr à la demande pour économiser la mémoire."""
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoProcessor
            
            logger.info(f"Initialisation du modèle dots.ocr ({self.model_name})")
            
            # Convertir le type de torch en objet torch.dtype
            if self.torch_dtype == "float16":
                torch_dtype = torch.float16
            elif self.torch_dtype == "float32":
                torch_dtype = torch.float32
            elif self.torch_dtype == "bfloat16":
                torch_dtype = torch.bfloat16
            else:
                torch_dtype = torch.float16
            
            # Charger le modèle avec les paramètres configurés
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                device_map=self.device_map,
                torch_dtype=torch_dtype,
                load_in_4bit=self.load_in_4bit
            )
            
            # Charger le processeur/tokenizer
            self.processor = AutoProcessor.from_pretrained(self.model_name)
            
            logger.info(f"Modèle dots.ocr initialisé avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du modèle dots.ocr: {str(e)}")
            return False
    
    def analyze_image(self, image_path, prompt):
        """Analyse une image à l'aide de l'API configurée.
        
        Args:
            image_path (str): Chemin vers l'image à analyser
            prompt (str): Instructions pour l'analyse
            
        Returns:
            tuple: (DataFrame des paramètres extraits, réponse brute)
        """
        try:
            # Vérifier que l'image existe
            if not os.path.exists(image_path):
                logger.error(f"L'image {image_path} n'existe pas")
                raise FileNotFoundError(f"L'image {image_path} n'existe pas")
            
            # Analyser l'image avec le fournisseur approprié
            if self.api_provider == "google":
                response = self._analyze_with_google(image_path, prompt)
            elif self.api_provider == "azure":
                response = self._analyze_with_azure(image_path, prompt)
            elif self.api_provider == "openai":
                response = self._analyze_with_openai(image_path, prompt)
            elif self.api_provider == "qwen":
                response = self._analyze_with_qwen(image_path, prompt)
            elif self.api_provider == "openrouter" or self.api_provider == "openrouter_deepseek" or self.api_provider == "openrouter_qwen":
                response = self._analyze_with_openrouter(image_path, prompt)
            elif self.api_provider == "dots_ocr":
                # Initialiser le modèle dots.ocr si nécessaire
                if self.model is None or self.processor is None:
                    if not self._initialize_dots_ocr_model():
                        raise ValueError("Impossible d'initialiser le modèle dots.ocr")
                response = self._analyze_with_dots_ocr(image_path, prompt)
            elif self.api_provider == "huggingface":
                response = self._analyze_with_huggingface_image(image_path, prompt)
            else:
                logger.error(f"Fournisseur {self.api_provider} non supporté")
                raise ValueError(f"Fournisseur {self.api_provider} non supporté")
            
            # Extraire les paramètres du résultat
            df = self._extract_parameters(response)
            
            return df, response
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de l'image: {str(e)}")
            raise
    
    def _analyze_with_dots_ocr(self, image_path, prompt):
        """Analyse une image avec le modèle dots.ocr local.
        
        Args:
            image_path (str): Chemin vers l'image
            prompt (str): Instructions pour l'analyse
            
        Returns:
            str: Résultat de l'analyse
        """
        try:
            import torch
            from PIL import Image
            
            # Charger l'image
            image = Image.open(image_path).convert('RGB')
            
            # Préparer les inputs pour le modèle
            inputs = self.processor(text=prompt, images=image, return_tensors="pt")
            
            # Déplacer les inputs sur le même device que le modèle
            for k, v in inputs.items():
                if isinstance(v, torch.Tensor):
                    inputs[k] = v.to(self.model.device)
            
            # Générer la réponse
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_tokens,
                    do_sample=True,
                    temperature=0.7,
                )
            
            # Décoder la réponse
            response = self.processor.decode(outputs[0], skip_special_tokens=True)
            
            # Nettoyer la mémoire pour économiser les ressources
            del outputs
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse avec dots.ocr: {str(e)}")
            raise
    
    def _encode_image(self, image_path):
        """Encode une image en base64.
        
        Args:
            image_path (str): Chemin vers l'image
            
        Returns:
            str: Image encodée en base64
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"Erreur lors de l'encodage de l'image: {str(e)}")
            raise
    
    def _analyze_with_google(self, image_path, prompt):
        """Analyse une image avec Google Cloud Vision API.
        
        Args:
            image_path (str): Chemin vers l'image
            prompt (str): Instructions pour l'analyse
            
        Returns:
            str: Résultat de l'analyse
        """
        try:
            # Encoder l'image en base64
            image_content = self._encode_image(image_path)
            
            # Préparer la requête
            request_data = {
                "requests": [
                    {
                        "image": {"content": image_content},
                        "features": [{"type": "TEXT_DETECTION"}]
                    }
                ]
            }
            
            # Envoyer la requête
            url = f"{self.api_endpoint}?key={self.api_key}"
            response = requests.post(url, json=request_data, timeout=(10, 30))
            
            # Vérifier la réponse
            if response.status_code != 200:
                logger.error(f"Erreur {response.status_code} lors de l'appel à l'API Google: {response.text}")
                raise Exception(f"Erreur {response.status_code} lors de l'appel à l'API Google")
            
            # Extraire le texte de la réponse
            response_json = response.json()
            text = response_json["responses"][0].get("fullTextAnnotation", {}).get("text", "")
            
            # Utiliser OpenAI pour analyser le texte extrait
            return self._analyze_with_openai_text(text, prompt)
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse avec Google Cloud Vision: {str(e)}")
            raise
    
    def _analyze_with_azure(self, image_path, prompt):
        """Analyse une image avec Azure Computer Vision API.
        
        Args:
            image_path (str): Chemin vers l'image
            prompt (str): Instructions pour l'analyse
            
        Returns:
            str: Résultat de l'analyse
        """
        try:
            # Préparer les en-têtes
            headers = {
                "Ocp-Apim-Subscription-Key": self.api_key,
                "Content-Type": "application/octet-stream"
            }
            
            # Préparer les paramètres
            params = {
                "visualFeatures": "Categories,Description,Objects",
                "language": "fr"
            }
            
            # Lire l'image
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
            
            # Envoyer la requête
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                params=params,
                data=image_data,
                timeout=(10, 60)
            )
            
            # Vérifier la réponse
            if response.status_code != 200:
                logger.error(f"Erreur {response.status_code} lors de l'appel à l'API Azure: {response.text}")
                raise Exception(f"Erreur {response.status_code} lors de l'appel à l'API Azure")
            
            # Extraire la description de l'image
            response_json = response.json()
            description = response_json.get("description", {}).get("captions", [{}])[0].get("text", "")
            
            # Utiliser OpenAI pour analyser la description
            return self._analyze_with_openai_text(description, prompt)
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse avec Azure Computer Vision: {str(e)}")
            raise
    
    def _analyze_with_openai(self, image_path, prompt):
        """Analyse une image avec OpenAI API.
        
        Args:
            image_path (str): Chemin vers l'image
            prompt (str): Instructions pour l'analyse
            
        Returns:
            str: Résultat de l'analyse
        """
        try:
            # Encoder l'image en base64
            image_content = self._encode_image(image_path)
            
            # Préparer les en-têtes
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Préparer la requête
            request_data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_content}"}}
                        ]
                    }
                ],
                "max_tokens": 4000
            }
            
            # Envoyer la requête
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=request_data,
                timeout=(10, 60)
            )
            
            # Vérifier la réponse
            if response.status_code != 200:
                logger.error(f"Erreur {response.status_code} lors de l'appel à l'API OpenAI: {response.text}")
                raise Exception(f"Erreur {response.status_code} lors de l'appel à l'API OpenAI")
            
            # Extraire le texte de la réponse
            response_json = response.json()
            return response_json["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse avec OpenAI: {str(e)}")
            raise
    
    def _analyze_with_qwen(self, image_path, prompt):
        """Analyse une image avec l'API Qwen.
        
        Args:
            image_path (str): Chemin vers l'image
            prompt (str): Instructions pour l'analyse
            
        Returns:
            str: Résultat de l'analyse
        """
        try:
            # Encoder l'image en base64
            image_content = self._encode_image(image_path)
            
            # Préparer les en-têtes
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Préparer la requête
            request_data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_content}"}}
                        ]
                    }
                ],
                "max_tokens": 4000
            }
            
            # Envoyer la requête
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=request_data
            )
            
            # Vérifier la réponse
            if response.status_code != 200:
                logger.error(f"Erreur {response.status_code} lors de l'appel à l'API Qwen: {response.text}")
                raise Exception(f"Erreur {response.status_code} lors de l'appel à l'API Qwen")
            
            # Extraire le texte de la réponse
            response_json = response.json()
            return response_json["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse avec Qwen: {str(e)}")
            raise
    
    def _analyze_with_openrouter(self, image_path=None, prompt=None, text=None, text_only=False):
        """Analyse une image ou du texte avec OpenRouter API.
        
        Args:
            image_path (str, optional): Chemin vers l'image
            prompt (str, optional): Instructions pour l'analyse
            text (str, optional): Texte à analyser
            text_only (bool, optional): Si True, analyse uniquement du texte
            
        Returns:
            str: Résultat de l'analyse
        """
        try:
            # Préparer les en-têtes
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://environmental-risk-analysis.app",
                "X-Title": "Environmental Risk Analysis App"
            }
            
            # Préparer la requête
            if text_only:
                # Requête pour analyse de texte uniquement
                request_data = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": text
                        }
                    ],
                    "max_tokens": 4000
                }
            else:
                # Encoder l'image en base64
                image_content = self._encode_image(image_path)
                
                # Requête pour analyse d'image
                request_data = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_content}"}}
                            ]
                        }
                    ],
                    "max_tokens": 4000
                }
            
            # Envoyer la requête
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=request_data
            )
            
            # Vérifier la réponse
            if response.status_code != 200:
                logger.error(f"Erreur {response.status_code} lors de l'appel à l'API OpenRouter: {response.text}")
                raise Exception(f"Erreur {response.status_code} lors de l'appel à l'API OpenRouter")
            
            # Extraire le texte de la réponse
            response_json = response.json()
            return response_json["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse avec OpenRouter: {str(e)}")
            raise
    
    def _analyze_with_openai_text(self, text, prompt):
        """Analyse un texte avec OpenAI API.
        
        Args:
            text (str): Texte à analyser
            prompt (str): Instructions pour l'analyse
            
        Returns:
            str: Résultat de l'analyse
        """
        try:
            # Préparer les en-têtes
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Préparer la requête
            request_data = {
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nTexte extrait de l'image:\n{text}"
                    }
                ],
                "max_tokens": 4000
            }
            
            # Envoyer la requête
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=request_data,
                timeout=(10, 60)
            )
            
            # Vérifier la réponse
            if response.status_code != 200:
                logger.error(f"Erreur {response.status_code} lors de l'appel à l'API OpenAI: {response.text}")
                raise Exception(f"Erreur {response.status_code} lors de l'appel à l'API OpenAI")
            
            # Extraire le texte de la réponse
            response_json = response.json()
            return response_json["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse avec OpenAI: {str(e)}")
            raise
    
    def analyze_text(self, prompt, provider=None):
        """
Analyse un texte à l'aide de l'API configurée.
        
Args:
            prompt (str): Texte à analyser ou instructions
            provider (str, optional): Fournisseur d'API à utiliser. Si None, utilise le fournisseur par défaut.
            
Returns:
            str: Résultat de l'analyse
        """
        try:
            # Utiliser le fournisseur spécifié ou celui par défaut
            current_provider = provider.lower() if provider else self.api_provider
            # Mapper 'gemini' (alias) vers 'google'
            if current_provider == "gemini":
                logger.info("Alias 'gemini' détecté pour l'analyse de texte, utilisation de 'google'.")
                current_provider = "google"
            logger.info(f"Analyse de texte avec le fournisseur {current_provider}")
            
            # Sauvegarder le fournisseur actuel
            original_provider = self.api_provider
            
            # Changer temporairement de fournisseur si nécessaire
            if current_provider != self.api_provider:
                self.api_provider = current_provider
                self._load_config()
            
            # Analyser le texte avec le fournisseur approprié
            if self.api_provider == "openai":
                response = self._analyze_text_with_openai(prompt)
            elif self.api_provider in ["openrouter", "openrouter_deepseek", "openrouter_qwen"]:
                response = self._analyze_text_with_openrouter(prompt)
            elif self.api_provider == "qwen":
                response = self._analyze_text_with_qwen(prompt)
            elif self.api_provider == "azure":
                response = self._analyze_text_with_azure(prompt)
            elif self.api_provider == "google":
                response = self._analyze_text_with_google(prompt)
            elif self.api_provider == "huggingface":
                response = self._analyze_text_with_huggingface(prompt)
            else:
                logger.error(f"Fournisseur {self.api_provider} non supporté pour l'analyse de texte")
                raise ValueError(f"Fournisseur {self.api_provider} non supporté pour l'analyse de texte")
            
            # Restaurer le fournisseur original si nécessaire
            if current_provider != original_provider:
                self.api_provider = original_provider
                self._load_config()
            
            return response
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de texte: {str(e)}")
            raise
    
    def _analyze_text_with_openai(self, prompt):
        """Analyse un texte avec OpenAI API.
        
        Args:
            prompt (str): Texte à analyser
            
        Returns:
            str: Résultat de l'analyse
        """
        try:
            # Préparer les en-têtes
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Préparer la requête
            request_data = {
                "model": "gpt-4",  # Utiliser GPT-4 pour le texte
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 4000,
                "temperature": 0.7
            }
            
            # Envoyer la requête
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=request_data
            )
            
            # Vérifier la réponse
            if response.status_code != 200:
                logger.error(f"Erreur {response.status_code} lors de l'appel à l'API OpenAI: {response.text}")
                raise Exception(f"Erreur {response.status_code} lors de l'appel à l'API OpenAI")
            
            # Extraire le texte de la réponse
            response_json = response.json()
            return response_json["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de texte avec OpenAI: {str(e)}")
            raise
    
    def _analyze_text_with_openrouter(self, prompt):
        """Analyse un texte avec OpenRouter API.
        
        Args:
            prompt (str): Texte à analyser
            
        Returns:
            str: Résultat de l'analyse
        """
        try:
            # Utiliser la méthode _analyze_with_openrouter avec text_only=True
            return self._analyze_with_openrouter(text=prompt, text_only=True)
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de texte avec OpenRouter: {str(e)}")
            raise
    
    def _analyze_text_with_qwen(self, prompt):
        """Analyse un texte avec Qwen API.
        
        Args:
            prompt (str): Texte à analyser
            
        Returns:
            str: Résultat de l'analyse
        """
        try:
            # Préparer les en-têtes
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Préparer la requête
            request_data = {
                "model": "qwen-max",  # Utiliser Qwen-Max pour le texte
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 4000,
                "temperature": 0.7
            }
            
            # Envoyer la requête
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=request_data
            )
            
            # Vérifier la réponse
            if response.status_code != 200:
                logger.error(f"Erreur {response.status_code} lors de l'appel à l'API Qwen: {response.text}")
                raise Exception(f"Erreur {response.status_code} lors de l'appel à l'API Qwen")
            
            # Extraire le texte de la réponse
            response_json = response.json()
            return response_json["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de texte avec Qwen: {str(e)}")
            raise
    
    def _analyze_text_with_azure(self, prompt):
        """Analyse un texte avec Azure OpenAI API.
        
        Args:
            prompt (str): Texte à analyser
            
        Returns:
            str: Résultat de l'analyse
        """
        try:
            # Préparer les en-têtes
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Préparer la requête
            request_data = {
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 4000,
                "temperature": 0.7
            }
            
            # Envoyer la requête
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=request_data
            )
            
            # Vérifier la réponse
            if response.status_code != 200:
                logger.error(f"Erreur {response.status_code} lors de l'appel à l'API Azure: {response.text}")
                raise Exception(f"Erreur {response.status_code} lors de l'appel à l'API Azure")
            
            # Extraire le texte de la réponse
            response_json = response.json()
            return response_json["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de texte avec Azure: {str(e)}")
            raise
    
    def _analyze_text_with_google(self, prompt):
        """Analyse un texte avec Google API.
        
        Args:
            prompt (str): Texte à analyser
            
        Returns:
            str: Résultat de l'analyse
        """
        try:
            # Préparer les en-têtes
            headers = {
                "Content-Type": "application/json"
            }
            
            # Préparer la requête pour Gemini
            request_data = {
                "contents": [
                    {"parts": [{"text": prompt}]}
                ],
                "generationConfig": {
                    "maxOutputTokens": 4000,
                    "temperature": 0.7
                }
            }
            
            # Envoyer la requête à l'API Gemini en utilisant self.gemini_endpoint
            response = requests.post(
                f"{self.gemini_endpoint}?key={self.api_key}",
                json=request_data,
                timeout=(10, 60)
            )
            
            # Vérifier la réponse
            if response.status_code != 200:
                logger.error(f"Erreur {response.status_code} lors de l'appel à l'API Google: {response.text}")
                raise Exception(f"Erreur {response.status_code} lors de l'appel à l'API Google")
            
            # Extraire le texte de la réponse
            response_json = response.json()
            return response_json["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de texte avec Google: {str(e)}")
            raise
    
    def _analyze_text_with_huggingface(self, prompt):
        """Analyse un texte avec l'API Hugging Face Inference.
        
        Args:
            prompt (str): Texte à analyser
            
        Returns:
            str: Résultat de l'analyse
        """
        try:
            # Préparer les en-têtes
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Utilitaire d'appel pour un modèle donné (construction d'URL robuste + retry 503)
            def _call_model(model_id: str):
                url = f"{self.api_endpoint.rstrip('/')}/{model_id.lstrip('/')}"
                request_data = {
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": self.max_tokens,
                        "temperature": 0.7,
                        "return_full_text": False
                    }
                }
                attempts = 0
                max_attempts = 2  # 1 essai + 1 retry sur 503 (model loading)
                last_resp = None
                while attempts <= max_attempts:
                    logger.debug(f"Appel Hugging Face: modèle='{model_id}', tentative {attempts+1}/{max_attempts+1}, prompt_len={len(prompt)}")
                    resp = requests.post(url, headers=headers, json=request_data, timeout=(10, 30))
                    last_resp = resp
                    if resp.status_code == 503:
                        # Modèle en cours de chargement: attendre puis retenter
                        wait_s = 10
                        try:
                            j = resp.json()
                            est = float(j.get("estimated_time", 0))
                            if est:
                                wait_s = max(5, min(est, 45))
                        except Exception:
                            pass
                        logger.warning(f"Hugging Face 503 (loading) pour '{model_id}' - attente {wait_s}s avant retry. URL {url}. Corps: {resp.text[:200]}")
                        time.sleep(wait_s)
                        attempts += 1
                        continue
                    return resp, url
                return last_resp, url

            # 1) Appel avec le modèle configuré
            response, full_url = _call_model(self.model)

            # 2) Si 404 (modèle introuvable/non disponible via Inference API), tenter un fallback léger
            if response.status_code == 404:
                logger.warning(
                    f"Hugging Face 404 pour le modèle '{self.model}' à l'URL {full_url}. "
                    f"Tentative de fallback avec 'Qwen/Qwen2-0.5B-Instruct'. Corps: {response.text}"
                )
                fallback_model = "Qwen/Qwen2-0.5B-Instruct"
                fb_response, fb_url = _call_model(fallback_model)
                if fb_response.status_code != 200:
                    logger.error(
                        f"Echec du fallback Hugging Face (modèle {fallback_model}) - "
                        f"Statut {fb_response.status_code} - URL {fb_url} - Corps: {fb_response.text}"
                    )
                    raise Exception(
                        f"Erreur {fb_response.status_code} lors de l'appel à l'API Hugging Face (fallback {fallback_model})"
                    )
                response_json = fb_response.json()
            else:
                # Autres erreurs
                if response.status_code != 200:
                    logger.error(
                        f"Erreur {response.status_code} lors de l'appel à l'API Hugging Face - "
                        f"URL {full_url} - Corps: {response.text}"
                    )
                    raise Exception(f"Erreur {response.status_code} lors de l'appel à l'API Hugging Face")
                response_json = response.json()

            # 3) Normaliser la réponse
            if isinstance(response_json, list) and len(response_json) > 0:
                item0 = response_json[0]
                if isinstance(item0, dict):
                    if "generated_text" in item0:
                        return item0["generated_text"]
                    if "summary_text" in item0:
                        return item0["summary_text"]
                return str(item0)
            if isinstance(response_json, dict):
                if "generated_text" in response_json:
                    return response_json["generated_text"]
                if "summary_text" in response_json:
                    return response_json["summary_text"]
                return str(response_json)
            return str(response_json)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de texte avec Hugging Face: {str(e)}")
            raise
    
    def _analyze_with_huggingface_image(self, image_path, prompt):
        """Analyse une image avec l'API Hugging Face.
        
        Note: Hugging Face Inference API ne supporte pas directement l'analyse d'images 
        pour tous les modèles. Cette méthode utilise OCR + analyse de texte comme solution de contournement.
        
        Args:
            image_path (str): Chemin vers l'image
            prompt (str): Instructions pour l'analyse
            
        Returns:
            str: Résultat de l'analyse
        """
        try:
            # Étape 1: Extraire le texte de l'image avec OCR
            import cv2
            import numpy as np
            try:
                import pytesseract
            except ImportError:
                logger.error("pytesseract non installé. Installation requise: pip install pytesseract")
                raise ImportError("pytesseract requis pour l'analyse d'images avec Hugging Face")
            
            # Charger et prétraiter l'image (robuste aux chemins Windows avec accents/espaces)
            image = None
            try:
                file_bytes = np.fromfile(image_path, dtype=np.uint8)
                image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                if image is None:
                    logger.warning(f"cv2.imdecode a retourné None pour le chemin: {image_path}")
            except Exception as e_load:
                logger.debug(f"Échec cv2.imdecode: {e_load}")

            if image is None:
                # Fallback PIL -> conversion vers OpenCV BGR (si Pillow est disponible)
                try:
                    if PILImage is not None:
                        with PILImage.open(image_path) as pil_img:
                            pil_img = pil_img.convert('RGB')
                            image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                            logger.info("Image chargée via fallback PIL (conversion vers OpenCV BGR).")
                    else:
                        logger.warning("Pillow (PIL) non installé, fallback PIL indisponible.")
                except Exception as e_pil:
                    logger.error(f"Impossible de charger l'image via PIL: {e_pil}")

            if image is None:
                raise ValueError(f"Impossible de charger l'image (cv2.imdecode et PIL ont échoué): {image_path}")

            # Convertir en niveaux de gris pour améliorer l'OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Appliquer un seuillage pour améliorer la lisibilité
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Extraire le texte avec OCR
            ocr_start = time.perf_counter()
            extracted_text = pytesseract.image_to_string(thresh, lang='fra+eng')
            ocr_duration = time.perf_counter() - ocr_start
            
            logger.info(f"Texte extrait de l'image: {len(extracted_text)} caractères (OCR {ocr_duration:.2f}s)")
            
            # Étape 2: Analyser le texte extrait avec Hugging Face
            combined_prompt = f"""
            {prompt}
            
            Voici le texte extrait d'une image environnementale:
            {extracted_text}
            
            Analysez ce contenu et identifiez tous les paramètres environnementaux présents.
            Structurez votre réponse sous forme de tableau avec les colonnes:
            Paramètre | Valeur | Unité | Commentaire
            """
            
            # Utiliser l'analyse de texte pour traiter le contenu extrait
            logger.debug(f"Appel Hugging Face (texte) depuis image: modèle={self.model}, prompt_len={len(combined_prompt)}")
            response = self._analyze_text_with_huggingface(combined_prompt)
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse d'image avec Hugging Face: {str(e)}")
            # En cas d'erreur OCR, essayer une approche simplifiée
            try:
                simplified_prompt = f"""
                Analysez cette image environnementale et identifiez les paramètres suivants si présents:
                - Qualité de l'air (particules, gaz)
                - Qualité de l'eau (pH, turbidité, polluants)
                - Qualité du sol (composition, contamination)
                - Conditions météorologiques
                - Présence de végétation ou faune
                
                {prompt}
                
                Formatez la réponse sous forme de tableau structuré.
                """
                return self._analyze_text_with_huggingface(simplified_prompt)
            except:
                raise e
    
    def extract_environmental_parameters_from_text(self, markdown_text):
        """Extrait les paramètres d'un tableau Markdown.
        
        Args:
            markdown_text (str): Texte Markdown contenant un tableau
            
{{ ... }}
            DataFrame: DataFrame contenant les paramètres extraits
        """
        try:
            # Initialiser un DataFrame vide
            df = pd.DataFrame()
            
            # Limiter la longueur du texte pour éviter les répétitions infinies
            if len(markdown_text) > 5000:
                markdown_text = markdown_text[:5000]
                logger.warning("Texte tronqué pour éviter les répétitions excessives")
            
            # Vérifier si le texte contient un tableau Markdown
            if "|" in markdown_text and "-" in markdown_text:
                # Extraire les lignes du tableau
                lines = [line.strip() for line in markdown_text.split("\n") if line.strip() and "|" in line]
                
                # Déduplication des lignes identiques
                unique_lines = []
                seen_lines = set()
                for line in lines:
                    if line not in seen_lines:
                        unique_lines.append(line)
                        seen_lines.add(line)
                lines = unique_lines
                
                if len(lines) >= 2:
                    # Extraire les en-têtes
                    headers = [header.strip() for header in lines[0].split("|") if header.strip()]
                    
                    # Ignorer la ligne de séparation (---)
                    data_lines = lines[2:] if len(lines) > 2 else []
                    
                    # Extraire les données avec déduplication
                    data = []
                    seen_rows = set()
                    for line in data_lines:
                        row = [cell.strip() for cell in line.split("|") if cell.strip()]
                        if len(row) == len(headers):
                            row_tuple = tuple(row)
                            if row_tuple not in seen_rows:
                                data.append(row)
                                seen_rows.add(row_tuple)
                    
                    # Créer le DataFrame
                    df = pd.DataFrame(data, columns=headers)
            else:
                # Format alternatif: liste de paramètres
                parameters = []
                values = []
                units = []
                seen_params = set()
                
                for line in markdown_text.split("\n"):
                    if line.strip().startswith("-") and ":" in line:
                        # Extraire le paramètre et la valeur
                        param_value = line.strip().split(":", 1)
                        if len(param_value) == 2:
                            param = param_value[0].strip("- ")
                            value_unit = param_value[1].strip().split(" ", 1)
                            
                            # Éviter les doublons
                            param_key = param.lower()
                            if param_key not in seen_params:
                                parameters.append(param)
                                seen_params.add(param_key)
                                if len(value_unit) == 2:
                                    values.append(value_unit[0])
                                    units.append(value_unit[1])
                                else:
                                    values.append(value_unit[0])
                                    units.append("")
                
                # Créer le DataFrame
                if parameters:
                    df = pd.DataFrame({
                        "Paramètre": parameters,
                        "Valeur mesurée": values,
                        "Unité": units
                    })
            
            # Limiter le nombre de lignes pour éviter les répétitions excessives
            if len(df) > 50:
                df = df.head(50)
                logger.warning("DataFrame tronqué à 50 lignes pour éviter les répétitions excessives")
            
            return df
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des paramètres: {str(e)}")
            # Retourner un DataFrame vide en cas d'erreur
            return pd.DataFrame()
    
    def _extract_parameters(self, response):
        """Extrait un DataFrame des paramètres à partir d'une réponse texte/JSON.
        
        Cette méthode unifie l'extraction pour tous les fournisseurs en utilisant
        d'abord la méthode interne permissive, puis un utilitaire global de
        détection de tableaux Markdown.
        """
        try:
            # Normaliser la réponse en texte
            if isinstance(response, (dict, list)):
                text = json.dumps(response, ensure_ascii=False)
            else:
                text = str(response) if response is not None else ""

            # 1) Extraction permissive
            df = self.extract_environmental_parameters_from_text(text)
            if df is not None and not df.empty:
                return df

            # 2) Fallback: utilitaire global
            try:
                df2 = extract_markdown_table(text)
                if df2 is not None and not df2.empty:
                    return df2
            except Exception as e_tab:
                logger.debug(f"Echec extract_markdown_table: {e_tab}")

            # 3) DataFrame vide standardisé
            return pd.DataFrame(columns=["Paramètre", "Valeur mesurée", "Unité"])
        except Exception as e:
            logger.error(f"Erreur _extract_parameters: {str(e)}")
            return pd.DataFrame()

    def cleanup(self):
        """Libère la mémoire utilisée par le modèle dots.ocr.
        
        Cette méthode est particulièrement importante pour le fournisseur dots_ocr
        qui utilise des ressources GPU locales. Elle supprime les références au modèle
        et au processeur, et libère la mémoire GPU si disponible.
        """
        try:
            if self.api_provider == "dots_ocr" and (self.model is not None or self.processor is not None):
                logger.info("Nettoyage des ressources du modèle dots.ocr")
                
                # Supprimer les références au modèle et au processeur
                if hasattr(self, 'model') and self.model is not None:
                    del self.model
                    self.model = None
                
                if hasattr(self, 'processor') and self.processor is not None:
                    del self.processor
                    self.processor = None
                
                # Libérer la mémoire GPU si disponible
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        logger.info("Mémoire GPU libérée")
                except ImportError:
                    logger.debug("Module torch non disponible, impossible de libérer la mémoire GPU")
                
                logger.info("Nettoyage des ressources terminé")
            else:
                logger.debug(f"Aucun nettoyage nécessaire pour le fournisseur {self.api_provider}")
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des ressources: {str(e)}")
            # Ne pas propager l'erreur pour éviter d'interrompre le flux d'exécution