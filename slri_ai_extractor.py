#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extracteur IA pour l'analyse SLRI - Utilise l'IA pour extraire et classifier automatiquement 
les paramètres environnementaux selon les références SLRI
"""

import os
import json
import tempfile
import logging
from typing import Dict, List, Any, Optional
import pandas as pd

# Configuration du logger
logger = logging.getLogger(__name__)
from gemini_integration import analyze_environmental_image_with_gemini

class SLRIAIExtractor:
    """
    Extracteur IA pour l'analyse SLRI utilisant Gemini API
    """
    
    def __init__(self):
        self.slri_references = self._load_slri_references()
        self.parameter_categories = {
            'eau': ['pH', 'Température', 'Turbidité', 'Conductivité', 'DBO5', 'DCO', 
                   'Oxygène dissous', 'Nitrates', 'Nitrites', 'Ammoniac', 'Phosphore total',
                   'Azote total', 'Plomb', 'Cadmium', 'Chrome', 'Cuivre', 'Zinc', 'Nickel',
                   'Mercure', 'Arsenic', 'Hydrocarbures totaux', 'HAP'],
            'sol': ['pH', 'Perméabilité', 'Matière organique', 'Carbone organique',
                   'Plomb', 'Cadmium', 'Chrome', 'Cuivre', 'Zinc', 'Nickel', 'Mercure',
                   'Arsenic', 'Azote total', 'Phosphore total'],
            'air': ['Poussières totales', 'PM10', 'PM2.5', 'SO2', 'NOx', 'CO', 'O3'],
            'biologique': ['Flore terrestre', 'Flore marine', 'Mammifères', 'Amphibiens',
                          'Reptiles', 'Statut de protection', 'Présence sur site'],
            'humain': ['Population riveraine', 'Distance habitations', 'Activités économiques',
                      'Patrimoine culturel', 'Accès aux ressources']
        }
    
    def _load_slri_references(self) -> Dict:
        """Charge les références SLRI complètes depuis les fichiers"""
        references = {}
        slri_dir = "SLRI"
        
        if os.path.exists(slri_dir):
            try:
                # Charger tous les fichiers SLRI de référence
                files_to_load = [
                    "Echelles.txt",
                    "PRE CONSTRUCTION.txt", 
                    "CONSTRUCTION.txt",
                    "exploitation.txt",
                    "démantalement.txt",
                    "matrice d'impacts.txt"
                ]
                
                for filename in files_to_load:
                    file_path = os.path.join(slri_dir, filename)
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            key = filename.replace('.txt', '').replace(' ', '_').lower()
                            references[key] = f.read()
                
                # Charger les seuils de référence détaillés
                references['seuils_detailles'] = self._parse_slri_thresholds(references)
                
                logger.info("Références SLRI complètes chargées avec succès")
            except Exception as e:
                logger.error(f"Erreur lors du chargement des références SLRI: {e}")
                references = self._get_default_references()
        else:
            references = self._get_default_references()
            
        return references
    
    def _parse_slri_thresholds(self, references: Dict) -> Dict:
        """Parse les seuils SLRI depuis les fichiers de référence"""
        thresholds = {
            'eau': {},
            'sol': {},
            'air': {}
        }
        
        try:
            # Parser les seuils depuis PRE CONSTRUCTION.txt
            if 'pre_construction' in references:
                content = references['pre_construction']
                lines = content.split('\n')
                
                current_section = None
                for line in lines:
                    line = line.strip()
                    if '=== MILIEU PHYSIQUE - EAU ===' in line:
                        current_section = 'eau'
                    elif '=== MILIEU PHYSIQUE - SOL ===' in line:
                        current_section = 'sol'
                    elif '=== MILIEU PHYSIQUE - AIR ===' in line:
                        current_section = 'air'
                    elif ':' in line and current_section:
                        # Parser les seuils (ex: "pH: 6-8")
                        parts = line.split(':')
                        if len(parts) >= 2:
                            param_name = parts[0].strip()
                            threshold_str = parts[1].strip()
                            
                            # Extraire les valeurs min/max
                            threshold = self._parse_threshold_value(threshold_str)
                            if threshold:
                                thresholds[current_section][param_name] = threshold
            
            # Parser les échelles depuis Echelles.txt
            if 'echelles' in references:
                self._parse_scoring_scales(references['echelles'], thresholds)
                
        except Exception as e:
            logger.error(f"Erreur parsing seuils SLRI: {e}")
        
        return thresholds
    
    def _parse_threshold_value(self, threshold_str: str) -> Dict:
        """Parse une valeur de seuil (ex: '6-8', '<5', '>5')"""
        try:
            import re
            
            # Cas: intervalle (6-8, 20-30°C)
            range_match = re.search(r'(\d+\.?\d*)-(\d+\.?\d*)', threshold_str)
            if range_match:
                min_val = float(range_match.group(1))
                max_val = float(range_match.group(2))
                return {'min': min_val, 'max': max_val, 'type': 'range'}
            
            # Cas: maximum (<5, <1000)
            max_match = re.search(r'<(\d+\.?\d*)', threshold_str)
            if max_match:
                max_val = float(max_match.group(1))
                return {'min': 0, 'max': max_val, 'type': 'max'}
            
            # Cas: minimum (>5, >1000)
            min_match = re.search(r'>(\d+\.?\d*)', threshold_str)
            if min_match:
                min_val = float(min_match.group(1))
                return {'min': min_val, 'max': float('inf'), 'type': 'min'}
            
            # Cas: valeur simple
            simple_match = re.search(r'(\d+\.?\d*)', threshold_str)
            if simple_match:
                val = float(simple_match.group(1))
                return {'min': val * 0.9, 'max': val * 1.1, 'type': 'target'}
                
        except Exception as e:
            logger.error(f"Erreur parsing seuil '{threshold_str}': {e}")
        
        return None
    
    def _parse_scoring_scales(self, echelles_content: str, thresholds: Dict):
        """Parse les échelles de scoring depuis Echelles.txt"""
        try:
            lines = echelles_content.split('\n')
            
            for line in lines:
                line = line.strip()
                # Parser les classifications de risque
                if 'FAIBLE' in line and '0-4' in line:
                    thresholds['scoring'] = {
                        'FAIBLE': (0, 4),
                        'MOYEN': (5, 8), 
                        'FORT': (9, 12),
                        'TRÈS GRAVE': (13, float('inf'))
                    }
                    break
                    
        except Exception as e:
            logger.error(f"Erreur parsing échelles: {e}")
    
    def _get_default_references(self) -> Dict:
        """Références par défaut si les fichiers ne sont pas disponibles"""
        return {
            'echelles': """
