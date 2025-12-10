#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validation pour vérifier l'intégration des 42 paramètres d'eau détaillés
"""

import sys
import os
import logging

# Ajouter le répertoire du projet au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from external_apis import ExternalAPIs
from water_parameters_collector import create_water_parameters_collector

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_detailed_water_integration():
    """Test complet de l'intégration des paramètres d'eau détaillés"""
    
    print("=" * 80)
    print("🧪 TEST D'INTÉGRATION DES PARAMÈTRES D'EAU DÉTAILLÉS")
    print("=" * 80)
    
    # Coordonnées de test (Casablanca, Maroc)
    test_lat = 33.5731
    test_lon = -7.5898
    
    print(f"\n📍 Coordonnées de test: {test_lat}, {test_lon}")
    
    # Test 1: Vérifier le collecteur de paramètres d'eau
    print("\n1️⃣ Test du collecteur de paramètres d'eau...")
    try:
        collector = create_water_parameters_collector()
        if collector:
            print("✅ Collecteur créé avec succès")
            
            # Collecter les données
            water_data = collector.collect_detailed_water_parameters((test_lat, test_lon))
            if water_data:
                print(f"✅ Données collectées: {len(water_data)} catégories")
                
                # Compter les paramètres
                total_params = 0
                for category, params in water_data.items():
                    if category != 'contexte' and isinstance(params, dict):
                        param_count = len(params)
                        total_params += param_count
                        print(f"   - {category}: {param_count} paramètres")
                
                print(f"📊 Total paramètres collectés: {total_params}")
                
                if total_params >= 42:
                    print("✅ Nombre de paramètres suffisant (≥42)")
                else:
                    print(f"⚠️  Nombre de paramètres insuffisant: {total_params}/42")
            else:
                print("❌ Aucune donnée collectée")
        else:
            print("❌ Impossible de créer le collecteur")
    except Exception as e:
        print(f"❌ Erreur lors du test du collecteur: {e}")
    
    # Test 2: Vérifier l'intégration dans ExternalAPIs
    print("\n2️⃣ Test de l'intégration dans ExternalAPIs...")
    try:
        api = ExternalAPIs()
        detailed_data = api.get_detailed_water_data(test_lat, test_lon)
        
        if detailed_data and "Erreur" not in detailed_data:
            print(f"✅ Données détaillées récupérées: {len(detailed_data)} paramètres")
            
            # Afficher quelques exemples
            print("\n📋 Exemples de paramètres récupérés:")
            count = 0
            for param, value in detailed_data.items():
                if count < 5:  # Afficher les 5 premiers
                    print(f"   - {param}: {value}")
                    count += 1
            
            if len(detailed_data) > 5:
                print(f"   ... et {len(detailed_data) - 5} autres paramètres")
            
            # Vérifier la présence de la qualité globale
            if "Qualité Globale de l'Eau" in detailed_data:
                print(f"✅ Résumé qualité présent: {detailed_data['Qualité Globale de l\'Eau']}")
            
        else:
            print(f"❌ Erreur dans la récupération: {detailed_data}")
    except Exception as e:
        print(f"❌ Erreur lors du test ExternalAPIs: {e}")
    
    # Test 3: Vérifier l'intégration dans collect_all_data
    print("\n3️⃣ Test de l'intégration dans collect_all_data...")
    try:
        api = ExternalAPIs()
        
        # Options pour tester uniquement les données d'eau
        api_options = {
            "weather": False,
            "air_quality": False,
            "soil": False,
            "worldbank": False,
            "osm": False,
            "copernicus": False,
            "gbif": False,
            "nasa": False,
            "eau": True
        }
        
        all_data_df = api.collect_all_data("Test Location", lat=test_lat, lon=test_lon, api_options=api_options)
        
        if all_data_df is not None and not all_data_df.empty:
            # Filtrer les paramètres d'eau
            water_params = all_data_df[all_data_df['Milieu'] == 'Eau']
            
            print(f"✅ DataFrame créé avec {len(all_data_df)} lignes totales")
            print(f"✅ Paramètres d'eau dans le DataFrame: {len(water_params)}")
            
            if len(water_params) >= 40:  # Au moins 40 paramètres (42 - quelques métadonnées)
                print("✅ Nombre suffisant de paramètres d'eau dans le DataFrame")
            else:
                print(f"⚠️  Nombre insuffisant de paramètres d'eau: {len(water_params)}")
            
            # Afficher quelques exemples
            print("\n📋 Exemples de paramètres dans le DataFrame:")
            for i, row in water_params.head(3).iterrows():
                print(f"   - {row['Paramètre']}: {row['Valeur mesurée']} {row['Unité']}")
                
        else:
            print("❌ Aucune donnée dans le DataFrame")
    except Exception as e:
        print(f"❌ Erreur lors du test collect_all_data: {e}")
    
    print("\n" + "=" * 80)
    print("🏁 FIN DES TESTS")
    print("=" * 80)

def test_specific_categories():
    """Test spécifique des catégories de paramètres d'eau"""
    
    print("\n" + "=" * 60)
    print("🔬 TEST DÉTAILLÉ DES CATÉGORIES DE PARAMÈTRES")
    print("=" * 60)
    
    try:
        collector = create_water_parameters_collector()
        if not collector:
            print("❌ Impossible de créer le collecteur")
            return
        
        # Coordonnées de test
        coords = (33.5731, -7.5898)
        data = collector.collect_detailed_water_parameters(coords)
        
        if not data:
            print("❌ Aucune donnée collectée")
            return
        
        # Catégories attendues
        expected_categories = [
            'physico_chimique',
            'pollution_organique', 
            'nutriments',
            'metaux_lourds',
            'microbiologie',
            'pesticides'
        ]
        
        print("\n📊 Analyse par catégorie:")
        total_found = 0
        
        for category in expected_categories:
            if category in data and isinstance(data[category], dict):
                param_count = len(data[category])
                total_found += param_count
                print(f"✅ {category.replace('_', ' ').title()}: {param_count} paramètres")
                
                # Afficher quelques paramètres de cette catégorie
                params_list = list(data[category].keys())[:3]
                for param in params_list:
                    details = data[category][param]
                    value = details.get('valeur_mesuree', 'N/A')
                    unit = details.get('unite', '')
                    conforme = details.get('conforme', None)
                    status = "✓" if conforme is True else ("✗" if conforme is False else "?")
                    print(f"   • {param}: {value} {unit} {status}")
            else:
                print(f"❌ {category.replace('_', ' ').title()}: Non trouvé")
        
        print(f"\n📈 Total paramètres trouvés: {total_found}")
        
        # Test du résumé qualité
        summary = collector.get_water_quality_summary(data)
        if summary:
            print(f"\n🎯 Résumé qualité:")
            print(f"   - Qualité globale: {summary.get('qualite_globale', 'N/A')}")
            print(f"   - Score: {summary.get('score_qualite', 'N/A')}%")
            print(f"   - Paramètres conformes: {summary.get('parametres_conformes', 'N/A')}")
            print(f"   - Paramètres non conformes: {summary.get('parametres_non_conformes', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur lors du test des catégories: {e}")

if __name__ == "__main__":
    test_detailed_water_integration()
    test_specific_categories()
