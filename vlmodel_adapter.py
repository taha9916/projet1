#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Adaptateur VLModel pour le modèle dots.ocr.

Ce module fournit un adaptateur qui permet d'utiliser le modèle dots.ocr
avec l'interface VLModel existante, résolvant ainsi l'erreur
"VLModel object has no attribute load_model".
"""

import os
import logging
import torch
import re
import pandas as pd
from typing import Optional, Dict, Any, Union
from PIL import Image

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# # Importer le patch pour dots.ocr pour contourner la dépendance à flash_attn
# try:
#     import patch_dots_ocr
#     logger.info("Patch pour dots.ocr chargé avec succès")
# except ImportError:
#     logger.warning("Impossible de charger le patch pour dots.ocr. Le modèle pourrait ne pas fonctionner correctement.")


class VLModelAdapter:
    """
    Adaptateur pour rendre compatible le modèle dots.ocr avec l'interface VLModel.
    
    Cet adaptateur résout l'erreur "VLModel object has no attribute load_model"
en fournissant une implémentation de la méthode load_model et en adaptant
les autres méthodes nécessaires.
    """
    
    def __init__(self, model_path: str = "models/dots_ocr", **kwargs):
        """
        Initialise l'adaptateur VLModel.
        
        Args:
            model_path (str, optional): Chemin vers le modèle dots.ocr.
            **kwargs: Arguments supplémentaires pour la configuration du modèle.
        """
        self.model_path = model_path
        self.config = kwargs
        self.model = None
        self.processor = None
        self._is_loaded = False
        
        # Configuration par défaut
        self.device_map = kwargs.get('device_map', 'auto')
        self.torch_dtype = kwargs.get('torch_dtype', torch.bfloat16)
        self.load_in_4bit = kwargs.get('load_in_4bit', True)
        self.low_cpu_mem_usage = kwargs.get('low_cpu_mem_usage', True)
        
        logger.info(f"Adaptateur VLModel initialisé avec le modèle: {model_path}")
    
    def load_model(self) -> bool:
        """
        Charge le modèle dots.ocr.
        
        Returns:
            bool: True si le chargement a réussi, False sinon.
        """
        if self._is_loaded:
            logger.info("Le modèle est déjà chargé")
            return True
        
        try:
            from models.dots_ocr.configuration_dots import DotsOCRConfig, DotsVLProcessor
            from transformers import AutoTokenizer, AutoImageProcessor, AutoModel
            
            logger.info(f"Chargement du modèle depuis {self.model_path}")
            
            # Forcer le chargement en mode CPU pour éviter les problèmes de mémoire GPU
            # et désactiver la quantification qui cause des problèmes
            model_kwargs = {
                'torch_dtype': torch.float32,  # Utiliser float32 au lieu de bfloat16
                'device_map': 'cpu',  # Forcer l'utilisation du CPU
                'trust_remote_code': True,
                'low_cpu_mem_usage': True
            }
            
            logger.info("Chargement du modèle en mode CPU avec précision float32")
            
            # Load config manually
            self.config = DotsOCRConfig.from_pretrained(self.model_path)
            
            # Load processor components separately
            tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            image_processor = AutoImageProcessor.from_pretrained(self.model_path)
            
            # Create processor instance
            self.processor = DotsVLProcessor(
                image_processor=image_processor,
                tokenizer=tokenizer
            )
            
            # Load model
            self.model = AutoModel.from_pretrained(
                self.model_path,
                config=self.config,
                trust_remote_code=True,
                torch_dtype=torch.float32,
                device_map="cpu"
            )
            
            self._is_loaded = True
            logger.info("Modèle chargé avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {str(e)}")
            self._is_loaded = False
            return False
    
    def unload_model(self) -> bool:
        """
        Décharge le modèle de la mémoire.
        
        Returns:
            bool: True si le déchargement a réussi, False sinon.
        """
        try:
            if self.model is not None:
                # Libérer la mémoire GPU si disponible
                if hasattr(self.model, 'to'):
                    self.model.to('cpu')
                
                # Supprimer les références au modèle et au processeur
                del self.model
                del self.processor
                
                # Forcer le garbage collector
                import gc
                gc.collect()
                
                # Vider le cache CUDA si disponible
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                self.model = None
                self.processor = None
                self._is_loaded = False
                
                logger.info("Modèle déchargé avec succès")
                return True
            else:
                logger.info("Aucun modèle à décharger")
                return True
        except Exception as e:
            logger.error(f"Erreur lors du déchargement du modèle: {str(e)}")
            return False
    
    def analyze_image(self, image_path: str, prompt: Optional[str] = None) -> str:
        """
        Analyse une image avec le modèle Vision-Language.
        
        Args:
            image_path (str): Chemin vers l'image à analyser.
            prompt (str, optional): Prompt à utiliser pour l'analyse.
            
        Returns:
            str: Résultat de l'analyse.
        """
        if not self._is_loaded:
            if not self.load_model():
                return "Erreur: Impossible de charger le modèle"
        
        try:
            # Charger l'image
            if image_path is None:
                # Cas spécial pour l'analyse de texte sans image
                logger.info("Analyse de texte sans image")
                # Utiliser une méthode alternative pour le texte seul
                if hasattr(self.processor, 'tokenizer'):
                    inputs = self.processor.tokenizer(prompt, return_tensors="pt")
                    if hasattr(self.model, 'device'):
                        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
                    
                    with torch.no_grad():
                        outputs = self.model.generate(
                            **inputs,
                            max_new_tokens=1024,
                            do_sample=True,
                            temperature=0.7,
                            top_p=0.9,
                            repetition_penalty=1.2
                        )
                    
                    result = self.processor.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
                    return result
                else:
                    return "Erreur: Processeur incompatible pour l'analyse de texte sans image"
            
            # Traitement normal avec image
            image = Image.open(image_path)
            
            # Si pas de prompt, utiliser un prompt par défaut
            if not prompt:
                prompt = "Décris cette image en détail."
            
            # Vérifier si le processeur a un chat template
            has_chat_template = hasattr(self.processor, 'apply_chat_template') or \
                              (hasattr(self.processor, 'tokenizer') and \
                               hasattr(self.processor.tokenizer, 'apply_chat_template'))
            
            try:
                if has_chat_template:
                    # Créer un message au format chat
                    messages = [
                        {
                            "role": "user",
                            "content": [
                                {"type": "image", "image": image},
                                {"type": "text", "text": prompt}
                            ]
                        }
                    ]
                    
                    # Appliquer le template de chat
                    try:
                        if hasattr(self.processor, 'apply_chat_template'):
                            prompt_text = self.processor.apply_chat_template(messages, add_generation_prompt=True)
                        else:
                            prompt_text = self.processor.tokenizer.apply_chat_template(messages, add_generation_prompt=True)
                        
                        inputs = self.processor(text=prompt_text, images=[image], return_tensors="pt")
                    except Exception as e:
                        logger.warning(f"Erreur lors de l'application du chat template: {str(e)}")
                        # Fallback en cas d'erreur avec le chat template
                        logger.info("Utilisation de la méthode alternative sans chat template")
                        inputs = self.processor(images=image, text=prompt, return_tensors="pt")
                else:
                    # Méthode alternative sans chat template
                    logger.info("Processeur sans chat template, utilisation d'une méthode alternative")
                    # Essayer différentes méthodes de préparation des entrées
                    if hasattr(self.processor, 'image_processor') and hasattr(self.processor, 'tokenizer'):
                        # Méthode 1: Traiter l'image et le texte séparément
                        pixel_values = self.processor.image_processor(images=image, return_tensors="pt").pixel_values
                        input_ids = self.processor.tokenizer(prompt, return_tensors="pt").input_ids
                        inputs = {"pixel_values": pixel_values, "input_ids": input_ids}
                    else:
                        # Méthode 2: Utiliser l'interface standard
                        inputs = self.processor(images=image, text=prompt, return_tensors="pt")
            except Exception as e:
                logger.warning(f"Erreur lors de la préparation des entrées: {str(e)}")
                # Méthode de dernier recours
                logger.info("Utilisation d'une méthode de dernier recours pour la préparation des entrées")
                # Créer des entrées minimales qui fonctionneront avec la plupart des modèles
                if hasattr(self.processor, 'image_processor'):
                    pixel_values = self.processor.image_processor(images=image, return_tensors="pt").pixel_values
                    inputs = {"pixel_values": pixel_values}
                    if hasattr(self.processor, 'tokenizer'):
                        inputs["input_ids"] = self.processor.tokenizer(prompt, return_tensors="pt").input_ids
                else:
                    # Dernier recours: essayer l'interface standard
                    inputs = self.processor(images=image, text=prompt, return_tensors="pt")
            
            # Déplacer les inputs sur le même device que le modèle
            for k, v in inputs.items():
                if hasattr(v, 'to') and hasattr(self.model, 'device'):
                    inputs[k] = v.to(self.model.device)
            
            # Générer la réponse
            with torch.no_grad():
                try:
                    # Vérifier quels paramètres sont acceptés par le modèle
                    generate_kwargs = {
                        "max_new_tokens": 1024,  # Augmenter le nombre de tokens générés
                        "do_sample": True,
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "repetition_penalty": 1.2  # Ajouter une pénalité de répétition
                    }
                    
                    # Vérifier si le modèle accepte pixel_values directement
                    if hasattr(self.model, 'forward') and 'pixel_values' in inputs and 'input_ids' not in inputs:
                        # Certains modèles ont besoin d'input_ids même s'ils sont vides
                        if hasattr(self.processor, 'tokenizer'):
                            inputs['input_ids'] = self.processor.tokenizer("", return_tensors="pt").input_ids
                            if hasattr(self.model, 'device'):
                                inputs['input_ids'] = inputs['input_ids'].to(self.model.device)
                    
                    # Pour les modèles qui n'acceptent pas pixel_values directement
                    if 'pixel_values' in inputs and not hasattr(self.model.config, 'vision_config'):
                        # Créer une copie des inputs sans pixel_values
                        filtered_inputs = {k: v for k, v in inputs.items() if k != 'pixel_values'}
                        outputs = self.model.generate(**filtered_inputs, **generate_kwargs)
                    else:
                        outputs = self.model.generate(**inputs, **generate_kwargs)
                except Exception as e:
                    logger.error(f"Erreur lors de la génération avec les paramètres standards: {str(e)}")
                    # Essayer avec des paramètres minimaux
                    logger.info("Tentative avec des paramètres minimaux")
                    
                    # Identifier les paramètres clés pour ce modèle
                    if 'input_ids' in inputs:
                        # Modèle basé sur le texte uniquement
                        outputs = self.model.generate(input_ids=inputs['input_ids'], max_new_tokens=512)
                    elif 'pixel_values' in inputs and hasattr(self.model, 'vision_encoder'):
                        # Modèle vision-language avec encodeur d'image séparé
                        outputs = self.model.generate(pixel_values=inputs['pixel_values'], max_new_tokens=512)
                    else:
                        # Dernier recours: essayer avec le premier paramètre disponible
                        first_key = next(iter(inputs))
                        outputs = self.model.generate(**{first_key: inputs[first_key]}, max_new_tokens=512)
            
            # Décoder la réponse
            try:
                if hasattr(self.processor, 'batch_decode'):
                    result = self.processor.batch_decode(outputs, skip_special_tokens=True)[0]
                elif hasattr(self.processor, 'tokenizer'):
                    result = self.processor.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
                elif hasattr(self.model, 'generate_for_vision_and_text') and hasattr(self.processor, 'decode'):
                    # Pour les modèles avec une méthode de génération spécifique
                    result = self.processor.decode(outputs[0], skip_special_tokens=True)
                else:
                    # Essayer de trouver une méthode de décodage alternative
                    logger.warning("Méthode de décodage standard non disponible, tentative de méthodes alternatives")
                    if hasattr(outputs, 'sequences') and hasattr(self.processor, 'tokenizer'):
                        result = self.processor.tokenizer.batch_decode(outputs.sequences, skip_special_tokens=True)[0]
                    elif hasattr(self.model, 'config') and hasattr(self.model.config, 'tokenizer_class'):
                        # Créer un tokenizer basé sur la configuration du modèle
                        from transformers import AutoTokenizer
                        temp_tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                        result = temp_tokenizer.decode(outputs[0], skip_special_tokens=True)
                    else:
                        return "Erreur: Aucune méthode de décodage compatible n'a été trouvée"
            except Exception as e:
                logger.error(f"Erreur lors du décodage de la réponse: {str(e)}")
                # Dernier recours: retourner les tokens bruts
                return f"Erreur de décodage: {str(e)}. Tokens bruts: {outputs}"
            
            # Extraire la réponse de l'assistant si présente
            if "Assistant:" in result:
                result = result.split("Assistant:", 1)[1].strip()
                
            # Nettoyer la réponse si nécessaire
            if prompt and result.startswith(prompt):
                result = result[len(prompt):].strip()
            
            # Détecter et corriger les répétitions infinies
            if len(result) > 1000:
                lines = result.split('\n')
                # Détecter les patterns répétitifs
                unique_lines = []
                seen_patterns = set()
                repetition_count = {}
                
                for line in lines:
                    line_clean = line.strip()
                    if line_clean:
                        # Compter les répétitions
                        if line_clean in repetition_count:
                            repetition_count[line_clean] += 1
                        else:
                            repetition_count[line_clean] = 1
                        
                        # Si une ligne se répète plus de 3 fois, l'ignorer
                        if repetition_count[line_clean] <= 3:
                            unique_lines.append(line)
                
                # Reconstruire le résultat sans répétitions excessives
                result = '\n'.join(unique_lines[:50])  # Limiter à 50 lignes max
                
                if len(unique_lines) > 50:
                    result += "\n[Résultat tronqué pour éviter les répétitions]"
            
            return result
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de l'image: {str(e)}")
            return f"Erreur: {str(e)}"
    
    def analyze_text(self, text: str, prompt: Optional[str] = None, max_new_tokens: Optional[int] = None, 
                    chunk_size: int = 1000, overlap: int = 100) -> pd.DataFrame:
        """
        Analyse un texte avec le modèle Vision-Language.
        
        Args:
            text (str): Texte à analyser
            prompt (str, optional): Instruction textuelle pour l'analyse
            max_new_tokens (int, optional): Nombre maximum de tokens à générer
            chunk_size (int): Taille des morceaux de texte pour le traitement par lots
            overlap (int): Chevauchement entre les morceaux pour maintenir le contexte
            
        Returns:
            pd.DataFrame: DataFrame contenant les paramètres extraits
        """
        if not self._is_loaded:
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
                    
                    # Utiliser la méthode analyze_image pour traiter le texte
                    chunk_response = self.analyze_image(None, chunk_prompt)
                    
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
                
                # Utiliser la méthode analyze_image pour traiter le texte
                response = self.analyze_image(None, full_prompt)
                
                logger.info("Analyse de texte terminée avec succès")
                return self.extract_parameters(response)
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du texte: {str(e)}")
            return pd.DataFrame()
    
    def extract_parameters(self, response):
        """Extrait les paramètres structurés à partir de la réponse du modèle."""
        try:
            if not response:
                logger.warning("Réponse vide, impossible d'extraire des paramètres")
                return pd.DataFrame()
                
            logger.info(f"Extraction des paramètres à partir d'une réponse de {len(response)} caractères")
            
            # Journaliser un extrait de la réponse pour le débogage
            preview = response[:200] + "..." if len(response) > 200 else response
            logger.debug(f"Aperçu de la réponse: {preview}")
            
            # Modèle de regex pour capturer les paramètres, valeurs et unités
            pattern = r"([\w\s]+)\s*:\s*([\d,.]+)\s*([\w/%²³°]+)?"  # Nom: Valeur Unité
            
            # Trouver toutes les correspondances
            matches = re.findall(pattern, response)
            
            parameters, values, units, intervals = [], [], [], []
            
            # Traiter chaque correspondance
            for match in matches:
                try:
                    if len(match) < 2:
                        logger.warning(f"Format de correspondance incorrect: {match}")
                        continue
                        
                    parameter = match[0].strip()
                    value_str = match[1].strip().replace(',', '.')
                    unit = match[2].strip() if len(match) > 2 else ""
                    
                    # Ignorer les paramètres vides ou trop courts
                    if not parameter or len(parameter) < 2:
                        continue
                    
                    # Ajouter aux listes
                    parameters.append(parameter)
                    values.append(value_str)
                    units.append(unit)
                    intervals.append("")  # Intervalle vide par défaut
                    
                    logger.debug(f"Paramètre extrait: {parameter} = {value_str} {unit}")
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement de la correspondance {match}: {str(e)}")
                    continue
            
            # Rechercher les intervalles acceptables dans la réponse
            # Patterns pour les intervalles acceptables
            interval_patterns = [
                r"([\w\s]+)[\s:]+([\d.,]+)\s*-\s*([\d.,]+)",  # Paramètre: 5-10
                r"([\w\s]+)[\s:]+<\s*([\d.,]+)",  # Paramètre: < 5
                r"([\w\s]+)[\s:]+>\s*([\d.,]+)",  # Paramètre: > 10
                r"intervalle acceptable[\s:]+([\d.,]+)\s*-\s*([\d.,]+)",  # intervalle acceptable: 5-10
                r"intervalle acceptable[\s:]+<\s*([\d.,]+)",  # intervalle acceptable: < 5
                r"intervalle acceptable[\s:]+>\s*([\d.,]+)",  # intervalle acceptable: > 10
                r"([\w\s]+).*\(intervalle acceptable[\s:]+([\d.,]+)\s*-\s*([\d.,]+)\)",  # Paramètre (intervalle acceptable: 5-10)
                r"([\w\s]+).*\(intervalle acceptable[\s:]+<\s*([\d.,]+)\)",  # Paramètre (intervalle acceptable: < 5)
                r"([\w\s]+).*\(intervalle acceptable[\s:]+>\s*([\d.,]+)\)"  # Paramètre (intervalle acceptable: > 10)
            ]
            
            # Rechercher les intervalles dans la réponse
            for pattern in interval_patterns:
                interval_matches = re.findall(pattern, response, re.IGNORECASE)
                for match in interval_matches:
                    try:
                        if len(match) >= 2:  # Vérifier qu'il y a au moins un paramètre et une valeur
                            if "intervalle acceptable" in pattern.lower():
                                # Si le pattern contient "intervalle acceptable", le format dépend du pattern
                                if len(match) == 2:  # Pour les patterns avec < ou >
                                    interval = f"< {match[1]}" if "<" in pattern else f"> {match[1]}"
                                    # Chercher le paramètre correspondant
                                    for i, param in enumerate(parameters):
                                        if match[0].lower() in param.lower() or param.lower() in match[0].lower():
                                            intervals[i] = interval
                                            break
                                elif len(match) == 3:  # Pour les patterns avec intervalle min-max
                                    interval = f"{match[1]}-{match[2]}"
                                    # Chercher le paramètre correspondant
                                    for i, param in enumerate(parameters):
                                        if match[0].lower() in param.lower() or param.lower() in match[0].lower():
                                            intervals[i] = interval
                                            break
                            else:
                                # Pour les patterns sans "intervalle acceptable"
                                param_name = match[0].strip()
                                if len(match) == 3:  # Format min-max
                                    interval = f"{match[1]}-{match[2]}"
                                else:  # Format < ou >
                                    interval = f"< {match[1]}" if "<" in pattern else f"> {match[1]}"
                                
                                # Chercher le paramètre correspondant
                                for i, param in enumerate(parameters):
                                    if param_name.lower() in param.lower() or param.lower() in param_name.lower():
                                        intervals[i] = interval
                                        break
                    except Exception as e:
                        logger.warning(f"Erreur lors du traitement de l'intervalle {match}: {str(e)}")
                        continue
            
            # Créer un DataFrame avec les données extraites
            df = pd.DataFrame({
                "Paramètre": parameters,
                "Valeur mesurée": values,
                "Unité": units,
                "Intervalle acceptable": intervals
            })
            
            # Ajouter une colonne Milieu par défaut
            df["Milieu"] = "Eau"  # Valeur par défaut
            
            logger.info(f"Extraction terminée: {len(df)} paramètres extraits")
            return df
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des paramètres: {str(e)}")
            return pd.DataFrame()
    
    def is_loaded(self) -> bool:
        """
        Vérifie si le modèle est chargé.
        
        Returns:
            bool: True si le modèle est chargé, False sinon.
        """
        return self._is_loaded
    
    def get_config(self) -> Dict[str, Any]:
        """
        Retourne la configuration du modèle.
        
        Returns:
            Dict[str, Any]: Configuration du modèle.
        """
        return {
            'model_path': self.model_path,
            'device_map': self.device_map,
            'torch_dtype': str(self.torch_dtype),
            'load_in_4bit': self.load_in_4bit,
            'low_cpu_mem_usage': self.low_cpu_mem_usage,
            'is_loaded': self._is_loaded
        }
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """
        Configure le modèle.
        
        Args:
            config (Dict[str, Any]): Configuration du modèle.
        """
        if 'model_path' in config:
            self.model_path = config['model_path']
        
        if 'device_map' in config:
            self.device_map = config['device_map']
        
        if 'torch_dtype' in config:
            if config['torch_dtype'] == 'float32':
                self.torch_dtype = torch.float32
            elif config['torch_dtype'] == 'float16':
                self.torch_dtype = torch.float16
            elif config['torch_dtype'] == 'bfloat16':
                self.torch_dtype = torch.bfloat16
        
        if 'load_in_4bit' in config:
            self.load_in_4bit = config['load_in_4bit']
        
        if 'low_cpu_mem_usage' in config:
            self.low_cpu_mem_usage = config['low_cpu_mem_usage']
        
        logger.info(f"Configuration mise à jour: {self.get_config()}")

# Fonction pour créer un adaptateur VLModel
def create_vlmodel_adapter(model_path: Optional[str] = None, **kwargs) -> VLModelAdapter:
    """
    Crée un adaptateur VLModel pour le modèle dots.ocr.
    
    Args:
        model_path (str, optional): Chemin vers le modèle dots.ocr.
        **kwargs: Arguments supplémentaires pour la configuration du modèle.
        
    Returns:
        VLModelAdapter: Adaptateur VLModel.
    """
    return VLModelAdapter(model_path, **kwargs)

# Fonction pour vérifier si un modèle est compatible avec l'adaptateur
def is_compatible_model(model_path: str) -> bool:
    """
    Vérifie si un modèle est compatible avec l'adaptateur VLModel.
    
    Args:
        model_path (str): Chemin vers le modèle à vérifier.
        
    Returns:
        bool: True si le modèle est compatible, False sinon.
    """
    try:
        # Vérifier si le répertoire du modèle existe
        if not os.path.exists(model_path):
            logger.warning(f"Le chemin du modèle n'existe pas: {model_path}")
            return False
        
        # Vérifier si les fichiers nécessaires existent
        config_file = os.path.join(model_path, 'config.json')
        if not os.path.exists(config_file):
            logger.warning(f"Fichier de configuration non trouvé: {config_file}")
            return False
        
        # Vérifier si le modèle est un modèle dots.ocr
        # Cette vérification peut être adaptée en fonction des caractéristiques spécifiques du modèle
        import json
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Vérifier si le modèle est un modèle de type causal LM
        if 'model_type' not in config:
            logger.warning(f"Type de modèle non spécifié dans la configuration")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de compatibilité du modèle: {str(e)}")
        return False

# Exemple d'utilisation
if __name__ == "__main__":
    # Chemin vers le modèle dots.ocr
    model_path = "./weights/DotsOCR"
    
    # Créer un adaptateur VLModel
    adapter = create_vlmodel_adapter(model_path)
    
    # Charger le modèle
    if adapter.load_model():
        print("Modèle chargé avec succès")
        
        # Analyser une image
        image_path = "./test.jpg"
        if os.path.exists(image_path):
            result = adapter.analyze_image(image_path, "Décris cette image en détail.")
            print(f"Résultat: {result}")
        
        # Décharger le modèle
        adapter.unload_model()
    else:
        print("Erreur lors du chargement du modèle")