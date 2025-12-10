# Guide d'utilisation du modèle dots.ocr

Ce guide explique comment utiliser le modèle dots.ocr dans le projet d'analyse environnementale. Le modèle dots.ocr est un modèle léger (1.7B paramètres) optimisé pour l'extraction de texte et l'analyse de documents, qui peut fonctionner avec moins de 10 Go de RAM grâce à la quantification 4-bit.

## Prérequis

- Python 3.8 ou supérieur
- Moins de 10 Go de RAM (le modèle fonctionne avec environ 4-6 Go en 4-bit)
- CPU ou GPU (le modèle peut fonctionner sur CPU, mais un GPU accélère le traitement)

## Installation

1. Exécutez le script d'installation pour installer les dépendances et télécharger le modèle :

```bash
python install_dots_ocr.py
```

Ce script installe les packages nécessaires et télécharge le modèle dots.ocr depuis Hugging Face.

## Utilisation dans le code

### Analyse d'images environnementales

Vous pouvez utiliser le modèle dots.ocr pour analyser des images environnementales en spécifiant `dots_ocr` comme fournisseur d'API :

```python
from cloud_api import analyze_environmental_image_cloud

# Analyser une image avec dots.ocr
result_df, raw_response = analyze_environmental_image_cloud(
    image_path="chemin/vers/image.jpg",
    api_provider="dots_ocr",
    prompt="Analysez cette image environnementale et identifiez les risques potentiels."
)

# Afficher les résultats
print(raw_response)
print(result_df)
```

### Utilisation directe de CloudVisionAPI

Vous pouvez également utiliser directement la classe CloudVisionAPI :

```python
from cloud_api import CloudVisionAPI

# Créer une instance avec dots_ocr comme fournisseur
cloud_api = CloudVisionAPI(api_provider="dots_ocr")

# Analyser une image
result = cloud_api.analyze_image(
    image_path="chemin/vers/image.jpg",
    prompt="Analysez cette image et identifiez les éléments environnementaux importants."
)

# Afficher le résultat
print(result)

# Libérer la mémoire (important pour les systèmes avec peu de RAM)
del cloud_api.model
del cloud_api.processor
import torch
if torch.cuda.is_available():
    torch.cuda.empty_cache()
```

## Test du modèle

Vous pouvez tester le modèle avec le script de test fourni :

```bash
python test_dots_ocr.py chemin/vers/image.jpg
```

Vous pouvez également spécifier un prompt personnalisé :

```bash
python test_dots_ocr.py chemin/vers/image.jpg --prompt "Analysez cette image et identifiez les polluants visibles."
```

## Avantages du modèle dots.ocr

- **Faible consommation de mémoire** : Environ 4-6 Go en 4-bit, parfait pour les systèmes avec moins de 10 Go de RAM
- **Multilingue** : Supporte le français et l'arabe
- **Spécialisé pour les documents** : Très bon pour l'extraction de texte, tableaux et rapports
- **Local** : Fonctionne entièrement en local, sans besoin d'API externe
- **Rapide** : Plus rapide que les grands modèles comme GPT-4 ou Claude

## Gestion de la mémoire

Pour économiser la mémoire, le modèle est chargé à la demande et peut être libéré après utilisation :

```python
# Après utilisation du modèle
del cloud_api.model
del cloud_api.processor
import torch
if torch.cuda.is_available():
    torch.cuda.empty_cache()
```

## Limitations

- Moins précis que les grands modèles comme GPT-4 ou Claude pour les tâches complexes
- Temps de chargement initial plus long (première utilisation)
- Nécessite environ 4-6 Go de RAM même avec la quantification 4-bit

## Dépannage

### Erreur de mémoire insuffisante

Si vous rencontrez des erreurs de mémoire insuffisante :

1. Assurez-vous qu'aucune autre application gourmande en mémoire ne tourne en arrière-plan
2. Redémarrez Python/votre application pour libérer la mémoire
3. Essayez de réduire la taille des images avant l'analyse

### Erreur lors du chargement du modèle

Si le modèle ne se charge pas correctement :

1. Vérifiez que toutes les dépendances sont installées : `pip install -r requirements.txt`
2. Assurez-vous que bitsandbytes est correctement installé : `pip install bitsandbytes`
3. Réexécutez le script d'installation : `python install_dots_ocr.py`

## Ressources supplémentaires

- [Documentation de Hugging Face Transformers](https://huggingface.co/docs/transformers/index)
- [Documentation de bitsandbytes](https://github.com/TimDettmers/bitsandbytes)
- [Modèle dots.ocr sur Hugging Face](https://huggingface.co/rednote-hilab/dots.ocr)