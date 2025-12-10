# Guide d'installation et d'utilisation du modèle dots.ocr

Ce guide vous explique comment installer et utiliser correctement le modèle dots.ocr dans votre application, en évitant les erreurs courantes comme `VLModel object has no attribute load_model`.

## Table des matières

1. [Prérequis](#prérequis)
2. [Installation](#installation)
3. [Utilisation de base](#utilisation-de-base)
4. [Intégration dans une application existante](#intégration-dans-une-application-existante)
5. [Optimisation de la mémoire](#optimisation-de-la-mémoire)
6. [Résolution des problèmes courants](#résolution-des-problèmes-courants)

## Prérequis

Avant d'installer et d'utiliser le modèle dots.ocr, assurez-vous d'avoir :

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Au moins 8 Go de RAM disponible (16 Go recommandés)
- Un GPU avec au moins 4 Go de VRAM (optionnel mais recommandé)
- CUDA 11.7 ou supérieur (si vous utilisez un GPU NVIDIA)

## Installation

### 1. Mise à jour des bibliothèques essentielles

```bash
pip install --upgrade pip
pip install --upgrade torch torchvision torchaudio
pip install --upgrade transformers
pip install --upgrade pillow
```

### 2. Installation du modèle dots.ocr

Vous pouvez installer le modèle dots.ocr directement depuis GitHub :

```bash
pip install git+https://github.com/rednote-hilab/dots.ocr.git
```

Ou, si vous rencontrez des problèmes, vous pouvez cloner le dépôt et l'installer localement :

```bash
git clone https://github.com/rednote-hilab/dots.ocr.git
cd dots.ocr
pip install -e .
```

## Utilisation de base

Les scripts fournis dans ce projet vous permettent d'utiliser facilement le modèle dots.ocr :

### Utilisation du script `dots_ocr_model.py`

Ce script fournit une classe `DotsOCRModel` qui gère correctement le chargement du modèle :

```bash
python dots_ocr_model.py chemin/vers/votre/image.jpg "Prompt optionnel"
```

### Utilisation du script `exemple_utilisation_dots_ocr.py`

Ce script offre plus d'options, comme forcer l'utilisation du CPU ou sauvegarder le résultat dans un fichier :

```bash
python exemple_utilisation_dots_ocr.py chemin/vers/votre/image.jpg --prompt "Extraire le texte de cette image" --cpu --output resultat.txt
```

## Intégration dans une application existante

Pour intégrer le modèle dots.ocr dans votre application existante, vous pouvez utiliser le script `integration_dots_ocr.py` qui fournit un adaptateur compatible avec l'interface `VLModel` :

### 1. Importez les fonctions nécessaires

```python
from integration_dots_ocr import initialize_dots_ocr_model, analyze_image_with_dots_ocr, unload_model
```

### 2. Remplacez l'initialisation du modèle

Remplacez :

```python
model = VLModel("dots.ocr")
model.load_model()
```

Par :

```python
model = initialize_dots_ocr_model("rednote-hilab/dots.ocr")
model.load_model()
```

### 3. Utilisez le modèle pour analyser des images

```python
resultat = model.analyze_image("chemin/vers/image.jpg", "Prompt optionnel")
```

Ou utilisez directement la fonction d'analyse :

```python
resultat = analyze_image_with_dots_ocr("chemin/vers/image.jpg", "Prompt optionnel")
```

### 4. Libérez la mémoire après utilisation

```python
model.unload_model()  # Si vous utilisez l'adaptateur
# OU
unload_model()  # Si vous utilisez la fonction d'analyse directe
```

## Optimisation de la mémoire

Le modèle dots.ocr peut consommer beaucoup de mémoire. Voici quelques conseils pour optimiser son utilisation :

### 1. Forcer l'utilisation du CPU

Si vous n'avez pas de GPU ou si votre GPU n'a pas assez de mémoire, forcez l'utilisation du CPU :

```python
model = DotsOCRModel()
model.device_map = "cpu"
model.torch_dtype = torch.float32
model.load_in_4bit = False
```

### 2. Utiliser la quantification 4-bit

La quantification 4-bit peut réduire considérablement la consommation de mémoire :

```python
model = DotsOCRModel()
model.load_in_4bit = True
```

### 3. Libérer la mémoire après utilisation

Assurez-vous de libérer la mémoire après avoir utilisé le modèle :

```python
model.unload_model()
```

### 4. Utiliser le chargement paresseux

La classe `DotsOCRModel` implémente un chargement paresseux, ce qui signifie que le modèle n'est chargé que lorsque c'est nécessaire :

```python
model = DotsOCRModel()
# Le modèle n'est pas encore chargé ici

resultat = model.analyze_image("chemin/vers/image.jpg")
# Le modèle est chargé automatiquement lors de l'appel à analyze_image
```

## Résolution des problèmes courants

### Erreur : `VLModel object has no attribute load_model`

Cette erreur se produit lorsque vous essayez d'utiliser la méthode `load_model` sur un objet `VLModel` qui ne l'implémente pas.

**Solution** : Utilisez l'adaptateur fourni dans `integration_dots_ocr.py` :

```python
from integration_dots_ocr import initialize_dots_ocr_model

model = initialize_dots_ocr_model("rednote-hilab/dots.ocr")
model.load_model()
```

### Erreur : `CUDA out of memory`

Cette erreur se produit lorsque votre GPU n'a pas assez de mémoire pour charger le modèle.

**Solutions** :

1. Forcez l'utilisation du CPU :

```python
model = DotsOCRModel()
model.device_map = "cpu"
model.torch_dtype = torch.float32
model.load_in_4bit = False
```

2. Utilisez la quantification 4-bit :

```python
model = DotsOCRModel()
model.load_in_4bit = True
```

3. Libérez la mémoire GPU avant de charger le modèle :

```python
import torch
torch.cuda.empty_cache()
```

### Erreur : `ModuleNotFoundError: No module named 'transformers'`

Cette erreur se produit lorsque la bibliothèque `transformers` n'est pas installée.

**Solution** : Installez la bibliothèque `transformers` :

```bash
pip install transformers
```

### Erreur : `ImportError: cannot import name 'DotsVLProcessor' from 'transformers'`

Cette erreur se produit lorsque le modèle dots.ocr n'est pas correctement installé.

**Solution** : Réinstallez le modèle dots.ocr :

```bash
pip install git+https://github.com/rednote-hilab/dots.ocr.git
```

---

Pour toute autre question ou problème, n'hésitez pas à consulter la documentation officielle du modèle dots.ocr ou à ouvrir une issue sur le dépôt GitHub.