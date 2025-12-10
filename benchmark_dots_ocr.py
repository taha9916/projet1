#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Benchmark complet du modèle dots.ocr comparé aux autres API cloud.

Ce script réalise un benchmark complet du modèle dots.ocr en le comparant aux autres
API cloud disponibles dans le projet. Il teste différents types d'images (documents,
tableaux, graphiques, etc.) et génère un rapport détaillé des performances.

Usage:
    python benchmark_dots_ocr.py --image_dir <répertoire_images> [--providers <liste_fournisseurs>]

Exemple:
    python benchmark_dots_ocr.py --image_dir ./test_images
    python benchmark_dots_ocr.py --image_dir ./test_images --providers dots_ocr,openai,google
"""

import argparse
import os
import sys
import logging
import pandas as pd
import time
from datetime import datetime
import torch
import json
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import numpy as np
from PIL import Image

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ajout du répertoire courant au chemin de recherche des modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import des modules du projet
from cloud_api import CloudVisionAPI
from utils import extract_markdown_tables

# Liste des fournisseurs disponibles
AVAILABLE_PROVIDERS = ["dots_ocr", "openai", "azure", "google", "qwen", "openrouter"]

# Catégories d'images pour le benchmark
IMAGE_CATEGORIES = {
    "document": ["pdf", "doc", "docx", "text"],
    "tableau": ["table", "spreadsheet", "excel"],
    "graphique": ["chart", "graph", "plot"],
    "photo": ["photo", "image", "picture"],
    "mixte": ["mixed", "combined"]
}

# Prompts spécifiques par catégorie
CATEGORY_PROMPTS = {
    "document": "Extrais tout le texte de ce document et résume son contenu principal.",
    "tableau": "Extrais ce tableau sous forme de tableau Markdown et analyse les données qu'il contient.",
    "graphique": "Décris ce graphique en détail et extrais les tendances ou informations clés qu'il présente.",
    "photo": "Analyse cette photo environnementale et identifie tous les éléments pertinents pour une analyse de risque.",
    "mixte": "Analyse cette image qui contient à la fois du texte et des éléments visuels. Extrais toutes les informations pertinentes."
}


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
    Détermine les fournisseurs d'API disponibles en fonction de la configuration.
    
    Returns:
        list: Liste des fournisseurs disponibles
    """
    config = load_api_config()
    available = ["dots_ocr"]  # dots.ocr est toujours disponible car local
    
    # Vérification des autres fournisseurs
    if config.get("openai", {}).get("api_key"):
        available.append("openai")
    if config.get("azure", {}).get("api_key"):
        available.append("azure")
    if config.get("google", {}).get("api_key"):
        available.append("google")
    if config.get("qwen", {}).get("api_key"):
        available.append("qwen")
    if config.get("openrouter", {}).get("api_key"):
        available.append("openrouter")
    
    return available


def categorize_image(image_path):
    """
    Catégorise une image en fonction de son nom de fichier.
    
    Args:
        image_path (str): Chemin vers l'image
        
    Returns:
        str: Catégorie de l'image
    """
    filename = os.path.basename(image_path).lower()
    
    for category, keywords in IMAGE_CATEGORIES.items():
        for keyword in keywords:
            if keyword in filename:
                return category
    
    # Par défaut, considérer comme une photo
    return "photo"


