#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script principal pour lancer les outils de diagnostic de l'application d'analyse de risque environnemental.

Ce script sert de point d'entrée unique pour tous les outils de diagnostic disponibles.
Il permet de diagnostiquer et résoudre les problèmes courants rencontrés lors de l'utilisation
de l'application, notamment les erreurs d'API et les problèmes d'extraction de paramètres.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    from logger import setup_logging, get_logger
except ImportError:
    print("Erreur: Impossible d'importer les modules nécessaires.")
    print("Assurez-vous que le fichier logger.py est présent dans le répertoire parent.")
    sys.exit(1)

# Configuration du logger
setup_logging()
logger = get_logger(__name__)

# Chemins des outils de diagnostic
DIAGNOSTIC_DIR = Path(__file__).resolve().parent
API_DIAGNOSTIC_PATH = DIAGNOSTIC_DIR / "api_diagnostic.py"
PARAMETER_EXTRACTOR_PATH = DIAGNOSTIC_DIR / "parameter_extractor.py"
CLOUD_API_TESTER_PATH = DIAGNOSTIC_DIR / "cloud_api_tester.py"
FIX_API_ISSUES_PATH = DIAGNOSTIC_DIR / "fix_api_issues.py"
FIX_EXTRACTION_ISSUES_PATH = DIAGNOSTIC_DIR / "fix_extraction_issues.py"


def run_api_diagnostic(args):
    """Lance l'outil de diagnostic API."""
    cmd = [sys.executable, str(API_DIAGNOSTIC_PATH)]
    
    if args.api_key:
        cmd.extend(["--api-key", args.api_key])
    
    if args.output:
        cmd.extend(["--output", args.output])
    
    if args.quiet:
        cmd.append("--quiet")
    
    logger.info(f"Lancement du diagnostic API: {' '.join(cmd)}")
    return subprocess.call(cmd)


def run_parameter_extractor(args):
    """Lance l'outil d'extraction de paramètres."""
    cmd = [sys.executable, str(PARAMETER_EXTRACTOR_PATH)]
    
    if args.file:
        cmd.extend(["--file", args.file])
    
    if args.output_excel:
        cmd.extend(["--output-excel", args.output_excel])
    
    if args.output_report:
        cmd.extend(["--output-report", args.output_report])
    
    logger.info(f"Lancement de l'extracteur de paramètres: {' '.join(cmd)}")
    return subprocess.call(cmd)


def run_cloud_api_tester(args):
    """Lance l'outil de test des API cloud."""
    cmd = [sys.executable, str(CLOUD_API_TESTER_PATH)]
    
    if args.all:
        cmd.append("--all")
    
    if args.google:
        cmd.append("--google")
    
    if args.azure:
        cmd.append("--azure")
    
    if args.openai:
        cmd.append("--openai")
    
    if args.output:
        cmd.extend(["--output", args.output])
    
    logger.info(f"Lancement du testeur d'API cloud: {' '.join(cmd)}")
    return subprocess.call(cmd)


def run_fix_api_issues(args):
    """Lance l'outil de correction des problèmes d'API."""
    cmd = [sys.executable, str(FIX_API_ISSUES_PATH)]
    
    if args.api_key:
        cmd.extend(["--api-key", args.api_key])
    
    if args.output:
        cmd.extend(["--output", args.output])
    
    if hasattr(args, 'open_console') and args.open_console:
        cmd.append("--open-console")
    
    if hasattr(args, 'test_alternatives') and args.test_alternatives:
        cmd.append("--test-alternatives")
    
    if hasattr(args, 'update_config') and args.update_config:
        cmd.append("--update-config")
    
    logger.info(f"Lancement de l'outil de correction des problèmes d'API: {' '.join(cmd)}")
    return subprocess.call(cmd)


def run_fix_extraction_issues(args):
    """Lance l'outil de correction des problèmes d'extraction."""
    cmd = [sys.executable, str(FIX_EXTRACTION_ISSUES_PATH)]
    
    if args.file:
        cmd.extend(["--file", args.file])
    
    if hasattr(args, 'output_excel') and args.output_excel:
        cmd.extend(["--output-excel", args.output_excel])
    
    if hasattr(args, 'output_report') and args.output_report:
        cmd.extend(["--output-report", args.output_report])
    
    if hasattr(args, 'analyze_only') and args.analyze_only:
        cmd.append("--analyze-only")
    
    if hasattr(args, 'suggest_improvements') and args.suggest_improvements:
        cmd.append("--suggest-improvements")
    
    logger.info(f"Lancement de l'outil de correction des problèmes d'extraction: {' '.join(cmd)}")
    return subprocess.call(cmd)


