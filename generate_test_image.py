#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Génération d'une image de test avec du texte pour tester le modèle dots.ocr.

Ce script génère une image contenant du texte et un tableau simple pour tester
les capacités d'OCR du modèle dots.ocr.

Usage:
    python generate_test_image.py [--output <chemin_sortie>] [--type <type_image>]

Exemple:
    python generate_test_image.py
    python generate_test_image.py --output ./test_images/test_tableau.png
    python generate_test_image.py --type tableau
"""

import argparse
import os
import sys
import logging
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_text_image(output_path=None):
    """
    Crée une image contenant du texte en français.
    
    Args:
        output_path (str, optional): Chemin de sortie pour l'image
        
    Returns:
        str: Chemin de l'image générée
    """
    # Détermination du chemin de sortie
    if output_path is None:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_images")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"test_texte_{timestamp}.png")
    
    # Création du répertoire parent si nécessaire
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Création de l'image
    width, height = 1000, 800
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # Chargement de la police
    try:
        font_path = os.path.join(os.environ.get('WINDIR', ''), 'Fonts', 'Arial.ttf')
        title_font = ImageFont.truetype(font_path, 36)
        subtitle_font = ImageFont.truetype(font_path, 24)
        body_font = ImageFont.truetype(font_path, 16)
    except IOError:
        # Utilisation d'une police par défaut si Arial n'est pas disponible
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
    
    # Ajout du titre
    title = "Rapport d'Analyse Environnementale"
    title_width = draw.textlength(title, font=title_font)
    draw.text(((width - title_width) / 2, 50), title, font=title_font, fill=(0, 0, 0))
    
    # Ajout du sous-titre
    subtitle = "Évaluation des Risques et Recommandations"
    subtitle_width = draw.textlength(subtitle, font=subtitle_font)
    draw.text(((width - subtitle_width) / 2, 100), subtitle, font=subtitle_font, fill=(0, 0, 0))
    
    # Ajout de la date
    date = f"Date: {datetime.now().strftime('%d/%m/%Y')}"
    draw.text((50, 150), date, font=body_font, fill=(0, 0, 0))
    
    # Ajout du contenu principal
    content = [
        "1. Introduction",
        "Ce rapport présente les résultats de l'analyse environnementale réalisée sur le site industriel XYZ. ",
        "L'objectif est d'identifier les risques potentiels et de proposer des mesures d'atténuation appropriées.",
        "",
        "2. Méthodologie",
        "L'analyse a été effectuée selon les normes ISO 14001 et inclut les étapes suivantes :",
        "  • Identification des aspects environnementaux",
        "  • Évaluation des impacts potentiels",
        "  • Détermination des mesures de contrôle",
        "  • Élaboration d'un plan d'action",
        "",
        "3. Résultats Principaux",
        "L'analyse a révélé plusieurs domaines nécessitant une attention particulière :",
        "  • Émissions atmosphériques dépassant les seuils réglementaires de 15%",
        "  • Consommation d'eau excessive (25 000 m³/mois)",
        "  • Gestion inadéquate des déchets dangereux (accumulation de 3,5 tonnes)",
        "",
        "4. Recommandations",
        "Sur la base des résultats, nous recommandons les actions suivantes :",
        "  • Installation de filtres à particules sur les cheminées principales",
        "  • Mise en place d'un système de recyclage des eaux usées",
        "  • Formation du personnel à la gestion des déchets dangereux",
        "  • Audit mensuel des pratiques environnementales"
    ]
    
    y_position = 200
    for line in content:
        if line.startswith("1.") or line.startswith("2.") or line.startswith("3.") or line.startswith("4."):
            # Titre de section
            draw.text((50, y_position), line, font=subtitle_font, fill=(0, 0, 100))
            y_position += 30
        elif line.strip() == "":
            # Ligne vide
            y_position += 20
        else:
            # Texte normal
            draw.text((50, y_position), line, font=body_font, fill=(0, 0, 0))
            y_position += 25
    
    # Ajout du pied de page
    footer = "Confidentiel - Usage Interne Uniquement"
    footer_width = draw.textlength(footer, font=body_font)
    draw.text(((width - footer_width) / 2, height - 50), footer, font=body_font, fill=(100, 100, 100))
    
    # Sauvegarde de l'image
    image.save(output_path)
    logger.info(f"Image de texte générée avec succès: {output_path}")
    
    return output_path


def create_table_image(output_path=None):
    """
    Crée une image contenant un tableau environnemental.
    
    Args:
        output_path (str, optional): Chemin de sortie pour l'image
        
    Returns:
        str: Chemin de l'image générée
    """
    # Détermination du chemin de sortie
    if output_path is None:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_images")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"test_tableau_{timestamp}.png")
    
    # Création du répertoire parent si nécessaire
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Création de l'image
    width, height = 1000, 800
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # Chargement de la police
    try:
        font_path = os.path.join(os.environ.get('WINDIR', ''), 'Fonts', 'Arial.ttf')
        title_font = ImageFont.truetype(font_path, 36)
        header_font = ImageFont.truetype(font_path, 18)
        body_font = ImageFont.truetype(font_path, 16)
    except IOError:
        # Utilisation d'une police par défaut si Arial n'est pas disponible
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
    
    # Ajout du titre
    title = "Tableau des Indicateurs Environnementaux"
    title_width = draw.textlength(title, font=title_font)
    draw.text(((width - title_width) / 2, 50), title, font=title_font, fill=(0, 0, 0))
    
    # Définition du tableau
    table_top = 150
    table_left = 50
    table_right = width - 50
    cell_height = 40
    
    # Définition des colonnes
    columns = [
        "Indicateur",
        "Valeur Mesurée",
        "Seuil Réglementaire",
        "Écart (%)",
        "Niveau de Risque"
    ]
    column_widths = [(table_right - table_left) / len(columns)] * len(columns)
    
    # Définition des données
    data = [
        ["Émissions CO2 (tonnes/an)", "1250", "1000", "+25%", "Élevé"],
        ["Consommation d'eau (m³/mois)", "25000", "20000", "+25%", "Moyen"],
        ["Déchets dangereux (tonnes)", "3.5", "2.0", "+75%", "Critique"],
        ["Niveau sonore (dB)", "68", "70", "-3%", "Faible"],
        ["Effluents liquides (pH)", "8.2", "6.5-8.5", "0%", "Acceptable"],
        ["Particules fines (µg/m³)", "45", "40", "+13%", "Moyen"],
        ["Consommation électrique (MWh)", "350", "400", "-13%", "Faible"],
        ["Fuites d'hydrocarbures (litres)", "0", "0", "0%", "Acceptable"]
    ]
    
    # Dessin de l'en-tête du tableau
    current_top = table_top
    current_left = table_left
    
    # Fond de l'en-tête
    draw.rectangle(
        [(table_left, current_top), (table_right, current_top + cell_height)],
        fill=(200, 220, 240)
    )
    
    # Texte de l'en-tête
    for i, column in enumerate(columns):
        cell_left = current_left
        cell_right = cell_left + column_widths[i]
        
        # Bordure de la cellule
        draw.rectangle(
            [(cell_left, current_top), (cell_right, current_top + cell_height)],
            outline=(0, 0, 0)
        )
        
        # Texte centré dans la cellule
        text_width = draw.textlength(column, font=header_font)
        text_x = cell_left + (column_widths[i] - text_width) / 2
        text_y = current_top + (cell_height - header_font.size) / 2
        draw.text((text_x, text_y), column, font=header_font, fill=(0, 0, 0))
        
        current_left = cell_right
    
    # Dessin des données du tableau
    for row_idx, row in enumerate(data):
        current_top = table_top + (row_idx + 1) * cell_height
        current_left = table_left
        
        # Fond alterné pour les lignes
        if row_idx % 2 == 0:
            draw.rectangle(
                [(table_left, current_top), (table_right, current_top + cell_height)],
                fill=(240, 240, 240)
            )
        
        # Coloration des cellules de risque
        risk_level = row[4]
        risk_color = (255, 255, 255)  # Blanc par défaut
        if risk_level == "Critique":
            risk_color = (255, 200, 200)  # Rouge clair
        elif risk_level == "Élevé":
            risk_color = (255, 230, 200)  # Orange clair
        elif risk_level == "Moyen":
            risk_color = (255, 255, 200)  # Jaune clair
        
        # Texte des cellules
        for i, cell in enumerate(row):
            cell_left = current_left
            cell_right = cell_left + column_widths[i]
            
            # Coloration spéciale pour la cellule de risque
            if i == 4:  # Colonne "Niveau de Risque"
                draw.rectangle(
                    [(cell_left, current_top), (cell_right, current_top + cell_height)],
                    fill=risk_color
                )
            
            # Bordure de la cellule
            draw.rectangle(
                [(cell_left, current_top), (cell_right, current_top + cell_height)],
                outline=(0, 0, 0)
            )
            
            # Alignement du texte selon le type de colonne
            if i == 0:  # Première colonne (Indicateur) - alignée à gauche
                text_x = cell_left + 10
            elif i in [1, 2]:  # Colonnes numériques - alignées à droite
                text_width = draw.textlength(cell, font=body_font)
                text_x = cell_right - text_width - 10
            else:  # Autres colonnes - centrées
                text_width = draw.textlength(cell, font=body_font)
                text_x = cell_left + (column_widths[i] - text_width) / 2
            
            text_y = current_top + (cell_height - body_font.size) / 2
            draw.text((text_x, text_y), cell, font=body_font, fill=(0, 0, 0))
            
            current_left = cell_right
    
    # Ajout d'une légende
    legend_top = table_top + (len(data) + 1) * cell_height + 30
    draw.text((table_left, legend_top), "Légende des niveaux de risque:", font=header_font, fill=(0, 0, 0))
    
    legend_items = [
        ("Critique", (255, 200, 200)),
        ("Élevé", (255, 230, 200)),
        ("Moyen", (255, 255, 200)),
        ("Faible", (240, 240, 240)),
        ("Acceptable", (255, 255, 255))
    ]
    
    for i, (text, color) in enumerate(legend_items):
        item_left = table_left + i * 150
        item_top = legend_top + 30
        
        # Carré de couleur
        draw.rectangle(
            [(item_left, item_top), (item_left + 20, item_top + 20)],
            fill=color,
            outline=(0, 0, 0)
        )
        
        # Texte
        draw.text((item_left + 30, item_top), text, font=body_font, fill=(0, 0, 0))
    
    # Ajout du pied de page
    footer = "Données collectées le " + datetime.now().strftime("%d/%m/%Y")
    footer_width = draw.textlength(footer, font=body_font)
    draw.text(((width - footer_width) / 2, height - 50), footer, font=body_font, fill=(100, 100, 100))
    
    # Sauvegarde de l'image
    image.save(output_path)
    logger.info(f"Image de tableau générée avec succès: {output_path}")
    
    return output_path


def create_mixed_image(output_path=None):
    """
    Crée une image contenant à la fois du texte et un tableau.
    
    Args:
        output_path (str, optional): Chemin de sortie pour l'image
        
    Returns:
        str: Chemin de l'image générée
    """
    # Détermination du chemin de sortie
    if output_path is None:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_images")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"test_mixte_{timestamp}.png")
    
    # Création du répertoire parent si nécessaire
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Création de l'image
    width, height = 1000, 1200
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # Chargement de la police
    try:
        font_path = os.path.join(os.environ.get('WINDIR', ''), 'Fonts', 'Arial.ttf')
        title_font = ImageFont.truetype(font_path, 36)
        subtitle_font = ImageFont.truetype(font_path, 24)
        header_font = ImageFont.truetype(font_path, 18)
        body_font = ImageFont.truetype(font_path, 16)
    except IOError:
        # Utilisation d'une police par défaut si Arial n'est pas disponible
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
    
    # Ajout du titre
    title = "Rapport d'Analyse des Risques Environnementaux"
    title_width = draw.textlength(title, font=title_font)
    draw.text(((width - title_width) / 2, 50), title, font=title_font, fill=(0, 0, 0))
    
    # Ajout du sous-titre
    subtitle = "Site Industriel XYZ - Maroc"
    subtitle_width = draw.textlength(subtitle, font=subtitle_font)
    draw.text(((width - subtitle_width) / 2, 100), subtitle, font=subtitle_font, fill=(0, 0, 0))
    
    # Ajout de la date
    date = f"Date: {datetime.now().strftime('%d/%m/%Y')}"
    draw.text((50, 150), date, font=body_font, fill=(0, 0, 0))
    
    # Ajout du contenu principal
    content = [
        "1. Résumé Exécutif",
        "Cette analyse identifie plusieurs risques environnementaux significatifs sur le site industriel XYZ. ",
        "Les émissions de CO2 et la gestion des déchets dangereux représentent les problèmes les plus critiques ",
        "nécessitant une intervention immédiate. Le tableau ci-dessous présente les principaux indicateurs."
    ]
    
    y_position = 200
    for line in content:
        if line.startswith("1."):
            # Titre de section
            draw.text((50, y_position), line, font=subtitle_font, fill=(0, 0, 100))
            y_position += 40
        else:
            # Texte normal
            draw.text((50, y_position), line, font=body_font, fill=(0, 0, 0))
            y_position += 25
    
    # Définition du tableau
    table_top = y_position + 30
    table_left = 50
    table_right = width - 50
    cell_height = 40
    
    # Définition des colonnes
    columns = [
        "Indicateur",
        "Valeur Mesurée",
        "Seuil Réglementaire",
        "Écart (%)",
        "Niveau de Risque"
    ]
    column_widths = [(table_right - table_left) / len(columns)] * len(columns)
    
    # Définition des données
    data = [
        ["Émissions CO2 (tonnes/an)", "1250", "1000", "+25%", "Élevé"],
        ["Déchets dangereux (tonnes)", "3.5", "2.0", "+75%", "Critique"],
        ["Consommation d'eau (m³/mois)", "25000", "20000", "+25%", "Moyen"],
        ["Particules fines (µg/m³)", "45", "40", "+13%", "Moyen"]
    ]
    
    # Dessin de l'en-tête du tableau
    current_top = table_top
    current_left = table_left
    
    # Fond de l'en-tête
    draw.rectangle(
        [(table_left, current_top), (table_right, current_top + cell_height)],
        fill=(200, 220, 240)
    )
    
    # Texte de l'en-tête
    for i, column in enumerate(columns):
        cell_left = current_left
        cell_right = cell_left + column_widths[i]
        
        # Bordure de la cellule
        draw.rectangle(
            [(cell_left, current_top), (cell_right, current_top + cell_height)],
            outline=(0, 0, 0)
        )
        
        # Texte centré dans la cellule
        text_width = draw.textlength(column, font=header_font)
        text_x = cell_left + (column_widths[i] - text_width) / 2
        text_y = current_top + (cell_height - header_font.size) / 2
        draw.text((text_x, text_y), column, font=header_font, fill=(0, 0, 0))
        
        current_left = cell_right
    
    # Dessin des données du tableau
    for row_idx, row in enumerate(data):
        current_top = table_top + (row_idx + 1) * cell_height
        current_left = table_left
        
        # Fond alterné pour les lignes
        if row_idx % 2 == 0:
            draw.rectangle(
                [(table_left, current_top), (table_right, current_top + cell_height)],
                fill=(240, 240, 240)
            )
        
        # Coloration des cellules de risque
        risk_level = row[4]
        risk_color = (255, 255, 255)  # Blanc par défaut
        if risk_level == "Critique":
            risk_color = (255, 200, 200)  # Rouge clair
        elif risk_level == "Élevé":
            risk_color = (255, 230, 200)  # Orange clair
        elif risk_level == "Moyen":
            risk_color = (255, 255, 200)  # Jaune clair
        
        # Texte des cellules
        for i, cell in enumerate(row):
            cell_left = current_left
            cell_right = cell_left + column_widths[i]
            
            # Coloration spéciale pour la cellule de risque
            if i == 4:  # Colonne "Niveau de Risque"
                draw.rectangle(
                    [(cell_left, current_top), (cell_right, current_top + cell_height)],
                    fill=risk_color
                )
            
            # Bordure de la cellule
            draw.rectangle(
                [(cell_left, current_top), (cell_right, current_top + cell_height)],
                outline=(0, 0, 0)
            )
            
            # Alignement du texte selon le type de colonne
            if i == 0:  # Première colonne (Indicateur) - alignée à gauche
                text_x = cell_left + 10
            elif i in [1, 2]:  # Colonnes numériques - alignées à droite
                text_width = draw.textlength(cell, font=body_font)
                text_x = cell_right - text_width - 10
            else:  # Autres colonnes - centrées
                text_width = draw.textlength(cell, font=body_font)
                text_x = cell_left + (column_widths[i] - text_width) / 2
            
            text_y = current_top + (cell_height - body_font.size) / 2
            draw.text((text_x, text_y), cell, font=body_font, fill=(0, 0, 0))
            
            current_left = cell_right
    
    # Ajout du contenu après le tableau
    y_position = table_top + (len(data) + 1) * cell_height + 50
    
    content_after = [
        "2. Recommandations",
        "Sur la base des résultats de l'analyse, nous recommandons les actions suivantes :",
        "",
        "2.1. Actions Immédiates (0-3 mois)",
        "• Installation de filtres à particules sur les cheminées principales",
        "• Mise en place d'un système de recyclage des eaux usées",
        "• Formation du personnel à la gestion des déchets dangereux",
        "",
        "2.2. Actions à Moyen Terme (3-12 mois)",
        "• Audit complet du système de gestion environnementale",
        "• Développement d'un plan de réduction des émissions de CO2",
        "• Modernisation des équipements les plus énergivores",
        "",
        "2.3. Suivi et Évaluation",
        "• Mise en place d'un tableau de bord mensuel des indicateurs environnementaux",
        "• Révision trimestrielle du plan d'action",
        "• Rapport annuel de performance environnementale"
    ]
    
    for line in content_after:
        if line.startswith("2.") and not line.startswith("2.1") and not line.startswith("2.2") and not line.startswith("2.3"):
            # Titre de section principal
            draw.text((50, y_position), line, font=subtitle_font, fill=(0, 0, 100))
            y_position += 40
        elif line.startswith("2.1") or line.startswith("2.2") or line.startswith("2.3"):
            # Sous-titre
            draw.text((50, y_position), line, font=header_font, fill=(0, 0, 100))
            y_position += 30
        elif line.strip() == "":
            # Ligne vide
            y_position += 20
        else:
            # Texte normal
            draw.text((50, y_position), line, font=body_font, fill=(0, 0, 0))
            y_position += 25
    
    # Ajout du pied de page
    footer = "Confidentiel - Usage Interne Uniquement"
    footer_width = draw.textlength(footer, font=body_font)
    draw.text(((width - footer_width) / 2, height - 50), footer, font=body_font, fill=(100, 100, 100))
    
    # Sauvegarde de l'image
    image.save(output_path)
    logger.info(f"Image mixte générée avec succès: {output_path}")
    
    return output_path


def main():
    # Analyse des arguments de la ligne de commande
    parser = argparse.ArgumentParser(description="Génération d'images de test pour le modèle dots.ocr")
    parser.add_argument("--output", help="Chemin de sortie pour l'image générée")
    parser.add_argument("--type", choices=["texte", "tableau", "mixte"], default="mixte",
                        help="Type d'image à générer (texte, tableau ou mixte)")
    
    args = parser.parse_args()
    
    # Génération de l'image selon le type demandé
    if args.type == "texte":
        output_path = create_text_image(args.output)
    elif args.type == "tableau":
        output_path = create_table_image(args.output)
    else:  # mixte
        output_path = create_mixed_image(args.output)
    
    print(f"\nImage générée: {output_path}")
    print("Vous pouvez maintenant tester le modèle dots.ocr avec cette image:")
    print(f"python test_dots_ocr.py --image {output_path}")


if __name__ == "__main__":
    main()