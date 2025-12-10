import os
import sys
import argparse
import tkinter as tk
from tkinter import messagebox
import pandas as pd
import json
from pathlib import Path

# Import des modules du projet
from config import OUTPUT_DIR
from app import RiskAnalysisApp
from pipeline import AnalysisPipeline
from utils import save_dataframe_to_excel, get_timestamp

# Import du nouveau système de logging centralisé
from logger import setup_logging, get_logger, AuditLogger

# Configuration du logging
logger = setup_logging()

# Initialiser le logger d'audit pour les actions importantes
audit_logger = AuditLogger()

def process_file(file_path, output_format='xlsx', user="system", ip="localhost"):
    """Traite un fichier d'entrée et retourne les résultats.
    
    Args:
        file_path: Chemin vers le fichier à traiter
        output_format: Format de sortie ('xlsx', 'csv', 'json')
        user: Nom de l'utilisateur effectuant l'action (pour l'audit)
        ip: Adresse IP de l'utilisateur (pour l'audit)
        
    Returns:
        Tuple (DataFrame, chemin_sortie ou chaîne JSON)
    """
    try:
        logger.info(f"Traitement du fichier: {file_path}")
        
        # Enregistrer l'action dans le log d'audit
        audit_logger.log_action(
            action="Début traitement fichier",
            user=user,
            ip=ip,
            fichier=file_path,
            format=output_format
        )
        
        # Utiliser le pipeline d'analyse
        pipeline = AnalysisPipeline()
        result = pipeline.process_file(file_path, output_format)
        
        if result is None:
            logger.error(f"Échec du traitement du fichier {file_path}")
            # Enregistrer l'échec dans le log d'audit
            audit_logger.log_action(
                action="Échec traitement fichier",
                user=user,
                ip=ip,
                fichier=file_path,
                format=output_format,
                level="ERROR"
            )
            return None, None
        
        # Si le résultat est un DataFrame (format='df')
        if isinstance(result, pd.DataFrame):
            output_path = save_dataframe_to_excel(result, directory=OUTPUT_DIR)
            logger.info(f"Traitement terminé. Résultats sauvegardés dans {output_path}")
            
            # Enregistrer le succès dans le log d'audit
            audit_logger.log_action(
                action="Fichier traité avec succès",
                user=user,
                ip=ip,
                fichier=file_path,
                resultat=output_path,
                nb_lignes=len(result)
            )
            
            return result, output_path
        
        # Si le résultat est une chaîne JSON
        elif output_format == 'json' and isinstance(result, str):
            logger.info("Traitement terminé. Résultats au format JSON.")
            
            # Enregistrer le succès dans le log d'audit
            audit_logger.log_action(
                action="Fichier traité avec succès (JSON)",
                user=user,
                ip=ip,
                fichier=file_path,
                format="json"
            )
            
            return None, result
        
        # Si le résultat est un chemin de fichier
        else:
            logger.info(f"Traitement terminé. Résultats sauvegardés dans {result}")
            
            # Enregistrer le succès dans le log d'audit
            audit_logger.log_action(
                action="Fichier traité avec succès",
                user=user,
                ip=ip,
                fichier=file_path,
                resultat=result
            )
            
            return None, result
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Erreur lors du traitement du fichier: {error_msg}")
        
        # Enregistrer l'erreur dans le log d'audit
        audit_logger.log_action(
            action="Erreur lors du traitement",
            user=user,
            ip=ip,
            fichier=file_path,
            erreur=error_msg,
            level="ERROR"
        )
        
        return None, None