SCORE PARAMÈTRE (0-2):
0 = Conforme aux normes
1 = Dépassement léger (≤ 10%)
2 = Dépassement important (> 10%)

CLASSIFICATION DES RISQUES:
0-4 = FAIBLE, 5-8 = MOYEN, 9-12 = FORT, 13+ = TRÈS GRAVE
            """,
            'seuils_eau': {
                'pH': (6.5, 8.5), 'Température': (15, 25), 'Turbidité': (0, 5),
                'Conductivité': (0, 1000), 'DBO5': (0, 5), 'DCO': (0, 25),
                'Oxygène dissous': (5, float('inf')), 'Nitrates': (0, 50),
                'Plomb': (0, 0.01), 'Cadmium': (0, 0.005), 'Mercure': (0, 0.001)
            }
        }
    
    def extract_parameters_from_text(self, text_data: str, data_type: str = "mixed") -> Dict:
        """
        Extrait les paramètres environnementaux d'un texte en utilisant l'IA
        """
        try:
            # Préparer le prompt pour Gemini
            prompt = self._create_extraction_prompt(text_data, data_type)
            
            # Utiliser Gemini pour l'extraction via gemini_integration
            try:
                # Créer un fichier temporaire avec le texte pour l'analyse
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                    temp_file.write(f"PROMPT: {prompt}\n\nDATA: {text_data}")
                    temp_path = temp_file.name
                
                # Utiliser l'analyseur d'image avec le fichier texte
                df, result = analyze_environmental_image_with_gemini(temp_path)
                
                # Nettoyer le fichier temporaire
                os.unlink(temp_path)
                
                if isinstance(result, dict) and any(key in result for key in ['parameters', 'eau', 'sol', 'air']):
                    return self._process_ai_extraction(result)
                else:
                    logger.warning("Résultat IA inattendu, utilisation de l'extraction par défaut")
                    return self._fallback_extraction(text_data)
                    
            except Exception as gemini_error:
                logger.error(f"Erreur Gemini: {gemini_error}")
                return self._fallback_extraction(text_data)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction IA: {e}")
            return self._fallback_extraction(text_data)
    
    def extract_parameters_from_file(self, file_path: str) -> Dict:
        """
        Extrait les paramètres environnementaux d'un fichier (image, PDF, Excel, etc.)
        """
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                return self._extract_from_image(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                return self._extract_from_excel(file_path)
            elif file_ext in ['.pdf']:
                return self._extract_from_pdf(file_path)
            elif file_ext in ['.txt', '.csv']:
                return self._extract_from_text_file(file_path)
            else:
                raise ValueError(f"Type de fichier non supporté: {file_ext}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du fichier {file_path}: {e}")
            return {"error": str(e)}
    
    def _extract_from_image(self, image_path: str) -> Dict:
        """Extrait les paramètres d'une image en utilisant Gemini Vision"""
        try:
            # Utiliser Gemini Vision pour analyser l'image
            df, result = analyze_environmental_image_with_gemini(image_path)
            
            if isinstance(result, dict) and 'parameters' in result:
                return self._process_ai_extraction(result['parameters'])
            else:
                # Traiter le DataFrame retourné
                return self._process_dataframe_extraction(df)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction d'image: {e}")
            return {"error": str(e)}
    
    def _extract_from_excel(self, excel_path: str) -> Dict:
        """Extrait les paramètres d'un fichier Excel"""
        try:
            # Lire toutes les feuilles Excel
            excel_data = pd.read_excel(excel_path, sheet_name=None)
            
            extracted_params = {}
            for sheet_name, df in excel_data.items():
                # Convertir le DataFrame en texte pour l'analyse IA
                sheet_text = df.to_string()
                sheet_params = self.extract_parameters_from_text(sheet_text, "excel")
                
                if sheet_params:
                    extracted_params[sheet_name] = sheet_params
            
            return extracted_params if extracted_params else {"error": "Aucun paramètre trouvé"}
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction Excel: {e}")
            return {"error": str(e)}
    
    def _extract_from_pdf(self, pdf_path: str) -> Dict:
        """Extrait les paramètres d'un fichier PDF avec solution alternative"""
        try:
            # Solution alternative : utiliser Gemini Vision directement sur le PDF
            # Gemini peut analyser les PDFs directement
            logger.info(f"Analyse PDF avec Gemini Vision: {pdf_path}")
            
            try:
                # Utiliser Gemini Vision pour analyser le PDF directement
                df, result = analyze_environmental_image_with_gemini(pdf_path)
                
                if isinstance(result, dict) and any(key in result for key in ['parameters', 'eau', 'sol', 'air']):
                    return self._process_ai_extraction(result)
                else:
                    # Traiter le DataFrame retourné
                    return self._process_dataframe_extraction(df)
                    
            except Exception as gemini_error:
                logger.error(f"Erreur Gemini Vision PDF: {gemini_error}")
                
                # Fallback final : extraction basique du nom de fichier
                return self._extract_pdf_fallback(pdf_path)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction PDF: {e}")
            return {"error": str(e)}
    
    def _extract_pdf_fallback(self, pdf_path: str) -> Dict:
        """Extraction de secours pour PDF basée sur le nom de fichier et métadonnées"""
        try:
            filename = os.path.basename(pdf_path)
            logger.info(f"Extraction fallback PDF pour: {filename}")
            
            # Analyser le nom de fichier pour des indices
            extracted = {
                'metadata': {
                    'extraction_method': 'PDF_Fallback',
                    'filename': filename,
                    'note': 'Extraction basée sur le nom de fichier - modules PDF non disponibles'
                },
                'eau': {},
                'sol': {},
                'air': {}
            }
            
            # Rechercher des mots-clés dans le nom de fichier
            filename_lower = filename.lower()
            
            # Mots-clés environnementaux
            if any(word in filename_lower for word in ['eau', 'water', 'hydro']):
                extracted['eau']['analyse_detectee'] = {'valeur': 'Présente', 'source': 'nom_fichier'}
            
            if any(word in filename_lower for word in ['sol', 'soil', 'terre']):
                extracted['sol']['analyse_detectee'] = {'valeur': 'Présente', 'source': 'nom_fichier'}
            
            if any(word in filename_lower for word in ['air', 'atmosphere', 'emission']):
                extracted['air']['analyse_detectee'] = {'valeur': 'Présente', 'source': 'nom_fichier'}
            
            # Rechercher des valeurs numériques dans le nom
            import re
            numbers = re.findall(r'\d+\.?\d*', filename)
            if numbers:
                extracted['metadata']['valeurs_detectees'] = numbers
            
            return extracted
            
        except Exception as e:
            logger.error(f"Erreur extraction fallback PDF: {e}")
            return {"error": str(e)}
    
    def _extract_from_text_file(self, file_path: str) -> Dict:
        """Extrait les paramètres d'un fichier texte"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.extract_parameters_from_text(content, "text")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du fichier texte: {e}")
            return {"error": str(e)}
    
    def _create_extraction_prompt(self, data: str, data_type: str) -> str:
        """Crée un prompt optimisé pour l'extraction de paramètres SLRI"""
        
        base_prompt = f"""
Analyse les données environnementales suivantes et EXTRAIS pour chaque paramètre uniquement :
- le nom du paramètre (ex: pH, Température, Plomb, etc.)
- la valeur numérique ou qualitative principale (PAS de phrase, PAS de citation)
- l'unité (ex: °C, mg/L, µg/m3, m, etc. ou vide si non applicable)

Répond STRICTEMENT au format JSON suivant (une LIGNE par paramètre) :
[
  {{"parametre": "...", "valeur": ..., "unite": "..."}},
  ...
]

AUCUNE PHRASE, AUCUN COMMENTAIRE, AUCUNE CITATION, AUCUNE REFERENCE DE PAGE.
Seulement la liste des paramètres détectés, valeur principale et unité.
Exemple :
[
  {{"parametre": "Température", "valeur": 39, "unite": "°C"}},
  {{"parametre": "pH", "valeur": 7.2, "unite": ""}}
]

Données à analyser :
{data}
"""
        return base_prompt
    
    def _process_ai_extraction(self, ai_result: Dict) -> Dict:
        """Traite les résultats de l'extraction IA"""
        try:
            processed = {
                'eau': {},
                'sol': {},
                'air': {},
                'biologique': {},
                'humain': {},
                'metadata': {
                    'extraction_method': 'AI',
                    'total_parameters': 0,
                    'conformes': 0,
                    'depassements': 0
                }
            }
            
            # Traiter chaque milieu
            for milieu in ['eau', 'sol', 'air', 'biologique', 'humain']:
                if milieu in ai_result:
                    processed[milieu] = ai_result[milieu]
                    processed['metadata']['total_parameters'] += len(ai_result[milieu])
                    
                    # Compter les conformités/dépassements
                    for param, data in ai_result[milieu].items():
                        if isinstance(data, dict) and 'statut' in data:
                            if data['statut'] == 'conforme':
                                processed['metadata']['conformes'] += 1
                            else:
                                processed['metadata']['depassements'] += 1
            
            return processed
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement des résultats IA: {e}")
            return {"error": str(e)}
    
    def _process_dataframe_extraction(self, df: pd.DataFrame) -> Dict:
        """Traite l'extraction à partir d'un DataFrame"""
        try:
            if df is None or df.empty:
                return {"error": "DataFrame vide"}
            
            # Convertir le DataFrame en format SLRI
            processed = {
                'eau': {},
                'sol': {},
                'air': {},
                'metadata': {
                    'extraction_method': 'DataFrame',
                    'total_parameters': len(df)
                }
            }
            
            # Traiter chaque ligne du DataFrame
            for _, row in df.iterrows():
                param_name = str(row.get('Paramètre', ''))
                param_value = row.get('Valeur', 0)
                param_unit = str(row.get('Unité', ''))
                
                # Classifier le paramètre par milieu
                milieu = self._classify_parameter(param_name)
                if milieu:
                    processed[milieu][param_name] = {
                        'valeur': param_value,
                        'unité': param_unit,
                        'score': self._calculate_slri_score(param_name, param_value),
                        'statut': 'à_evaluer'
                    }
            
            return processed
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement DataFrame: {e}")
            return {"error": str(e)}
    
    def _classify_parameter(self, param_name: str) -> Optional[str]:
        """Classifie un paramètre par milieu environnemental"""
        param_lower = param_name.lower()
        
        for milieu, params in self.parameter_categories.items():
            for param in params:
                if param.lower() in param_lower or param_lower in param.lower():
                    return milieu
        
        return None
    
    def _calculate_slri_score(self, param_name: str, value: float, milieu: str = 'eau') -> int:
        """Calcule le score SLRI (0-2) pour un paramètre selon les références SLRI"""
        try:
            # Obtenir les seuils détaillés depuis les références SLRI
            seuils_detailles = self.slri_references.get('seuils_detailles', {})
            
            if milieu in seuils_detailles:
                milieu_seuils = seuils_detailles[milieu]
                
                # Chercher le paramètre (avec variations de noms)
                threshold = None
                for seuil_name, seuil_data in milieu_seuils.items():
                    if (param_name.lower() in seuil_name.lower() or 
                        seuil_name.lower() in param_name.lower()):
                        threshold = seuil_data
                        break
                
                if threshold:
                    return self._evaluate_parameter_score(value, threshold)
            
            # Fallback: utiliser les seuils par défaut
            return self._calculate_default_score(param_name, value, milieu)
            
        except Exception as e:
            logger.error(f"Erreur calcul score SLRI pour {param_name}: {e}")
            return 0
    
    def _evaluate_parameter_score(self, value: float, threshold: Dict) -> int:
        """Évalue le score d'un paramètre selon son seuil SLRI"""
        try:
            min_val = threshold.get('min', 0)
            max_val = threshold.get('max', float('inf'))
            threshold_type = threshold.get('type', 'range')
            
            # Paramètre dans l'intervalle acceptable
            if min_val <= value <= max_val:
                return 0  # Conforme aux normes
            
            # Calculer le dépassement
            if threshold_type == 'max' and value > max_val:
                depassement_pct = ((value - max_val) / max_val) * 100
            elif threshold_type == 'min' and value < min_val:
                depassement_pct = ((min_val - value) / min_val) * 100
            elif threshold_type == 'range':
                if value > max_val:
                    depassement_pct = ((value - max_val) / max_val) * 100
                elif value < min_val:
                    depassement_pct = ((min_val - value) / min_val) * 100
                else:
                    return 0
            else:
                return 0
            
            # Classification selon SLRI
            if depassement_pct <= 10:
                return 1  # Dépassement léger (≤ 10%)
            else:
                return 2  # Dépassement important (> 10%)
                
        except Exception as e:
            logger.error(f"Erreur évaluation score: {e}")
            return 0
    
    def _calculate_default_score(self, param_name: str, value: float, milieu: str) -> int:
        """Calcul de score par défaut si pas de seuils SLRI trouvés"""
        # Seuils par défaut basés sur les normes générales
        default_thresholds = {
            'eau': {
                'ph': {'min': 6.5, 'max': 8.5},
                'temperature': {'min': 15, 'max': 25},
                'turbidity': {'min': 0, 'max': 5},
                'conductivity': {'min': 0, 'max': 1000}
            },
            'sol': {
                'ph': {'min': 6.0, 'max': 8.0},
                'organic_matter': {'min': 2, 'max': 5}
            },
            'air': {
                'pm10': {'min': 0, 'max': 50},
                'pm25': {'min': 0, 'max': 25},
                'so2': {'min': 0, 'max': 125}
            }
        }
        
        if milieu in default_thresholds:
            for param, threshold in default_thresholds[milieu].items():
                if param.lower() in param_name.lower():
                    return self._evaluate_parameter_score(value, threshold)
        
        return 0  # Par défaut conforme
    
    def _fallback_extraction(self, text_data: str) -> Dict:
        """Extraction de secours sans IA"""
        try:
            # Extraction basique par mots-clés
            extracted = {
                'eau': {},
                'sol': {},
                'air': {},
                'metadata': {
                    'extraction_method': 'Fallback',
                    'note': 'Extraction basique sans IA'
                }
            }
            
            lines = text_data.split('\n')
            for line in lines:
                # Rechercher des patterns de paramètres
                if ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        param_name = parts[0].strip()
                        param_value = parts[1].strip()
                        
                        milieu = self._classify_parameter(param_name)
                        if milieu:
                            extracted[milieu][param_name] = {
                                'valeur': param_value,
                                'extraction': 'basique'
                            }
            
            return extracted
            
        except Exception as e:
            logger.error(f"Erreur extraction de secours: {e}")
            return {"error": str(e)}

