#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Visualisation des données de qualité de l'air

Ce script permet de visualiser les données de qualité de l'air sur une carte
pour plusieurs localisations et de comparer les niveaux de polluants.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
import folium
from folium.plugins import MarkerCluster
from datetime import datetime
from external_apis import ExternalAPIs
from external_apis import get_coordinates

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Définition des seuils pour chaque polluant (en µg/m³)
POLLUTANT_THRESHOLDS = {
    "PM2.5": {"good": 10, "moderate": 25, "poor": 50, "very_poor": 75, "extremely_poor": 100},
    "PM10": {"good": 20, "moderate": 50, "poor": 100, "very_poor": 150, "extremely_poor": 200},
    "NO₂": {"good": 40, "moderate": 90, "poor": 120, "very_poor": 230, "extremely_poor": 340},
    "SO₂": {"good": 20, "moderate": 80, "poor": 250, "very_poor": 350, "extremely_poor": 500},
    "O₃": {"good": 60, "moderate": 100, "poor": 140, "very_poor": 180, "extremely_poor": 240},
    "CO": {"good": 4400, "moderate": 9400, "poor": 12400, "very_poor": 15400, "extremely_poor": 30400}
}

# Couleurs pour chaque niveau de qualité de l'air
AQI_COLORS = {
    "good": "#00e400",  # Vert
    "moderate": "#ffff00",  # Jaune
    "poor": "#ff7e00",  # Orange
    "very_poor": "#ff0000",  # Rouge
    "extremely_poor": "#99004c"  # Violet
}

def get_air_quality_data(location):
    """
    Récupère les données de qualité de l'air pour une localisation donnée.
    
    Args:
        location (str): Nom de la localisation ou coordonnées (lat, lon)
        
    Returns:
        tuple: (lat, lon, data) où data est un dictionnaire contenant les données de qualité de l'air
    """
    try:
        # Récupération des coordonnées
        lat, lon = get_coordinates(location)
        if lat is None or lon is None:
            print(f"\n{'='*80}")
            print(f"ERREUR: Impossible de trouver les coordonnées pour {location}")
            print(f"{'='*80}\n")
            return None, None, None
        
        # Récupération des données de qualité de l'air
        api = ExternalAPIs()
        air_data = api.get_air_quality_data(lat, lon)
        
        if air_data is None:
            print(f"\n{'='*80}")
            print(f"ERREUR: Impossible de récupérer les données de qualité de l'air pour {location}")
            print(f"{'='*80}\n")
            return lat, lon, None
        
        return lat, lon, air_data
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"ERREUR: Une erreur s'est produite lors de la récupération des données pour {location}")
        print(f"Détail: {str(e)}")
        print(f"{'='*80}\n")
        return None, None, None

def get_pollutant_level(pollutant, value):
    """
    Détermine le niveau de qualité de l'air pour un polluant donné.
    
    Args:
        pollutant (str): Nom du polluant (PM2.5, PM10, NO₂, SO₂, O₃, CO)
        value (float): Valeur mesurée du polluant (en µg/m³)
        
    Returns:
        str: Niveau de qualité de l'air (good, moderate, poor, very_poor, extremely_poor)
    """
    thresholds = POLLUTANT_THRESHOLDS.get(pollutant, {})
    
    if not thresholds or value is None:
        return "unknown"
    
    if value <= thresholds["good"]:
        return "good"
    elif value <= thresholds["moderate"]:
        return "moderate"
    elif value <= thresholds["poor"]:
        return "poor"
    elif value <= thresholds["very_poor"]:
        return "very_poor"
    else:
        return "extremely_poor"

