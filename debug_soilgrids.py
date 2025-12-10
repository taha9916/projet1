#!/usr/bin/env python3
"""
Script de débogage pour SoilGrids API
"""
import requests
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_soilgrids_direct():
    """Test direct de l'API SoilGrids"""
    url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    params = {
        "lon": -6.8416,
        "lat": 34.0209,
        "property": ["phh2o", "clay", "sand", "soc", "bdod"],
        "depth": "0-5cm",
        "value": "mean"
    }
    
    print("=== Test direct SoilGrids API ===")
    print(f"URL: {url}")
    print(f"Paramètres: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n=== Structure JSON complète ===")
            print(json.dumps(data, indent=2))
            
            print("\n=== Analyse des données ===")
            if "properties" in data:
                print("✓ Clé 'properties' trouvée")
                if "layers" in data["properties"]:
                    layers = data["properties"]["layers"]
                    print(f"✓ {len(layers)} couches trouvées")
                    
                    for i, layer in enumerate(layers):
                        print(f"\n--- Couche {i+1} ---")
                        print(f"Nom: {layer.get('name', 'N/A')}")
                        if "depths" in layer and len(layer["depths"]) > 0:
                            depth = layer["depths"][0]
                            print(f"Profondeur: {depth.get('label', 'N/A')}")
                            if "values" in depth:
                                values = depth["values"]
                                print(f"Valeurs: {values}")
                                mean_val = values.get("mean")
                                print(f"Moyenne: {mean_val}")
                        else:
                            print("Pas de données de profondeur")
                else:
                    print("❌ Clé 'layers' non trouvée dans 'properties'")
            else:
                print("❌ Clé 'properties' non trouvée")
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(f"Réponse: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_soilgrids_direct()
