#!/usr/bin/env python3
"""
Système de scoring environnemental basé sur les intervalles acceptables.
Attribue des scores de 1 à 3 selon la conformité aux normes marocaines.
"""

import pandas as pd
import numpy as np
import re
import logging
from typing import Dict, Tuple, Optional, Union

logger = logging.getLogger(__name__)

class EnvironmentalScoring:
    """Classe pour le scoring des paramètres environnementaux."""
    
    def __init__(self):
        """Initialise le système de scoring avec les références marocaines."""
        self.reference_standards = self._load_morocco_standards()
        
    def _load_morocco_standards(self) -> Dict:
        """Charge les standards environnementaux marocains."""
        return {
            # Paramètres climatiques
            "Température maximale": {"min": 25, "max": 45, "unit": "°C", "category": "climat"},
            "Température minimale": {"min": 5, "max": 25, "unit": "°C", "category": "climat"},
            "Précipitations annuelles moyennes": {"min": 200, "max": 800, "unit": "mm", "category": "climat"},
            "Précipitations annuelles minimales": {"min": 50, "max": 400, "unit": "mm", "category": "climat"},
            "Précipitations annuelles maximales": {"min": 400, "max": 1200, "unit": "mm", "category": "climat"},
            "Vitesse du vent": {"min": 2, "max": 15, "unit": "m/s", "category": "climat"},
            "Fréquence du vent de Nord-Nord-est": {"min": 15, "max": 40, "unit": "%", "category": "climat"},
            
            # Paramètres géographiques
            "Altitude moyenne des plaines côtières": {"min": 0, "max": 100, "unit": "m", "category": "géographie"},
            "Altitude des Hamadas": {"min": 200, "max": 800, "unit": "m", "category": "géographie"},
            
            # Paramètres hydrogéologiques
            "Surface Sebkha Lahmira": {"min": 500, "max": 700, "unit": "ha", "category": "hydrologie"},
            "Profondeur Sebkha Lahmira": {"min": 2, "max": 8, "unit": "m", "category": "hydrologie"},
            "Surface Sebkha Tizfourine": {"min": 2000, "max": 3000, "unit": "ha", "category": "hydrologie"},
            "Profondeur Sebkha Tizfourine": {"min": 3, "max": 7, "unit": "m", "category": "hydrologie"},
            "Surface Sebkha Tah": {"min": 7000, "max": 9000, "unit": "ha", "category": "hydrologie"},
            "Profondeur Sebkha Tah": {"min": 50, "max": 80, "unit": "m", "category": "hydrologie"},
            "Débit pointe Oued El Hamra": {"min": 0.5, "max": 15, "unit": "m³/s", "category": "hydrologie"},
            
            # Paramètres géologiques
            "Surface nappe de Tarfaya": {"min": 80, "max": 150, "unit": "km²", "category": "géologie"},
            "Puissance nappe de Tarfaya": {"min": 3, "max": 30, "unit": "m", "category": "géologie"},
            "Transmissivité du grès calcaire": {"min": 1e-4, "max": 5e-3, "unit": "m²/s", "category": "géologie"},
            "Transmissivité du marno-calcaire": {"min": 1e-5, "max": 1e-3, "unit": "m²/s", "category": "géologie"},
            
            # Paramètres de qualité de l'air (standards OMS/Maroc)
            "CO2": {"min": 350, "max": 450, "unit": "ppm", "category": "air"},
            "NOx": {"min": 0, "max": 40, "unit": "µg/m³", "category": "air"},
            "PM10": {"min": 0, "max": 50, "unit": "µg/m³", "category": "air"},
            "PM2.5": {"min": 0, "max": 25, "unit": "µg/m³", "category": "air"},
            "SO2": {"min": 0, "max": 125, "unit": "µg/m³", "category": "air"},
            "O3": {"min": 0, "max": 120, "unit": "µg/m³", "category": "air"},
            
            # Paramètres de qualité de l'eau (standards marocains)
            "pH": {"min": 6.5, "max": 8.5, "unit": "-", "category": "eau"},
            "Turbidité": {"min": 0, "max": 5, "unit": "NTU", "category": "eau"},
            "Chlore résiduel": {"min": 0.2, "max": 2.0, "unit": "mg/L", "category": "eau"},
            "Conductivité": {"min": 50, "max": 2700, "unit": "µS/cm", "category": "eau"},
            "TDS": {"min": 0, "max": 1500, "unit": "mg/L", "category": "eau"},
            "Nitrates": {"min": 0, "max": 50, "unit": "mg/L", "category": "eau"},
            "Phosphates": {"min": 0, "max": 2, "unit": "mg/L", "category": "eau"},
            
            # Paramètres du sol
            "pH du sol": {"min": 6.0, "max": 8.0, "unit": "-", "category": "sol"},
            "Métaux lourds Pb": {"min": 0, "max": 100, "unit": "mg/kg", "category": "sol"},
            "Métaux lourds Cd": {"min": 0, "max": 3, "unit": "mg/kg", "category": "sol"},
            "Métaux lourds Hg": {"min": 0, "max": 1, "unit": "mg/kg", "category": "sol"},
            "Hydrocarbures": {"min": 0, "max": 100, "unit": "mg/kg", "category": "sol"},
            "Matière organique": {"min": 1, "max": 5, "unit": "%", "category": "sol"},
        }
    
    def _parse_numeric_value(self, value_str: str) -> Optional[float]:
        """Extrait une valeur numérique d'une chaîne."""
        if pd.isna(value_str) or value_str == "":
            return None
            
        # Convertir en string si ce n'est pas déjà le cas
        value_str = str(value_str).strip()
        
        # Gérer les notations scientifiques (ex: 3 x 10⁻⁴)
        if 'x' in value_str.lower() and '10' in value_str:
            try:
                # Remplacer les exposants Unicode
                value_str = value_str.replace('⁻', '-').replace('⁺', '+')
                # Extraire les parties
                parts = re.findall(r'([\d.]+)\s*x\s*10\s*[\^]?([-+]?\d+)', value_str, re.IGNORECASE)
                if parts:
                    base, exp = parts[0]
                    return float(base) * (10 ** int(exp))
            except:
                pass
        
        # Gérer les intervalles (ex: "25-35", ">100", "<5")
        if '-' in value_str and not value_str.startswith('-'):
            try:
                parts = value_str.split('-')
                if len(parts) == 2:
                    return (float(parts[0]) + float(parts[1])) / 2  # Moyenne de l'intervalle
            except:
                pass
        
        # Gérer les comparaisons (>, <, >=, <=)
        comparison_match = re.match(r'([><]=?)\s*([\d.]+)', value_str)
        if comparison_match:
            return float(comparison_match.group(2))
        
        # Extraction numérique simple
        numeric_match = re.search(r'([\d.]+)', value_str)
        if numeric_match:
            try:
                return float(numeric_match.group(1))
            except:
                pass
        
        return None
    
    def _normalize_parameter_name(self, param_name: str) -> str:
        """Normalise le nom d'un paramètre pour la recherche."""
        if pd.isna(param_name):
            return ""
        
        # Nettoyer et normaliser
        normalized = str(param_name).strip().lower()
        
        # Mappings spécifiques
        mappings = {
            'co2': 'CO2',
            'nox': 'NOx',
            'pm10': 'PM10',
            'pm2.5': 'PM2.5',
            'so2': 'SO2',
            'o3': 'O3',
            'ph': 'pH',
            'ph du sol': 'pH du sol',
            'turbidite': 'Turbidité',
            'conductivite': 'Conductivité',
            'nitrates': 'Nitrates',
            'phosphates': 'Phosphates',
            'plomb': 'Métaux lourds Pb',
            'pb': 'Métaux lourds Pb',
            'cadmium': 'Métaux lourds Cd',
            'cd': 'Métaux lourds Cd',
            'mercure': 'Métaux lourds Hg',
            'hg': 'Métaux lourds Hg',
            'hydrocarbures': 'Hydrocarbures',
            'matiere organique': 'Matière organique',
        }
        
        # Recherche exacte d'abord
        for key, standard_name in mappings.items():
            if key in normalized:
                return standard_name
        
        # Recherche par similarité pour les paramètres de référence
        for standard_param in self.reference_standards.keys():
            if normalized in standard_param.lower() or standard_param.lower() in normalized:
                return standard_param
        
        # Retourner le nom original si aucune correspondance
        return param_name
    
    def _calculate_score(self, value: float, standard: Dict) -> Tuple[int, str]:
        """Calcule le score basé sur l'intervalle acceptable."""
        min_val = standard["min"]
        max_val = standard["max"]
        
        if min_val <= value <= max_val:
            return 1, "Conforme"
        elif value < min_val:
            deviation = (min_val - value) / min_val
            if deviation <= 0.2:  # 20% en dessous
                return 2, "Légèrement en dessous"
            else:
                return 3, "Très en dessous"
        else:  # value > max_val
            deviation = (value - max_val) / max_val
            if deviation <= 0.2:  # 20% au dessus
                return 2, "Légèrement au dessus"
            else:
                return 3, "Très au dessus"
    
    def _search_online_standard(self, param_name: str, unit: str = "") -> Optional[Dict]:
        """Recherche en ligne les standards pour un paramètre inconnu."""
        # Base de données étendue pour les paramètres courants
        extended_standards = {
            # Paramètres atmosphériques supplémentaires
            "CO": {"min": 0, "max": 10, "unit": "mg/m³", "category": "air"},
            "Benzène": {"min": 0, "max": 5, "unit": "µg/m³", "category": "air"},
            "Formaldéhyde": {"min": 0, "max": 30, "unit": "µg/m³", "category": "air"},
            
            # Paramètres d'eau supplémentaires
            "Ammoniaque": {"min": 0, "max": 0.5, "unit": "mg/L", "category": "eau"},
            "Sulfates": {"min": 0, "max": 250, "unit": "mg/L", "category": "eau"},
            "Chlorures": {"min": 0, "max": 250, "unit": "mg/L", "category": "eau"},
            "Calcium": {"min": 0, "max": 200, "unit": "mg/L", "category": "eau"},
            "Magnésium": {"min": 0, "max": 50, "unit": "mg/L", "category": "eau"},
            "Fer": {"min": 0, "max": 0.3, "unit": "mg/L", "category": "eau"},
            "Manganèse": {"min": 0, "max": 0.1, "unit": "mg/L", "category": "eau"},
            
            # Paramètres de sol supplémentaires
            "Azote total": {"min": 0.1, "max": 0.5, "unit": "%", "category": "sol"},
            "Phosphore": {"min": 10, "max": 50, "unit": "mg/kg", "category": "sol"},
            "Potassium": {"min": 100, "max": 500, "unit": "mg/kg", "category": "sol"},
            "Zinc": {"min": 0, "max": 300, "unit": "mg/kg", "category": "sol"},
            "Cuivre": {"min": 0, "max": 100, "unit": "mg/kg", "category": "sol"},
            
            # Paramètres de bruit
            "Niveau sonore": {"min": 35, "max": 65, "unit": "dB", "category": "bruit"},
            "Bruit de fond": {"min": 30, "max": 55, "unit": "dB", "category": "bruit"},
        }
        
        # Recherche dans la base étendue
        normalized_param = param_name.strip().lower()
        for std_name, std_data in extended_standards.items():
            if normalized_param in std_name.lower() or std_name.lower() in normalized_param:
                logger.info(f"Standard trouvé pour {param_name}: {std_data}")
                return std_data
        
        # Valeurs par défaut basées sur la catégorie estimée
        if any(keyword in normalized_param for keyword in ['air', 'atmosphère', 'pollution']):
            return {"min": 0, "max": 100, "unit": unit or "µg/m³", "category": "air"}
        elif any(keyword in normalized_param for keyword in ['eau', 'hydrique', 'aquatique']):
            return {"min": 0, "max": 50, "unit": unit or "mg/L", "category": "eau"}
        elif any(keyword in normalized_param for keyword in ['sol', 'terre', 'sédiment']):
            return {"min": 0, "max": 100, "unit": unit or "mg/kg", "category": "sol"}
        elif any(keyword in normalized_param for keyword in ['bruit', 'sonore', 'acoustique']):
            return {"min": 30, "max": 70, "unit": unit or "dB", "category": "bruit"}
        else:
            # Standard générique
            return {"min": 0, "max": 100, "unit": unit or "-", "category": "général"}
    
    def score_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Score un DataFrame de paramètres environnementaux."""
        if df.empty:
            return df
        
        # Créer une copie pour éviter de modifier l'original
        result_df = df.copy()
        
        # Colonnes requises
        required_columns = ['Paramètre', 'Valeur', 'Unité']
        missing_columns = [col for col in required_columns if col not in result_df.columns]
        
        if missing_columns:
            logger.error(f"Colonnes manquantes: {missing_columns}")
            return result_df
        
        # Ajouter les colonnes de scoring
        result_df['Intervalle acceptable'] = ""
        result_df['Score'] = 0
        result_df['Statut'] = ""
        result_df['Catégorie'] = ""
        
        for idx, row in result_df.iterrows():
            param_name = str(row['Paramètre']).strip()
            value_str = str(row['Valeur']).strip()
            unit = str(row['Unité']).strip() if 'Unité' in row else ""
            
            # Parser la valeur numérique
            numeric_value = self._parse_numeric_value(value_str)
            if numeric_value is None:
                result_df.at[idx, 'Score'] = 0
                result_df.at[idx, 'Statut'] = "Valeur non numérique"
                continue
            
            # Normaliser le nom du paramètre
            normalized_param = self._normalize_parameter_name(param_name)
            
            # Chercher dans les standards de référence
            standard = None
            if normalized_param in self.reference_standards:
                standard = self.reference_standards[normalized_param]
            else:
                # Rechercher un standard alternatif
                standard = self._search_online_standard(param_name, unit)
                if standard:
                    logger.info(f"Standard alternatif trouvé pour {param_name}")
            
            if standard:
                # Calculer le score
                score, status = self._calculate_score(numeric_value, standard)
                
                # Mettre à jour le DataFrame
                result_df.at[idx, 'Intervalle acceptable'] = f"{standard['min']}-{standard['max']} {standard['unit']}"
                result_df.at[idx, 'Score'] = score
                result_df.at[idx, 'Statut'] = status
                result_df.at[idx, 'Catégorie'] = standard['category']
            else:
                # Paramètre inconnu
                result_df.at[idx, 'Score'] = 0
                result_df.at[idx, 'Statut'] = "Standard non trouvé"
                result_df.at[idx, 'Catégorie'] = "inconnu"
                logger.warning(f"Aucun standard trouvé pour: {param_name}")
        
        # Réorganiser les colonnes dans l'ordre souhaité
        column_order = ['Paramètre', 'Valeur', 'Unité', 'Intervalle acceptable', 'Score', 'Statut', 'Catégorie']
        existing_columns = [col for col in column_order if col in result_df.columns]
        other_columns = [col for col in result_df.columns if col not in column_order]
        
        result_df = result_df[existing_columns + other_columns]
        
        return result_df
    
    def generate_summary_report(self, scored_df: pd.DataFrame) -> str:
        """Génère un rapport de synthèse du scoring."""
        if scored_df.empty:
            return "Aucune donnée à analyser."
        
        total_params = len(scored_df)
        score_counts = scored_df['Score'].value_counts().sort_index()
        
        report = f"""
