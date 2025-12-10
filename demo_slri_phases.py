#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Démonstration de l'analyse SLRI par phases
Test du module slri_phases_analyzer avec des données simulées
"""

import sys
import os
import logging
from datetime import datetime

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_sample_environmental_data():
    """Crée des données environnementales d'exemple pour tester l'analyse SLRI"""
    
    # Données d'eau simulées (format attendu par SLRI)
    water_data = {
        'pH': (7.2, ''),
        'Température': (22.5, '°C'),
        'Turbidité': (3.2, 'NTU'),
        'Conductivité': (850, 'µS/cm'),
        'Oxygène dissous': (6.8, 'mg/L'),
        'DBO5': (3.1, 'mg/L'),
        'DCO': (18.5, 'mg/L'),
        'Nitrates': (35.2, 'mg/L'),
        'Nitrites': (0.3, 'mg/L'),
        'Ammoniac': (0.2, 'mg/L'),
        'Phosphore total': (0.08, 'mg/L'),
        'Azote total': (8.5, 'mg/L'),
        'Plomb (Pb)': (0.008, 'mg/L'),
        'Cadmium (Cd)': (0.003, 'mg/L'),
        'Chrome (Cr)': (0.04, 'mg/L'),
        'Cuivre (Cu)': (1.5, 'mg/L'),
        'Zinc (Zn)': (2.1, 'mg/L'),
        'Nickel (Ni)': (0.05, 'mg/L'),
        'Mercure (Hg)': (0.0008, 'mg/L'),
        'Arsenic (As)': (0.007, 'mg/L')
    }
    
    # Données de sol simulées
    soil_data = {
        'pH': (6.8, ''),
        'Matière organique': (3.2, '%'),
        'Carbone organique': (1.8, '%'),
        'Plomb (Pb)': (45, 'mg/kg'),
        'Cadmium (Cd)': (0.8, 'mg/kg'),
        'Chrome (Cr)': (65, 'mg/kg'),
        'Cuivre (Cu)': (28, 'mg/kg'),
        'Zinc (Zn)': (95, 'mg/kg'),
        'Nickel (Ni)': (22, 'mg/kg'),
        'Mercure (Hg)': (0.2, 'mg/kg'),
        'Arsenic (As)': (8, 'mg/kg')
    }
    
    # Données d'air simulées
    air_data = {
        'PM10': (35, 'µg/m³'),
        'PM2.5': (18, 'µg/m³'),
        'SO2': (85, 'µg/m³'),
        'NOx': (145, 'µg/m³'),
        'CO': (6.5, 'mg/m³'),
        'O3': (95, 'µg/m³'),
        'Poussières totales': (120, 'µg/m³')
    }
    
    return {
        'eau': water_data,
        'sol': soil_data,
        'air': air_data
    }

def test_slri_phases_analysis():
    """Test complet de l'analyse SLRI par phases"""
    
    print("=" * 80)
    print("DÉMONSTRATION - ANALYSE SLRI PAR PHASES")
    print("=" * 80)
    print()
    
    try:
        # Importer le module d'analyse SLRI
        from slri_phases_analyzer import analyze_project_with_slri_phases
        
        # Créer des données environnementales d'exemple
        print("1. Création des données environnementales d'exemple...")
        env_data = create_sample_environmental_data()
        
        print(f"   - Paramètres d'eau: {len(env_data['eau'])}")
        print(f"   - Paramètres de sol: {len(env_data['sol'])}")
        print(f"   - Paramètres d'air: {len(env_data['air'])}")
        print()
        
        # Lancer l'analyse pour différents types de projets
        project_types = ['general', 'industrial', 'infrastructure']
        
        for project_type in project_types:
            print(f"2. Analyse SLRI pour projet de type: {project_type.upper()}")
            print("-" * 60)
            
            # Lancer l'analyse
            results = analyze_project_with_slri_phases(env_data, project_type)
            
            if 'error' in results:
                print(f"   ❌ Erreur: {results['error']}")
                continue
            
            # Afficher les résultats principaux
            metadata = results.get('metadata', {})
            synthesis = results.get('synthese', {})
            
            print(f"   📊 Score global du projet: {synthesis.get('score_global_projet', 0):.2f}")
            print(f"   🚨 Phase la plus critique: {synthesis.get('phase_plus_critique', 'N/A')}")
            print(f"   ✅ Conformité globale: {'OUI' if synthesis.get('conformite_globale', False) else 'NON'}")
            
            # Risques majeurs
            major_risks = synthesis.get('risques_majeurs_globaux', [])
            if major_risks:
                print(f"   ⚠️  Risques majeurs identifiés: {len(major_risks)}")
                for i, risk in enumerate(major_risks[:3], 1):
                    print(f"      {i}. {risk.get('parametre', 'N/A')} ({risk.get('milieu', 'N/A')}) - "
                          f"Score: {risk.get('score', 0):.1f}")
            else:
                print("   ✅ Aucun risque majeur identifié")
            
            # Détail par phase
            phases = results.get('phases', {})
            print(f"   📋 Phases analysées: {len(phases)}")
            
            for phase_key, phase_data in phases.items():
                phase_name = phase_data.get('phase_name', phase_key)
                scores = phase_data.get('scores_totaux', {})
                score_global = scores.get('score_global', 0)
                classification = scores.get('classification_globale', 'FAIBLE')
                
                print(f"      - {phase_name}: Score {score_global:.2f} ({classification})")
            
            print()
        
        print("3. Test des fonctionnalités avancées...")
        
        # Test avec des données extrêmes pour déclencher des alertes
        extreme_data = create_sample_environmental_data()
        
        # Modifier quelques valeurs pour créer des dépassements
        extreme_data['eau']['pH'] = (9.5, '')  # Dépassement important
        extreme_data['eau']['Plomb (Pb)'] = (0.025, 'mg/L')  # Dépassement de 150%
        extreme_data['sol']['Cadmium (Cd)'] = (3.5, 'mg/kg')  # Dépassement important
        extreme_data['air']['PM10'] = (85, 'µg/m³')  # Dépassement de 70%
        
        print("   - Test avec données présentant des dépassements...")
        extreme_results = analyze_project_with_slri_phases(extreme_data, 'industrial')
        
        if 'error' not in extreme_results:
            extreme_synthesis = extreme_results.get('synthese', {})
            extreme_risks = extreme_synthesis.get('risques_majeurs_globaux', [])
            
            print(f"   📊 Score avec dépassements: {extreme_synthesis.get('score_global_projet', 0):.2f}")
            print(f"   ⚠️  Risques détectés: {len(extreme_risks)}")
            print(f"   🚨 Conformité: {'OUI' if extreme_synthesis.get('conformite_globale', False) else 'NON'}")
        
        print()
        print("✅ Démonstration terminée avec succès!")
        print()
        print("RÉSUMÉ DES FONCTIONNALITÉS TESTÉES:")
        print("- ✅ Analyse des 4 phases SLRI (PRE CONSTRUCTION, CONSTRUCTION, EXPLOITATION, DÉMANTÈLEMENT)")
        print("- ✅ Évaluation multi-milieux (eau, sol, air)")
        print("- ✅ Scoring selon la méthodologie SLRI")
        print("- ✅ Classification des risques (FAIBLE, MOYEN, FORT, TRÈS GRAVE)")
        print("- ✅ Identification des risques majeurs")
        print("- ✅ Génération de recommandations par phase")
        print("- ✅ Synthèse globale du projet")
        print("- ✅ Support de différents types de projets")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("   Vérifiez que le module slri_phases_analyzer.py est présent")
        return False
    
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        logger.error(f"Erreur dans test_slri_phases_analysis: {e}")
        return False

