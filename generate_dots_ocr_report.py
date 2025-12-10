#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Génération d'un rapport PDF sur l'utilisation du modèle dots.ocr dans le projet.

Ce script génère un rapport PDF détaillé expliquant comment utiliser le modèle dots.ocr
dans le projet d'analyse environnementale. Il inclut des exemples de code, des captures
d'écran et des comparaisons avec les autres API cloud.

Usage:
    python generate_dots_ocr_report.py [--output <chemin_sortie>]

Exemple:
    python generate_dots_ocr_report.py
    python generate_dots_ocr_report.py --output ./rapports/guide_dots_ocr.pdf
"""

import argparse
import os
import sys
import logging
from datetime import datetime
import markdown
import pdfkit
import json

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


def load_guide_content():
    """
    Charge le contenu du guide d'utilisation depuis le fichier GUIDE_DOTS_OCR.md.
    
    Returns:
        str: Contenu du guide d'utilisation
    """
    guide_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GUIDE_DOTS_OCR.md")
    try:
        with open(guide_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        logger.error(f"Erreur lors du chargement du guide d'utilisation: {e}")
        return ""


def generate_html_content():
    """
    Génère le contenu HTML du rapport.
    
    Returns:
        str: Contenu HTML du rapport
    """
    # Chargement du contenu du guide
    guide_content = load_guide_content()
    if not guide_content:
        guide_content = "# Guide d'utilisation du modèle dots.ocr\n\nContenu du guide non disponible."
    
    # Chargement de la configuration des API
    api_config = load_api_config()
    dots_ocr_config = api_config.get("dots_ocr", {})
    
    # Conversion du contenu Markdown en HTML
    guide_html = markdown.markdown(guide_content, extensions=['tables', 'fenced_code'])
    
    # Génération du contenu HTML complet
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Guide d'utilisation du modèle dots.ocr</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
            h1, h2, h3, h4 {{ color: #333; }}
            code {{ background-color: #f5f5f5; padding: 2px 5px; border-radius: 3px; font-family: monospace; }}
            pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
            pre code {{ background-color: transparent; padding: 0; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .info-box {{ background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 10px; margin: 15px 0; }}
            .warning-box {{ background-color: #ffffcc; border-left: 6px solid #ffeb3b; padding: 10px; margin: 15px 0; }}
            .footer {{ margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px; font-size: 0.8em; color: #777; }}
            .page-break {{ page-break-after: always; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Guide d'utilisation du modèle dots.ocr</h1>
            <p>Rapport généré le {datetime.now().strftime("%d/%m/%Y à %H:%M:%S")}</p>
        </div>
        
        <div class="content">
            {guide_html}
        </div>
        
        <div class="page-break"></div>
        
        <h2>Configuration actuelle du modèle dots.ocr</h2>
        <div class="info-box">
            <p>La configuration suivante est définie dans le fichier <code>cloud_api_config.json</code> :</p>
            <pre><code>{json.dumps(dots_ocr_config, indent=4)}</code></pre>
        </div>
        
        <h2>Exemples de code supplémentaires</h2>
        
        <h3>Exemple 1: Analyse d'une image avec dots.ocr</h3>
        <pre><code>from cloud_api import CloudVisionAPI

# Création d'une instance avec Google Vision API comme fournisseur
cloud_api = CloudVisionAPI(api_provider="google")

# Analyse d'une image
result = cloud_api.analyze_image(
    image_path="chemin/vers/image.jpg",
    prompt="Extrais tout le texte de cette image et formate-le correctement."
)

# Affichage du résultat
print(result)

# Pas besoin de libérer la mémoire avec l'API Google Vision
# car elle fonctionne dans le cloud</code></pre>
        
        <h3>Exemple 2: Extraction de tableaux d'une image</h3>
        <pre><code>from cloud_api import CloudVisionAPI
from utils import extract_markdown_tables

# Création d'une instance avec Google Vision API comme fournisseur
cloud_api = CloudVisionAPI(api_provider="google")

# Analyse d'une image contenant un tableau
result = cloud_api.analyze_image(
    image_path="chemin/vers/tableau.jpg",
    prompt="Extrais ce tableau sous forme de tableau Markdown."
)

# Extraction des tableaux Markdown
tables = extract_markdown_tables(result)

# Affichage des tableaux extraits
# Exemple de code pour afficher les tableaux
# for i, table in enumerate(tables):
#     print("Tableau " + str(i+1) + ":")
#     print(table)
#     print()

# Pas besoin de libérer la mémoire avec l'API Google Vision
# car elle fonctionne dans le cloud</code></pre>
        
        <h3>Exemple 3: Traitement par lots d'images</h3>
        <pre><code>import os
from cloud_api import CloudVisionAPI
import torch

# Liste des images à traiter
image_paths = [
    "chemin/vers/image1.jpg",
    "chemin/vers/image2.jpg",
    "chemin/vers/image3.jpg"
]

# Création d'une instance avec Google Vision API comme fournisseur
cloud_api = CloudVisionAPI(api_provider="google")

# Exemple de code pour le traitement des images une par une
# results = []
# for image_path in image_paths:
#     print("Traitement de " + image_path + "...")
#     result = cloud_api.analyze_image(
#         image_path=image_path,
#         prompt="Extrais tout le texte de cette image."
#     )
#     results.append(result)
#     
#     # Libération de la mémoire après chaque image
#     if torch.cuda.is_available():
#         torch.cuda.empty_cache()

# Exemple de code pour l'affichage des résultats
# for i, result in enumerate(results):
#     print("Résultat pour l'image " + str(i+1) + ":")
#     print(result[:500] + "..." if len(result) > 500 else result)
#     print()

# Pas besoin de libérer la mémoire avec l'API Google Vision
# car elle fonctionne dans le cloud</code></pre>
        
        <div class="info-box">
            <h3>Avantages de l'API Google Vision</h3>
            <p>L'API Google Vision offre plusieurs avantages :</p>
            <ul>
                <li>Aucune consommation de mémoire locale car le traitement se fait dans le cloud</li>
                <li>Traitement rapide des images</li>
                <li>Excellente précision pour la reconnaissance de texte</li>
                <li>Possibilité de traiter des lots d'images sans contrainte de mémoire</li>
                <li>Pas besoin d'installer de modèles locaux volumineux</li>
            </ul>
        </div>
        
        <div class="page-break"></div>
        
        <h2>Comparaison avec les autres API cloud</h2>
        
        <table>
            <tr>
                <th>Caractéristique</th>
                <th>dots.ocr</th>
                <th>OpenAI</th>
                <th>Google</th>
                <th>Azure</th>
            </tr>
            <tr>
                <td>Coût</td>
                <td>Gratuit (local)</td>
                <td>Payant (par requête)</td>
                <td>Payant (par requête)</td>
                <td>Payant (par requête)</td>
            </tr>
            <tr>
                <td>Confidentialité</td>
                <td>Élevée (100% local)</td>
                <td>Faible (données envoyées)</td>
                <td>Faible (données envoyées)</td>
                <td>Faible (données envoyées)</td>
            </tr>
            <tr>
                <td>Précision OCR</td>
                <td>Bonne</td>
                <td>Excellente</td>
                <td>Très bonne</td>
                <td>Très bonne</td>
            </tr>
            <tr>
                <td>Vitesse</td>
                <td>Moyenne (dépend du matériel)</td>
                <td>Rapide (serveurs cloud)</td>
                <td>Rapide (serveurs cloud)</td>
                <td>Rapide (serveurs cloud)</td>
            </tr>
            <tr>
                <td>Mémoire requise</td>
                <td>4-6 Go (4-bit)</td>
                <td>Minimale (API)</td>
                <td>Minimale (API)</td>
                <td>Minimale (API)</td>
            </tr>
            <tr>
                <td>Connexion Internet</td>
                <td>Non requise</td>
                <td>Requise</td>
                <td>Requise</td>
                <td>Requise</td>
            </tr>
            <tr>
                <td>Support multilingue</td>
                <td>Français, Arabe, Anglais</td>
                <td>Nombreuses langues</td>
                <td>Nombreuses langues</td>
                <td>Nombreuses langues</td>
            </tr>
        </table>
        
        <h3>Quand utiliser dots.ocr vs API cloud</h3>
        
        <p><strong>Utilisez dots.ocr quand :</strong></p>
        <ul>
            <li>Vous avez besoin de confidentialité (données sensibles)</li>
            <li>Vous n'avez pas de connexion Internet fiable</li>
            <li>Vous voulez éviter les coûts des API cloud</li>
            <li>Vous travaillez principalement avec des documents en français ou en arabe</li>
            <li>Vous avez au moins 4-6 Go de RAM disponible</li>
        </ul>
        
        <p><strong>Utilisez les API cloud quand :</strong></p>
        <ul>
            <li>Vous avez besoin d'une précision maximale</li>
            <li>Vous avez très peu de RAM disponible (< 4 Go)</li>
            <li>Vous traitez des langues non supportées par dots.ocr</li>
            <li>Vous avez besoin de performances maximales</li>
            <li>Le budget n'est pas une contrainte</li>
        </ul>
        
        <div class="footer">
            <p>© {datetime.now().year} - Projet d'analyse de risque environnemental - Maroc</p>
        </div>
    </body>
    </html>
    """
    
    return html_content


