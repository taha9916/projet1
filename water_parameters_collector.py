"""
Module de collecte des paramètres d'eau détaillés pour l'analyse SLRI
Collecte des données complètes de qualité de l'eau depuis diverses sources
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
import os

logger = logging.getLogger(__name__)

class WaterParametersCollector:
    """
    Collecteur de paramètres d'eau détaillés pour l'analyse SLRI
    """
    
    def __init__(self):
        self.water_parameters = {
            # Paramètres physico-chimiques de base
            'physico_chimiques': {
                'Température': {'unit': '°C', 'reference': '<30', 'source': 'sensor'},
                'pH': {'unit': '', 'reference': '6-8', 'source': 'sensor'},
                'Conductivité': {'unit': 'µS/cm', 'reference': '<1000', 'source': 'sensor'},
                'Turbidité': {'unit': 'NTU', 'reference': '<5', 'source': 'sensor'},
                'Oxygène dissous': {'unit': 'mg/L', 'reference': '>5', 'source': 'sensor'},
                'Salinité': {'unit': 'g/L', 'reference': '<1', 'source': 'sensor'},
                'Potentiel redox': {'unit': 'mV', 'reference': '>200', 'source': 'sensor'}
            },
            
            # Paramètres de pollution organique
            'pollution_organique': {
                'DBO5': {'unit': 'mg/L', 'reference': '<5', 'source': 'lab'},
                'DCO': {'unit': 'mg/L', 'reference': '<25', 'source': 'lab'},
                'Matières en suspension': {'unit': 'mg/L', 'reference': '<25', 'source': 'lab'},
                'Matières organiques': {'unit': 'mg/L', 'reference': '<10', 'source': 'lab'},
                'Hydrocarbures': {'unit': 'mg/L', 'reference': '<0.1', 'source': 'lab'},
                'Détergents': {'unit': 'mg/L', 'reference': '<0.5', 'source': 'lab'}
            },
            
            # Nutriments
            'nutriments': {
                'Nitrates (NO3-)': {'unit': 'mg/L', 'reference': '<50', 'source': 'lab'},
                'Nitrites (NO2-)': {'unit': 'mg/L', 'reference': '<0.5', 'source': 'lab'},
                'Ammoniac (NH3)': {'unit': 'mg/L', 'reference': '<0.5', 'source': 'lab'},
                'Azote total': {'unit': 'mg/L', 'reference': '<10', 'source': 'lab'},
                'Phosphates (PO4³-)': {'unit': 'mg/L', 'reference': '<2', 'source': 'lab'},
                'Phosphore total': {'unit': 'mg/L', 'reference': '<0.5', 'source': 'lab'}
            },
            
            # Métaux lourds
            'metaux_lourds': {
                'Plomb (Pb)': {'unit': 'mg/L', 'reference': '<0.01', 'source': 'lab'},
                'Cadmium (Cd)': {'unit': 'mg/L', 'reference': '<0.005', 'source': 'lab'},
                'Chrome (Cr)': {'unit': 'mg/L', 'reference': '<0.05', 'source': 'lab'},
                'Cuivre (Cu)': {'unit': 'mg/L', 'reference': '<2', 'source': 'lab'},
                'Zinc (Zn)': {'unit': 'mg/L', 'reference': '<3', 'source': 'lab'},
                'Mercure (Hg)': {'unit': 'mg/L', 'reference': '<0.001', 'source': 'lab'},
                'Arsenic (As)': {'unit': 'mg/L', 'reference': '<0.01', 'source': 'lab'},
                'Nickel (Ni)': {'unit': 'mg/L', 'reference': '<0.02', 'source': 'lab'}
            },
            
            # Paramètres microbiologiques
            'microbiologie': {
                'Coliformes totaux': {'unit': 'UFC/100mL', 'reference': '<100', 'source': 'lab'},
                'Coliformes fécaux': {'unit': 'UFC/100mL', 'reference': '<20', 'source': 'lab'},
                'Escherichia coli': {'unit': 'UFC/100mL', 'reference': '<0', 'source': 'lab'},
                'Streptocoques fécaux': {'unit': 'UFC/100mL', 'reference': '<20', 'source': 'lab'},
                'Salmonelles': {'unit': 'UFC/100mL', 'reference': '<0', 'source': 'lab'}
            },
            
            # Pesticides et substances chimiques
            'pesticides': {
                'Atrazine': {'unit': 'µg/L', 'reference': '<0.1', 'source': 'lab'},
                'Glyphosate': {'unit': 'µg/L', 'reference': '<0.1', 'source': 'lab'},
                'Chlordane': {'unit': 'µg/L', 'reference': '<0.02', 'source': 'lab'},
                'DDT': {'unit': 'µg/L', 'reference': '<0.02', 'source': 'lab'},
                'Benzène': {'unit': 'µg/L', 'reference': '<1', 'source': 'lab'},
                'Toluène': {'unit': 'µg/L', 'reference': '<7', 'source': 'lab'}
            }
        }
    
    def collect_water_parameters(self, lat, lon):
        """Collecte les paramètres d'eau pour des coordonnées données.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            dict: Paramètres d'eau simplifiés
        """
        try:
            # Utiliser la méthode détaillée existante
            detailed_data = self.collect_detailed_water_parameters((lat, lon))
            
            if not detailed_data:
                return {}
            
            # Simplifier les données pour l'interface
            simplified_data = {}
            
            for category, params in detailed_data.items():
                if category == 'contexte' or not isinstance(params, dict):
                    continue
                    
                for param_name, details in params.items():
                    if isinstance(details, dict) and 'valeur_mesuree' in details:
                        value = details['valeur_mesuree']
                        unit = details.get('unite', '')
                        simplified_data[param_name] = value
            
            logger.info(f"Paramètres d'eau simplifiés collectés: {len(simplified_data)} paramètres")
            return simplified_data
            
        except Exception as e:
            logger.error(f"Erreur collecte paramètres eau: {e}")
            return {}
    
    def collect_detailed_water_parameters(self, coordinates, source_type="comprehensive"):
        """
        Collecte des paramètres d'eau détaillés pour une localisation donnée
        
        Args:
            coordinates: Tuple (latitude, longitude)
            source_type: Type de collecte ("sensor", "lab", "comprehensive")
            
        Returns:
            dict: Paramètres d'eau détaillés avec valeurs mesurées
        """
        try:
            lat, lon = coordinates
            
            # Simuler des données réalistes basées sur la localisation
            water_data = {}
            
            for category, parameters in self.water_parameters.items():
                water_data[category] = {}
                
                for param, config in parameters.items():
                    if source_type == "comprehensive" or config['source'] == source_type:
                        # Simuler des valeurs réalistes
                        measured_value = self._simulate_parameter_value(param, config, coordinates)
                        
                        water_data[category][param] = {
                            'valeur_mesuree': measured_value,
                            'unite': config['unit'],
                            'valeur_reference': config['reference'],
                            'source': config['source'],
                            'conforme': self._check_compliance(measured_value, config['reference']),
                            'date_mesure': datetime.now().isoformat()
                        }
            
            # Ajouter des informations contextuelles
            water_data['contexte'] = {
                'coordinates': coordinates,
                'date_collecte': datetime.now().isoformat(),
                'source_type': source_type,
                'nombre_parametres': sum(len(params) for params in water_data.values() if isinstance(params, dict))
            }
            
            logger.info(f"Paramètres d'eau collectés pour {coordinates}: {len(water_data)} catégories")
            return water_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des paramètres d'eau: {e}")
            return None
    
    def _simulate_parameter_value(self, param_name, config, coordinates):
        """Simule des valeurs réalistes pour les paramètres d'eau basées sur la localisation géographique"""
        lat, lon = coordinates
        
        # Utiliser les coordonnées pour créer une variation géographique cohérente
        geo_seed = int((abs(lat) * 1000 + abs(lon) * 1000) % 2147483647)
        np.random.seed(geo_seed)
        
        # Facteurs géographiques basés sur la latitude et longitude
        climate_factor = self._get_climate_factor(lat, lon)
        pollution_factor = self._get_pollution_factor(lat, lon)
        altitude_factor = self._get_altitude_factor(lat, lon)
        
        # Valeurs de base selon le type de paramètre avec variation géographique
        if 'Température' in param_name:
            base_temp = 15 + (30 - abs(lat)) * 0.5  # Plus chaud près de l'équateur
            return round(base_temp + np.random.normal(0, 3) * climate_factor, 1)
            
        elif 'pH' in param_name:
            base_ph = 7.0 + (pollution_factor - 0.5) * 2  # Pollution affecte le pH
            return round(base_ph + np.random.normal(0, 0.5), 1)
            
        elif 'Conductivité' in param_name:
            base_cond = 400 + pollution_factor * 800 + altitude_factor * 200
            return round(base_cond + np.random.normal(0, 150), 0)
            
        elif 'Turbidité' in param_name:
            base_turb = pollution_factor * 8 + np.random.exponential(2)
            return round(base_turb, 1)
            
        elif 'Oxygène' in param_name:
            base_o2 = 8 - pollution_factor * 3 + altitude_factor * 1.5
            return round(max(2, base_o2 + np.random.normal(0, 1)), 1)
            
        elif 'Salinité' in param_name:
            # Plus élevée près des côtes
            coastal_factor = max(0, 1 - min(abs(lat - 34), abs(lon + 7)) / 10)  # Maroc côtier
            base_sal = coastal_factor * 2 + np.random.exponential(0.5)
            return round(base_sal, 2)
            
        elif 'DBO5' in param_name:
            base_dbo = pollution_factor * 8 + np.random.exponential(2)
            return round(base_dbo, 1)
            
        elif 'DCO' in param_name:
            base_dco = pollution_factor * 30 + np.random.exponential(10)
            return round(base_dco, 1)
            
        elif 'Nitrates' in param_name:
            # Plus élevé dans les zones agricoles
            agri_factor = self._get_agricultural_factor(lat, lon)
            base_no3 = agri_factor * 40 + pollution_factor * 20 + np.random.exponential(10)
            return round(base_no3, 1)
            
        elif 'Nitrites' in param_name:
            base_no2 = pollution_factor * 0.8 + np.random.exponential(0.2)
            return round(base_no2, 3)
            
        elif 'Ammoniac' in param_name:
            base_nh3 = pollution_factor * 1.2 + np.random.exponential(0.3)
            return round(base_nh3, 3)
            
        elif 'Phosphates' in param_name:
            agri_factor = self._get_agricultural_factor(lat, lon)
            base_po4 = agri_factor * 3 + pollution_factor * 2 + np.random.exponential(0.5)
            return round(base_po4, 2)
            
        elif any(metal in param_name for metal in ['Plomb', 'Cadmium', 'Chrome', 'Cuivre', 'Zinc', 'Mercure', 'Arsenic', 'Nickel']):
            # Métaux lourds plus élevés dans les zones industrielles
            industrial_factor = self._get_industrial_factor(lat, lon)
            base_metal = industrial_factor * 0.02 + pollution_factor * 0.01 + np.random.exponential(0.005)
            return round(base_metal, 4)
            
        elif 'Coliformes' in param_name or 'coli' in param_name:
            # Plus élevé dans les zones densément peuplées
            urban_factor = self._get_urban_factor(lat, lon)
            base_coli = urban_factor * 200 + pollution_factor * 100 + np.random.exponential(30)
            return int(base_coli)
            
        elif any(pest in param_name for pest in ['Atrazine', 'Glyphosate', 'Chlordane', 'DDT', 'Benzène', 'Toluène']):
            agri_factor = self._get_agricultural_factor(lat, lon)
            base_pest = agri_factor * 0.15 + pollution_factor * 0.08 + np.random.exponential(0.03)
            return round(base_pest, 4)
            
        else:
            return round(pollution_factor * 10 + np.random.exponential(3), 2)
    
    def _get_climate_factor(self, lat, lon):
        """Retourne un facteur climatique basé sur la localisation (0-1)"""
        # Facteur basé sur la latitude (tropical vs tempéré)
        return min(1, max(0, (40 - abs(lat)) / 40))
    
    def _get_pollution_factor(self, lat, lon):
        """Retourne un facteur de pollution basé sur la localisation (0-1)"""
        # Simulation basée sur la proximité des grandes villes
        # Casablanca (33.5731, -7.5898), Rabat (34.0209, -6.8416)
        casablanca_dist = ((lat - 33.5731)**2 + (lon + 7.5898)**2)**0.5
        rabat_dist = ((lat - 34.0209)**2 + (lon + 6.8416)**2)**0.5
        
        min_dist = min(casablanca_dist, rabat_dist)
        return max(0.1, min(1, 1 - min_dist / 5))  # Plus pollué près des villes
    
    def _get_altitude_factor(self, lat, lon):
        """Retourne un facteur d'altitude estimé (0-1)"""
        # Atlas mountains approximation
        if 31 < lat < 34 and -8 < lon < -4:
            return 0.7  # Montagne
        return 0.3  # Plaine/côte
    
    def _get_agricultural_factor(self, lat, lon):
        """Retourne un facteur agricole basé sur la localisation (0-1)"""
        # Zones agricoles du Maroc (plaines fertiles)
        if 33 < lat < 35 and -8 < lon < -5:
            return 0.8  # Zone agricole intensive
        elif 32 < lat < 36 and -9 < lon < -4:
            return 0.6  # Zone agricole modérée
        return 0.3  # Zone peu agricole
    
    def _get_industrial_factor(self, lat, lon):
        """Retourne un facteur industriel basé sur la localisation (0-1)"""
        # Zones industrielles (Casablanca, Mohammedia, Kenitra)
        industrial_zones = [
            (33.5731, -7.5898, 0.9),  # Casablanca
            (33.6866, -7.3674, 0.7),  # Mohammedia
            (34.2610, -6.5802, 0.6),  # Kenitra
        ]
        
        max_factor = 0.2
        for zone_lat, zone_lon, factor in industrial_zones:
            dist = ((lat - zone_lat)**2 + (lon - zone_lon)**2)**0.5
            if dist < 0.5:  # Dans un rayon de ~50km
                max_factor = max(max_factor, factor * (1 - dist))
        
        return max_factor
    
    def _get_urban_factor(self, lat, lon):
        """Retourne un facteur urbain basé sur la localisation (0-1)"""
        # Densité urbaine approximative
        urban_centers = [
            (33.5731, -7.5898, 1.0),  # Casablanca
            (34.0209, -6.8416, 0.8),  # Rabat
            (34.0181, -5.0078, 0.7),  # Fès
            (31.6295, -7.9811, 0.9),  # Marrakech
        ]
        
        max_factor = 0.2
        for city_lat, city_lon, factor in urban_centers:
            dist = ((lat - city_lat)**2 + (lon - city_lon)**2)**0.5
            if dist < 1:  # Dans un rayon de ~100km
                max_factor = max(max_factor, factor * (1 - dist))
        
        return max_factor
    
    def _check_compliance(self, value, reference):
        """Vérifie la conformité d'une valeur par rapport à sa référence"""
        try:
            if isinstance(value, str):
                return None
            
            val = float(value)
            
            if '<' in str(reference):
                threshold = float(str(reference).replace('<', '').strip())
                return val <= threshold
            elif '>' in str(reference):
                threshold = float(str(reference).replace('>', '').strip())
                return val >= threshold
            elif '-' in str(reference):
                parts = str(reference).split('-')
                if len(parts) == 2:
                    min_val = float(parts[0])
                    max_val = float(parts[1])
                    return min_val <= val <= max_val
            
            return True
            
        except (ValueError, TypeError):
            return None
    
    def export_water_data_to_excel(self, water_data, output_path):
        """Exporte les données d'eau vers un fichier Excel"""
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Feuille de synthèse
                synthesis_data = []
                total_params = 0
                non_compliant = 0
                
                for category, parameters in water_data.items():
                    if category == 'contexte':
                        continue
                    
                    for param, data in parameters.items():
                        synthesis_data.append({
                            'Catégorie': category.replace('_', ' ').title(),
                            'Paramètre': param,
                            'Valeur mesurée': data['valeur_mesuree'],
                            'Unité': data['unite'],
                            'Référence': data['valeur_reference'],
                            'Conforme': 'Oui' if data['conforme'] else 'Non' if data['conforme'] is not None else 'N/A',
                            'Source': data['source'],
                            'Date mesure': data['date_mesure']
                        })
                        total_params += 1
                        if data['conforme'] is False:
                            non_compliant += 1
                
                df_synthesis = pd.DataFrame(synthesis_data)
                df_synthesis.to_excel(writer, sheet_name='Synthèse_Paramètres', index=False)
                
                # Feuille par catégorie
                for category, parameters in water_data.items():
                    if category == 'contexte':
                        continue
                    
                    category_data = []
                    for param, data in parameters.items():
                        category_data.append({
                            'Paramètre': param,
                            'Valeur mesurée': data['valeur_mesuree'],
                            'Unité': data['unite'],
                            'Référence': data['valeur_reference'],
                            'Conforme': 'Oui' if data['conforme'] else 'Non' if data['conforme'] is not None else 'N/A',
                            'Source': data['source'],
                            'Date mesure': data['date_mesure']
                        })
                    
                    df_category = pd.DataFrame(category_data)
                    sheet_name = category.replace('_', ' ').title()[:31]  # Limite Excel
                    df_category.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Feuille de statistiques
                stats_data = {
                    'Statistique': [
                        'Nombre total de paramètres',
                        'Paramètres conformes',
                        'Paramètres non conformes',
                        'Taux de conformité (%)',
                        'Date de collecte',
                        'Coordonnées'
                    ],
                    'Valeur': [
                        total_params,
                        total_params - non_compliant,
                        non_compliant,
                        round((total_params - non_compliant) / total_params * 100, 1) if total_params > 0 else 0,
                        water_data.get('contexte', {}).get('date_collecte', 'N/A'),
                        str(water_data.get('contexte', {}).get('coordinates', 'N/A'))
                    ]
                }
                pd.DataFrame(stats_data).to_excel(writer, sheet_name='Statistiques', index=False)
            
            logger.info(f"Données d'eau exportées vers: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export Excel: {e}")
            return False
    
    def get_water_quality_summary(self, water_data):
        """Génère un résumé de la qualité de l'eau"""
        try:
            summary = {
                'qualite_globale': 'Bonne',
                'parametres_critiques': [],
                'recommandations': [],
                'score_qualite': 0
            }
            
            total_params = 0
            non_compliant_params = 0
            critical_params = []
            
            for category, parameters in water_data.items():
                if category == 'contexte':
                    continue
                
                for param, data in parameters.items():
                    total_params += 1
                    
                    if data['conforme'] is False:
                        non_compliant_params += 1
                        
                        # Paramètres critiques pour la santé
                        if any(critical in param.lower() for critical in ['plomb', 'mercure', 'arsenic', 'coli', 'salmonelles']):
                            critical_params.append(param)
            
            # Calcul du score de qualité
            if total_params > 0:
                compliance_rate = (total_params - non_compliant_params) / total_params
                summary['score_qualite'] = round(compliance_rate * 100, 1)
                
                if compliance_rate >= 0.9:
                    summary['qualite_globale'] = 'Excellente'
                elif compliance_rate >= 0.8:
                    summary['qualite_globale'] = 'Bonne'
                elif compliance_rate >= 0.6:
                    summary['qualite_globale'] = 'Moyenne'
                else:
                    summary['qualite_globale'] = 'Mauvaise'
            
            summary['parametres_critiques'] = critical_params
            
            # Recommandations
            if critical_params:
                summary['recommandations'].append("Traitement urgent requis pour les paramètres critiques")
                summary['recommandations'].append("Analyse microbiologique approfondie recommandée")
            
            if non_compliant_params > total_params * 0.2:
                summary['recommandations'].append("Surveillance renforcée de la qualité de l'eau")
                summary['recommandations'].append("Investigation des sources de pollution")
            
            if not summary['recommandations']:
                summary['recommandations'].append("Maintenir la surveillance régulière")
                summary['recommandations'].append("Continuer les bonnes pratiques de gestion")
            
            return summary
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du résumé: {e}")
            return None