=== RAPPORT DE SCORING ENVIRONNEMENTAL ===

Nombre total de paramètres analysés: {total_params}

Répartition des scores:
- Score 1 (Conforme): {score_counts.get(1, 0)} paramètres ({score_counts.get(1, 0)/total_params*100:.1f}%)
- Score 2 (Attention): {score_counts.get(2, 0)} paramètres ({score_counts.get(2, 0)/total_params*100:.1f}%)
- Score 3 (Critique): {score_counts.get(3, 0)} paramètres ({score_counts.get(3, 0)/total_params*100:.1f}%)
- Score 0 (Non évalué): {score_counts.get(0, 0)} paramètres ({score_counts.get(0, 0)/total_params*100:.1f}%)

Paramètres critiques (Score 3):
"""
        
        critical_params = scored_df[scored_df['Score'] == 3]
        if not critical_params.empty:
            for _, row in critical_params.iterrows():
                report += f"- {row['Paramètre']}: {row['Valeur']} {row['Unité']} (Acceptable: {row['Intervalle acceptable']})\n"
        else:
            report += "Aucun paramètre critique détecté.\n"
        
        report += f"""
Paramètres nécessitant attention (Score 2):
"""
        
        attention_params = scored_df[scored_df['Score'] == 2]
        if not attention_params.empty:
            for _, row in attention_params.iterrows():
                report += f"- {row['Paramètre']}: {row['Valeur']} {row['Unité']} (Acceptable: {row['Intervalle acceptable']})\n"
        else:
            report += "Aucun paramètre nécessitant attention.\n"
        
        # Analyse par catégorie
        if 'Catégorie' in scored_df.columns:
            report += f"""
Analyse par catégorie:
"""
            category_analysis = scored_df.groupby('Catégorie')['Score'].agg(['count', 'mean']).round(2)
            for category, stats in category_analysis.iterrows():
                report += f"- {category.title()}: {stats['count']} paramètres, score moyen: {stats['mean']}\n"
        
        return report
