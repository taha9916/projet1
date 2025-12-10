# Guide d'utilisation de dots.ocr - IA Locale

Ce guide explique comment utiliser le modèle dots.ocr comme IA locale pour l'analyse d'images et l'extraction de texte dans le cadre du projet d'analyse de risque environnemental pour le Maroc.

## Présentation

dots.ocr est un modèle léger (1.7B paramètres) optimisé pour l'extraction de texte et l'analyse de documents. Il nécessite moins de ressources que les grands modèles de vision et peut fonctionner sur CPU.

## Prérequis

- Python 3.8 ou supérieur
- Bibliothèques requises : transformers, torch, PIL

## Lancement rapide

Le moyen le plus simple d'utiliser dots.ocr est d'exécuter le script `lancer_dots_ocr.bat` qui ouvre une console avec toutes les options disponibles :

```bash
lancer_dots_ocr.bat
```

Vous pouvez également créer un raccourci sur votre bureau en exécutant :

```powershell
powershell -ExecutionPolicy Bypass -File creer_raccourci_bureau.ps1
```

## Scripts disponibles

Ce projet contient plusieurs scripts pour utiliser dots.ocr :

### 1. demo_dots_ocr_local.py

Ce script de démonstration montre comment utiliser dots.ocr pour analyser des images environnementales.

**Usage :**
```bash
python demo_dots_ocr_local.py <chemin_image> [-p prompt]
```

**Exemple :**
```bash
python demo_dots_ocr_local.py images/pollution.jpg -p "Identifie les polluants visibles dans cette image."
```

### 2. tester_dots_ocr.py

Ce script effectue un test rapide de dots.ocr en créant une image de test et en l'analysant.

**Usage :**
```bash
python tester_dots_ocr.py
```

### 3. verifier_dots_ocr.py

Ce script vérifie si dots.ocr est correctement installé et configuré.

**Usage :**
```bash
python verifier_dots_ocr.py
```

### 4. utiliser_dots_ocr.py

Ce script charge directement le modèle dots.ocr depuis Hugging Face et l'utilise pour analyser une image.

**Usage :**
```bash
python utiliser_dots_ocr.py <chemin_image> [prompt]
```

**Exemple :**
```bash
python utiliser_dots_ocr.py images/facture.jpg "Extrais toutes les informations de cette facture."
```

### 5. utiliser_dots_ocr_api.py

Ce script utilise l'API CloudVisionAPI pour analyser une image avec dots.ocr.

**Usage :**
```bash
python utiliser_dots_ocr_api.py <chemin_image> [prompt]
```

**Exemple :**
```bash
python utiliser_dots_ocr_api.py images/document.jpg "Résume ce document."
```

### 6. analyser_environnement.py

Ce script est spécialisé dans l'analyse d'images environnementales (documents techniques, relevés, etc.) avec dots.ocr.

**Usage :**
```bash
python analyser_environnement.py <chemin_image>
```

### 7. extraire_donnees_rapports.py

Ce script permet d'extraire des données structurées à partir de rapports environnementaux (PDF ou images).

**Usage :**
```bash
python extraire_donnees_rapports.py <chemin_fichier> --type <type_rapport> --format <format_sortie> [--save]
```

**Exemple :**
```bash
python extraire_donnees_rapports.py rapports/rapport_env.pdf --type environnement --format markdown --save
```

### 8. demo_extraction_rapports.py

Ce script de démonstration montre comment utiliser le module d'extraction de données de rapports.

**Usage :**
```bash
python demo_extraction_rapports.py <chemin_fichier> --type <type_rapport> --format <format_sortie> [--save]
```

**Exemple :**
```bash
python demo_extraction_rapports.py rapports/pollution.jpg --type pollution --format json
```

## Intégration dans votre code

### Analyse d'images

```python
from cloud_api import CloudVisionAPI

# Créer une instance avec dots_ocr comme fournisseur
api = CloudVisionAPI(api_provider="dots_ocr")

# Analyser une image
df, response = api.analyze_image("chemin/vers/image.jpg", "Décrivez les éléments environnementaux visibles dans cette image.")

# Afficher les résultats
print(response)
print(df)

# Libérer la mémoire (important pour les ressources limitées)
api.cleanup()
```

### Extraction de données de rapports

```python
from extraire_donnees_rapports import extraire_donnees_rapport

# Extraire des données d'un rapport
resultat = extraire_donnees_rapport(
    "chemin/vers/rapport.pdf",
    type_rapport="environnement",
    format_sortie="markdown"
)

# Afficher les résultats
print(resultat)
```

**Usage original de analyser_environnement.py :**
```bash
python analyser_environnement.py <chemin_image> [langue]
```

## Dépannage

### Problèmes de mémoire

Si vous rencontrez des problèmes de mémoire ("Out of memory"), essayez les solutions suivantes :

1. Fermez les applications gourmandes en mémoire avant d'utiliser dots.ocr
2. Utilisez l'option de nettoyage après chaque analyse : `api.cleanup()`
3. Redémarrez votre environnement Python entre les analyses

### Erreurs d'importation

Si vous obtenez des erreurs d'importation, vérifiez que tous les modules nécessaires sont installés :

```bash
pip install pillow pandas numpy torch transformers
```

Pour les fonctionnalités PDF, installez également :

```bash
pip install pymupdf
```

**Exemple :**
```bash
python analyser_environnement.py <chemin_image> [langue]
```

## Documentation complémentaire

Pour plus d'informations, consultez les guides suivants :

- `GUIDE_DOTS_OCR.md` : Documentation détaillée sur le modèle dots.ocr
- `GUIDE_EXTRACTION_RAPPORTS.md` : Guide d'utilisation pour l'extraction de données de rapports
- `GUIDE_LANCEMENT_RAPIDE.md` : Instructions pour le lancement rapide de l'application

## Conseils d'utilisation

### Optimisation de la mémoire

- Le modèle dots.ocr nécessite environ 4-6 Go de RAM, même en mode 4-bit.
- Après utilisation, les scripts libèrent automatiquement la mémoire.

### Prompts efficaces

Pour obtenir les meilleurs résultats avec dots.ocr, utilisez des prompts clairs et spécifiques :

- **Extraction générale** : "Extrais tout le texte visible dans cette image."
- **Documents structurés** : "Extrais les informations sous forme de tableau."
- **Factures** : "Identifie le montant total, la date et le numéro de facture."
- **Relevés** : "Extrais les valeurs et unités des paramètres environnementaux."

### Limitations

- Le modèle est moins précis que les grands modèles de vision.
- Le temps de chargement initial peut être long, surtout sur CPU.
- La qualité des résultats dépend de la clarté de l'image et du prompt.

## Dépannage

### Erreurs de mémoire

Si vous rencontrez des erreurs de mémoire insuffisante :

1. Fermez les applications gourmandes en mémoire.
2. Utilisez le mode CPU avec `device_map="cpu"`.
3. Désactivez la quantification 4-bit avec `load_in_4bit=False`.

### Problèmes de chargement du modèle

Si le modèle ne se charge pas correctement :

1. Vérifiez que toutes les dépendances sont installées.
2. Essayez de charger le modèle avec des paramètres simplifiés.
3. Utilisez l'API CloudVisionAPI qui gère automatiquement les erreurs.

## Ressources supplémentaires

- [Documentation officielle de dots.ocr](https://huggingface.co/rednote-hilab/dots.ocr)
- [Guide d'utilisation de transformers](https://huggingface.co/docs/transformers/)