import pandas as pd
import numpy as np
import json
import os
import logging
import time
from datetime import datetime
from cache_manager import cached
from external_apis import collect_environmental_data_from_apis
from calculate_risk_scores_morocco import calculate_environmental_risk_score_morocco

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_environmental_risk_assessment(latitude, longitude, project_type, country="morocco"):
    """Exécute une évaluation complète des risques environnementaux pour un site donné.
    
    Args:
        latitude (float): Latitude du site
        longitude (float): Longitude du site
        project_type (str): Type de projet (ex: "Minier", "Énergétique")
        country (str): Pays pour lequel utiliser les seuils spécifiques (par défaut: morocco)
        
    Returns:
        pandas.DataFrame: DataFrame contenant les données environnementales et les scores de risque
    """
    start_time = time.time()
    
    # Étape 1: Collecter les données environnementales (utilise le cache)
    logger.info(f"Collecte des données environnementales pour le site ({latitude}, {longitude})")
    # Formater les coordonnées au format "lat,lon" pour la fonction collect_environmental_data_from_apis
    location = f"{latitude},{longitude}"
    env_data = collect_environmental_data_from_apis(location, project_type)
    
    # Étape 2: Calculer les scores de risque avec les seuils spécifiques au pays
    logger.info(f"Calcul des scores de risque avec les seuils spécifiques à {country}")
    risk_scores = calculate_environmental_risk_score_morocco(env_data, country)
    
    # Étape 3: Ajouter des métadonnées
    risk_scores['latitude'] = latitude
    risk_scores['longitude'] = longitude
    risk_scores['project_type'] = project_type
    risk_scores['assessment_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    risk_scores['country'] = country
    
    # Étape 4: Enregistrer les résultats
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"risk_assessment_{timestamp}.xlsx")
    
    risk_scores.to_excel(output_file, index=False)
    logger.info(f"Résultats enregistrés dans {output_file}")
    
    # Afficher le temps d'exécution
    execution_time = time.time() - start_time
    logger.info(f"Évaluation des risques terminée en {execution_time:.2f} secondes")
    
    return risk_scores

def test_environmental_risk_assessment():
    """Teste l'évaluation des risques environnementaux pour plusieurs sites."""
    # Définir quelques sites de test
    test_sites = [
        {"latitude": 31.6295, "longitude": -7.9811, "project_type": "Minier", "description": "Site minier près de Marrakech"},
        {"latitude": 33.5731, "longitude": -7.5898, "project_type": "Énergétique", "description": "Site énergétique près de Casablanca"},
        {"latitude": 35.7595, "longitude": -5.8340, "project_type": "Industriel", "description": "Site industriel près de Tanger"}
    ]
    
    results = []
    
    # Exécuter l'évaluation pour chaque site
    for i, site in enumerate(test_sites):
        print(f"\n--- Évaluation du site {i+1}: {site['description']} ---")
        
        # Premier appel (miss de cache attendu)
        start_time = time.time()
        risk_scores = run_environmental_risk_assessment(
            site['latitude'], 
            site['longitude'], 
            site['project_type']
        )
        first_call_time = time.time() - start_time
        
        # Deuxième appel (hit de cache attendu)
        start_time = time.time()
        risk_scores_cached = run_environmental_risk_assessment(
            site['latitude'], 
            site['longitude'], 
            site['project_type']
        )
        second_call_time = time.time() - start_time
        
        # Vérifier que les résultats sont identiques
        results_match = risk_scores.equals(risk_scores_cached)
        
        # Calculer l'accélération
        speedup = first_call_time / second_call_time if second_call_time > 0 else float('inf')
        
        # Afficher les résultats
        print(f"Niveau de risque: {risk_scores['niveau_risque'].iloc[0]}")
        print(f"Score global: {risk_scores['score_global'].iloc[0]:.2f}/10")
        print(f"Temps d'exécution (premier appel): {first_call_time:.2f} secondes")
        print(f"Temps d'exécution (deuxième appel): {second_call_time:.2f} secondes")
        print(f"Accélération: {speedup:.2f}x")
        print(f"Résultats identiques: {results_match}")
        
        # Stocker les résultats pour le résumé
        results.append({
            "site": site['description'],
            "niveau_risque": risk_scores['niveau_risque'].iloc[0],
            "score_global": risk_scores['score_global'].iloc[0],
            "speedup": speedup
        })
    
    # Afficher un résumé
    print("\n=== Résumé des évaluations de risque ===")
    for result in results:
        print(f"{result['site']}: {result['niveau_risque']} (Score: {result['score_global']:.2f}/10, Accélération: {result['speedup']:.2f}x)")

if __name__ == "__main__":
    test_environmental_risk_assessment()