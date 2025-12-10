"""
Module SLRI autonome pour l'analyse des risques environnementaux
Implémente la structure SLRI exacte selon les tableaux de référence
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from water_parameters_collector import create_water_parameters_collector

logger = logging.getLogger(__name__)

class SLRICompleteAnalyzer:
    """
    Analyseur SLRI complet avec structure exacte des tableaux de référence
    """
    
    def __init__(self, slri_path: str = None):
        self.slri_path = slri_path or os.path.join(os.path.dirname(__file__), "SLRI")
        self.water_collector = create_water_parameters_collector()
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
    
    def analyze_complete_slri(self, coordinates, project_type="industriel"):
        """
        Analyse SLRI complète selon la structure de référence
        
        Args:
            coordinates: Tuple (latitude, longitude)
            project_type: Type de projet
            
        Returns:
            dict: Résultats de l'analyse SLRI
        """
        try:
            # Simuler la collecte de données environnementales
            environmental_data = self._simulate_environmental_data(coordinates)
            
            # Structure SLRI de référence
            slri_structure = {
                "eau": {
                    'Température': '<30°C',
                    'pH': '6-8',
                    'Turbidité': '<5 NTU',
                    'Conductivité': '<1000 µS/cm',
                    'DBO5': '<5 mg/L',
                    'DCO': '<25 mg/L',
                    'Oxygène dissous': '>5 mg/L',
                    'Nitrates': '<50 mg/L',
                    'Nitrites': '<0.5 mg/L',
                    'Ammoniac': '<0.5 mg/L',
                    'Phosphates': '<2 mg/L'
                },
                "sol": {
                    'pH': '6-8',
                    'Matière organique': '>2%',
                    'Azote total': '0.1-0.3%',
                    'Phosphore': '20-50 mg/kg',
                    'Potassium': '100-300 mg/kg',
                    'Plomb': '<100 mg/kg',
                    'Cadmium': '<3 mg/kg',
                    'Chrome': '<150 mg/kg',
                    'Cuivre': '<100 mg/kg',
                    'Zinc': '<300 mg/kg'
                },
                "air": {
                    'PM2.5': '<25 µg/m³',
                    'PM10': '<50 µg/m³',
                    'NO2': '<40 µg/m³',
                    'SO2': '<20 µg/m³',
                    'O3': '<120 µg/m³',
                    'CO': '<10 mg/m³',
                    'Benzène': '<5 µg/m³',
                    'Formaldéhyde': '<30 µg/m³'
                },
                "biologique": {
                    'Diversité floristique': '>50 espèces',
                    'Diversité faunistique': '>30 espèces',
                    'Espèces endémiques': '>5',
                    'Biomasse': '>100 kg/ha',
                    'Couverture végétale': '>70%'
                },
                "humain": {
                    'Densité population': '<500 hab/km²',
                    'Distance habitations': '>500m',
                    'Activités économiques': 'Compatible',
                    'Patrimoine culturel': 'Préservé',
                    'Accès aux services': 'Maintenu'
                }
            }
            
            # Analyser chaque phase
            phases_results = {}
            for phase in ['PRE CONSTRUCTION', 'CONSTRUCTION', 'exploitation', 'démantalement']:
                phases_results[phase] = self._analyze_phase(phase, slri_structure, environmental_data)
            
            # Calculer les risques majeurs et recommandations
            major_risks = self._identify_major_risks(phases_results)
            recommendations = self._generate_recommendations(major_risks, project_type)
            
            results = {
                'coordinates': coordinates,
                'project_type': project_type,
                'phases': phases_results,
                'risques_majeurs': major_risks,
                'recommandations': recommendations,
                'date_analyse': datetime.now().isoformat()
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse SLRI: {e}")
            return None
    
    def simulate_environmental_data(self, coordinates, project_type="industriel"):
        """
        Simule des données environnementales réalistes basées sur les coordonnées
        Intègre les paramètres d'eau détaillés du collecteur
        
        Args:
            coordinates: Tuple (latitude, longitude)
            project_type: Type de projet
            
        Returns:
            dict: Données environnementales simulées avec paramètres d'eau détaillés
        """
        lat, lon = coordinates
        np.random.seed(int((lat + lon) * 1000) % 2147483647)
        
        # Collecte des paramètres d'eau détaillés
        detailed_water_data = {}
        if self.water_collector:
            water_params = self.water_collector.collect_detailed_water_parameters(coordinates)
            if water_params:
                # Convertir les données détaillées en format compatible SLRI
                for category, parameters in water_params.items():
                    if category != 'contexte' and isinstance(parameters, dict):
                        for param, data in parameters.items():
                            detailed_water_data[param] = data['valeur_mesuree']
        
        # Données de base par milieu avec paramètres d'eau détaillés
        data = {
            'eau': detailed_water_data if detailed_water_data else {
                'Température': np.random.normal(22, 4),
                'pH': np.random.normal(7.2, 0.8),
                'Conductivité': np.random.normal(800, 300),
                'Turbidité': np.random.exponential(3),
                'Oxygène dissous': np.random.normal(6.5, 1.5),
                'DBO5': np.random.exponential(4),
                'DCO': np.random.exponential(20),
                'Nitrates': np.random.exponential(30),
                'Phosphates': np.random.exponential(1.5),
                'Coliformes totaux': np.random.exponential(100),
                'Métaux lourds': np.random.exponential(0.01)
            },
            "sol": {
                'pH': np.random.normal(7, 0.5),
                'Matière organique': np.random.normal(3, 1),
                'Azote total': np.random.normal(0.2, 0.05),
                'Phosphore': np.random.normal(35, 10),
                'Potassium': np.random.normal(200, 50),
                'Plomb': np.random.exponential(50),
                'Cadmium': np.random.exponential(1.5),
                'Chrome': np.random.exponential(75),
                'Cuivre': np.random.exponential(50),
                'Zinc': np.random.exponential(150)
            },
            "air": {
                'PM2.5': np.random.exponential(15),
                'PM10': np.random.exponential(30),
                'NO2': np.random.exponential(25),
                'SO2': np.random.exponential(10),
                'O3': np.random.exponential(80),
                'CO': np.random.exponential(5),
                'Benzène': np.random.exponential(3),
                'Formaldéhyde': np.random.exponential(20)
            },
            "biologique": {
                'Diversité floristique': np.random.poisson(45),
                'Diversité faunistique': np.random.poisson(25),
                'Espèces endémiques': np.random.poisson(3),
                'Biomasse': np.random.normal(80, 20),
                'Couverture végétale': np.random.normal(65, 15)
            },
            "humain": {
                'Densité population': np.random.exponential(300),
                'Distance habitations': np.random.exponential(800),
                'Activités économiques': np.random.choice(['Compatible', 'Partiellement compatible', 'Incompatible']),
                'Patrimoine culturel': np.random.choice(['Préservé', 'Menacé', 'Dégradé']),
                'Accès aux services': np.random.choice(['Maintenu', 'Réduit', 'Interrompu'])
            }
        }
    
    def _analyze_phase(self, phase, slri_structure, environmental_data):
        """Analyse une phase spécifique du projet"""
        phase_results = {
            'parametres': {},
            'score_global': 0,
            'classification': 'Faible'
        }
        
        total_score = 0
        param_count = 0
        
        for milieu, parametres in slri_structure.items():
            phase_results['parametres'][milieu] = {}
            
            for param, reference in parametres.items():
                if param in environmental_data.get(milieu, {}):
                    valeur_mesuree = environmental_data[milieu][param]
                    score = self._calculate_parameter_score(valeur_mesuree, reference)
                    
                    phase_results['parametres'][milieu][param] = {
                        'valeur_mesuree': valeur_mesuree,
                        'valeur_reference': reference,
                        'score': score,
                        'conforme': score == 0
                    }
                    
                    if isinstance(score, (int, float)):
                        total_score += score
                        param_count += 1
                else:
                    # Paramètre manquant
                    phase_results['parametres'][milieu][param] = {
                        'valeur_mesuree': 'Non analysé',
                        'valeur_reference': reference,
                        'score': '',
                        'conforme': None
                    }
        
        # Calculer le score global
        if param_count > 0:
            phase_results['score_global'] = total_score / param_count
            
            # Classification selon SLRI
            if phase_results['score_global'] <= 0.5:
                phase_results['classification'] = 'Faible'
            elif phase_results['score_global'] <= 1.0:
                phase_results['classification'] = 'Moyen'
            elif phase_results['score_global'] <= 1.5:
                phase_results['classification'] = 'Fort'
            else:
                phase_results['classification'] = 'Très grave'
        
        return phase_results
    
    def _calculate_parameter_score(self, valeur, reference):
        """Calcule le score d'un paramètre selon sa référence"""
        try:
            if isinstance(valeur, str):
                if valeur in ['Compatible', 'Préservé', 'Maintenu']:
                    return 0
                elif valeur in ['Partiellement compatible', 'Menacé', 'Réduit']:
                    return 1
                else:
                    return 2
            
            val = float(valeur)
            
            if '<' in str(reference):
                seuil = float(str(reference).replace('<', '').replace('µg/m³', '').replace('mg/L', '').replace('mg/kg', '').replace('mg/m³', '').replace('NTU', '').replace('µS/cm', '').replace('°C', '').strip())
                return 0 if val <= seuil else 2
            elif '>' in str(reference):
                seuil = float(str(reference).replace('>', '').replace('%', '').replace('espèces', '').replace('kg/ha', '').replace('hab/km²', '').replace('m', '').strip())
                return 0 if val >= seuil else 2
            elif '-' in str(reference):
                parts = str(reference).replace('°C', '').replace('%', '').split('-')
                if len(parts) == 2:
                    min_val = float(parts[0])
                    max_val = float(parts[1])
                    return 0 if min_val <= val <= max_val else 2
            
            return 0
            
        except (ValueError, TypeError):
            return ""
    
    def _identify_major_risks(self, phases_results):
        """Identifie les risques majeurs à travers toutes les phases"""
        major_risks = []
        
        for phase, results in phases_results.items():
            if results['classification'] in ['Fort', 'Très grave']:
                major_risks.append(f"Risque {results['classification'].lower()} en phase {phase}")
            
            # Identifier les paramètres critiques
            for milieu, parametres in results['parametres'].items():
                for param, data in parametres.items():
                    if isinstance(data.get('score'), (int, float)) and data['score'] >= 2:
                        major_risks.append(f"Dépassement critique: {param} ({milieu}) en phase {phase}")
        
        return major_risks[:10]  # Limiter à 10 risques majeurs
    
    def _generate_recommendations(self, major_risks, project_type):
        """Génère des recommandations basées sur les risques identifiés"""
        recommendations = []
        
        if not major_risks:
            recommendations.append("Projet conforme aux standards SLRI")
            recommendations.append("Maintenir la surveillance environnementale")
        else:
            recommendations.append("Mise en place de mesures de mitigation prioritaires")
            recommendations.append("Surveillance renforcée des paramètres critiques")
            
            if any('eau' in risk for risk in major_risks):
                recommendations.append("Traitement des eaux usées avant rejet")
                recommendations.append("Système de collecte et traitement des eaux pluviales")
            
            if any('sol' in risk for risk in major_risks):
                recommendations.append("Dépollution des sols contaminés")
                recommendations.append("Mise en place de barrières de confinement")
            
            if any('air' in risk for risk in major_risks):
                recommendations.append("Installation de systèmes de filtration d'air")
                recommendations.append("Surveillance continue de la qualité de l'air")
            
            if any('biologique' in risk for risk in major_risks):
                recommendations.append("Plan de compensation écologique")
                recommendations.append("Création de corridors biologiques")
            
            if any('humain' in risk for risk in major_risks):
                recommendations.append("Consultation et information des populations")
                recommendations.append("Mesures de protection du patrimoine culturel")
        
        return recommendations[:8]  # Limiter à 8 recommandations
    
    def export_slri_to_excel(self, coordinates, project_type, output_path):
        """Exporte l'analyse SLRI vers un fichier Excel"""
        try:
            results = self.analyze_complete_slri(coordinates, project_type)
            if not results:
                return False
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Feuille de synthèse
                synthesis_data = {
                    'Coordonnées': [f"{coordinates[0]:.4f}, {coordinates[1]:.4f}"],
                    'Type de projet': [project_type],
                    'Date d\'analyse': [results['date_analyse']],
                    'Nombre de risques majeurs': [len(results['risques_majeurs'])]
                }
                pd.DataFrame(synthesis_data).to_excel(writer, sheet_name='Synthèse', index=False)
                
                # Feuille par phase
                for phase, phase_data in results['phases'].items():
                    phase_df_data = []
                    for milieu, parametres in phase_data['parametres'].items():
                        for param, data in parametres.items():
                            phase_df_data.append({
                                'Milieu': milieu,
                                'Paramètre': param,
                                'Valeur mesurée': data['valeur_mesuree'],
                                'Valeur de référence': data['valeur_reference'],
                                'Score': data['score'],
                                'Conforme': data['conforme']
                            })
                    
                    if phase_df_data:
                        pd.DataFrame(phase_df_data).to_excel(writer, sheet_name=phase[:31], index=False)
                
                # Feuille des risques et recommandations
                risks_data = {
                    'Risques majeurs': results['risques_majeurs'] + [''] * (10 - len(results['risques_majeurs'])),
                    'Recommandations': results['recommandations'] + [''] * (10 - len(results['recommandations']))
                }
                pd.DataFrame(risks_data).to_excel(writer, sheet_name='Risques_Recommandations', index=False)
            
            logger.info(f"Rapport SLRI exporté vers: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export Excel: {e}")
            return False