def get_image_info(image_path):
    """
    Obtient des informations sur une image (dimensions, taille, etc.).
    
    Args:
        image_path (str): Chemin vers l'image
        
    Returns:
        dict: Informations sur l'image
    """
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            format = img.format
            mode = img.mode
        
        file_size = os.path.getsize(image_path) / 1024  # Taille en Ko
        
        return {
            "width": width,
            "height": height,
            "format": format,
            "mode": mode,
            "size_kb": file_size
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'obtention des informations sur l'image {image_path}: {e}")
        return {}


def benchmark_image(image_path, providers, prompt=None):
    """
    Réalise un benchmark sur une image avec différents fournisseurs.
    
    Args:
        image_path (str): Chemin vers l'image
        providers (list): Liste des fournisseurs à comparer
        prompt (str, optional): Prompt à utiliser pour l'analyse
        
    Returns:
        dict: Résultats du benchmark
    """
    # Catégorisation de l'image
    category = categorize_image(image_path)
    
    # Utilisation du prompt spécifique à la catégorie si aucun prompt n'est fourni
    if prompt is None:
        prompt = CATEGORY_PROMPTS.get(category, "Analyse cette image et extrais toutes les informations pertinentes.")
    
    # Obtention des informations sur l'image
    image_info = get_image_info(image_path)
    
    results = {
        "image_path": image_path,
        "category": category,
        "image_info": image_info,
        "prompt": prompt,
        "providers": {}
    }
    
    for provider in providers:
        try:
            # Création de l'instance CloudVisionAPI
            cloud_api = CloudVisionAPI(api_provider=provider)
            
            # Analyse de l'image avec mesure du temps d'exécution
            start_time = time.time()
            response = cloud_api.analyze_image(
                image_path=image_path,
                prompt=prompt
            )
            end_time = time.time()
            
            # Calcul du temps d'exécution
            execution_time = end_time - start_time
            
            # Extraction des tableaux si présents
            tables = extract_markdown_tables(response)
            
            # Stockage des résultats
            results["providers"][provider] = {
                "execution_time": execution_time,
                "response": response,
                "tables": tables,
                "table_count": len(tables),
                "response_length": len(response),
                "word_count": len(response.split())
            }
            
            # Libération de la mémoire pour dots.ocr
            if provider == "dots_ocr":
                if hasattr(cloud_api, 'model'):
                    del cloud_api.model
                if hasattr(cloud_api, 'processor'):
                    del cloud_api.processor
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    
        except Exception as e:
            logger.error(f"Erreur avec le fournisseur {provider} pour l'image {image_path}: {e}")
            results["providers"][provider] = {
                "error": str(e),
                "execution_time": None,
                "response": None,
                "tables": [],
                "table_count": 0,
                "response_length": 0,
                "word_count": 0
            }
    
    return results


def run_benchmark(image_dir, providers, output_dir="benchmark_results"):
    """
    Exécute le benchmark sur un répertoire d'images.
    
    Args:
        image_dir (str): Répertoire contenant les images
        providers (list): Liste des fournisseurs à comparer
        output_dir (str): Répertoire de sortie pour les résultats
        
    Returns:
        list: Résultats du benchmark
    """
    # Création du répertoire de sortie s'il n'existe pas
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Récupération de la liste des images
    image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif"]
    images = []
    
    for root, _, files in os.walk(image_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in image_extensions):
                images.append(os.path.join(root, file))
    
    if not images:
        logger.error(f"Aucune image trouvée dans le répertoire {image_dir}")
        return []
    
    logger.info(f"Benchmark sur {len(images)} images avec {len(providers)} fournisseurs")
    
    # Exécution du benchmark sur chaque image
    results = []
    for image_path in tqdm(images, desc="Benchmark en cours"):
        result = benchmark_image(image_path, providers)
        results.append(result)
    
    # Sauvegarde des résultats bruts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(os.path.join(output_dir, f"benchmark_results_{timestamp}.json"), "w", encoding="utf-8") as f:
        # Conversion des DataFrames en listes pour la sérialisation JSON
        serializable_results = []
        for result in results:
            serializable_result = result.copy()
            for provider, provider_result in result["providers"].items():
                serializable_provider_result = provider_result.copy()
                serializable_provider_result["tables"] = [
                    table.to_dict(orient="records") for table in provider_result["tables"]
                ]
                serializable_result["providers"][provider] = serializable_provider_result
            serializable_results.append(serializable_result)
        
        json.dump(serializable_results, f, indent=2)
    
    return results


def generate_summary_table(results):
    """
    Génère un tableau récapitulatif des résultats du benchmark.
    
    Args:
        results (list): Résultats du benchmark
        
    Returns:
        pandas.DataFrame: Tableau récapitulatif
    """
    data = []
    
    for result in results:
        image_path = result["image_path"]
        category = result["category"]
        
        for provider, provider_result in result["providers"].items():
            data.append({
                "Image": os.path.basename(image_path),
                "Catégorie": category,
                "Fournisseur": provider,
                "Temps d'exécution (s)": round(provider_result["execution_time"], 2) if provider_result["execution_time"] else None,
                "Longueur de la réponse": provider_result["response_length"],
                "Nombre de mots": provider_result["word_count"],
                "Nombre de tableaux extraits": provider_result["table_count"],
                "Erreur": provider_result.get("error", "")
            })
    
    return pd.DataFrame(data)


def generate_performance_charts(summary_df, output_dir):
    """
    Génère des graphiques de performance à partir du tableau récapitulatif.
    
    Args:
        summary_df (pandas.DataFrame): Tableau récapitulatif
        output_dir (str): Répertoire de sortie pour les graphiques
    """
    # Configuration de seaborn
    sns.set(style="whitegrid")
    plt.figure(figsize=(12, 8))
    
    # 1. Temps d'exécution moyen par fournisseur
    plt.figure(figsize=(10, 6))
    chart = sns.barplot(x="Fournisseur", y="Temps d'exécution (s)", data=summary_df, errorbar=None)
    chart.set_title("Temps d'exécution moyen par fournisseur")
    chart.set_ylabel("Temps (secondes)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "execution_time_by_provider.png"))
    plt.close()
    
    # 2. Temps d'exécution moyen par fournisseur et par catégorie
    plt.figure(figsize=(12, 8))
    chart = sns.barplot(x="Fournisseur", y="Temps d'exécution (s)", hue="Catégorie", data=summary_df, errorbar=None)
    chart.set_title("Temps d'exécution moyen par fournisseur et par catégorie")
    chart.set_ylabel("Temps (secondes)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "execution_time_by_provider_and_category.png"))
    plt.close()
    
    # 3. Longueur de réponse moyenne par fournisseur
    plt.figure(figsize=(10, 6))
    chart = sns.barplot(x="Fournisseur", y="Longueur de la réponse", data=summary_df, errorbar=None)
    chart.set_title("Longueur de réponse moyenne par fournisseur")
    chart.set_ylabel("Nombre de caractères")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "response_length_by_provider.png"))
    plt.close()
    
    # 4. Nombre de tableaux extraits par fournisseur
    plt.figure(figsize=(10, 6))
    chart = sns.barplot(x="Fournisseur", y="Nombre de tableaux extraits", data=summary_df, errorbar=None)
    chart.set_title("Nombre moyen de tableaux extraits par fournisseur")
    chart.set_ylabel("Nombre de tableaux")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "table_count_by_provider.png"))
    plt.close()
    
    # 5. Nombre de mots par fournisseur
    plt.figure(figsize=(10, 6))
    chart = sns.barplot(x="Fournisseur", y="Nombre de mots", data=summary_df, errorbar=None)
    chart.set_title("Nombre moyen de mots par fournisseur")
    chart.set_ylabel("Nombre de mots")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "word_count_by_provider.png"))
    plt.close()


