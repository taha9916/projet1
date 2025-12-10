# Guide d'utilisation de dots.ocr pour l'extraction de données de rapports

Ce guide explique comment utiliser le modèle dots.ocr pour extraire des données structurées à partir de rapports environnementaux, de pollution, ou de biodiversité.

## Introduction

Le modèle dots.ocr est un modèle léger (1.7B paramètres) optimisé pour l'extraction de texte et l'analyse de documents. Il peut fonctionner avec moins de 10 Go de RAM grâce à la quantification 4-bit, ce qui le rend accessible sur des machines avec des ressources limitées.

Dans ce projet, nous avons intégré dots.ocr pour extraire automatiquement des données structurées à partir de rapports environnementaux, facilitant ainsi l'analyse et le traitement des informations.

## Prérequis

- Python 3.8 ou supérieur
- Moins de 10 Go de RAM (le modèle fonctionne avec environ 4-6 Go en 4-bit)
- CPU ou GPU (le modèle peut fonctionner sur CPU, mais un GPU accélère le traitement)
- Les bibliothèques requises (installées automatiquement par le script d'installation)

## Installation

1. Exécutez le script d'installation pour installer les dépendances et télécharger le modèle :

```bash
python install_dots_ocr.py
```

Ce script installe les packages nécessaires et télécharge le modèle dots.ocr depuis Hugging Face.

## Extraction de données de rapports

Nous avons créé deux scripts principaux pour l'extraction de données :

1. `extraire_donnees_rapports.py` : Script principal pour extraire des données de rapports
2. `demo_extraction_rapports.py` : Script de démonstration avec des fonctionnalités supplémentaires

### Utilisation de base

Pour extraire des données d'un rapport (image ou PDF), utilisez la commande suivante :

```bash
python extraire_donnees_rapports.py chemin/vers/rapport.jpg
```

Par défaut, le script considère qu'il s'agit d'un rapport environnemental et renvoie les résultats sous forme de DataFrame pandas.

### Options avancées

Vous pouvez spécifier le type de rapport et le format de sortie :

```bash
python extraire_donnees_rapports.py chemin/vers/rapport.pdf environnement markdown
```

Types de rapports disponibles :
- `environnement` (par défaut) : Pour les rapports environnementaux généraux
- `pollution` : Pour les rapports de pollution (air, eau, sol)
- `biodiversite` : Pour les rapports de biodiversité

Formats de sortie disponibles :
- `dataframe` (par défaut) : Renvoie un DataFrame pandas
- `json` : Renvoie une chaîne JSON
- `dict` : Renvoie un dictionnaire Python
- `markdown` : Renvoie le texte brut avec les tableaux au format Markdown

### Utilisation du script de démonstration

Le script de démonstration offre une interface plus conviviale avec des options supplémentaires :

```bash
python demo_extraction_rapports.py chemin/vers/rapport.jpg -t environnement -f markdown
```

Options disponibles :
- `-t, --type` : Type de rapport (`environnement`, `pollution`, `biodiversite`)
- `-f, --format` : Format de sortie (`dataframe`, `json`, `dict`, `markdown`)
- `-n, --no-save` : Ne pas sauvegarder les résultats

## Utilisation dans votre code

Vous pouvez également utiliser les fonctions d'extraction directement dans votre code :

```python
from extraire_donnees_rapports import extraire_donnees_rapport

# Extraire des données d'un rapport environnemental
resultat = extraire_donnees_rapport(
    fichier_path="chemin/vers/rapport.jpg",
    type_rapport="environnement",
    format_sortie="dataframe"
)

# Afficher les résultats
print(resultat)

# Sauvegarder les résultats
resultat.to_excel("resultats.xlsx", index=False)
```

## Extraction de tableaux Markdown

Si vous obtenez des résultats au format Markdown, vous pouvez extraire les tableaux et les convertir en DataFrames :

```python
from extraire_donnees_rapports import extraire_tableaux_markdown, convertir_tableaux_en_dataframes

# Extraire des données au format Markdown
resultat_markdown = extraire_donnees_rapport(
    fichier_path="chemin/vers/rapport.jpg",
    type_rapport="environnement",
    format_sortie="markdown"
)

# Extraire les tableaux du texte Markdown
tableaux = extraire_tableaux_markdown(resultat_markdown)

# Convertir les tableaux en DataFrames
dataframes = convertir_tableaux_en_dataframes(tableaux)

# Traiter chaque DataFrame
for i, df in enumerate(dataframes, 1):
    print(f"Tableau {i}:")
    print(df)
    
    # Sauvegarder le DataFrame
    df.to_excel(f"tableau_{i}.xlsx", index=False)
```

## Traitement des PDF

Le script peut également traiter des fichiers PDF en les convertissant page par page en images, puis en analysant chaque image avec dots.ocr. Pour cela, vous devez installer la bibliothèque PyMuPDF :

```bash
pip install pymupdf
```

Ensuite, vous pouvez utiliser le script normalement avec des fichiers PDF :

```bash
python extraire_donnees_rapports.py chemin/vers/rapport.pdf
```

## Avantages de dots.ocr pour l'extraction de données

- **Faible consommation de mémoire** : Fonctionne avec environ 4-6 Go de RAM
- **Multilingue** : Supporte le français et l'arabe
- **Spécialisé pour les documents** : Très bon pour l'extraction de texte, tableaux et rapports
- **Local** : Fonctionne entièrement en local, sans besoin d'API externe
- **Rapide** : Plus rapide que les grands modèles comme GPT-4 ou Claude

## Gestion de la mémoire

Pour économiser la mémoire, le modèle est chargé à la demande et peut être libéré après utilisation :

```python
# Après utilisation du modèle
del api.model
del api.processor
import torch
if torch.cuda.is_available():
    torch.cuda.empty_cache()
```

## Exemples d'utilisation

### Exemple 1 : Extraction de paramètres environnementaux

```bash
python demo_extraction_rapports.py rapports/rapport_environnement.jpg -t environnement -f markdown
```

### Exemple 2 : Extraction de données de pollution

```bash
python demo_extraction_rapports.py rapports/rapport_pollution.pdf -t pollution -f dataframe
```

### Exemple 3 : Extraction de données de biodiversité

```bash
python demo_extraction_rapports.py rapports/rapport_biodiversite.jpg -t biodiversite -f json
```

## Dépannage

### Problèmes de mémoire

Si vous rencontrez des problèmes de mémoire, essayez les solutions suivantes :

1. Assurez-vous que le modèle est chargé en 4-bit (paramètre par défaut)
2. Fermez les applications gourmandes en mémoire
3. Traitez les PDF page par page plutôt qu'en une seule fois
4. Utilisez un GPU si disponible

### Erreurs d'installation

Si vous rencontrez des erreurs lors de l'installation, vérifiez les points suivants :

1. Assurez-vous d'avoir Python 3.8 ou supérieur
2. Vérifiez que vous avez les droits d'administrateur pour installer les packages
3. Essayez d'installer les dépendances manuellement :

```bash
pip install torch transformers pillow pandas pymupdf
```

## Conclusion

L'utilisation de dots.ocr pour l'extraction de données de rapports environnementaux offre une solution légère, rapide et locale pour automatiser l'analyse de documents. Les scripts fournis permettent d'extraire facilement des données structurées à partir d'images ou de PDF, facilitant ainsi le traitement et l'analyse des informations environnementales.