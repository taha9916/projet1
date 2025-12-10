import subprocess
import sys

def install_dependencies():
    """Installe les dépendances nécessaires pour le tableau de bord."""
    dependencies = [
        'pandas',
        'openpyxl',  # Pour lire les fichiers Excel
        'dash',
        'plotly',
        'xlsxwriter'  # Déjà installé mais inclus pour être complet
    ]
    
    print("Installation des dépendances nécessaires...")
    
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

def main():
    """Fonction principale."""
    print("=== Installation des dépendances pour le tableau de bord d'analyse environnementale ===")
    success = install_dependencies()
    
    if success:
        print("\nVous pouvez maintenant exécuter le tableau de bord avec la commande:")
        print("python create_dashboard.py resultats/analyse_risques.xlsx resultats/recommandations.xlsx resultats/plan_action.xlsx")
    else:
        print("\nL'installation des dépendances a échoué. Veuillez résoudre les problèmes ci-dessus et réessayer.")

if __name__ == "__main__":
    main()