"""
Module d'intégration SLRI complète pour l'application principale
Implémente la structure SLRI exacte selon les tableaux de référence
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
# from slri_integration import SLRIAnalyzer  # Commented out due to syntax errors

logger = logging.getLogger(__name__)

class SLRICompleteAnalyzer:
    """
    Analyseur SLRI complet avec structure exacte des tableaux de référence
    """
    
    def __init__(self, slri_path: str = None):
        self.slri_path = slri_path or os.path.join(os.path.dirname(__file__), "SLRI")
        self.slri_data = None
        self.load_slri_data()
    
    def load_slri_data(self):
        """Charge les données SLRI depuis les fichiers de référence"""
        try:
            self.slri_data = {
                'phases': ['PRE CONSTRUCTION', 'CONSTRUCTION', 'exploitation', 'démantalement'],
                'milieux': ['eau', 'sol', 'air', 'biologique', 'humain'],
                'parametres': {}
            }
            
            # Charger les échelles d'évaluation
            echelles_path = os.path.join(self.slri_path, "Echelles.txt")
            if os.path.exists(echelles_path):
                with open(echelles_path, 'r', encoding='utf-8') as f:
                    self.slri_data['echelles'] = f.read()
            
            logger.info("Données SLRI chargées avec succès")
            return self.slri_data
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données SLRI: {e}")
            return None
        
        # Structure complète SLRI selon les fichiers de référence
        self.slri_reference_structure = {
            "eau": {
                'Température': '20-30°C',
                'pH': '6-8',
                'Turbidité': '<5 NTU',
                'Conductivité': '<1000 µS/cm',
                'DBO5': '<5 mg/L',
                'DCO': '<25 mg/L',
                'Oxygène dissous': '>5 mg/L',
                'Nitrates': '<50 mg/L',
                'Nitrites': '<0.5 mg/L',
                'Ammoniac': '<0.5 mg/L',
                'Phosphore total': '<0.1 mg/L',
                'Azote total': '<10 mg/L',
                'Plomb (Pb)': '<0.01 mg/L',
                'Cadmium (Cd)': '<0.005 mg/L',
                'Chrome (Cr)': '<0.05 mg/L',
                'Cuivre (Cu)': '<2 mg/L',
                'Zinc (Zn)': '<3 mg/L',
                'Nickel (Ni)': '<0.07 mg/L',
                'Mercure (Hg)': '<0.001 mg/L',
                'Arsenic (As)': '<0.01 mg/L',
                'Hydrocarbures totaux (HCT)': '<0.05 mg/L',
                'Hydrocarbures aromatiques polycycliques (HAP)': '<0.0002 mg/L'
            },
            "sol": {
                'pH': '6-8',
                'Perméabilité': '10-6 à 10-4 m/s',
                'Matière organique': '2-5%',
                'Carbone organique': '1-3%',
                'Plomb (Pb)': '<85 mg/kg',
                'Cadmium (Cd)': '<1.4 mg/kg',
                'Chrome (Cr)': '<100 mg/kg',
                'Cuivre (Cu)': '<36 mg/kg',
                'Zinc (Zn)': '<140 mg/kg',
                'Nickel (Ni)': '<35 mg/kg',
                'Mercure (Hg)': '<0.4 mg/kg',
                'Arsenic (As)': '<12 mg/kg',
                'Azote total': '0.1-0.5%',
                'Phosphore total': '400-1200 mg/kg'
            },
            "air": {
                'Poussières totales': '<150 µg/m³',
                'PM10': '<50 µg/m³',
                'PM2.5': '<25 µg/m³',
                'SO2': '<125 µg/m³',
                'NOx': '<200 µg/m³',
                'CO': '<10 mg/m³',
                'O3 (ozone)': '<120 µg/m³'
            },
            "biologique": {
                'Flore terrestre': 'Présence/Absence',
                'Flore marine': 'Présence/Absence',
                'Mammifères': 'Présence/Absence',
                'Amphibiens': 'Présence/Absence',
                'Reptiles': 'Présence/Absence',
                'Statut de protection': 'Oui/Non',
                'Présence sur site': 'Oui/Non'
            },
            "humain": {
                'Population riveraine': 'Nombre d\'habitants',
                'Distance habitations': 'mètres',
                'Activités économiques': 'Type',
                'Patrimoine culturel': 'Présence/Absence',
                'Accès aux ressources': 'Oui/Non'
            }
        }
    
    def analyze_with_complete_slri_structure(self, coordinates, project_type="industriel", collected_data=None):
        """
        Analyse complète selon la structure SLRI de référence avec tous les paramètres
        """
        try:
            # Utiliser les données collectées ou simuler si non fournies
            if collected_data is None:
                collected_data = self._simulate_enhanced_data_collection(coordinates)
            
            # Créer la structure complète SLRI
            complete_slri_analysis = self._create_complete_slri_structure(collected_data, coordinates, project_type)
            
            logger.info(f"Analyse SLRI complète générée pour les coordonnées {coordinates}")
            return complete_slri_analysis
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse SLRI complète: {e}")
            return None

    def _simulate_enhanced_data_collection(self, coordinates):
        """
        Simulation améliorée de collecte de données environnementales
        """
        lat, lon = coordinates
        
        # Simulation de données environnementales réalistes
        simulated_data = {
            "EAU": {
                'Température': (22, '°C'),
                'pH': (7.2, ''),
                'Turbidité': (3, 'NTU'),
                'Conductivité': (850, 'µS/cm'),
                'DBO5': (4, 'mg/L'),
                'DCO': (20, 'mg/L'),
                'Oxygène dissous': (6, 'mg/L'),
                'Nitrates': (55, 'mg/L'),  # Dépassement léger
                'Nitrites': ('', 'mg/L'),  # Non analysé
                'Ammoniac': ('', 'mg/L'),  # Non analysé
                'Phosphore total': (0.08, 'mg/L'),
                'Azote total': ('', 'mg/L'),  # Non analysé
                'Plomb (Pb)': (0.008, 'mg/L'),
                'Cadmium (Cd)': ('', 'mg/L'),  # Non analysé
                'Chrome (Cr)': ('', 'mg/L'),  # Non analysé
                'Cuivre (Cu)': (1.5, 'mg/L'),
                'Zinc (Zn)': ('', 'mg/L'),  # Non analysé
                'Nickel (Ni)': ('', 'mg/L'),  # Non analysé
                'Mercure (Hg)': ('', 'mg/L'),  # Non analysé
                'Arsenic (As)': ('', 'mg/L'),  # Non analysé
                'Hydrocarbures totaux (HCT)': ('', 'mg/L'),  # Non analysé
                'Hydrocarbures aromatiques polycycliques (HAP)': ('', 'mg/L')  # Non analysé
            },
            "SOL": {
                'pH': (7.5, ''),
                'Perméabilité': ('', 'm/s'),  # Non analysé
                'Matière organique': (3.2, '%'),
                'Carbone organique': ('', '%'),  # Non analysé
                'Plomb (Pb)': (45, 'mg/kg'),
                'Cadmium (Cd)': ('', 'mg/kg'),  # Non analysé
                'Chrome (Cr)': ('', 'mg/kg'),  # Non analysé
                'Cuivre (Cu)': (28, 'mg/kg'),
                'Zinc (Zn)': ('', 'mg/kg'),  # Non analysé
                'Nickel (Ni)': ('', 'mg/kg'),  # Non analysé
                'Mercure (Hg)': ('', 'mg/kg'),  # Non analysé
                'Arsenic (As)': ('', 'mg/kg'),  # Non analysé
                'Azote total': ('', '%'),  # Non analysé
                'Phosphore total': ('', 'mg/kg')  # Non analysé
            },
            "AIR": {
                'Poussières totales': ('', 'µg/m³'),  # Non analysé
                'PM10': (65, 'µg/m³'),  # Dépassement important
                'PM2.5': (30, 'µg/m³'),  # Dépassement léger
                'SO2': (95, 'µg/m³'),
                'NOx': ('', 'µg/m³'),  # Non analysé
                'CO': (8, 'mg/m³'),
                'O3 (ozone)': ('', 'µg/m³')  # Non analysé
            },
            "BIOLOGIQUE": {
                'Flore terrestre': ('Présente', ''),
                'Flore marine': ('', ''),  # Non évaluée
                'Mammifères': ('Présents', ''),
                'Amphibiens': ('', ''),  # Non évalués
                'Reptiles': ('', ''),  # Non évalués
                'Statut de protection': ('', ''),  # Non évalué
                'Présence sur site': ('Oui', '')
            },
            "HUMAIN": {
                'Population riveraine': ('', 'habitants'),  # Non évaluée
                'Distance habitations': (500, 'm'),
                'Activités économiques': ('Agriculture', ''),
                'Patrimoine culturel': ('', ''),  # Non évalué
                'Accès aux ressources': ('', '')  # Non évalué
            }
        }
        
        return simulated_data

    def _create_complete_slri_structure(self, collected_data, coordinates, project_type):
        """
        Crée la structure SLRI complète selon les tableaux de référence
        """
        # Créer la structure complète pour la phase PRE CONSTRUCTION
        phase_parametres = {}
        major_risks = []
        
        for milieu, parametres in self.slri_reference_structure.items():
            phase_parametres[milieu] = {}
            
            for param_name, seuil in parametres.items():
                # Récupérer la valeur mesurée si disponible
                valeur_mesuree = ""
                score = ""
                amplitude = "NON ANALYSÉ"
                
                if milieu.upper() in collected_data and param_name in collected_data[milieu.upper()]:
                    valeur_data = collected_data[milieu.upper()][param_name]
                    if isinstance(valeur_data, tuple):
                        if valeur_data[0] != "":
                            valeur_mesuree = f"{valeur_data[0]}{' ' + valeur_data[1] if valeur_data[1] else ''}".strip()
                        else:
                            valeur_mesuree = ""
                    else:
                        valeur_mesuree = str(valeur_data) if valeur_data != "" else ""
                    
                    # Calculer le score si la valeur est numérique
                    if valeur_data[0] != "" and isinstance(valeur_data[0], (int, float)):
                        score = self._calculate_parameter_score(valeur_data[0], seuil)
                        if score == 0:
                            amplitude = "CONFORME"
                        elif score == 1:
                            amplitude = "MOYEN"
                        else:
                            amplitude = "FORT"
                            
                        # Ajouter aux risques majeurs si nécessaire
                        if score >= 1:
                            major_risks.append({
                                'parameter': param_name,
                                'milieu': milieu.upper(),
                                'amplitude': amplitude,
                                'valeur': valeur_mesuree,
                                'seuil': seuil
                            })
                    elif valeur_data[0] != "" and isinstance(valeur_data[0], str):
                        # Pour les paramètres qualitatifs
                        if milieu == "biologique":
                            if valeur_data[0] in ["Présente", "Présents", "Oui"]:
                                amplitude = "IDENTIFIÉE" if "Présent" in valeur_data[0] else "CONFIRMÉE"
                            else:
                                amplitude = "NON ÉVALUÉE"
                        elif milieu == "humain":
                            if valeur_data[0] != "":
                                amplitude = "MESURÉE" if param_name == "Distance habitations" else "IDENTIFIÉES"
                            else:
                                amplitude = "NON ÉVALUÉE"
                
                phase_parametres[milieu][param_name] = {
                    'valeur': valeur_mesuree,
                    'seuil': seuil,
                    'score': score,
                    'amplitude': amplitude
                }
        
        # Calculer le score global de la phase
        valid_scores = [param['score'] for milieu_params in phase_parametres.values() 
                       for param in milieu_params.values() if param['score'] != "" and isinstance(param['score'], (int, float))]
        phase_score = np.mean(valid_scores) if valid_scores else 0
        
        # Classification de la phase
        if phase_score <= 0.5:
            phase_classification = "FAIBLE"
        elif phase_score <= 1.0:
            phase_classification = "MOYEN"
        else:
            phase_classification = "FORT"
        
        # Générer des recommandations spécifiques
        recommendations = self._generate_specific_recommendations(major_risks, phase_parametres)
        
        # Structure finale compatible avec l'interface web
        complete_analysis = {
            'coordinates': {'lat': coordinates[0], 'lon': coordinates[1]},
            'projectType': project_type,
            'phases': {
                'PRE CONSTRUCTION': {
                    'score': phase_score,
                    'classification': phase_classification,
                    'parametres': phase_parametres
                }
            },
            'globalScore': phase_score,
            'majorRisks': major_risks,
            'recommendations': recommendations
        }
        
        return complete_analysis

    def _generate_specific_recommendations(self, major_risks, phase_parametres):
        """
        Génère des recommandations spécifiques basées sur l'analyse SLRI
        """
        recommendations = []
        
        # Analyser les risques par milieu
        milieux_impactes = {}
        for risk in major_risks:
            milieu = risk['milieu']
            if milieu not in milieux_impactes:
                milieux_impactes[milieu] = []
            milieux_impactes[milieu].append(risk)
        
        # Recommandations spécifiques par milieu
        if 'EAU' in milieux_impactes:
            recommendations.append('Mettre en place un système de monitoring continu pour PM10 et PM2.5')
            recommendations.append('Traitement des eaux pour réduire les nitrates')
        
        if 'AIR' in milieux_impactes:
            recommendations.append('Mesures anti-poussières pendant la construction')
            recommendations.append('Surveillance continue de la qualité de l\'air')
        
        if 'SOL' in milieux_impactes:
            recommendations.append('Plan de gestion et protection des sols')
            recommendations.append('Analyses complémentaires des métaux lourds dans les sols')
        
        # Recommandations pour les paramètres manquants
        missing_params = []
        for milieu_params in phase_parametres.values():
            for param_name, param_data in milieu_params.items():
                if param_data['amplitude'] == 'NON ANALYSÉ':
                    missing_params.append(param_name)
        
        if missing_params:
            recommendations.append('Compléter les analyses manquantes pour les métaux lourds')
            recommendations.append('Évaluation biologique approfondie des espèces protégées')
        
        # Recommandations générales
        recommendations.append('Élaborer un plan de gestion environnementale détaillé selon SLRI')
        
        return recommendations

    def integrate_with_main_app(self, coordinates, project_type="industriel", external_data=None):
        """
        Intégration principale avec l'application
        """
        try:
            # Analyser avec la structure SLRI complète
            slri_analysis = self.analyze_with_complete_slri_structure(
                coordinates, project_type, external_data
            )
            
            if slri_analysis:
                logger.info("Analyse SLRI complète intégrée avec succès")
                return slri_analysis
            else:
                logger.error("Échec de l'analyse SLRI complète")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de l'intégration SLRI: {e}")
            return None


def create_slri_complete_analyzer():
    """
    Factory function pour créer un analyseur SLRI complet
    """
    try:
        analyzer = SLRICompleteAnalyzer()
        logger.info("Analyseur SLRI complet créé avec succès")
        return analyzer
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'analyseur SLRI: {e}")
        return None