def generate_html_report(summary_df, results, output_dir):
    """
    Génère un rapport HTML détaillé du benchmark.
    
    Args:
        summary_df (pandas.DataFrame): Tableau récapitulatif
        results (list): Résultats du benchmark
        output_dir (str): Répertoire de sortie pour le rapport
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(output_dir, f"benchmark_report_{timestamp}.html")
    
    # Calcul des statistiques globales
    providers = summary_df["Fournisseur"].unique()
    categories = summary_df["Catégorie"].unique()
    
    # Création du contenu HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Benchmark dots.ocr vs API Cloud</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
            h1, h2, h3, h4 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .chart {{ margin: 20px 0; max-width: 100%; }}
            .provider-section {{ margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 20px; }}
            .error {{ color: red; }}
            .success {{ color: green; }}
        </style>
    </head>
    <body>
        <h1>Benchmark dots.ocr vs API Cloud</h1>
        <p>Rapport généré le {datetime.now().strftime("%d/%m/%Y à %H:%M:%S")}</p>
        
        <h2>Résumé</h2>
        <ul>
            <li><strong>Nombre d'images testées:</strong> {len(results)}</li>
            <li><strong>Fournisseurs comparés:</strong> {', '.join(providers)}</li>
            <li><strong>Catégories d'images:</strong> {', '.join(categories)}</li>
        </ul>
        
        <h2>Tableau récapitulatif</h2>
        {summary_df.to_html(index=False)}
        
        <h2>Graphiques de performance</h2>
        <div class="chart">
            <h3>Temps d'exécution moyen par fournisseur</h3>
            <img src="execution_time_by_provider.png" alt="Temps d'exécution moyen par fournisseur">
        </div>
        
        <div class="chart">
            <h3>Temps d'exécution moyen par fournisseur et par catégorie</h3>
            <img src="execution_time_by_provider_and_category.png" alt="Temps d'exécution moyen par fournisseur et par catégorie">
        </div>
        
        <div class="chart">
            <h3>Longueur de réponse moyenne par fournisseur</h3>
            <img src="response_length_by_provider.png" alt="Longueur de réponse moyenne par fournisseur">
        </div>
        
        <div class="chart">
            <h3>Nombre moyen de tableaux extraits par fournisseur</h3>
            <img src="table_count_by_provider.png" alt="Nombre moyen de tableaux extraits par fournisseur">
        </div>
        
        <div class="chart">
            <h3>Nombre moyen de mots par fournisseur</h3>
            <img src="word_count_by_provider.png" alt="Nombre moyen de mots par fournisseur">
        </div>
        
        <h2>Résultats détaillés par fournisseur</h2>
    """
    
    # Ajout des résultats détaillés par fournisseur
    for provider in providers:
        provider_df = summary_df[summary_df["Fournisseur"] == provider]
        
        html_content += f"""
        <div class="provider-section">
            <h3>{provider}</h3>
            <p><strong>Temps d'exécution moyen:</strong> {provider_df["Temps d'exécution (s)"].mean():.2f} secondes</p>
            <p><strong>Longueur de réponse moyenne:</strong> {provider_df["Longueur de la réponse"].mean():.0f} caractères</p>
            <p><strong>Nombre moyen de mots:</strong> {provider_df["Nombre de mots"].mean():.0f} mots</p>
            <p><strong>Nombre moyen de tableaux extraits:</strong> {provider_df["Nombre de tableaux extraits"].mean():.2f} tableaux</p>
            
            <h4>Performance par catégorie</h4>
            <table>
                <tr>
                    <th>Catégorie</th>
                    <th>Temps d'exécution moyen (s)</th>
                    <th>Longueur de réponse moyenne</th>
                    <th>Nombre moyen de tableaux</th>
                </tr>
        """
        
        for category in categories:
            category_df = provider_df[provider_df["Catégorie"] == category]
            if not category_df.empty:
                html_content += f"""
                <tr>
                    <td>{category}</td>
                    <td>{category_df["Temps d'exécution (s)"].mean():.2f}</td>
                    <td>{category_df["Longueur de la réponse"].mean():.0f}</td>
                    <td>{category_df["Nombre de tableaux extraits"].mean():.2f}</td>
                </tr>
                """
        
        html_content += """
            </table>
        </div>
        """
    
    # Ajout des résultats détaillés par image
    html_content += """
        <h2>Résultats détaillés par image</h2>
    """
    
    for result in results:
        image_path = result["image_path"]
        category = result["category"]
        image_info = result["image_info"]
        
        html_content += f"""
        <div class="image-section">
            <h3>{os.path.basename(image_path)} (Catégorie: {category})</h3>
            <p><strong>Dimensions:</strong> {image_info.get("width", "N/A")}x{image_info.get("height", "N/A")} pixels</p>
            <p><strong>Format:</strong> {image_info.get("format", "N/A")}</p>
            <p><strong>Taille:</strong> {image_info.get("size_kb", "N/A"):.2f} Ko</p>
            
            <table>
                <tr>
                    <th>Fournisseur</th>
                    <th>Temps d'exécution (s)</th>
                    <th>Longueur de la réponse</th>
                    <th>Nombre de mots</th>
                    <th>Nombre de tableaux</th>
                    <th>Statut</th>
                </tr>
        """
        
        for provider, provider_result in result["providers"].items():
            status = "<span class='error'>Erreur</span>" if "error" in provider_result else "<span class='success'>Succès</span>"
            execution_time = f"{provider_result['execution_time']:.2f}" if provider_result["execution_time"] else "N/A"
            
            html_content += f"""
                <tr>
                    <td>{provider}</td>
                    <td>{execution_time}</td>
                    <td>{provider_result["response_length"]}</td>
                    <td>{provider_result["word_count"]}</td>
                    <td>{provider_result["table_count"]}</td>
                    <td>{status}</td>
                </tr>
            """
        
        html_content += """
            </table>
        </div>
        """
    
    # Fermeture du document HTML
    html_content += """
    </body>
    </html>
    """
    
    # Écriture du rapport HTML
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    logger.info(f"Rapport HTML généré: {report_path}")
    return report_path


