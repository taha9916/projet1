#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ajouter les polluants individuels dans le DataFrame

Ce script montre comment ajouter les polluants individuels (PM2.5, PM10, NO₂, SO₂, CO, O₃)
dans un DataFrame pour identifier la source du problème de pollution.
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer les modules nécessaires
from external_apis import ExternalAPIs, get_coordinates

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_pollutants_to_dataframe(location):
    """
    Ajoute les polluants individuels dans un DataFrame pour une localisation donnée.
    
    Args:
        location (str): Nom de la localisation (ville, région, etc.)
        
    Returns:
        pandas.DataFrame: DataFrame contenant les données des polluants
    """
    # Initialiser l'objet ExternalAPIs
    apis = ExternalAPIs()
    
    # Récupérer les coordonnées géographiques
    lat, lon = get_coordinates(location)
    
    if lat is None or lon is None:
        # Utiliser print au lieu de logger pour s'assurer que les messages s'affichent correctement
        print(f"\n{'='*80}")
        print(f"ERREUR: Impossible de trouver les coordonnées pour {location}")
        print(f"\nRésolution du problème:")
        print(f"1. Vérifiez que le nom de la localisation est correct")
        print(f"2. Essayez d'utiliser un format de coordonnées (latitude, longitude)")
        print(f"3. Essayez d'utiliser un nom de ville plus connu")
        print(f"{'='*80}\n")
        return None
    
    # Récupérer les données de qualité de l'air
    try:
        air_data = apis.get_air_quality_data(lat, lon)
        
        if air_data is None:
            # Utiliser print au lieu de logger pour s'assurer que les messages s'affichent correctement
            print(f"\n{'='*80}")
            print(f"ERREUR: Impossible de récupérer les données de qualité de l'air pour {location}")
            print(f"\nRésolution du problème:")
            print(f"1. Vérifiez que votre clé API OpenWeatherMap est valide dans le fichier external_api_config.json")
            print(f"2. Vérifiez que le service OpenWeatherMap est disponible")
            print(f"3. Essayez avec une autre localisation")
            print(f"{'='*80}\n")
            return None
    except Exception as e:
        # Utiliser print au lieu de logger pour s'assurer que les messages s'affichent correctement
        print(f"\n{'='*80}")
        print(f"ERREUR: Impossible de récupérer les données de qualité de l'air")
        print(f"Détail: {str(e)}")
        print(f"\nRésolution du problème:")
        print(f"1. Vérifiez que votre clé API OpenWeatherMap est valide dans le fichier external_api_config.json")
        print(f"2. Vous pouvez obtenir une clé API gratuite sur https://openweathermap.org/api")
        print(f"3. Après avoir obtenu une nouvelle clé, remplacez-la dans le fichier external_api_config.json")
        print(f"4. Note: Les nouvelles clés API peuvent prendre jusqu'à 2 heures pour être activées")
        print(f"{'='*80}\n")
        return None
    
    # Créer un DataFrame vide
    df = pd.DataFrame(columns=["Milieu", "Paramètre", "Unité", "Valeur mesurée", "Résultat conformité", "Score"])
    
    # Définir des seuils pour chaque polluant (à adapter selon les normes)
    seuils = {
        "PM2.5": 25,  # µg/m³, seuil OMS
        "PM10": 50,   # µg/m³, seuil OMS
        "NO₂": 40,    # µg/m³, seuil OMS
        "SO₂": 20,    # µg/m³, seuil OMS
        "O₃": 100,    # µg/m³, seuil OMS
        "CO": 4000    # µg/m³, seuil approximatif
    }
    
    # Extraire les données des polluants individuels
    pollutants_data = {}
    for key, value in air_data.items():
        if key in ["PM2.5", "PM10", "NO₂", "SO₂", "CO", "O₃"]:
            pollutants_data[key] = value
    
    # Ajouter chaque polluant au DataFrame
    for pollutant, (value, unit) in pollutants_data.items():
        # Vérifier si la valeur est un nombre
        if isinstance(value, (int, float)):
            # Déterminer le seuil pour ce polluant
            seuil = seuils.get(pollutant, 100)
            
            # Ajouter au DataFrame
            new_row = {
                "Milieu": "Air",
                "Paramètre": pollutant,
                "Unité": unit,
                "Valeur mesurée": value,
                "Résultat conformité": "Conforme" if value < seuil else "Non conforme",
                "Score": 100 if value < seuil else int(40 + (60 * (1 - min(value / seuil, 2) / 2)))
            }
                
            # Ajouter la ligne au DataFrame
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    
    return df

def main():
    """
    Fonction principale du script.
    """
    # Demander la localisation à l'utilisateur
    location = input("Entrez une localisation (ville, région, etc.): ")
    
    # Récupérer les données des polluants
    df = add_pollutants_to_dataframe(location)
    
    if df is not None and not df.empty:
        # Afficher les résultats
        print("\nDonnées des polluants:")
        print(df.to_string(index=False))
        
        # Enregistrer les résultats dans un fichier Excel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 f"pollutants_data_{location.replace(' ', '_')}_{timestamp}.xlsx")
        
        df.to_excel(output_file, index=False)
        print(f"\nLes résultats ont été enregistrés dans {output_file}")
        
        # Identifier les polluants problématiques
        problematic = df[df["Résultat conformité"] == "Non conforme"]
        if not problematic.empty:
            print("\nPolluants problématiques:")
            print(problematic.to_string(index=False))
            print("\nSources possibles de pollution:")
            
            # Identifier les sources possibles de pollution
            for _, row in problematic.iterrows():
                pollutant = row["Paramètre"]
                if pollutant == "PM2.5":
                    print(f"- {pollutant} élevé: Trafic routier, combustion industrielle, chauffage au bois")
                elif pollutant == "PM10":
                    print(f"- {pollutant} élevé: Poussières, construction, agriculture, industries")
                elif pollutant == "NO₂":
                    print(f"- {pollutant} élevé: Trafic routier, centrales électriques, industries")
                elif pollutant == "SO₂":
                    print(f"- {pollutant} élevé: Industries, centrales électriques, combustion de combustibles fossiles")
                elif pollutant == "O₃":
                    print(f"- {pollutant} élevé: Réaction photochimique (NOx + COV + lumière solaire), trafic routier")
                elif pollutant == "CO":
                    print(f"- {pollutant} élevé: Combustion incomplète, trafic routier, chauffage")
        else:
            print("\nAucun polluant problématique détecté.")
    else:
        # Message d'erreur déjà affiché par add_pollutants_to_dataframe
        pass

if __name__ == "__main__":
    main()