def check_wkhtmltopdf():
    """
    Vérifie si wkhtmltopdf est installé sur le système.
    
    Returns:
        bool: True si wkhtmltopdf est installé, False sinon
    """
    try:
        import subprocess
        subprocess.run(['wkhtmltopdf', '-V'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.warning("wkhtmltopdf n'est pas installé ou n'est pas dans le PATH")
        return False

def generate_pdf_report(output_path=None):
    """
    Génère un rapport PDF à partir du contenu HTML.
    Si wkhtmltopdf n'est pas installé, génère un rapport HTML.
    
    Args:
        output_path (str, optional): Chemin de sortie pour le rapport PDF
        
    Returns:
        str: Chemin du rapport PDF ou HTML généré
    """
    # Génération du contenu HTML
    html_content = generate_html_content()
    
    # Détermination du chemin de sortie
    if output_path is None:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rapports")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"guide_dots_ocr_{timestamp}.pdf")
    
    # Création du répertoire parent si nécessaire
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Vérification de wkhtmltopdf
    if not check_wkhtmltopdf():
        # Si wkhtmltopdf n'est pas installé, sauvegarde en HTML
        html_path = output_path.replace(".pdf", ".html")
        try:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"wkhtmltopdf non disponible. Contenu HTML sauvegardé: {html_path}")
            return html_path
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du HTML: {e}")
            return None
    
    # Configuration des options de pdfkit
    options = {
        'page-size': 'A4',
        'margin-top': '20mm',
        'margin-right': '20mm',
        'margin-bottom': '20mm',
        'margin-left': '20mm',
        'encoding': "UTF-8",
        'no-outline': None,
        'enable-local-file-access': None
    }
    
    try:
        # Génération du PDF
        pdfkit.from_string(html_content, output_path, options=options)
        logger.info(f"Rapport PDF généré avec succès: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport PDF: {e}")
        
        # Sauvegarde du contenu HTML en cas d'échec
        html_path = output_path.replace(".pdf", ".html")
        try:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"Contenu HTML sauvegardé: {html_path}")
            return html_path
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du HTML: {e}")
            return None


def main():
    # Analyse des arguments de la ligne de commande
    parser = argparse.ArgumentParser(description="Génération d'un rapport PDF sur l'utilisation du modèle dots.ocr")
    parser.add_argument("--output", help="Chemin de sortie pour le rapport PDF")
    
    args = parser.parse_args()
    
    # Vérification de wkhtmltopdf
    if not check_wkhtmltopdf():
        print("\nwkhtmltopdf n'est pas installé sur votre système.")
        print("Le rapport sera généré au format HTML uniquement.")
        print("Pour générer un PDF, veuillez installer wkhtmltopdf:")
        print("- Windows: Téléchargez depuis https://wkhtmltopdf.org/downloads.html")
        print("- Linux: sudo apt-get install wkhtmltopdf")
        print("- macOS: brew install wkhtmltopdf")
        print("Puis exécutez: python install_report_dependencies.py")
    
    # Génération du rapport
    output_path = generate_pdf_report(args.output)
    
    if output_path:
        print(f"\nRapport généré: {output_path}")
    else:
        print("\nÉchec de la génération du rapport.")


if __name__ == "__main__":
    main()