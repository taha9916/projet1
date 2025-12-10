# Guide de Lancement Rapide

Ce guide explique comment lancer rapidement l'application d'analyse de risque environnemental et utiliser dots.ocr comme IA locale.

## Méthodes de lancement

Vous pouvez lancer l'application de plusieurs façons :

### 1. Lancement de l'interface graphique

Pour lancer l'application avec l'interface graphique, double-cliquez simplement sur le fichier :

```
lancer_application.bat
```

Cela ouvrira l'interface graphique de l'application où vous pourrez charger et analyser vos fichiers.

### 2. Lancement du serveur web

Pour lancer l'application en mode serveur web, double-cliquez sur le fichier :

```
lancer_serveur_web.bat
```

Cela démarrera un serveur web local accessible à l'adresse http://127.0.0.1:5000 dans votre navigateur.

### 3. Lancement en ligne de commande

Vous pouvez également lancer l'application avec des options spécifiques en utilisant la ligne de commande :

```
python main.py [commande] [options]
```

Commandes disponibles :
- `gui` : Lance l'interface graphique
- `file` : Traite un fichier spécifique
- `batch` : Traite tous les fichiers dans un répertoire
- `server` : Lance le serveur web

Exemples :
```
python main.py file chemin/vers/fichier.xlsx --format xlsx
python main.py batch chemin/vers/dossier --format json
```

## Prérequis

Assurez-vous que Python est installé sur votre système et que toutes les dépendances du projet sont installées. Si ce n'est pas le cas, exécutez :

```
pip install -r requirements.txt
```

## Utilisation de dots.ocr comme IA locale

Le projet intègre dots.ocr, un modèle léger (1.7B paramètres) qui fonctionne entièrement en local pour l'extraction de texte et l'analyse de documents.

### Installation de dots.ocr

Pour installer dots.ocr, exécutez le script d'installation :

```
python install_dots_ocr.py
```

Ce script installe les dépendances nécessaires et télécharge le modèle depuis Hugging Face.

### Utilisation de dots.ocr dans l'application

Pour utiliser dots.ocr comme IA locale par défaut :

1. Ouvrez le fichier `cloud_api_config.json`
2. Modifiez la valeur de `default_provider` à `"dots_ocr"`

```json
{
  "default_provider": "dots_ocr",
  "providers": {
    "dots_ocr": {
      "model_id": "rednote-hilab/dots.ocr"
    },
    ...
  }
}
```

### Utilisation en ligne de commande

Vous pouvez utiliser dots.ocr directement en ligne de commande avec plusieurs scripts :

```
# Script de démonstration simple
python demo_dots_ocr_local.py chemin/vers/image.jpg

# Avec un prompt personnalisé
python demo_dots_ocr_local.py chemin/vers/image.jpg -p "Analysez cette image et identifiez les polluants visibles."

# Utilisation directe du modèle
python utiliser_dots_ocr.py chemin/vers/image.jpg

# Utilisation via l'API
python utiliser_dots_ocr_api.py chemin/vers/image.jpg
```

### Extraction de données de rapports

Pour extraire des données de rapports environnementaux :

```
python extraire_donnees_rapports.py chemin/vers/rapport.jpg
```

Ou avec le script de démonstration :

```
python demo_extraction_rapports.py chemin/vers/rapport.jpg
```

Pour plus d'informations, consultez le fichier `GUIDE_DOTS_OCR.md` et `GUIDE_EXTRACTION_RAPPORTS.md`.

## Problèmes courants

Si vous rencontrez des problèmes lors du lancement de l'application :

1. Vérifiez que Python est correctement installé et accessible dans votre PATH système
2. Assurez-vous que toutes les dépendances sont installées
3. Consultez les fichiers de log dans le répertoire du projet pour plus d'informations sur les erreurs