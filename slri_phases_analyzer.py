#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyseur SLRI par phases - Implémente les 4 étapes d'analyse environnementale
PRE CONSTRUCTION, CONSTRUCTION, EXPLOITATION, DÉMANTÈLEMENT
"""

import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Any
import numpy as np

logger = logging.getLogger(__name__)

class SLRIPhasesAnalyzer:
    """
    Analyseur SLRI pour les 4 phases du cycle de vie d'un projet
    """
    
    def __init__(self):
        self.phases = {
            'PRE_CONSTRUCTION': 'Pré-construction',
            'CONSTRUCTION': 'Construction', 
            'EXPLOITATION': 'Exploitation',
            'DEMANTELEMENT': 'Démantèlement'
        }
        
        # Échelles d'évaluation SLRI
        self.scoring_scales = {
            'parameter_score': {
                0: 'Conforme aux normes',
                1: 'Dépassement léger (≤10%)',
                2: 'Dépassement important (>10%)'
            },
            'duree': {
                0: 'Temporaire (<1 an)',
                1: 'Courte durée (1-5 ans)',
                2: 'Durée moyenne (5-15 ans)',
                3: 'Longue durée (15-30 ans)',
                4: 'Permanente (>30 ans)'
            },
            'etendue': {
                0: 'Ponctuelle (site projet)',
                1: 'Locale (<1 km)',
                2: 'Régionale (1-10 km)',
                3: 'Large échelle (>10 km)'
            },
            'frequence': {
                0: 'Rare (<1 fois/an)',
                1: 'Occasionnelle (1-12 fois/an)',
                2: 'Intermittente (1-4 fois/mois)',
                3: 'Régulière (1-6 fois/semaine)',
                4: 'Continue (quotidienne)'
            }
        }
        
        # Classification des risques
        self.risk_classification = {
            'FAIBLE': {'range': (0, 4), 'color': 'Vert', 'actions': [
                'Surveillance de routine',
                'Maintien des bonnes pratiques'
            ]},
            'MOYEN': {'range': (5, 8), 'color': 'Jaune', 'actions': [
                'Surveillance renforcée',
                'Mesures préventives',
                'Révision des procédures'
            ]},
            'FORT': {'range': (9, 12), 'color': 'Orange', 'actions': [
                'Mesures correctives immédiates',
                'Plan d\'action détaillé',
                'Surveillance continue'
            ]},
            'TRES_GRAVE': {'range': (13, float('inf')), 'color': 'Rouge', 'actions': [
                'Arrêt temporaire des activités',
                'Mesures d\'urgence',
                'Réhabilitation nécessaire',
                'Notification aux autorités'
            ]}
        }
        
        # Seuils de référence par milieu
        self.reference_thresholds = {
            'eau': {
                'pH': {'min': 6.5, 'max': 8.5, 'unit': ''},
                'Température': {'min': 15, 'max': 25, 'unit': '°C'},
                'Turbidité': {'max': 5, 'unit': 'NTU'},
                'Conductivité': {'max': 1000, 'unit': 'µS/cm'},
                'Oxygène dissous': {'min': 5, 'unit': 'mg/L'},
                'DBO5': {'max': 5, 'unit': 'mg/L'},
                'DCO': {'max': 25, 'unit': 'mg/L'},
                'Nitrates': {'max': 50, 'unit': 'mg/L'},
                'Nitrites': {'max': 0.5, 'unit': 'mg/L'},
                'Ammoniac': {'max': 0.5, 'unit': 'mg/L'},
                'Phosphore total': {'max': 0.1, 'unit': 'mg/L'},
                'Azote total': {'max': 10, 'unit': 'mg/L'},
                'Plomb (Pb)': {'max': 0.01, 'unit': 'mg/L'},
                'Cadmium (Cd)': {'max': 0.005, 'unit': 'mg/L'},
                'Chrome (Cr)': {'max': 0.05, 'unit': 'mg/L'},
                'Cuivre (Cu)': {'max': 2, 'unit': 'mg/L'},
                'Zinc (Zn)': {'max': 3, 'unit': 'mg/L'},
                'Nickel (Ni)': {'max': 0.07, 'unit': 'mg/L'},
                'Mercure (Hg)': {'max': 0.001, 'unit': 'mg/L'},
                'Arsenic (As)': {'max': 0.01, 'unit': 'mg/L'}
            },
            'sol': {
                'pH': {'min': 6.0, 'max': 8.0, 'unit': ''},
                'Matière organique': {'min': 2, 'max': 5, 'unit': '%'},
                'Carbone organique': {'min': 1, 'max': 3, 'unit': '%'},
                'Plomb (Pb)': {'max': 85, 'unit': 'mg/kg'},
                'Cadmium (Cd)': {'max': 1.4, 'unit': 'mg/kg'},
                'Chrome (Cr)': {'max': 100, 'unit': 'mg/kg'},
                'Cuivre (Cu)': {'max': 36, 'unit': 'mg/kg'},
                'Zinc (Zn)': {'max': 140, 'unit': 'mg/kg'},
                'Nickel (Ni)': {'max': 35, 'unit': 'mg/kg'},
                'Mercure (Hg)': {'max': 0.4, 'unit': 'mg/kg'},
                'Arsenic (As)': {'max': 12, 'unit': 'mg/kg'}
            },
            'air': {
                'PM10': {'max': 50, 'unit': 'µg/m³'},
                'PM2.5': {'max': 25, 'unit': 'µg/m³'},
                'SO2': {'max': 125, 'unit': 'µg/m³'},
                'NOx': {'max': 200, 'unit': 'µg/m³'},
                'CO': {'max': 10, 'unit': 'mg/m³'},
                'O3': {'max': 120, 'unit': 'µg/m³'},
                'Poussières totales': {'max': 150, 'unit': 'µg/m³'}
            }
        }
    
    def analyze_project_phases(self, environmental_data: Dict, project_type: str = "general") -> Dict:
        """
        Analyse complète des 4 phases du projet selon la méthodologie SLRI
        
        Args:
            environmental_data: Données environnementales collectées
            project_type: Type de projet (général, industriel, infrastructure, etc.)
            
        Returns:
            Dict: Résultats d'analyse par phase
        """
        try:
            results = {
                'metadata': {
                    'date_analyse': datetime.now().isoformat(),
                    'project_type': project_type,
                    'methodology': 'SLRI - Standardiser l\'évaluation des risques et impacts'
                },
                'phases': {}
            }
            
            # Analyser chaque phase
            for phase_key, phase_name in self.phases.items():
                logger.info(f"Analyse de la phase: {phase_name}")
                phase_results = self._analyze_single_phase(
                    phase_key, environmental_data, project_type
                )
                results['phases'][phase_key] = phase_results
            
            # Synthèse globale
            results['synthese'] = self._generate_global_synthesis(results['phases'])
            
            logger.info("Analyse SLRI par phases terminée avec succès")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse SLRI par phases: {e}")
            return {'error': str(e)}
    
    def _analyze_single_phase(self, phase: str, environmental_data: Dict, project_type: str) -> Dict:
        """Analyse une phase spécifique du projet"""
        
        phase_results = {
            'phase_name': self.phases[phase],
            'milieux': {},
            'scores_totaux': {},
            'risques_majeurs': [],
            'recommandations': []
        }
        
        # Analyser chaque milieu
        for milieu in ['eau', 'sol', 'air']:
            if milieu in environmental_data:
                milieu_analysis = self._analyze_milieu_for_phase(
                    milieu, environmental_data[milieu], phase, project_type
                )
                phase_results['milieux'][milieu] = milieu_analysis
        
        # Calculer les scores totaux
        phase_results['scores_totaux'] = self._calculate_phase_scores(phase_results['milieux'])
        
        # Identifier les risques majeurs
        phase_results['risques_majeurs'] = self._identify_major_risks(phase_results['milieux'])
        
        # Générer les recommandations
        phase_results['recommandations'] = self._generate_phase_recommendations(
            phase, phase_results['scores_totaux'], phase_results['risques_majeurs']
        )
        
        return phase_results
    
    def _analyze_milieu_for_phase(self, milieu: str, milieu_data: Dict, phase: str, project_type: str) -> Dict:
        """Analyse un milieu spécifique pour une phase donnée"""
        
        milieu_results = {
            'parametres': {},
            'score_milieu': 0,
            'classification_risque': 'FAIBLE',
            'nb_parametres_non_conformes': 0
        }
        
        # Facteurs temporels et spatiaux selon la phase
        temporal_factors = self._get_phase_temporal_factors(phase, project_type)
        
        # Analyser chaque paramètre
        for param_name, param_data in milieu_data.items():
            if isinstance(param_data, tuple) and len(param_data) >= 2:
                value, unit = param_data[0], param_data[1]
                
                # Calculer le score du paramètre
                param_analysis = self._analyze_parameter(
                    param_name, value, unit, milieu, temporal_factors
                )
                
                milieu_results['parametres'][param_name] = param_analysis
                
                # Mettre à jour les totaux
                if param_analysis['score_final'] > 4:  # Seuil de non-conformité
                    milieu_results['nb_parametres_non_conformes'] += 1
        
        # Calculer le score global du milieu
        if milieu_results['parametres']:
            scores = [p['score_final'] for p in milieu_results['parametres'].values()]
            milieu_results['score_milieu'] = sum(scores) / len(scores)
            milieu_results['classification_risque'] = self._classify_risk(milieu_results['score_milieu'])
        
        return milieu_results
    
    def _analyze_parameter(self, param_name: str, value: Any, unit: str, milieu: str, temporal_factors: Dict) -> Dict:
        """Analyse un paramètre individuel selon la méthodologie SLRI"""
        
        try:
            # Extraire la valeur numérique si c'est une chaîne formatée
            if isinstance(value, str):
                # Nettoyer la valeur (enlever les indicateurs ✓/✗)
                clean_value = value.split()[0] if value.split() else value
                try:
                    numeric_value = float(clean_value)
                except ValueError:
                    numeric_value = None
            else:
                numeric_value = float(value) if value is not None else None
            
            # Score de base du paramètre (0-2)
            base_score = self._calculate_parameter_base_score(param_name, numeric_value, milieu)
            
            # Score final avec facteurs temporels/spatiaux
            score_final = base_score * (
                temporal_factors['duree'] + 
                temporal_factors['etendue'] + 
                temporal_factors['frequence']
            )
            
            # Classification du risque
            risk_class = self._classify_risk(score_final)
            
            return {
                'valeur_mesuree': numeric_value,
                'unite': unit,
                'score_base': base_score,
                'facteurs_temporels': temporal_factors,
                'score_final': score_final,
                'classification_risque': risk_class,
                'conforme': score_final <= 4,
                'seuil_reference': self._get_parameter_threshold(param_name, milieu)
            }
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'analyse du paramètre {param_name}: {e}")
            return {
                'valeur_mesuree': value,
                'unite': unit,
                'score_base': 0,
                'score_final': 0,
                'classification_risque': 'FAIBLE',
                'conforme': True,
                'erreur': str(e)
            }
    
    def _calculate_parameter_base_score(self, param_name: str, value: float, milieu: str) -> int:
        """Calcule le score de base d'un paramètre (0-2)"""
        
        if value is None:
            return 0
        
        threshold = self._get_parameter_threshold(param_name, milieu)
        if not threshold:
            return 0
        
        # Vérifier le dépassement des seuils
        if 'max' in threshold:
            max_val = threshold['max']
            if value <= max_val:
                return 0  # Conforme
            elif value <= max_val * 1.1:
                return 1  # Dépassement léger (≤10%)
            else:
                return 2  # Dépassement important (>10%)
        
        elif 'min' in threshold:
            min_val = threshold['min']
            if value >= min_val:
                return 0  # Conforme
            elif value >= min_val * 0.9:
                return 1  # Dépassement léger
            else:
                return 2  # Dépassement important
        
        elif 'min' in threshold and 'max' in threshold:
            min_val, max_val = threshold['min'], threshold['max']
            if min_val <= value <= max_val:
                return 0  # Conforme
            elif (min_val * 0.9 <= value < min_val) or (max_val < value <= max_val * 1.1):
                return 1  # Dépassement léger
            else:
                return 2  # Dépassement important
        
        return 0
    
    def _get_parameter_threshold(self, param_name: str, milieu: str) -> Dict:
        """Récupère le seuil de référence d'un paramètre"""
        
        if milieu in self.reference_thresholds:
            milieu_thresholds = self.reference_thresholds[milieu]
            
            # Recherche exacte
            if param_name in milieu_thresholds:
                return milieu_thresholds[param_name]
            
            # Recherche approximative
            for threshold_param, threshold_data in milieu_thresholds.items():
                if param_name.lower() in threshold_param.lower() or threshold_param.lower() in param_name.lower():
                    return threshold_data
        
        return {}
    
    def _get_phase_temporal_factors(self, phase: str, project_type: str) -> Dict:
        """Retourne les facteurs temporels et spatiaux selon la phase"""
        
        # Facteurs par défaut selon la phase
        phase_factors = {
            'PRE_CONSTRUCTION': {'duree': 1, 'etendue': 1, 'frequence': 1},
            'CONSTRUCTION': {'duree': 2, 'etendue': 2, 'frequence': 3},
            'EXPLOITATION': {'duree': 4, 'etendue': 2, 'frequence': 4},
            'DEMANTELEMENT': {'duree': 1, 'etendue': 2, 'frequence': 2}
        }
        
        return phase_factors.get(phase, {'duree': 1, 'etendue': 1, 'frequence': 1})
    
    def _classify_risk(self, score: float) -> str:
        """Classifie le niveau de risque selon le score SLRI"""
        
        for risk_level, risk_data in self.risk_classification.items():
            min_val, max_val = risk_data['range']
            if min_val <= score <= max_val:
                return risk_level
        
        return 'FAIBLE'
    
    def _calculate_phase_scores(self, milieux_data: Dict) -> Dict:
        """Calcule les scores totaux d'une phase"""
        
        scores = {
            'score_global': 0,
            'scores_par_milieu': {},
            'classification_globale': 'FAIBLE'
        }
        
        total_score = 0
        milieu_count = 0
        
        for milieu, milieu_data in milieux_data.items():
            milieu_score = milieu_data.get('score_milieu', 0)
            scores['scores_par_milieu'][milieu] = milieu_score
            total_score += milieu_score
            milieu_count += 1
        
        if milieu_count > 0:
            scores['score_global'] = total_score / milieu_count
            scores['classification_globale'] = self._classify_risk(scores['score_global'])
        
        return scores
    
    def _identify_major_risks(self, milieux_data: Dict) -> List[Dict]:
        """Identifie les risques majeurs d'une phase"""
        
        major_risks = []
        
        for milieu, milieu_data in milieux_data.items():
            for param_name, param_data in milieu_data.get('parametres', {}).items():
                if param_data.get('score_final', 0) > 8:  # Seuil de risque majeur
                    major_risks.append({
                        'milieu': milieu,
                        'parametre': param_name,
                        'score': param_data.get('score_final', 0),
                        'classification': param_data.get('classification_risque', 'FAIBLE'),
                        'valeur': param_data.get('valeur_mesuree'),
                        'unite': param_data.get('unite', '')
                    })
        
        # Trier par score décroissant
        major_risks.sort(key=lambda x: x['score'], reverse=True)
        
        return major_risks
    
    def _generate_phase_recommendations(self, phase: str, scores: Dict, major_risks: List) -> List[str]:
        """Génère les recommandations pour une phase"""
        
        recommendations = []
        
        # Recommandations selon le niveau de risque global
        global_risk = scores.get('classification_globale', 'FAIBLE')
        if global_risk in self.risk_classification:
            recommendations.extend(self.risk_classification[global_risk]['actions'])
        
        # Recommandations spécifiques aux risques majeurs
        if major_risks:
            recommendations.append(f"Attention particulière requise pour {len(major_risks)} paramètre(s) à risque élevé")
            
            for risk in major_risks[:3]:  # Top 3 des risques
                recommendations.append(
                    f"- {risk['parametre']} ({risk['milieu']}): "
                    f"Score {risk['score']:.1f} - Surveillance renforcée nécessaire"
                )
        
        # Recommandations spécifiques à la phase
        phase_specific = {
            'PRE_CONSTRUCTION': [
                "Établir l'état de référence environnemental",
                "Mettre en place le système de surveillance"
            ],
            'CONSTRUCTION': [
                "Surveiller les impacts temporaires",
                "Appliquer les mesures de mitigation"
            ],
            'EXPLOITATION': [
                "Maintenir la surveillance continue",
                "Optimiser les performances environnementales"
            ],
            'DEMANTELEMENT': [
                "Planifier la restauration du site",
                "Gérer les déchets de démolition"
            ]
        }
        
        if phase in phase_specific:
            recommendations.extend(phase_specific[phase])
        
        return recommendations
    
    def _generate_global_synthesis(self, phases_data: Dict) -> Dict:
        """Génère une synthèse globale de toutes les phases"""
        
        synthesis = {
            'score_global_projet': 0,
            'phase_plus_critique': '',
            'risques_majeurs_globaux': [],
            'recommandations_prioritaires': [],
            'conformite_globale': True
        }
        
        # Calculer le score global du projet
        phase_scores = []
        max_score = 0
        critical_phase = ''
        
        for phase, phase_data in phases_data.items():
            phase_score = phase_data.get('scores_totaux', {}).get('score_global', 0)
            phase_scores.append(phase_score)
            
            if phase_score > max_score:
                max_score = phase_score
                critical_phase = phase
            
            # Collecter les risques majeurs
            major_risks = phase_data.get('risques_majeurs', [])
            for risk in major_risks:
                risk['phase'] = phase
                synthesis['risques_majeurs_globaux'].append(risk)
        
        # Score global
        if phase_scores:
            synthesis['score_global_projet'] = sum(phase_scores) / len(phase_scores)
        
        synthesis['phase_plus_critique'] = critical_phase
        
        # Trier les risques globaux
        synthesis['risques_majeurs_globaux'].sort(key=lambda x: x['score'], reverse=True)
        
        # Recommandations prioritaires
        if synthesis['score_global_projet'] > 8:
            synthesis['recommandations_prioritaires'].extend([
                "Révision complète du projet nécessaire",
                "Consultation d'experts environnementaux",
                "Renforcement des mesures de mitigation"
            ])
        elif synthesis['score_global_projet'] > 4:
            synthesis['recommandations_prioritaires'].extend([
                "Surveillance environnementale renforcée",
                "Mise en place de mesures correctives",
                "Suivi régulier des paramètres critiques"
            ])
        
        # Conformité globale
        synthesis['conformite_globale'] = synthesis['score_global_projet'] <= 4
        
        return synthesis


def create_slri_phases_analyzer():
    """Factory function pour créer un analyseur SLRI par phases"""
    return SLRIPhasesAnalyzer()


# Fonction d'intégration avec le système principal
def analyze_project_with_slri_phases(environmental_data: Dict, project_type: str = "general") -> Dict:
    """
    Fonction principale pour analyser un projet selon les 4 phases SLRI
    
    Args:
        environmental_data: Données environnementales collectées
        project_type: Type de projet
        
    Returns:
        Dict: Résultats complets de l'analyse SLRI par phases
    """
    try:
        analyzer = create_slri_phases_analyzer()
        return analyzer.analyze_project_phases(environmental_data, project_type)
    except Exception as e:
        logger.error(f"Erreur dans l'analyse SLRI par phases: {e}")
        return {'error': str(e)}
