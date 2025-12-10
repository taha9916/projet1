import os
import logging
import json
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import pandas as pd

# Import des modules du projet
from config import OUTPUT_DIR
from pipeline import AnalysisPipeline
from utils import setup_logging

# Configuration du logging
logger = setup_logging()

# Initialisation de l'application Flask
app = Flask(__name__)

# Configuration de l'upload
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

# Extensions autorisées
ALLOWED_EXTENSIONS = {
    'xlsx', 'xls', 'csv',  # Fichiers tabulaires
    'pdf', 'txt', 'docx',  # Fichiers texte
    'jpg', 'jpeg', 'png'   # Images
}

def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Page d'accueil de l'API."""
    return jsonify({
        "message": "API d'Analyse de Risque Environnemental - Maroc",
        "endpoints": {
            "/analyze": "POST - Analyser un fichier",
            "/results": "GET - Obtenir la liste des résultats",
            "/results/<filename>": "GET - Télécharger un fichier de résultats"
        }
    })

@app.route('/analyze', methods=['POST'])
def analyze_file():
    """Endpoint pour analyser un fichier."""
    # Vérifier si un fichier a été envoyé
    if 'file' not in request.files:
        return jsonify({"error": "Aucun fichier n'a été envoyé"}), 400
    
    file = request.files['file']
    
    # Vérifier si un fichier a été sélectionné
    if file.filename == '':
        return jsonify({"error": "Aucun fichier n'a été sélectionné"}), 400
    
    # Vérifier si l'extension est autorisée
    if not allowed_file(file.filename):
        return jsonify({"error": "Type de fichier non autorisé"}), 400
    
    # Sécuriser le nom du fichier et sauvegarder le fichier
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Récupérer le format de sortie demandé
    output_format = request.form.get('format', 'json')
    if output_format not in ['xlsx', 'csv', 'json']:
        output_format = 'json'
    
    try:
        # Analyser le fichier avec le pipeline
        pipeline = AnalysisPipeline()
        result = pipeline.process_file(file_path, output_format)
        
        if result is None:
            return jsonify({"error": "Échec de l'analyse du fichier"}), 500
        
        # Retourner les résultats selon le format demandé
        if output_format == 'json':
            # Si le résultat est déjà une chaîne JSON
            if isinstance(result, str):
                try:
                    # Vérifier que c'est un JSON valide
                    json_data = json.loads(result)
                    return jsonify({"result": json_data})
                except json.JSONDecodeError:
                    return jsonify({"error": "Erreur lors de la conversion en JSON"}), 500
            # Si le résultat est un chemin de fichier
            else:
                return jsonify({"result_file": os.path.basename(result)})
        else:
            # Pour xlsx et csv, retourner le chemin du fichier généré
            return jsonify({"result_file": os.path.basename(result)})
    
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du fichier: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
    finally:
        # Nettoyer le fichier uploadé après traitement
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning(f"Impossible de supprimer le fichier temporaire: {str(e)}")

@app.route('/results', methods=['GET'])
def list_results():
    """Liste les fichiers de résultats disponibles."""
    try:
        files = [f for f in os.listdir(OUTPUT_DIR) 
                if os.path.isfile(os.path.join(OUTPUT_DIR, f)) and 
                f.startswith("resultat_analyse_risque_")]
        
        return jsonify({"results": files})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des résultats: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/results/<filename>', methods=['GET'])
def download_result(filename):
    """Télécharge un fichier de résultats."""
    try:
        return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement du fichier: {str(e)}")
        return jsonify({"error": str(e)}), 404

def run_server(host="127.0.0.1", port=5000):
    """Lance le serveur Flask."""
    logger.info(f"Démarrage du serveur sur {host}:{port}")
    app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    run_server()