def create_map(locations_data):
    """
    Crée une carte interactive avec les données de qualité de l'air.
    
    Args:
        locations_data (list): Liste de tuples (location, lat, lon, data)
        
    Returns:
        folium.Map: Carte interactive
    """
    # Création de la carte
    map_center = [0, 0]
    valid_coords = [(lat, lon) for _, lat, lon, _ in locations_data if lat is not None and lon is not None]
    
    if valid_coords:
        # Calcul du centre de la carte
        map_center = [sum(lat for lat, _ in valid_coords) / len(valid_coords),
                     sum(lon for _, lon in valid_coords) / len(valid_coords)]
    
    # Création de la carte
    m = folium.Map(location=map_center, zoom_start=4, tiles="CartoDB positron")
    
    # Ajout des marqueurs
    for location, lat, lon, data in locations_data:
        if lat is None or lon is None or data is None:
            continue
        
        # Récupération des données des polluants
        pollutants = {
            "PM2.5": data.get("PM2.5 (µg/m³)"),
            "PM10": data.get("PM10 (µg/m³)"),
            "NO₂": data.get("NO₂ (µg/m³)"),
            "SO₂": data.get("SO₂ (µg/m³)"),
            "O₃": data.get("O₃ (µg/m³)"),
            "CO": data.get("CO (µg/m³)")
        }
        
        # Détermination du niveau global de qualité de l'air
        levels = [get_pollutant_level(pollutant, value) 
                 for pollutant, value in pollutants.items() 
                 if value is not None and value != "N/A" and value != "Erreur"]
        
        if not levels:
            continue
        
        # Détermination du niveau le plus mauvais
        level_order = ["good", "moderate", "poor", "very_poor", "extremely_poor"]
        worst_level = max(levels, key=lambda x: level_order.index(x) if x in level_order else -1)
        
        # Couleur du marqueur
        color = AQI_COLORS.get(worst_level, "#808080")  # Gris par défaut
        
        # Création du popup
        popup_html = f"""<div style='width: 300px'>
            <h4>{location}</h4>
            <table style='width: 100%; border-collapse: collapse;'>
                <tr style='background-color: #f2f2f2;'>
                    <th style='padding: 8px; text-align: left; border: 1px solid #ddd;'>Polluant</th>
                    <th style='padding: 8px; text-align: left; border: 1px solid #ddd;'>Valeur (µg/m³)</th>
                    <th style='padding: 8px; text-align: left; border: 1px solid #ddd;'>Niveau</th>
                </tr>"""
        
        for pollutant, value in pollutants.items():
            if value is not None and value != "N/A" and value != "Erreur":
                level = get_pollutant_level(pollutant, value)
                level_color = AQI_COLORS.get(level, "#808080")
                
                popup_html += f"""<tr>
                    <td style='padding: 8px; text-align: left; border: 1px solid #ddd;'>{pollutant}</td>
                    <td style='padding: 8px; text-align: left; border: 1px solid #ddd;'>{value}</td>
                    <td style='padding: 8px; text-align: left; border: 1px solid #ddd; background-color: {level_color};'>{level.replace('_', ' ').title()}</td>
                </tr>"""
        
        popup_html += """</table>
            </div>"""
        
        # Ajout du marqueur
        folium.CircleMarker(
            location=[lat, lon],
            radius=10,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=350)
        ).add_to(m)
    
    # Ajout de la légende
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; padding: 10px; border: 2px solid grey; border-radius: 5px;">
        <p><strong>Qualité de l'air</strong></p>
    '''
    
    for level, color in AQI_COLORS.items():
        legend_html += f'''
        <p><i class="fa fa-circle" style="color:{color}"></i> {level.replace('_', ' ').title()}</p>
        '''
    
    legend_html += '</div>'
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def create_bar_chart(locations_data, pollutant):
    """
    Crée un graphique à barres pour comparer les niveaux d'un polluant entre différentes localisations.
    
    Args:
        locations_data (list): Liste de tuples (location, lat, lon, data)
        pollutant (str): Nom du polluant à comparer
        
    Returns:
        matplotlib.figure.Figure: Figure du graphique
    """
    # Préparation des données
    locations = []
    values = []
    colors = []
    
    for location, _, _, data in locations_data:
        if data is None:
            continue
        
        # Récupération de la valeur du polluant
        value = data.get(f"{pollutant} (µg/m³)")
        
        if value is None or value == "N/A" or value == "Erreur":
            continue
        
        # Détermination du niveau de qualité de l'air
        level = get_pollutant_level(pollutant, value)
        color = AQI_COLORS.get(level, "#808080")  # Gris par défaut
        
        locations.append(location)
        values.append(value)
        colors.append(color)
    
    if not locations:
        return None
    
    # Création du graphique
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Création des barres
    bars = ax.bar(locations, values, color=colors)
    
    # Ajout des valeurs au-dessus des barres
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height + 0.1,
                f"{value:.1f}", ha='center', va='bottom')
    
    # Ajout des titres et labels
    ax.set_title(f"Comparaison des niveaux de {pollutant} entre différentes localisations", fontsize=14)
    ax.set_xlabel("Localisation", fontsize=12)
    ax.set_ylabel(f"Concentration ({pollutant}) (µg/m³)", fontsize=12)
    
    # Ajout des seuils
    thresholds = POLLUTANT_THRESHOLDS.get(pollutant, {})
    if thresholds:
        for level, threshold in thresholds.items():
            ax.axhline(y=threshold, linestyle='--', color=AQI_COLORS.get(level, "#808080"), alpha=0.7)
            ax.text(len(locations) - 0.5, threshold + 0.5, f"{level.replace('_', ' ').title()} ({threshold})", 
                    ha='right', va='bottom', color=AQI_COLORS.get(level, "#808080"))
    
    # Ajout de la légende
    legend_elements = []
    for level, color in AQI_COLORS.items():
        legend_elements.append(Patch(facecolor=color, edgecolor='black',
                                    label=level.replace('_', ' ').title()))
    
    ax.legend(handles=legend_elements, loc='upper right')
    
    # Ajustement de la mise en page
    plt.tight_layout()
    
    return fig

def main():
    """
    Fonction principale du script.
    """
    print("\nVisualisation des données de qualité de l'air\n")
    print("Ce script permet de visualiser les données de qualité de l'air sur une carte")
    print("pour plusieurs localisations et de comparer les niveaux de polluants.\n")
    
    # Demander les localisations à l'utilisateur
    locations_input = input("Entrez les localisations séparées par des virgules (ville, région, coordonnées, etc.): ")
    
    # Normaliser l'entrée pour gérer les formats de coordonnées français et anglais
    # Remplacer les virgules utilisées comme séparateurs décimaux par des points
    normalized_input = locations_input
    
    # Détecter et traiter les coordonnées au format français (27,94, -12,91)
    import re
    # Rechercher des motifs comme "nombre,nombre, nombre,nombre" ou "nombre.nombre, nombre.nombre"
    coord_pattern = re.compile(r'(\d+[,.]\d+)\s*,\s*(-?\d+[,.]\d+)')
    match = coord_pattern.search(locations_input)
    
    if match:
        # Extraire les coordonnées potentielles
        lat_str = match.group(1).replace(',', '.')
        lon_str = match.group(2).replace(',', '.')
        
        try:
            lat = float(lat_str)
            lon = float(lon_str)
            
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                # C'est une paire de coordonnées valide
                print(f"\nCoordonnées détectées: {lat}, {lon}")
                locations = [f"{lat},{lon}"]
            else:
                print(f"\nCoordonnées hors limites: {lat}, {lon}")
                # Traiter comme des localisations séparées
                locations = [loc.strip() for loc in locations_input.split(",") if loc.strip()]
        except ValueError:
            print(f"\nImpossible de convertir en coordonnées valides")
            # Si la conversion en float échoue, traiter comme des localisations séparées
            locations = [loc.strip() for loc in locations_input.split(",") if loc.strip()]
    else:
        # Traiter comme des localisations séparées
        locations = [loc.strip() for loc in locations_input.split(",") if loc.strip()]
    
    if not locations:
        print("\nAucune localisation valide n'a été fournie.")
        return
    
    # Récupération des données pour chaque localisation
    locations_data = []
    for location in locations:
        print(f"\nRécupération des données pour {location}...")
        lat, lon, data = get_air_quality_data(location)
        locations_data.append((location, lat, lon, data))
    
    # Vérification des données
    valid_data = [(loc, lat, lon, data) for loc, lat, lon, data in locations_data if data is not None]
    
    if not valid_data:
        print("\nAucune donnée valide n'a été récupérée pour les localisations fournies.")
        return
    
    # Création de la carte
    print("\nCréation de la carte...")
    m = create_map(locations_data)
    
    # Sauvegarde de la carte
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    map_filename = f"air_quality_map_{timestamp}.html"
    m.save(map_filename)
    print(f"\nCarte enregistrée dans {os.path.abspath(map_filename)}")
    
    # Création des graphiques pour chaque polluant
    pollutants = ["PM2.5", "PM10", "NO₂", "SO₂", "O₃", "CO"]
    
    for pollutant in pollutants:
        print(f"\nCréation du graphique pour {pollutant}...")
        fig = create_bar_chart(locations_data, pollutant)
        
        if fig is not None:
            # Sauvegarde du graphique
            chart_filename = f"air_quality_{pollutant}_{timestamp}.png"
            fig.savefig(chart_filename, dpi=300, bbox_inches='tight')
            print(f"Graphique enregistré dans {os.path.abspath(chart_filename)}")
    
    print("\nVisualisation terminée.")

if __name__ == "__main__":
    main()