# Fonction d'interface principale
def extract_environmental_parameters(source, source_type="auto") -> Dict:
    """
    Fonction principale pour extraire les paramètres environnementaux
    
    Args:
        source: Chemin de fichier, texte, ou données à analyser
        source_type: "file", "text", "coordinates", ou "auto"
    
    Returns:
        Dict contenant les paramètres extraits et classifiés selon SLRI
    """
    extractor = SLRIAIExtractor()
    
    try:
        if source_type == "file" or (source_type == "auto" and os.path.isfile(str(source))):
            return extractor.extract_parameters_from_file(source)
        elif source_type == "text" or (source_type == "auto" and isinstance(source, str)):
            return extractor.extract_parameters_from_text(source)
        else:
            return {"error": "Type de source non reconnu"}
            
    except Exception as e:
        logger.error(f"Erreur extraction paramètres: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # Test de l'extracteur
    extractor = SLRIAIExtractor()
    
    # Test avec données texte
    test_data = """
    Analyse de l'eau:
    pH: 7.2
    Température: 22°C
    Turbidité: 3.5 NTU
    Conductivité: 850 µS/cm
    DBO5: 4.2 mg/L
    Plomb: 0.008 mg/L
    """
    
    result = extractor.extract_parameters_from_text(test_data)
    print("Résultat extraction:", json.dumps(result, indent=2, ensure_ascii=False))
