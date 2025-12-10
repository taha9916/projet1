#!/usr/bin/env python3
"""
Script de debug pour tester l'API World Bank directement.
"""

import logging
import requests
from external_apis import ExternalAPIs

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_worldbank_direct():
    """Test direct de l'API World Bank."""
    
    print("=== Test direct API World Bank ===\n")
    
    # Test 1: Requête manuelle à l'API World Bank
    print("1. Test requête manuelle:")
    
    try:
        url = "https://api.worldbank.org/v2/country/MA/indicator/ER.H2O.FWRN.PC.K3?format=json"
        print(f"URL: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Réponse: {data[:2] if isinstance(data, list) else data}")
            
            if isinstance(data, list) and len(data) > 1:
                records = data[1]
                if records:
                    latest = records[0]
                    print(f"Dernière donnée: {latest}")
                else:
                    print("Aucun enregistrement trouvé")
        else:
            print(f"Erreur: {response.text}")
            
    except Exception as e:
        print(f"Erreur requête manuelle: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Via la classe ExternalAPIs
    print("2. Test via ExternalAPIs:")
    
    try:
        api = ExternalAPIs()
        
        # Vérifier la configuration
        wb_config = api.config.get("worldbank", {})
        print(f"Config World Bank: {wb_config}")
        
        # Test avec un seul indicateur
        indicators = ["ER.H2O.FWRN.PC.K3"]
        result = api.get_worldbank_data(indicators)
        
        print(f"Résultat get_worldbank_data: {result}")
        
    except Exception as e:
        print(f"Erreur via ExternalAPIs: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Test du fallback complet
    print("3. Test fallback complet:")
    
    try:
        api = ExternalAPIs()
        result = api.get_water_data_fallback()
        print(f"Résultat fallback: {result}")
        
    except Exception as e:
        print(f"Erreur fallback: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_worldbank_direct()
