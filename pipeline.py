import os
import logging
import pandas as pd
from typing import Optional, Union, Dict, List, Any
from pathlib import Path
import json

# Import des modules du projet
from config import OUTPUT_DIR
from utils import extract_text_from_file, save_dataframe_to_excel, get_timestamp
from data_processing import load_data, enrich_data, clean_data, analyze_environmental_data
from model_interface import QwenVLModel, analyze_environmental_image

logger = logging.getLogger(__name__)

class AnalysisPipeline:
    """Classe principale pour orchestrer le pipeline d'analyse de risque environnemental.
    
    Cette classe gère le traitement de différents types de fichiers (Excel, CSV, PDF, texte, images)
    et l'exportation des résultats dans différents formats (XLSX, CSV, JSON).
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialise le pipeline d'analyse.
        
        Args:
            model_path: Chemin vers le modèle Qwen2-VL (optionnel)
        """
        self.model = QwenVLModel(model_path)
        logger.info("Pipeline d'analyse initialisé")
    
    def process_file(self, file_path: str, output_format: str = 'xlsx') -> Optional[Union[str, pd.DataFrame]]:
        """Traite un fichier et retourne les résultats.
        
        Args:
            file_path: Chemin vers le fichier à analyser
            output_format: Format de sortie ('xlsx', 'csv', 'json', 'df')
            
        Returns:
            Selon output_format:
                - 'xlsx' ou 'csv': Chemin vers le fichier de sortie
                - 'json': Chaîne JSON
                - 'df': DataFrame pandas
                - None en cas d'erreur
        """
        try:
            logger.info(f"Traitement du fichier: {file_path}")
            
            # Vérifier que le fichier existe
            if not os.path.exists(file_path):
                logger.error(f"Le fichier {file_path} n'existe pas")
                return None
            
            # Déterminer le type de fichier
            ext = os.path.splitext(file_path)[1].lower()
            
            # Traiter selon le type de fichier
            if ext in ['.xlsx', '.xls', '.csv']:
                return self._process_tabular_file(file_path, output_format)
            elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                return self._process_image_file(file_path, output_format)
            elif ext in ['.pdf', '.txt', '.docx']:
                return self._process_text_file(file_path, output_format)
            else:
                logger.error(f"Type de fichier non pris en charge: {ext}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du fichier {file_path}: {str(e)}")
            return None
    
    def process_batch(self, input_dir: str, output_dir: Optional[str] = None, 
                      output_format: str = 'xlsx') -> Dict[str, Union[str, None]]:
        """Traite tous les fichiers dans un répertoire.
        
        Args:
            input_dir: Répertoire contenant les fichiers à analyser
            output_dir: Répertoire de sortie (par défaut: OUTPUT_DIR)
            output_format: Format de sortie ('xlsx', 'csv', 'json')
            
        Returns:
            Dictionnaire {nom_fichier: chemin_résultat ou None si erreur}
        """
        if output_dir is None:
            output_dir = OUTPUT_DIR
        
        os.makedirs(output_dir, exist_ok=True)
        results = {}
        
        for filename in os.listdir(input_dir):
            file_path = os.path.join(input_dir, filename)
            if os.path.isfile(file_path):
                result = self.process_file(file_path, output_format)
                results[filename] = result
        
        return results
    
    def _process_tabular_file(self, file_path: str, output_format: str) -> Optional[Union[str, pd.DataFrame]]:
        """Traite un fichier tabulaire (Excel, CSV)."""
        # Charger les données
        df = load_data(file_path)
        if df is None:
            return None
        
        # Nettoyer les données
        df = clean_data(df)
        
        # Enrichir les données
        df = enrich_data(df)
        
        # Analyser les données
        df = analyze_environmental_data(df)
        
        # Exporter les résultats
        return self._export_results(df, output_format)
    
    def _process_image_file(self, file_path: str, output_format: str) -> Optional[Union[str, pd.DataFrame]]:
        """Traite une image."""
        try:
            # Analyser l'image avec le modèle
            result_df = analyze_environmental_image(file_path, self.model)
            
            if result_df is None or result_df.empty:
                logger.warning(f"Aucun résultat obtenu pour l'image {file_path}")
                return None
            
            # Enrichir les données
            result_df = enrich_data(result_df)
            
            # Analyser les données
            result_df = analyze_environmental_data(result_df)
            
            # Exporter les résultats
            return self._export_results(result_df, output_format)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'image {file_path}: {str(e)}")
            return None
    
    def _process_text_file(self, file_path: str, output_format: str) -> Optional[Union[str, pd.DataFrame]]:
        """Traite un fichier texte (PDF, TXT, DOCX)."""
        try:
            # Extraire le texte du fichier
            text = extract_text_from_file(file_path)
            
            if not text:
                logger.warning(f"Aucun texte extrait du fichier {file_path}")
                return None
            
            # Analyser le texte avec le modèle
            result_df = self.model.analyze_text(text)
            
            if result_df is None or result_df.empty:
                logger.warning(f"Aucun résultat obtenu pour le texte extrait de {file_path}")
                return None
            
            # Enrichir les données
            result_df = enrich_data(result_df)
            
            # Analyser les données
            result_df = analyze_environmental_data(result_df)
            
            # Exporter les résultats
            return self._export_results(result_df, output_format)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du fichier texte {file_path}: {str(e)}")
            return None
    
    def _export_results(self, df: pd.DataFrame, output_format: str) -> Union[str, pd.DataFrame]:
        """Exporte les résultats dans le format spécifié."""
        if output_format == 'df':
            return df
        
        timestamp = get_timestamp()
        
        if output_format == 'xlsx':
            output_path = os.path.join(OUTPUT_DIR, f"resultat_analyse_risque_{timestamp}.xlsx")
            save_dataframe_to_excel(df, output_path)
            logger.info(f"Résultats exportés vers {output_path}")
            return output_path
            
        elif output_format == 'csv':
            output_path = os.path.join(OUTPUT_DIR, f"resultat_analyse_risque_{timestamp}.csv")
            df.to_csv(output_path, index=False, encoding='utf-8')
            logger.info(f"Résultats exportés vers {output_path}")
            return output_path
            
        elif output_format == 'json':
            json_str = df.to_json(orient='records', force_ascii=False, indent=2)
            logger.info("Résultats convertis en JSON")
            return json_str
        
        else:
            logger.warning(f"Format de sortie non pris en charge: {output_format}. Utilisation du format xlsx par défaut.")
            output_path = os.path.join(OUTPUT_DIR, f"resultat_analyse_risque_{timestamp}.xlsx")
            save_dataframe_to_excel(df, output_path)
            logger.info(f"Résultats exportés vers {output_path}")
            return output_path