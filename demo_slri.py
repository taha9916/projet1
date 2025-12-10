#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Démonstration de l'intégration SLRI
Script simple pour tester et démontrer les fonctionnalités SLRI
"""

import os
import sys
from pathlib import Path

# Configuration du chemin
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def demo_slri():
    """Démonstration des fonctionnalités SLRI"""
    print("=== DÉMONSTRATION SLRI ===\n")
    
    try:
        # 1. Import du module
        print("1. Importation du module SLRI...")
        from slri_integration import SLRIAnalyzer, integrate_slri_with_main_system
        print("   ✓ Module importé avec succès\n")
        
        # 2. Vérification du répertoire SLRI
        print("2. Vérification des fichiers SLRI...")
        slri_dir = project_root / "SLRI"
        if not slri_dir.exists():
            print(f"   ✗ Répertoire SLRI non trouvé: {slri_dir}")
            return False
            
        required_files = [
            "PRE CONSTRUCTION.txt",
            "CONSTRUCTION.txt", 
            "exploitation.txt",
            "démantalement.txt",
            "matrice d'impacts.txt",
            "Echelles.txt"
        ]
        
        for file_name in required_files:
            file_path = slri_dir / file_name
            if file_path.exists():
                print(f"   ✓ {file_name}")
            else:
                print(f"   ⚠ {file_name} manquant")
        print()
        
        # 3. Initialisation de l'analyseur
        print("3. Initialisation de l'analyseur SLRI...")
        analyzer = SLRIAnalyzer(str(slri_dir))
        print("   ✓ Analyseur initialisé\n")
        
        # 4. Chargement des données
        print("4. Chargement des données SLRI...")
        slri_data = analyzer.load_slri_data()
        
        if slri_data:
            print(f"   ✓ {len(slri_data)} phases chargées:")
            for phase_name, phase_data in slri_data.items():
                if isinstance(phase_data, list):
                    print(f"     - {phase_name}: {len(phase_data)} paramètres")
                else:
                    print(f"     - {phase_name}: données disponibles")
        else:
            print("   ✗ Aucune donnée chargée")
            return False
        print()
        
        # 5. Test d'évaluation simple
        print("5. Test d'évaluation des paramètres...")
        test_cases = [
            (7.0, "6-8", "pH dans l'intervalle acceptable"),
            (9.5, "6-8", "pH légèrement élevé"),
            (12.0, "6-8", "pH très élevé"),
            (25.0, "20-30", "Température normale"),
            (35.0, "20-30", "Température élevée")
        ]
        
        for valeur, intervalle, description in test_cases:
            score = analyzer._score_parameter(valeur, intervalle)
            risk_level = ["Faible", "Moyen", "Élevé"][min(score, 2)]
            print(f"   - {description}: {valeur} (intervalle: {intervalle}) → Score: {score} ({risk_level})")
        print()
        
        # 6. Test d'intégration complète
        print("6. Test d'intégration complète...")
        coordinates = (34.0209, -6.8416)  # Rabat, Maroc
        print(f"   Coordonnées de test: {coordinates}")
        
        results = integrate_slri_with_main_system(coordinates, "SLRI")
        
        if "error" in results:
            print(f"   ✗ Erreur: {results['error']}")
            return False
        
        print("   ✓ Intégration réussie")
        
        # Affichage des résultats
        stats = results.get("statistiques_globales", {})
        
        if "scores_par_phase" in stats:
            print("\n   Scores par phase:")
            for phase, score in stats["scores_par_phase"].items():
                print(f"     - {phase}: {score:.2f}")
        
        if "risques_majeurs" in stats and stats["risques_majeurs"]:
            print(f"\n   Risques majeurs identifiés ({len(stats['risques_majeurs'])}):")
            for i, risque in enumerate(stats["risques_majeurs"][:5], 1):
                print(f"     {i}. {risque['parametre']} ({risque['milieu']}) - {risque['amplitude']}")
        
        if "recommandations" in stats and stats["recommandations"]:
            print(f"\n   Recommandations ({len(stats['recommandations'])}):")
            for i, rec in enumerate(stats["recommandations"][:3], 1):
                print(f"     {i}. {rec}")
        
        print("\n=== DÉMONSTRATION TERMINÉE AVEC SUCCÈS ===")
        return True
        
    except ImportError as e:
        print(f"✗ Erreur d'importation: {e}")
        print("Vérifiez que tous les modules requis sont installés.")
        return False
    except Exception as e:
        print(f"✗ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = demo_slri()
    if success:
        print("\n🎉 La démonstration SLRI s'est déroulée avec succès !")
        print("L'intégration SLRI est opérationnelle et prête à être utilisée.")
    else:
        print("\n⚠️ La démonstration a rencontré des problèmes.")
        print("Vérifiez la configuration et les fichiers SLRI.")