def main():
    # Analyse des arguments de la ligne de commande
    parser = argparse.ArgumentParser(description="Benchmark complet du modèle dots.ocr comparé aux autres API cloud")
    parser.add_argument("--image_dir", required=True, help="Répertoire contenant les images à analyser")
    parser.add_argument("--providers", help="Liste des fournisseurs à comparer, séparés par des virgules")
    parser.add_argument("--output", default="benchmark_results", help="Répertoire de sortie pour les résultats")
    
    args = parser.parse_args()
    
    # Vérification de l'existence du répertoire d'images
    if not os.path.isdir(args.image_dir):
        logger.error(f"Le répertoire {args.image_dir} n'existe pas.")
        sys.exit(1)
    
    # Détermination des fournisseurs disponibles
    available_providers = get_available_providers()
    logger.info(f"Fournisseurs disponibles: {', '.join(available_providers)}")
    
    # Sélection des fournisseurs à comparer
    if args.providers:
        providers = [p.strip() for p in args.providers.split(",")]
        # Vérification que les fournisseurs spécifiés sont disponibles
        for provider in providers:
            if provider not in available_providers:
                logger.warning(f"Le fournisseur {provider} n'est pas disponible et sera ignoré.")
        providers = [p for p in providers if p in available_providers]
    else:
        providers = available_providers
    
    if not providers:
        logger.error("Aucun fournisseur disponible pour la comparaison.")
        sys.exit(1)
    
    logger.info(f"Fournisseurs sélectionnés pour le benchmark: {', '.join(providers)}")
    
    # Exécution du benchmark
    results = run_benchmark(args.image_dir, providers, args.output)
    
    if not results:
        logger.error("Le benchmark n'a produit aucun résultat.")
        sys.exit(1)
    
    # Génération du tableau récapitulatif
    summary_df = generate_summary_table(results)
    summary_df.to_csv(os.path.join(args.output, "benchmark_summary.csv"), index=False)
    
    # Génération des graphiques de performance
    generate_performance_charts(summary_df, args.output)
    
    # Génération du rapport HTML
    report_path = generate_html_report(summary_df, results, args.output)
    
    print(f"\nBenchmark terminé. Rapport disponible à: {report_path}")


if __name__ == "__main__":
    main()