def create_slri_complete_analyzer(slri_path: str = None):
    """
    Fonction utilitaire pour créer un analyseur SLRI complet
    
    Args:
        slri_path: Chemin vers le dossier SLRI (optionnel)
        
    Returns:
        SLRICompleteAnalyzer: Instance de l'analyseur
    """
    try:
        analyzer = SLRICompleteAnalyzer(slri_path)
        logger.info("Analyseur SLRI complet créé avec succès")
        return analyzer
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'analyseur SLRI: {e}")
        return None

if __name__ == "__main__":
    # Test de l'analyseur
    analyzer = create_slri_complete_analyzer()
    if analyzer:
        # Test avec des coordonnées du Maroc
        coordinates = (33.5731, -7.5898)  # Casablanca
        results = analyzer.analyze_complete_slri(coordinates, "industriel")
        
        if results:
            print("=== ANALYSE SLRI COMPLÈTE ===")
            print(f"Coordonnées: {results['coordinates']}")
            print(f"Type de projet: {results['project_type']}")
            print(f"Nombre de risques majeurs: {len(results['risques_majeurs'])}")
            
            print("\nRisques majeurs:")
            for risk in results['risques_majeurs'][:5]:
                print(f"- {risk}")
            
            print("\nRecommandations:")
            for rec in results['recommandations'][:5]:
                print(f"- {rec}")
        else:
            print("Erreur lors de l'analyse SLRI")
    else:
        print("Erreur lors de la création de l'analyseur SLRI")