def run_full_diagnostic(args):
    """Lance un diagnostic complet avec tous les outils."""
    logger.info("Lancement du diagnostic complet")
    
    # Étape 1: Diagnostic API
    print("\n" + "=" * 80)
    print("ÉTAPE 1: DIAGNOSTIC DE L'API GOOGLE CLOUD VISION")
    print("=" * 80)
    api_result = run_api_diagnostic(args)
    
    # Étape 2: Test des API alternatives
    print("\n" + "=" * 80)
    print("ÉTAPE 2: TEST DES API ALTERNATIVES")
    print("=" * 80)
    api_test_args = argparse.Namespace(all=True, google=False, azure=False, openai=False, output=args.output)
    api_test_result = run_cloud_api_tester(api_test_args)
    
    # Étape 3: Correction des problèmes d'API (si diagnostic API a échoué)
    if api_result != 0:
        print("\n" + "=" * 80)
        print("ÉTAPE 3: CORRECTION DES PROBLÈMES D'API")
        print("=" * 80)
        fix_api_args = argparse.Namespace(
            api_key=args.api_key,
            output=args.output,
            test_alternatives=True,
            update_config=True,
            open_console=False
        )
        fix_api_result = run_fix_api_issues(fix_api_args)
    else:
        fix_api_result = 0
    
    # Étape 4: Extraction de paramètres (si un fichier est spécifié)
    if args.file:
        print("\n" + "=" * 80)
        print("ÉTAPE 4: ANALYSE DE L'EXTRACTION DE PARAMÈTRES")
        print("=" * 80)
        extractor_args = argparse.Namespace(
            file=args.file,
            output_excel=args.output_excel,
            output_report=args.output_report
        )
        extractor_result = run_parameter_extractor(extractor_args)
        
        # Étape 5: Correction des problèmes d'extraction (si extraction a échoué)
        if extractor_result != 0:
            print("\n" + "=" * 80)
            print("ÉTAPE 5: CORRECTION DES PROBLÈMES D'EXTRACTION")
            print("=" * 80)
            fix_extraction_args = argparse.Namespace(
                file=args.file,
                output_excel=args.output_excel,
                output_report=args.output_report,
                analyze_only=False,
                suggest_improvements=True
            )
            fix_extraction_result = run_fix_extraction_issues(fix_extraction_args)
        else:
            fix_extraction_result = 0
    else:
        extractor_result = 0
        fix_extraction_result = 0
    
    # Résumé
    print("\n" + "=" * 80)
    print("RÉSUMÉ DU DIAGNOSTIC COMPLET")
    print("=" * 80)
    print(f"Diagnostic API: {'Succès' if api_result == 0 else 'Échec'}")
    print(f"Test des API alternatives: {'Succès' if api_test_result == 0 else 'Échec'}")
    if api_result != 0:
        print(f"Correction des problèmes d'API: {'Succès' if fix_api_result == 0 else 'Échec'}")
    if args.file:
        print(f"Extraction de paramètres: {'Succès' if extractor_result == 0 else 'Échec'}")
        if extractor_result != 0:
            print(f"Correction des problèmes d'extraction: {'Succès' if fix_extraction_result == 0 else 'Échec'}")
    
    print("\nConsultez les rapports générés pour plus de détails.")
    print("Pour des instructions détaillées sur la résolution des problèmes, consultez:")
    print(f"  {DIAGNOSTIC_DIR / 'diagnostic_guide.md'}")
    
    return 0