def run_batch_processing(input_dir, output_dir=None, output_format='xlsx', file_types=None):
    """Traite tous les fichiers dans un répertoire.
    
    Args:
        input_dir: Répertoire contenant les fichiers à traiter
        output_dir: Répertoire de sortie (par défaut: OUTPUT_DIR)
        output_format: Format de sortie ('xlsx', 'csv', 'json')
        file_types: Liste des extensions de fichiers à traiter (par défaut: tous les types supportés)
        
    Returns:
        Liste des résultats de traitement
    """
    if output_dir is None:
        output_dir = OUTPUT_DIR
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Types de fichiers supportés par défaut
    if file_types is None:
        file_types = ['.xlsx', '.xls', '.csv', '.pdf', '.txt', '.docx', '.jpg', '.jpeg', '.png']
    
    logger.info(f"Traitement par lot des fichiers dans {input_dir}")
    results = []
    
    # Utiliser le pipeline d'analyse
    pipeline = AnalysisPipeline()
    
    # Traiter tous les fichiers du répertoire
    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)
        if os.path.isfile(file_path) and any(filename.lower().endswith(ext) for ext in file_types):
            if filename.startswith("~$"):  # Ignorer les fichiers temporaires
                continue
                
            logger.info(f"Traitement du fichier: {filename}")
            result = pipeline.process_file(file_path, output_format)
            
            if result is not None:
                output_file = result if isinstance(result, str) else os.path.basename(result)
                results.append({
                    "input_file": filename,
                    "output_file": output_file,
                    "status": "Succès"
                })
            else:
                results.append({
                    "input_file": filename,
                    "output_file": "",
                    "status": "Échec"
                })
    
    # Créer un rapport de traitement par lot
    if results:
        report_df = pd.DataFrame(results)
        timestamp = get_timestamp()
        report_path = os.path.join(output_dir, f"rapport_traitement_{timestamp}.xlsx")
        report_df.to_excel(report_path, index=False)
        logger.info(f"Rapport de traitement par lot sauvegardé dans {report_path}")
    
    return results

def run_gui():
    """Lance l'interface graphique de l'application."""
    try:
        logger.info("Démarrage de l'interface graphique")
        root = tk.Tk()
        app = RiskAnalysisApp(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'interface graphique: {str(e)}")
        messagebox.showerror("Erreur de Démarrage", f"Une erreur est survenue au démarrage de l'application :\n{str(e)}")

def setup_argparse():
    """Configure l'analyseur d'arguments en ligne de commande."""
    parser = argparse.ArgumentParser(description="Analyse de Risque Environnemental - Maroc")
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")
    
    # Sous-commande pour l'interface graphique
    gui_parser = subparsers.add_parser("gui", help="Lance l'interface graphique")
    
    # Sous-commande pour traiter un fichier unique
    file_parser = subparsers.add_parser("file", help="Traite un fichier spécifique")
    file_parser.add_argument("file_path", help="Chemin vers le fichier à traiter")
    file_parser.add_argument("--format", choices=["xlsx", "csv", "json"], default="xlsx",
                           help="Format de sortie (xlsx, csv, json)")
    
    # Sous-commande pour traiter un lot de fichiers
    batch_parser = subparsers.add_parser("batch", help="Traite tous les fichiers dans un répertoire")
    batch_parser.add_argument("input_dir", help="Répertoire contenant les fichiers à traiter")
    batch_parser.add_argument("--output-dir", help="Répertoire de sortie")
    batch_parser.add_argument("--format", choices=["xlsx", "csv", "json"], default="xlsx",
                            help="Format de sortie (xlsx, csv, json)")
    batch_parser.add_argument("--file-types", nargs="+", 
                            help="Types de fichiers à traiter (ex: .xlsx .pdf .jpg)")
    
    # Sous-commande pour lancer le serveur web
    server_parser = subparsers.add_parser("server", help="Lance le serveur web")
    server_parser.add_argument("--host", default="127.0.0.1", help="Adresse d'hôte du serveur")
    server_parser.add_argument("--port", type=int, default=5000, help="Port du serveur")
    
    return parser

if __name__ == "__main__":
    # Créer le répertoire de sortie s'il n'existe pas
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Configurer l'analyseur d'arguments
    parser = setup_argparse()
    args = parser.parse_args()
    
    # Exécuter la commande appropriée
    if args.command == "gui" or args.command is None:
        # Par défaut, lancer l'interface graphique
        run_gui()
    
    elif args.command == "file":
        # Traiter un fichier unique
        result, output = process_file(args.file_path, args.format)
        
        if output is not None:
            if args.format == "json":
                print(output)  # Afficher le JSON dans la console
            else:
                print(f"Traitement terminé. Résultats sauvegardés dans {output}")
        else:
            print("Échec du traitement du fichier.")
    
    elif args.command == "batch":
        # Traiter un lot de fichiers
        file_types = args.file_types if args.file_types else None
        results = run_batch_processing(
            args.input_dir, 
            args.output_dir, 
            args.format, 
            file_types
        )
        print(f"{len(results)} fichiers traités.")
    
    elif args.command == "server":
        # Lancer le serveur web
        try:
            from server import run_server
            run_server(args.host, args.port)
        except ImportError:
            logger.error("Module server.py non trouvé. Veuillez créer ce module pour utiliser cette fonctionnalité.")
            print("Erreur: Module server.py non trouvé. Veuillez créer ce module pour utiliser cette fonctionnalité.")
    
    else:
        # Afficher l'aide si aucune commande n'est spécifiée
        parser.print_help()