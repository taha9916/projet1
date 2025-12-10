import os
import datetime
import logging
from PIL import Image
import pdfplumber
import pytesseract
import docx
import pandas as pd

# Importer le nouveau système de logging centralisé
from logger import setup_logging, get_logger

# Initialiser le logging pour ce module
logger = get_logger(__name__)

def get_timestamp():
    """Retourne un horodatage formaté pour les noms de fichiers."""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def save_dataframe_to_excel(df, base_filename="resultat_analyse_risque", directory=None):
    """Sauvegarde un DataFrame dans un fichier Excel avec horodatage."""
    timestamp = get_timestamp()
    filename = f"{base_filename}_{timestamp}.xlsx"
    
    if directory:
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, filename)
    else:
        filepath = filename
    
    # S'assurer que les colonnes sont dans le bon ordre (comme dans le modèle)
    model_columns = ["Milieu", "Paramètre", "Unité", "Intervalle acceptable", "Valeur mesurée", "Résultat conformité", "Score", "Observations", "Description", "Évaluation"]
    
    # Vérifier que toutes les colonnes du modèle existent dans le DataFrame
    for col in model_columns:
        if col not in df.columns:
            df[col] = ""  # Ajouter les colonnes manquantes
    
    # Réorganiser les colonnes dans l'ordre du modèle
    df = df[model_columns]
    
    # Sauvegarder le DataFrame dans un fichier Excel
    df.to_excel(filepath, index=False)
    logger.info(f"Données sauvegardées dans {filepath}")
    return filepath

def iter_pdf_text_pages(file_path, ocr_fallback=False, dpi=200, lang="eng+fra"):
    """Itère page par page sur un PDF et renvoie (index_page, texte).
    
    Args:
        file_path: Chemin du fichier PDF
        ocr_fallback: Si True, tente un OCR si aucune chaîne n'est extraite
        dpi: Résolution utilisée pour la conversion en image (OCR)
        lang: Langues pour Tesseract (par ex. "eng+fra")
    Yields:
        Tuple (page_index, text)
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext != ".pdf":
        raise ValueError("iter_pdf_text_pages ne supporte que les fichiers PDF")
    try:
        with pdfplumber.open(file_path) as pdf:
            total = len(pdf.pages)
            logger.info(f"Extraction PDF page par page: {file_path} ({total} pages)")
            for idx, page in enumerate(pdf.pages):
                text = ""
                try:
                    text = page.extract_text() or ""
                except Exception as e:
                    logger.warning(f"Échec extract_text sur la page {idx+1}: {str(e)}")
                if not text and ocr_fallback:
                    try:
                        # Convertir la page en image et appliquer l'OCR
                        page_image = page.to_image(resolution=dpi).original
                        text = pytesseract.image_to_string(page_image, lang=lang)
                    except Exception as e:
                        logger.warning(f"Échec OCR fallback sur la page {idx+1}: {str(e)}")
                        text = ""
                yield idx, text
    except Exception as e:
        logger.error(f"Erreur lors de l'ouverture du PDF {file_path}: {str(e)}")


def extract_pdf_text_by_pages(file_path, ocr_fallback=False, dpi=200, lang="eng+fra"):
    """Retourne une liste des textes par page pour un PDF."""
    return [text for _, text in iter_pdf_text_pages(file_path, ocr_fallback=ocr_fallback, dpi=dpi, lang=lang)]


def extract_text_from_file(file_path):
    """Extrait le texte de différents types de fichiers."""
    logger.info(f"Extraction de texte depuis {file_path}")
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == ".pdf":
            with pdfplumber.open(file_path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        elif ext in [".png", ".jpg", ".jpeg"]:
            image = Image.open(file_path)
            return pytesseract.image_to_string(image)
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif ext == ".csv":
            import csv
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                return "\n".join([", ".join(row) for row in reader])
        elif ext == ".docx":
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        elif ext == ".xlsx":
            df = pd.read_excel(file_path)
            return df.to_csv(index=False)
        else:
            logger.warning(f"Format de fichier non supporté: {ext}")
            return ""
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction de texte: {str(e)}")
        return ""