def parse_arguments():
    """Parse les arguments de ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Outils de diagnostic pour l'application d'analyse de risque environnemental"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")
    
    # Sous-commande pour le diagnostic API
    api_parser = subparsers.add_parser("api", help="Diagnostic de l'API Google Cloud Vision")
    api_parser.add_argument("--api-key", help="Clé API Google Cloud Vision à tester")
    api_parser.add_argument("--output", help="Chemin du fichier de sortie pour le rapport JSON")
    api_parser.add_argument("--quiet", action="store_true", help="Mode silencieux (n'affiche pas le résumé)")
    
    # Sous-commande pour l'extracteur de paramètres
    extractor_parser = subparsers.add_parser("extract", help="Extraction améliorée des paramètres environnementaux")
    extractor_parser.add_argument("--file", required=True, help="Fichier texte à analyser")
    extractor_parser.add_argument("--output-excel", help="Chemin du fichier Excel de sortie")
    extractor_parser.add_argument("--output-report", help="Chemin du fichier de rapport texte")
    
    # Sous-commande pour le testeur d'API cloud
    api_test_parser = subparsers.add_parser("test-api", help="Test des API cloud (Google, Azure, OpenAI)")
    api_test_parser.add_argument("--all", action="store_true", help="Tester toutes les API configurées")
    api_test_parser.add_argument("--google", action="store_true", help="Tester l'API Google Cloud Vision")
    api_test_parser.add_argument("--azure", action="store_true", help="Tester l'API Azure Computer Vision")
    api_test_parser.add_argument("--openai", action="store_true", help="Tester l'API OpenAI")
    api_test_parser.add_argument("--output", help="Chemin du fichier de sortie pour le rapport JSON")
    
    # Sous-commande pour la correction des problèmes d'API
    fix_api_parser = subparsers.add_parser("fix-api", help="Correction des problèmes d'API Google Cloud Vision")
    fix_api_parser.add_argument("--api-key", help="Clé API Google Cloud Vision à tester")
    fix_api_parser.add_argument("--output", help="Chemin du fichier de sortie pour le rapport JSON")
    fix_api_parser.add_argument("--test-alternatives", action="store_true", help="Tester les API alternatives")
    fix_api_parser.add_argument("--update-config", action="store_true", help="Mettre à jour la configuration avec l'API fonctionnelle")
    fix_api_parser.add_argument("--open-console", action="store_true", help="Ouvrir la console Google Cloud")
    
    # Sous-commande pour la correction des problèmes d'extraction
    fix_extract_parser = subparsers.add_parser("fix-extract", help="Correction des problèmes d'extraction de paramètres")
    fix_extract_parser.add_argument("--file", required=True, help="Fichier texte à analyser")
    fix_extract_parser.add_argument("--output-excel", help="Chemin du fichier Excel de sortie")
    fix_extract_parser.add_argument("--output-report", help="Chemin du fichier de rapport texte")
    fix_extract_parser.add_argument("--analyze-only", action="store_true", help="Analyser uniquement sans appliquer de corrections")
    fix_extract_parser.add_argument("--suggest-improvements", action="store_true", help="Suggérer des améliorations pour le fichier")
    
    # Sous-commande pour le diagnostic complet
    full_parser = subparsers.add_parser("full", help="Diagnostic complet avec tous les outils")
    full_parser.add_argument("--api-key", help="Clé API Google Cloud Vision à tester")
    full_parser.add_argument("--file", help="Fichier texte à analyser pour l'extraction de paramètres")
    full_parser.add_argument("--output-excel", help="Chemin du fichier Excel de sortie pour l'extraction")
    full_parser.add_argument("--output-report", help="Chemin du fichier de rapport texte pour l'extraction")
    full_parser.add_argument("--output", help="Chemin du fichier de sortie pour les rapports JSON")
    
    return parser.parse_args()


def main():
    """Fonction principale."""
    args = parse_arguments()
    
    try:
        if args.command == "api":
            return run_api_diagnostic(args)
        elif args.command == "extract":
            return run_parameter_extractor(args)
        elif args.command == "test-api":
            return run_cloud_api_tester(args)
        elif args.command == "fix-api":
            return run_fix_api_issues(args)
        elif args.command == "fix-extract":
            return run_fix_extraction_issues(args)
        elif args.command == "full":
            return run_full_diagnostic(args)
        else:
            # Si aucune commande n'est spécifiée, afficher l'aide
            print("Veuillez spécifier une commande. Utilisez -h pour afficher l'aide.")
            print("\nCommandes disponibles:")
            print("  api         : Diagnostic de l'API Google Cloud Vision")
            print("  extract     : Extraction améliorée des paramètres environnementaux")
            print("  test-api    : Test des API cloud (Google, Azure, OpenAI)")
            print("  fix-api     : Correction des problèmes d'API Google Cloud Vision")
            print("  fix-extract : Correction des problèmes d'extraction de paramètres")
            print("  full        : Diagnostic complet avec tous les outils")
            return 1
    
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du diagnostic: {str(e)}")
        import traceback
        print(f"\nERREUR: {str(e)}")
        print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())