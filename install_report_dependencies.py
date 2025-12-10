import subprocess
import sys
import os
import platform

def check_wkhtmltopdf():
    """
    Vérifie si wkhtmltopdf est installé sur le système.
    
    Returns:
        bool: True si wkhtmltopdf est installé, False sinon
    """
    try:
        result = subprocess.run(["wkhtmltopdf", "--version"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def install_dependencies():
    """Installe les dépendances nécessaires pour la génération du rapport complet."""
    dependencies = [
        'pandas',
        'openpyxl',  # Pour lire les fichiers Excel
        'matplotlib',
        'numpy',
        'markdown',  # Pour la conversion Markdown vers HTML
        'xlsxwriter',  # Déjà installé mais inclus pour être complet
        'pdfkit'  # Pour la génération de PDF à partir de HTML
    ]
    
    print("Installation des dépendances nécessaires pour la génération du rapport...")
    
    for dependency in dependencies:
        print(f"Installation de {dependency}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dependency])
            print(f"{dependency} installé avec succès.")
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors de l'installation de {dependency}: {e}")
            return False
    
    print("\nToutes les dépendances ont été installées avec succès.")
    return True

def install_wkhtmltopdf():
    """
    Affiche les instructions pour installer wkhtmltopdf.
    """
    system = platform.system()
    print("\nwkhtmltopdf n'est pas installé sur votre système.")
    print("Cette bibliothèque est nécessaire pour générer des PDF à partir de HTML.")
    print("\nInstructions d'installation:")
    
    if system == "Windows":
        print("1. Téléchargez l'installateur depuis: https://wkhtmltopdf.org/downloads.html")
        print("2. Exécutez l'installateur et suivez les instructions")
        print("3. Assurez-vous que wkhtmltopdf est ajouté au PATH système")
    elif system == "Darwin":  # macOS
        print("1. Installez avec Homebrew: brew install wkhtmltopdf")
        print("   OU")
        print("2. Téléchargez l'installateur depuis: https://wkhtmltopdf.org/downloads.html")
    elif system == "Linux":
        print("1. Sur Ubuntu/Debian: sudo apt-get install wkhtmltopdf")
        print("2. Sur Fedora: sudo dnf install wkhtmltopdf")
        print("3. Sur CentOS/RHEL: sudo yum install wkhtmltopdf")
    
    print("\nAprès l'installation, relancez ce script pour continuer.")

def create_reports_directory():
    """
    Crée le répertoire pour stocker les rapports générés.
    """
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rapports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
        print(f"Répertoire créé: {reports_dir}")
    else:
        print(f"Le répertoire existe déjà: {reports_dir}")

def main():
    """Fonction principale."""
    print("=== Installation des dépendances pour la génération du rapport complet ===")
    
    # Vérification de wkhtmltopdf
    if not check_wkhtmltopdf():
        install_wkhtmltopdf()
        print("\nVeuillez installer wkhtmltopdf puis relancer ce script.")
        print("\nVous pouvez quand même continuer avec l'installation des autres dépendances.")
    
    # Installation des dépendances Python
    success = install_dependencies()
    
    # Création du répertoire pour les rapports
    if success:
        create_reports_directory()
        print("\nVous pouvez maintenant générer:")
        print("1. Le rapport complet avec la commande:")
        print("   python generate_complete_report.py resultats/analyse_risques.xlsx resultats/recommandations.xlsx resultats/plan_action.xlsx rapports")
        print("2. Le rapport sur dots.ocr avec la commande:")
        print("   python generate_dots_ocr_report.py")
    else:
        print("\nL'installation des dépendances a échoué. Veuillez résoudre les problèmes ci-dessus et réessayer.")

if __name__ == "__main__":
    main()