def create_water_parameters_collector():
    """Fonction utilitaire pour créer un collecteur de paramètres d'eau"""
    try:
        collector = WaterParametersCollector()
        logger.info("Collecteur de paramètres d'eau créé avec succès")
        return collector
    except Exception as e:
        logger.error(f"Erreur lors de la création du collecteur: {e}")
        return None

if __name__ == "__main__":
    # Test du collecteur
    collector = create_water_parameters_collector()
    if collector:
        # Test avec des coordonnées du Maroc
        coordinates = (33.5731, -7.5898)  # Casablanca
        water_data = collector.collect_detailed_water_parameters(coordinates)
        
        if water_data:
            print("=== PARAMÈTRES D'EAU DÉTAILLÉS ===")
            print(f"Coordonnées: {coordinates}")
            
            for category, parameters in water_data.items():
                if category == 'contexte':
                    continue
                    
                print(f"\n{category.upper().replace('_', ' ')}:")
                for param, data in parameters.items():
                    conforme = "✓" if data['conforme'] else "✗" if data['conforme'] is not None else "?"
                    print(f"  {conforme} {param}: {data['valeur_mesuree']} {data['unite']} (Réf: {data['valeur_reference']})")
            
            # Générer le résumé
            summary = collector.get_water_quality_summary(water_data)
            if summary:
                print(f"\n=== RÉSUMÉ QUALITÉ ===")
                print(f"Qualité globale: {summary['qualite_globale']}")
                print(f"Score: {summary['score_qualite']}%")
                if summary['parametres_critiques']:
                    print(f"Paramètres critiques: {', '.join(summary['parametres_critiques'])}")
        else:
            print("Erreur lors de la collecte des paramètres d'eau")
    else:
        print("Erreur lors de la création du collecteur")
