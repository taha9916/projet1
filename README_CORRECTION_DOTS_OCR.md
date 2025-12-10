# Correction de l'erreur `VLModel object has no attribute load_model`

Ce projet contient des scripts pour corriger l'erreur `VLModel object has no attribute load_model` lors de l'utilisation du modèle dots.ocr.

## Table des matières

1. [Présentation du problème](#présentation-du-problème)
2. [Solution proposée](#solution-proposée)
3. [Installation](#installation)
4. [Utilisation](#utilisation)
5. [Tests](#tests)
6. [Optimisation de la mémoire](#optimisation-de-la-mémoire)
7. [Résolution des problèmes courants](#résolution-des-problèmes-courants)

## Présentation du problème

L'erreur `VLModel object has no attribute load_model` se produit lorsque vous essayez d'utiliser la méthode `load_model` sur un objet `VLModel` qui ne l'implémente pas. Cette erreur est courante lors de l'utilisation du modèle dots.ocr dans une application existante.

## Solution proposée

La solution proposée consiste à créer une classe `DotsOCRModel` qui implémente correctement la méthode `load_model` et à fournir un adaptateur compatible avec l'interface `VLModel` pour intégrer facilement le modèle dots.ocr dans une application existante.

## Installation

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Au moins 8 Go de RAM disponible (16 Go recommandés)
- Un GPU avec au moins 4 Go de VRAM (optionnel mais recommandé)
- CUDA 11.7 ou supérieur (si vous utilisez un GPU NVIDIA)

### Installation automatique

Utilisez le script `installer_dots_ocr.py` pour installer automatiquement les dépendances nécessaires et le modèle dots.ocr :

```bash
python installer_dots_ocr.py
```

Options disponibles :

- `--skip-dependencies` : Saute l'installation des dépendances
- `--skip-dots-ocr` : Saute l'installation du modèle dots.ocr
- `--force` : Force la réinstallation même si déjà installé

### Installation manuelle

Si vous préférez installer manuellement les dépendances, suivez ces étapes :

1. Mettez à jour pip :

```bash
pip install --upgrade pip
```

2. Installez les dépendances :

```bash
pip install --upgrade torch torchvision torchaudio
pip install --upgrade transformers
pip install --upgrade pillow
pip install --upgrade tqdm
pip install --upgrade accelerate
pip install --upgrade bitsandbytes
```

3. Installez le modèle dots.ocr :

```bash
pip install git+https://github.com/rednote-hilab/dots.ocr.git
```

## Utilisation

### Utilisation de base

Utilisez le script `dots_ocr_model.py` pour analyser une image avec le modèle dots.ocr :

```bash
python dots_ocr_model.py chemin/vers/votre/image.jpg "Prompt optionnel"
```

### Utilisation avancée

Utilisez le script `exemple_utilisation_dots_ocr.py` pour plus d'options :

```bash
python exemple_utilisation_dots_ocr.py chemin/vers/votre/image.jpg --prompt "Extraire le texte de cette image" --cpu --output resultat.txt
```

Options disponibles :

- `--prompt` : Instructions pour l'analyse
- `--cpu` : Force l'utilisation du CPU
- `--output` : Chemin pour sauvegarder le résultat

### Intégration dans une application existante

Utilisez le script `integration_dots_ocr.py` pour intégrer le modèle dots.ocr dans une application existante :

```python
from integration_dots_ocr import initialize_dots_ocr_model, analyze_image_with_dots_ocr, unload_model

# Initialiser le modèle
model = initialize_dots_ocr_model("rednote-hilab/dots.ocr")
model.load_model()

# Analyser une image
resultat = model.analyze_image("chemin/vers/image.jpg", "Prompt optionnel")

# Libérer la mémoire
model.unload_model()
```

Ou utilisez directement la fonction d'analyse :

```python
from integration_dots_ocr import analyze_image_with_dots_ocr, unload_model

# Analyser une image
resultat = analyze_image_with_dots_ocr("chemin/vers/image.jpg", "Prompt optionnel")

# Libérer la mémoire
unload_model()
```

## Tests

Utilisez le script `test_dots_ocr_implementation.py` pour tester l'implémentation :

```bash
python test_dots_ocr_implementation.py --image chemin/vers/votre/image.jpg
```

Options disponibles :

- `--image` : Chemin vers une image de test
- `--skip-model-tests` : Saute les tests qui nécessitent le chargement du modèle

## Optimisation de la mémoire

Le modèle dots.ocr peut consommer beaucoup de mémoire. Voici quelques conseils pour optimiser son utilisation :

### Forcer l'utilisation du CPU

Si vous n'avez pas de GPU ou si votre GPU n'a pas assez de mémoire, forcez l'utilisation du CPU :

```python
from dots_ocr_model import DotsOCRModel
import torch

model = DotsOCRModel()
model.device_map = "cpu"
model.torch_dtype = torch.float32
model.load_in_4bit = False
```

### Utiliser la quantification 4-bit

La quantification 4-bit peut réduire considérablement la consommation de mémoire :

```python
from dots_ocr_model import DotsOCRModel

model = DotsOCRModel()
model.load_in_4bit = True
```

### Libérer la mémoire après utilisation

Assurez-vous de libérer la mémoire après avoir utilisé le modèle :

```python
model.unload_model()
```

## Résolution des problèmes courants

Consultez le fichier `GUIDE_INSTALLATION_DOTS_OCR.md` pour plus d'informations sur la résolution des problèmes courants.

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
from dots_ocr_model import DotsOCRModel
import torch

model = DotsOCRModel()
model.device_map = "cpu"
model.torch_dtype = torch.float32
model.load_in_4bit = False
```

2. Utilisez la quantification 4-bit :

```python
from dots_ocr_model import DotsOCRModel

model = DotsOCRModel()
model.load_in_4bit = True
```

3. Libérez la mémoire GPU avant de charger le modèle :

```python
import torch
torch.cuda.empty_cache()
```

---

Pour plus d'informations, consultez le fichier `GUIDE_INSTALLATION_DOTS_OCR.md`.