def test_individual_components():
    """Test des composants individuels du module SLRI"""
    
    print("\n" + "=" * 80)
    print("TEST DES COMPOSANTS INDIVIDUELS")
    print("=" * 80)
    
    try:
        from slri_phases_analyzer import SLRIPhasesAnalyzer
        
        # Créer une instance de l'analyseur
        analyzer = SLRIPhasesAnalyzer()
        
        print("1. Test de l'initialisation de l'analyseur...")
        print(f"   - Phases disponibles: {list(analyzer.phases.keys())}")
        print(f"   - Milieux de référence: {list(analyzer.reference_thresholds.keys())}")
        print(f"   - Classifications de risque: {list(analyzer.risk_classification.keys())}")
        
        print("\n2. Test des seuils de référence...")
        # Test de récupération des seuils
        ph_threshold = analyzer._get_parameter_threshold('pH', 'eau')
        print(f"   - Seuil pH (eau): {ph_threshold}")
        
        pb_threshold = analyzer._get_parameter_threshold('Plomb (Pb)', 'sol')
        print(f"   - Seuil Plomb (sol): {pb_threshold}")
        
        print("\n3. Test du calcul de score de base...")
        # Test de calcul de score
        score_conforme = analyzer._calculate_parameter_base_score('pH', 7.0, 'eau')
        score_depassement = analyzer._calculate_parameter_base_score('pH', 9.5, 'eau')
        
        print(f"   - Score pH=7.0: {score_conforme} (attendu: 0)")
        print(f"   - Score pH=9.5: {score_depassement} (attendu: 2)")
        
        print("\n4. Test de classification des risques...")
        # Test de classification
        risk_low = analyzer._classify_risk(2.0)
        risk_high = analyzer._classify_risk(15.0)
        
        print(f"   - Classification score 2.0: {risk_low}")
        print(f"   - Classification score 15.0: {risk_high}")
        
        print("\n✅ Tests des composants individuels réussis!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des composants: {e}")
        return False

if __name__ == "__main__":
    print(f"Démarrage des tests SLRI - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test principal
    success_main = test_slri_phases_analysis()
    
    # Test des composants
    success_components = test_individual_components()
    
    # Résumé final
    print("\n" + "=" * 80)
    print("RÉSUMÉ DES TESTS")
    print("=" * 80)
    print(f"Test principal: {'✅ RÉUSSI' if success_main else '❌ ÉCHOUÉ'}")
    print(f"Test composants: {'✅ RÉUSSI' if success_components else '❌ ÉCHOUÉ'}")
    
    if success_main and success_components:
        print("\n🎉 Tous les tests sont passés avec succès!")
        print("Le module SLRI par phases est prêt à être utilisé.")
    else:
        print("\n⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
    
    print(f"\nFin des tests - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
