#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comparaison détaillée des performances du modèle dots.ocr avec les autres modèles disponibles.

Ce script effectue une comparaison approfondie des performances du modèle dots.ocr
avec les autres modèles d'OCR disponibles dans le projet. Il génère un rapport détaillé
avec des métriques de performance, des exemples de résultats et des recommandations.

Usage:
    python compare_ocr_models_detailed.py [--image <chemin_image>] [--providers <liste_fournisseurs>] [--output <chemin_sortie>]

Exemple:
    python compare_ocr_models_detailed.py
    python compare_ocr_models_detailed.py --image ./test_images/test_tableau.png
    python compare_ocr_models_detailed.py --providers dots_ocr,openai,google
"""

import argparse
import os
import sys
import json
import logging
import time
import re
import csv
import shutil
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import torch

# Import des modules du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cloud_api import CloudVisionAPI, analyze_environmental_image_cloud
from utils import extract_markdown_tables

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_api_config():
    """
    Charge la configuration des API depuis le fichier cloud_api_config.json.
    
    Returns:
        dict: Configuration des API
    """
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloud_api_config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration des API: {e}")
        return {}


def get_available_providers():
    """
    Récupère la liste des fournisseurs d'API disponibles dans la configuration.
    
    Returns:
        list: Liste des fournisseurs d'API disponibles
    """
    config = load_api_config()
    providers = list(config.keys())
    
    # Filtrer les fournisseurs non valides
    valid_providers = []
    for provider in providers:
        if provider in ["openai", "azure", "google", "qwen", "openrouter", "dots_ocr", "smolvlm", "moondream"]:
            valid_providers.append(provider)
    
    return valid_providers


def count_words(text):
    """
    Compte le nombre de mots dans un texte.
    
    Args:
        text (str): Texte à analyser
        
    Returns:
        int: Nombre de mots
    """
    if not text:
        return 0
    return len(re.findall(r'\w+', text))


def count_numbers(text):
    """
    Compte le nombre de nombres dans un texte.
    
    Args:
        text (str): Texte à analyser
        
    Returns:
        int: Nombre de nombres
    """
    if not text:
        return 0
    return len(re.findall(r'\b\d+[\d.,]*\b', text))


def count_special_chars(text):
    """
    Compte le nombre de caractères spéciaux dans un texte.
    
    Args:
        text (str): Texte à analyser
        
    Returns:
        int: Nombre de caractères spéciaux
    """
    if not text:
        return 0
    return len(re.findall(r'[^\w\s]', text))


def analyze_image_with_provider(image_path, provider, prompt=None):
    """
    Analyse une image avec un fournisseur d'API spécifique.
    
    Args:
        image_path (str): Chemin de l'image à analyser
        provider (str): Fournisseur d'API à utiliser
        prompt (str, optional): Prompt à utiliser pour l'analyse
        
    Returns:
        tuple: (résultat, temps d'exécution, erreur)
    """
    if not prompt:
        prompt = "Extrais tout le texte de cette image, y compris les tableaux. Pour les tableaux, formate-les en Markdown."
    
    start_time = time.time()
    result = ""
    error = None
    
    try:
        # Utilisation de l'API Cloud Vision
        cloud_api = CloudVisionAPI(api_provider=provider)
        result = cloud_api.analyze_image(image_path=image_path, prompt=prompt)
        
        # Libération de la mémoire pour dots.ocr
        if provider == "dots_ocr" and hasattr(cloud_api, "model"):
            del cloud_api.model
            del cloud_api.processor
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    except Exception as e:
        error = str(e)
        logger.error(f"Erreur lors de l'analyse avec {provider}: {e}")
    
    execution_time = time.time() - start_time
    
    return result, execution_time, error


def analyze_image_with_all_providers(image_path, providers, prompt=None):
    """
    Analyse une image avec tous les fournisseurs d'API spécifiés.
    
    Args:
        image_path (str): Chemin de l'image à analyser
        providers (list): Liste des fournisseurs d'API à utiliser
        prompt (str, optional): Prompt à utiliser pour l'analyse
        
    Returns:
        dict: Résultats pour chaque fournisseur
    """
    results = {}
    
    for provider in providers:
        logger.info(f"Analyse de l'image avec {provider}...")
        result, execution_time, error = analyze_image_with_provider(image_path, provider, prompt)
        
        # Extraction des tableaux Markdown
        tables = []
        if result and not error:
            tables = extract_markdown_tables(result)
        
        # Calcul des métriques
        word_count = count_words(result)
        number_count = count_numbers(result)
        special_char_count = count_special_chars(result)
        
        results[provider] = {
            "result": result,
            "execution_time": execution_time,
            "error": error,
            "tables": tables,
            "table_count": len(tables),
            "word_count": word_count,
            "number_count": number_count,
            "special_char_count": special_char_count,
            "result_length": len(result) if result else 0
        }
    
    return results


def save_results_to_csv(results, output_dir):
    """
    Sauvegarde les résultats dans un fichier CSV.
    
    Args:
        results (dict): Résultats de l'analyse
        output_dir (str): Répertoire de sortie
        
    Returns:
        str: Chemin du fichier CSV
    """
    csv_path = os.path.join(output_dir, "resultats_comparaison.csv")
    
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Fournisseur", "Temps d'exécution (s)", "Longueur du résultat", "Nombre de mots", 
                        "Nombre de chiffres", "Caractères spéciaux", "Nombre de tableaux", "Erreur"])
        
        for provider, data in results.items():
            writer.writerow([
                provider,
                round(data["execution_time"], 2),
                data["result_length"],
                data["word_count"],
                data["number_count"],
                data["special_char_count"],
                data["table_count"],
                data["error"] if data["error"] else ""
            ])
    
    logger.info(f"Résultats sauvegardés dans {csv_path}")
    return csv_path


def save_raw_results(results, output_dir):
    """
    Sauvegarde les résultats bruts dans des fichiers texte.
    
    Args:
        results (dict): Résultats de l'analyse
        output_dir (str): Répertoire de sortie
    """
    raw_dir = os.path.join(output_dir, "resultats_bruts")
    os.makedirs(raw_dir, exist_ok=True)
    
    for provider, data in results.items():
        # Sauvegarde du résultat brut
        if data["result"]:
            result_path = os.path.join(raw_dir, f"{provider}_resultat.txt")
            with open(result_path, "w", encoding="utf-8") as f:
                f.write(data["result"])
        
        # Sauvegarde des tableaux extraits
        if data["tables"]:
            tables_dir = os.path.join(raw_dir, f"{provider}_tableaux")
            os.makedirs(tables_dir, exist_ok=True)
            
            for i, table in enumerate(data["tables"]):
                table_path = os.path.join(tables_dir, f"tableau_{i+1}.md")
                with open(table_path, "w", encoding="utf-8") as f:
                    f.write(table)
    
    logger.info(f"Résultats bruts sauvegardés dans {raw_dir}")


def generate_performance_charts(results, output_dir):
    """
    Génère des graphiques de performance.
    
    Args:
        results (dict): Résultats de l'analyse
        output_dir (str): Répertoire de sortie
        
    Returns:
        list: Chemins des graphiques générés
    """
    charts_dir = os.path.join(output_dir, "graphiques")
    os.makedirs(charts_dir, exist_ok=True)
    
    chart_paths = []
    
    # Préparation des données
    providers = list(results.keys())
    execution_times = [results[p]["execution_time"] for p in providers]
    result_lengths = [results[p]["result_length"] for p in providers]
    word_counts = [results[p]["word_count"] for p in providers]
    table_counts = [results[p]["table_count"] for p in providers]
    
    # Graphique des temps d'exécution
    plt.figure(figsize=(10, 6))
    bars = plt.bar(providers, execution_times, color='skyblue')
    plt.title('Temps d\'exécution par fournisseur')
    plt.xlabel('Fournisseur')
    plt.ylabel('Temps (secondes)')
    plt.xticks(rotation=45)
    
    # Ajout des valeurs sur les barres
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.2f}s', ha='center', va='bottom')
    
    plt.tight_layout()
    time_chart_path = os.path.join(charts_dir, "temps_execution.png")
    plt.savefig(time_chart_path)
    plt.close()
    chart_paths.append(time_chart_path)
    
    # Graphique des longueurs de résultat
    plt.figure(figsize=(10, 6))
    bars = plt.bar(providers, result_lengths, color='lightgreen')
    plt.title('Longueur des résultats par fournisseur')
    plt.xlabel('Fournisseur')
    plt.ylabel('Nombre de caractères')
    plt.xticks(rotation=45)
    
    # Ajout des valeurs sur les barres
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height}', ha='center', va='bottom')
    
    plt.tight_layout()
    length_chart_path = os.path.join(charts_dir, "longueur_resultats.png")
    plt.savefig(length_chart_path)
    plt.close()
    chart_paths.append(length_chart_path)
    
    # Graphique des nombres de mots
    plt.figure(figsize=(10, 6))
    bars = plt.bar(providers, word_counts, color='salmon')
    plt.title('Nombre de mots extraits par fournisseur')
    plt.xlabel('Fournisseur')
    plt.ylabel('Nombre de mots')
    plt.xticks(rotation=45)
    
    # Ajout des valeurs sur les barres
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height}', ha='center', va='bottom')
    
    plt.tight_layout()
    words_chart_path = os.path.join(charts_dir, "nombre_mots.png")
    plt.savefig(words_chart_path)
    plt.close()
    chart_paths.append(words_chart_path)
    
    # Graphique des nombres de tableaux
    plt.figure(figsize=(10, 6))
    bars = plt.bar(providers, table_counts, color='lightblue')
    plt.title('Nombre de tableaux extraits par fournisseur')
    plt.xlabel('Fournisseur')
    plt.ylabel('Nombre de tableaux')
    plt.xticks(rotation=45)
    
    # Ajout des valeurs sur les barres
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height}', ha='center', va='bottom')
    
    plt.tight_layout()
    tables_chart_path = os.path.join(charts_dir, "nombre_tableaux.png")
    plt.savefig(tables_chart_path)
    plt.close()
    chart_paths.append(tables_chart_path)
    
    # Graphique radar pour comparaison globale
    metrics = ['Temps d\'exécution (inv)', 'Longueur', 'Mots', 'Tableaux']
    
    # Normalisation des données pour le radar
    max_time = max(execution_times) if execution_times else 1
    max_length = max(result_lengths) if result_lengths else 1
    max_words = max(word_counts) if word_counts else 1
    max_tables = max(table_counts) if table_counts else 1
    
    # Inversion du temps (plus court = meilleur)
    norm_times = [1 - (t / max_time) if max_time > 0 else 0 for t in execution_times]
    norm_lengths = [l / max_length if max_length > 0 else 0 for l in result_lengths]
    norm_words = [w / max_words if max_words > 0 else 0 for w in word_counts]
    norm_tables = [t / max_tables if max_tables > 0 else 0 for t in table_counts]
    
    # Création du graphique radar
    plt.figure(figsize=(10, 8))
    angles = np.linspace(0, 2*np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]  # Fermer le polygone
    
    ax = plt.subplot(111, polar=True)
    
    for i, provider in enumerate(providers):
        values = [norm_times[i], norm_lengths[i], norm_words[i], norm_tables[i]]
        values += values[:1]  # Fermer le polygone
        
        ax.plot(angles, values, linewidth=2, label=provider)
        ax.fill(angles, values, alpha=0.1)
    
    plt.xticks(angles[:-1], metrics)
    plt.yticks([])
    plt.legend(loc='upper right')
    plt.title('Comparaison globale des performances')
    
    radar_chart_path = os.path.join(charts_dir, "comparaison_radar.png")
    plt.savefig(radar_chart_path)
    plt.close()
    chart_paths.append(radar_chart_path)
    
    logger.info(f"Graphiques générés dans {charts_dir}")
    return chart_paths


def generate_html_report(results, image_path, chart_paths, output_dir):
    """
    Génère un rapport HTML détaillé.
    
    Args:
        results (dict): Résultats de l'analyse
        image_path (str): Chemin de l'image analysée
        chart_paths (list): Chemins des graphiques générés
        output_dir (str): Répertoire de sortie
        
    Returns:
        str: Chemin du rapport HTML
    """
    html_path = os.path.join(output_dir, "rapport_comparaison.html")
    
    # Copie de l'image dans le répertoire de sortie
    image_filename = os.path.basename(image_path)
    image_copy_path = os.path.join(output_dir, image_filename)
    shutil.copy2(image_path, image_copy_path)
    
    # Création du contenu HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Rapport de Comparaison des Modèles OCR</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
            h1, h2, h3, h4 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .chart-container {{ margin: 20px 0; text-align: center; }}
            .chart {{ max-width: 100%; height: auto; }}
            .provider-section {{ margin-bottom: 40px; border-bottom: 1px solid #eee; padding-bottom: 20px; }}
            .image-container {{ text-align: center; margin: 20px 0; }}
            .image {{ max-width: 100%; height: auto; border: 1px solid #ddd; }}
            .highlight {{ background-color: #e7f3fe; padding: 10px; border-left: 6px solid #2196F3; }}
            .error {{ color: red; }}
            .footer {{ margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px; font-size: 0.8em; color: #777; }}
        </style>
    </head>
    <body>
        <h1>Rapport de Comparaison des Modèles OCR</h1>
        <p>Date: {datetime.now().strftime("%d/%m/%Y à %H:%M:%S")}</p>
        
        <div class="image-container">
            <h2>Image Analysée</h2>
            <img src="{image_filename}" alt="Image analysée" class="image">
        </div>
        
        <h2>Tableau Comparatif</h2>
        <table>
            <tr>
                <th>Fournisseur</th>
                <th>Temps d'exécution</th>
                <th>Longueur du résultat</th>
                <th>Nombre de mots</th>
                <th>Nombre de chiffres</th>
                <th>Caractères spéciaux</th>
                <th>Nombre de tableaux</th>
                <th>Statut</th>
            </tr>
    """
    
    # Ajout des lignes du tableau
    for provider, data in results.items():
        status = "<span class='error'>Erreur</span>" if data["error"] else "Succès"
        html_content += f"""
            <tr>
                <td>{provider}</td>
                <td>{data["execution_time"]:.2f}s</td>
                <td>{data["result_length"]}</td>
                <td>{data["word_count"]}</td>
                <td>{data["number_count"]}</td>
                <td>{data["special_char_count"]}</td>
                <td>{data["table_count"]}</td>
                <td>{status}</td>
            </tr>
        """
    
    html_content += """
        </table>
        
        <h2>Graphiques de Performance</h2>
    """
    
    # Ajout des graphiques
    for chart_path in chart_paths:
        chart_filename = os.path.basename(chart_path)
        # Copie du graphique dans le répertoire de sortie
        shutil.copy2(chart_path, os.path.join(output_dir, chart_filename))
        
        html_content += f"""
        <div class="chart-container">
            <img src="{chart_filename}" alt="Graphique de performance" class="chart">
        </div>
        """
    
    html_content += """
        <h2>Résultats Détaillés par Fournisseur</h2>
    """
    
    # Ajout des sections par fournisseur
    for provider, data in results.items():
        html_content += f"""
        <div class="provider-section">
            <h3>{provider}</h3>
            <p><strong>Temps d'exécution:</strong> {data["execution_time"]:.2f} secondes</p>
            <p><strong>Longueur du résultat:</strong> {data["result_length"]} caractères</p>
            <p><strong>Nombre de mots:</strong> {data["word_count"]}</p>
            <p><strong>Nombre de tableaux extraits:</strong> {data["table_count"]}</p>
        """
        
        if data["error"]:
            html_content += f"""
            <p class="error"><strong>Erreur:</strong> {data["error"]}</p>
            """
        else:
            # Affichage des premiers caractères du résultat
            preview = data["result"][:500] + "..." if len(data["result"]) > 500 else data["result"]
            html_content += f"""
            <h4>Aperçu du résultat:</h4>
            <pre>{preview}</pre>
            
            <p><a href="resultats_bruts/{provider}_resultat.txt" target="_blank">Voir le résultat complet</a></p>
            """
            
            # Affichage des tableaux extraits
            if data["tables"]:
                html_content += f"""
                <h4>Tableaux extraits ({data["table_count"]}):</h4>
                <p><a href="resultats_bruts/{provider}_tableaux/" target="_blank">Voir tous les tableaux</a></p>
                
                <div class="highlight">
                    <h5>Premier tableau extrait:</h5>
                    <pre>{data["tables"][0]}</pre>
                </div>
                """
        
        html_content += """
        </div>
        """
    
    # Ajout de la section d'analyse comparative
    html_content += """
        <h2>Analyse Comparative</h2>
        
        <h3>Performance Globale</h3>
        <p>Cette section compare les performances globales des différents fournisseurs d'API OCR.</p>
    """
    
    # Détermination du meilleur fournisseur pour chaque métrique
    best_time = min([(p, data["execution_time"]) for p, data in results.items() if not data["error"]], key=lambda x: x[1], default=(None, 0))
    best_length = max([(p, data["result_length"]) for p, data in results.items() if not data["error"]], key=lambda x: x[1], default=(None, 0))
    best_words = max([(p, data["word_count"]) for p, data in results.items() if not data["error"]], key=lambda x: x[1], default=(None, 0))
    best_tables = max([(p, data["table_count"]) for p, data in results.items() if not data["error"]], key=lambda x: x[1], default=(None, 0))
    
    html_content += f"""
        <div class="highlight">
            <h4>Meilleurs Performances:</h4>
            <ul>
                <li><strong>Temps d'exécution le plus rapide:</strong> {best_time[0]} ({best_time[1]:.2f}s)</li>
                <li><strong>Résultat le plus complet:</strong> {best_length[0]} ({best_length[1]} caractères)</li>
                <li><strong>Plus grand nombre de mots extraits:</strong> {best_words[0]} ({best_words[1]} mots)</li>
                <li><strong>Plus grand nombre de tableaux extraits:</strong> {best_tables[0]} ({best_tables[1]} tableaux)</li>
            </ul>
        </div>
        
        <h3>Analyse du modèle dots.ocr</h3>
    """
    
    # Analyse spécifique de dots.ocr
    if "dots_ocr" in results and not results["dots_ocr"]["error"]:
        dots_ocr_data = results["dots_ocr"]
        
        # Calcul des ratios par rapport aux meilleurs
        time_ratio = dots_ocr_data["execution_time"] / best_time[1] if best_time[1] > 0 else float('inf')
        length_ratio = dots_ocr_data["result_length"] / best_length[1] if best_length[1] > 0 else 0
        words_ratio = dots_ocr_data["word_count"] / best_words[1] if best_words[1] > 0 else 0
        tables_ratio = dots_ocr_data["table_count"] / best_tables[1] if best_tables[1] > 0 else 0
        
        html_content += f"""
        <p>Le modèle dots.ocr est un modèle local qui peut être utilisé sans connexion Internet et sans coût d'API.</p>
        
        <h4>Forces et faiblesses par rapport aux autres modèles:</h4>
        <ul>
            <li><strong>Temps d'exécution:</strong> {dots_ocr_data["execution_time"]:.2f}s ({time_ratio:.2f}x par rapport au meilleur)</li>
            <li><strong>Complétude du résultat:</strong> {length_ratio:.2%} par rapport au meilleur modèle</li>
            <li><strong>Extraction de mots:</strong> {words_ratio:.2%} par rapport au meilleur modèle</li>
            <li><strong>Extraction de tableaux:</strong> {tables_ratio:.2%} par rapport au meilleur modèle</li>
        </ul>
        
        <h4>Recommandations d'utilisation:</h4>
        <p>Basé sur cette analyse, voici quand utiliser dots.ocr par rapport aux autres modèles:</p>
        <ul>
        """
        
        # Recommandations dynamiques basées sur les résultats
        if time_ratio < 2.0:  # Si dots.ocr est moins de 2x plus lent que le meilleur
            html_content += "<li><strong>Rapidité:</strong> dots.ocr offre de bonnes performances en termes de vitesse.</li>"
        else:
            html_content += "<li><strong>Rapidité:</strong> dots.ocr est significativement plus lent que les meilleures alternatives.</li>"
        
        if length_ratio > 0.8:  # Si dots.ocr extrait au moins 80% du contenu du meilleur
            html_content += "<li><strong>Complétude:</strong> dots.ocr extrait la majorité du contenu par rapport aux meilleures alternatives.</li>"
        else:
            html_content += "<li><strong>Complétude:</strong> dots.ocr extrait significativement moins de contenu que les meilleures alternatives.</li>"
        
        if tables_ratio > 0.8:  # Si dots.ocr extrait au moins 80% des tableaux du meilleur
            html_content += "<li><strong>Tableaux:</strong> dots.ocr est efficace pour l'extraction de tableaux.</li>"
        else:
            html_content += "<li><strong>Tableaux:</strong> dots.ocr est moins efficace pour l'extraction de tableaux que les meilleures alternatives.</li>"
        
        html_content += """
            <li><strong>Avantage principal:</strong> Utilisation locale sans coût d'API et sans connexion Internet.</li>
            <li><strong>Mémoire:</strong> Nécessite environ 4-6 Go de RAM en mode 4-bit.</li>
        </ul>
        """
    else:
        html_content += """
        <p class="error">Le modèle dots.ocr n'a pas pu être évalué correctement. Veuillez vérifier l'installation et réessayer.</p>
        """
    
    html_content += """
        <h3>Conclusion</h3>
    """
    
    # Génération d'une conclusion basée sur les résultats
    best_overall = None
    best_score = -1
    
    for provider, data in results.items():
        if data["error"]:
            continue
        
        # Score simple basé sur plusieurs métriques
        time_score = 1.0 / (data["execution_time"] + 0.1)  # Inverse du temps (plus rapide = meilleur)
        length_score = data["result_length"] / (best_length[1] + 1)  # Normalisation par rapport au meilleur
        words_score = data["word_count"] / (best_words[1] + 1)  # Normalisation par rapport au meilleur
        tables_score = data["table_count"] / (best_tables[1] + 1) if best_tables[1] > 0 else 0  # Normalisation par rapport au meilleur
        
        # Score global (ajustez les poids selon l'importance relative)
        score = (time_score * 0.3) + (length_score * 0.3) + (words_score * 0.2) + (tables_score * 0.2)
        
        if score > best_score:
            best_score = score
            best_overall = provider
    
    if best_overall:
        html_content += f"""
        <p>Basé sur l'analyse globale des performances, <strong>{best_overall}</strong> offre le meilleur équilibre entre vitesse et qualité d'extraction pour ce type d'image.</p>
        
        <p>Pour les cas d'utilisation où la confidentialité des données, l'absence de connexion Internet ou l'absence de coûts d'API sont prioritaires, <strong>dots.ocr</strong> représente une alternative viable, particulièrement pour les documents contenant principalement du texte et des tableaux simples.</p>
        """
    else:
        html_content += """
        <p>Aucun fournisseur n'a pu être déterminé comme le meilleur global en raison d'erreurs ou de données insuffisantes.</p>
        """
    
    html_content += """
        <div class="footer">
            <p>© {datetime.now().year} - Projet d'analyse de risque environnemental - Maroc</p>
        </div>
    </body>
    </html>
    """
    
    # Écriture du fichier HTML
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    logger.info(f"Rapport HTML généré: {html_path}")
    return html_path


def main():
    # Analyse des arguments de la ligne de commande
    parser = argparse.ArgumentParser(description="Comparaison détaillée des modèles OCR")
    parser.add_argument("--image", help="Chemin de l'image à analyser")
    parser.add_argument("--providers", help="Liste des fournisseurs à comparer, séparés par des virgules")
    parser.add_argument("--output", help="Répertoire de sortie pour les résultats")
    parser.add_argument("--prompt", help="Prompt à utiliser pour l'analyse")
    
    args = parser.parse_args()
    
    # Détermination de l'image à analyser
    image_path = args.image
    if not image_path:
        # Recherche d'images de test
        test_images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_images")
        if os.path.exists(test_images_dir):
            image_files = [f for f in os.listdir(test_images_dir) if f.endswith((".png", ".jpg", ".jpeg"))]
            if image_files:
                image_path = os.path.join(test_images_dir, image_files[0])
                logger.info(f"Utilisation de l'image de test: {image_path}")
    
    if not image_path or not os.path.exists(image_path):
        logger.error("Aucune image valide spécifiée ou trouvée.")
        print("\nVeuillez spécifier une image valide avec l'option --image.")
        print("Vous pouvez générer une image de test avec: python generate_test_image.py")
        return
    
    # Détermination des fournisseurs à comparer
    available_providers = get_available_providers()
    if not available_providers:
        logger.error("Aucun fournisseur d'API disponible dans la configuration.")
        return
    
    providers = args.providers.split(",") if args.providers else available_providers
    providers = [p.strip() for p in providers if p.strip() in available_providers]
    
    if not providers:
        logger.error("Aucun fournisseur valide spécifié.")
        print(f"\nFournisseurs disponibles: {', '.join(available_providers)}")
        return
    
    # Détermination du répertoire de sortie
    if args.output:
        output_dir = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rapports", f"comparaison_{timestamp}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Analyse de l'image avec tous les fournisseurs
    print(f"\nAnalyse de l'image avec {len(providers)} fournisseurs: {', '.join(providers)}")
    results = analyze_image_with_all_providers(image_path, providers, args.prompt)
    
    # Sauvegarde des résultats
    save_results_to_csv(results, output_dir)
    save_raw_results(results, output_dir)
    
    # Génération des graphiques
    try:
        chart_paths = generate_performance_charts(results, output_dir)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des graphiques: {e}")
        chart_paths = []
    
    # Génération du rapport HTML
    html_path = generate_html_report(results, image_path, chart_paths, output_dir)
    
    print(f"\nRapport de comparaison généré: {html_path}")
    print(f"Tous les résultats sont disponibles dans: {output_dir}")


if __name__ == "__main__":
    main()