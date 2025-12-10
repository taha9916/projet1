#!/usr/bin/env python3
"""
Gestionnaire de projets pour l'analyse environnementale.
Permet de créer, sauvegarder et gérer des projets avec accumulation de paramètres.
"""

import os
import json
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import uuid

logger = logging.getLogger(__name__)

class ProjectManager:
    """Gestionnaire de projets d'analyse environnementale."""
    
    def __init__(self, projects_dir: str = "projects"):
        """Initialise le gestionnaire de projets.
        
        Args:
            projects_dir: Répertoire de stockage des projets
        """
        self.projects_dir = projects_dir
        self.current_project = None
        self.current_project_data = None
        
        # Créer le répertoire des projets s'il n'existe pas
        os.makedirs(self.projects_dir, exist_ok=True)
        
        logger.info(f"ProjectManager initialisé avec répertoire: {self.projects_dir}")
    
    def create_project(self, name: str, description: str = "", location: str = "") -> str:
        """Crée un nouveau projet.
        
        Args:
            name: Nom du projet
            description: Description du projet
            location: Localisation du projet
            
        Returns:
            ID du projet créé
        """
        project_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        
        project_data = {
            "id": project_id,
            "name": name,
            "description": description,
            "location": location,
            "created_at": timestamp,
            "last_modified": timestamp,
            "analyses": [],
            "parameters": [],
            "metadata": {
                "total_analyses": 0,
                "total_parameters": 0,
                "last_analysis_date": None
            }
        }
        
        # Sauvegarder le projet
        project_file = os.path.join(self.projects_dir, f"{project_id}.json")
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Projet créé: {name} (ID: {project_id})")
        return project_id
    
    def load_project(self, project_id: str) -> bool:
        """Charge un projet existant.
        
        Args:
            project_id: ID du projet à charger
            
        Returns:
            True si le projet a été chargé avec succès
        """
        project_file = os.path.join(self.projects_dir, f"{project_id}.json")
        
        if not os.path.exists(project_file):
            logger.error(f"Projet non trouvé: {project_id}")
            return False
        
        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                self.current_project_data = json.load(f)
            
            self.current_project = project_id
            logger.info(f"Projet chargé: {self.current_project_data['name']} (ID: {project_id})")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du projet {project_id}: {e}")
            return False
    
    def list_projects(self) -> List[Dict]:
        """Liste tous les projets disponibles.
        
        Returns:
            Liste des informations des projets
        """
        projects = []
        
        for filename in os.listdir(self.projects_dir):
            if filename.endswith('.json'):
                project_id = filename[:-5]  # Enlever .json
                try:
                    project_file = os.path.join(self.projects_dir, filename)
                    with open(project_file, 'r', encoding='utf-8') as f:
                        project_data = json.load(f)
                    
                    projects.append({
                        "id": project_id,
                        "name": project_data.get("name", "Sans nom"),
                        "description": project_data.get("description", ""),
                        "location": project_data.get("location", ""),
                        "created_at": project_data.get("created_at", ""),
                        "total_analyses": project_data.get("metadata", {}).get("total_analyses", 0),
                        "total_parameters": project_data.get("metadata", {}).get("total_parameters", 0)
                    })
                    
                except Exception as e:
                    logger.warning(f"Erreur lors de la lecture du projet {filename}: {e}")
        
        # Trier par date de création (plus récent en premier)
        projects.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return projects
    
    def add_analysis_to_project(self, analysis_df: pd.DataFrame, analysis_name: str = "", 
                               source_file: str = "", analysis_method: str = "") -> bool:
        """Ajoute une nouvelle analyse au projet courant.
        
        Args:
            analysis_df: DataFrame contenant les paramètres analysés
            analysis_name: Nom de l'analyse
            source_file: Fichier source de l'analyse
            analysis_method: Méthode d'analyse utilisée
            
        Returns:
            True si l'analyse a été ajoutée avec succès
        """
        if not self.current_project or not self.current_project_data:
            logger.error("Aucun projet chargé")
            return False
        
        if analysis_df.empty:
            logger.warning("DataFrame d'analyse vide")
            return False
        
        timestamp = datetime.now().isoformat()
        analysis_id = str(uuid.uuid4())[:8]
        
        # Créer l'entrée d'analyse
        analysis_entry = {
            "id": analysis_id,
            "name": analysis_name or f"Analyse {len(self.current_project_data['analyses']) + 1}",
            "timestamp": timestamp,
            "source_file": source_file,
            "method": analysis_method,
            "parameter_count": len(analysis_df)
        }
        
        # Convertir le DataFrame en liste de dictionnaires pour stockage JSON
        new_parameters = analysis_df.to_dict('records')
        
        # Ajouter l'ID d'analyse à chaque paramètre
        for param in new_parameters:
            param['analysis_id'] = analysis_id
            param['analysis_name'] = analysis_entry['name']
            param['timestamp'] = timestamp
        
        # Fusionner avec les paramètres existants
        merged_parameters = self._merge_parameters(self.current_project_data['parameters'], new_parameters)
        
        # Mettre à jour les données du projet
        self.current_project_data['analyses'].append(analysis_entry)
        self.current_project_data['parameters'] = merged_parameters
        self.current_project_data['last_modified'] = timestamp
        self.current_project_data['metadata'].update({
            "total_analyses": len(self.current_project_data['analyses']),
            "total_parameters": len(merged_parameters),
            "last_analysis_date": timestamp
        })
        
        # Sauvegarder le projet
        if self._save_current_project():
            logger.info(f"Analyse ajoutée au projet: {analysis_entry['name']} ({len(new_parameters)} paramètres)")
            return True
        
        return False
    
    def _merge_parameters(self, existing_parameters: List[Dict], new_parameters: List[Dict]) -> List[Dict]:
        """Fusionne les nouveaux paramètres avec les existants.
        
        Args:
            existing_parameters: Paramètres existants dans le projet
            new_parameters: Nouveaux paramètres à ajouter
            
        Returns:
            Liste fusionnée des paramètres
        """
        # Créer un dictionnaire pour détecter les doublons
        param_dict = {}
        
        # Ajouter les paramètres existants
        for param in existing_parameters:
            key = self._get_parameter_key(param)
            if key not in param_dict:
                param_dict[key] = []
            param_dict[key].append(param)
        
        # Ajouter les nouveaux paramètres
        for param in new_parameters:
            key = self._get_parameter_key(param)
            if key not in param_dict:
                param_dict[key] = []
            
            # Vérifier si c'est vraiment un doublon (même valeur et unité)
            is_duplicate = False
            for existing in param_dict[key]:
                if (existing.get('Valeur') == param.get('Valeur') and 
                    existing.get('Unité') == param.get('Unité')):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                param_dict[key].append(param)
        
        # Convertir en liste plate
        merged = []
        for param_list in param_dict.values():
            merged.extend(param_list)
        
        return merged
    
    def _get_parameter_key(self, param: Dict) -> str:
        """Génère une clé unique pour un paramètre basée sur son nom."""
        param_name = param.get('Paramètre', '').strip().lower()
        # Normaliser les variations de noms
        param_name = param_name.replace('é', 'e').replace('è', 'e').replace('à', 'a')
        return param_name
    
    def get_project_dataframe(self) -> Optional[pd.DataFrame]:
        """Retourne le DataFrame complet du projet courant.
        
        Returns:
            DataFrame contenant tous les paramètres du projet
        """
        if not self.current_project_data:
            return None
        
        if not self.current_project_data['parameters']:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.current_project_data['parameters'])
        
        # Réorganiser les colonnes dans un ordre logique
        column_order = ['Paramètre', 'Valeur', 'Unité', 'Intervalle acceptable', 
                       'Score', 'Statut', 'Catégorie', 'analysis_name', 'timestamp']
        existing_columns = [col for col in column_order if col in df.columns]
        other_columns = [col for col in df.columns if col not in column_order]
        
        return df[existing_columns + other_columns]
    
    def get_project_summary(self) -> Dict:
        """Retourne un résumé du projet courant.
        
        Returns:
            Dictionnaire contenant les statistiques du projet
        """
        if not self.current_project_data:
            return {}
        
        df = self.get_project_dataframe()
        
        summary = {
            "project_info": {
                "name": self.current_project_data.get("name", ""),
                "description": self.current_project_data.get("description", ""),
                "location": self.current_project_data.get("location", ""),
                "created_at": self.current_project_data.get("created_at", ""),
                "last_modified": self.current_project_data.get("last_modified", "")
            },
            "statistics": {
                "total_analyses": len(self.current_project_data.get("analyses", [])),
                "total_parameters": len(self.current_project_data.get("parameters", [])),
                "unique_parameters": len(df['Paramètre'].unique()) if df is not None and not df.empty else 0
            },
            "score_distribution": {},
            "category_distribution": {},
            "analyses": self.current_project_data.get("analyses", [])
        }
        
        if df is not None and not df.empty and 'Score' in df.columns:
            summary["score_distribution"] = df['Score'].value_counts().to_dict()
            
        if df is not None and not df.empty and 'Catégorie' in df.columns:
            summary["category_distribution"] = df['Catégorie'].value_counts().to_dict()
        
        return summary
    
    def export_project(self, output_path: str, format: str = "xlsx") -> bool:
        """Exporte le projet vers un fichier.
        
        Args:
            output_path: Chemin de sortie
            format: Format d'export (xlsx, csv, json)
            
        Returns:
            True si l'export a réussi
        """
        if not self.current_project_data:
            logger.error("Aucun projet chargé pour l'export")
            return False
        
        try:
            df = self.get_project_dataframe()
            
            if format.lower() == "xlsx":
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    # Feuille principale avec tous les paramètres
                    df.to_excel(writer, sheet_name='Paramètres', index=False)
                    
                    # Feuille de résumé
                    summary = self.get_project_summary()
                    summary_df = pd.DataFrame([summary["project_info"]])
                    summary_df.to_excel(writer, sheet_name='Résumé Projet', index=False)
                    
                    # Feuille des analyses
                    analyses_df = pd.DataFrame(summary["analyses"])
                    if not analyses_df.empty:
                        analyses_df.to_excel(writer, sheet_name='Analyses', index=False)
                        
            elif format.lower() == "csv":
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
                
            elif format.lower() == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_project_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Projet exporté vers: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export: {e}")
            return False
    
    def _save_current_project(self) -> bool:
        """Sauvegarde le projet courant."""
        if not self.current_project or not self.current_project_data:
            return False
        
        try:
            project_file = os.path.join(self.projects_dir, f"{self.current_project}.json")
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_project_data, f, indent=2, ensure_ascii=False)
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            return False
    
    def delete_project(self, project_id: str) -> bool:
        """Supprime un projet.
        
        Args:
            project_id: ID du projet à supprimer
            
        Returns:
            True si le projet a été supprimé
        """
        project_file = os.path.join(self.projects_dir, f"{project_id}.json")
        
        if not os.path.exists(project_file):
            logger.error(f"Projet non trouvé: {project_id}")
            return False
        
        try:
            os.remove(project_file)
            
            # Si c'est le projet courant, le décharger
            if self.current_project == project_id:
                self.current_project = None
                self.current_project_data = None
            
            logger.info(f"Projet supprimé: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression: {e}")
            return False
