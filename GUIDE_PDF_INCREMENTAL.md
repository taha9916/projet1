# Guide du Traitement PDF Incrémental

## Vue d'ensemble

Le système d'analyse PDF incrémental permet de traiter de gros fichiers PDF page par page, en maintenant la réactivité de l'interface utilisateur et en offrant un contrôle de progression détaillé.

## Architecture

### Composants principaux

1. **`utils.iter_pdf_text_pages()`** - Générateur pour l'extraction incrémentale
2. **`RiskAnalysisApp._analyze_pdf_file()`** - Interface utilisateur et orchestration
3. **`CloudVisionAPI.analyze_text()`** - Analyse IA du texte extrait
4. **Threading** - Traitement en arrière-plan

### Flux de traitement

```
PDF sélectionné → _analyze_single_file() → _analyze_pdf_file()
                                              ↓
Interface de progression ← Worker Thread → iter_pdf_text_pages()
                                              ↓
Sauvegarde incrémentale → Analyse IA → Affichage des résultats
```

## Fonctionnalités

### 1. Extraction incrémentale

- **Page par page** : Traitement séquentiel pour éviter la surcharge mémoire
- **OCR de secours** : Utilise `pytesseract` si l'extraction de texte échoue
- **Sauvegarde continue** : Le texte est sauvegardé au fur et à mesure
- **Gestion d'erreurs** : Continue même si une page échoue

### 2. Interface utilisateur réactive

- **Barre de progression déterminée** : Pendant l'extraction (% de pages)
- **Barre de progression indéterminée** : Pendant l'analyse IA
- **Bouton d'annulation** : Disponible uniquement pendant l'extraction
- **Mises à jour en temps réel** : Statut et nombre de pages traitées

### 3. Intégration IA

- **Analyse locale** : Via `VLModelAdapter` (si disponible)
- **Analyse cloud** : Via `CloudVisionAPI` avec support multi-fournisseurs
- **Fournisseurs supportés** : OpenAI, Google/Gemini, Azure, Qwen, OpenRouter, dots.ocr

## Configuration requise

### Dépendances Python

```python
# Extraction PDF
pdfplumber>=0.7.0
pytesseract>=0.3.10

# Interface utilisateur
tkinter (inclus avec Python)
threading (inclus avec Python)

# Analyse IA
pandas>=1.3.0
requests>=2.25.0
```

### Clés API (pour analyse cloud)

Configurez dans `cloud_api_config.json` :

```json
{
    "openai": {
        "api_key": "sk-..."
    },
    "google": {
        "api_key": "AIza..."
    },
    "openrouter": {
        "api_key": "sk-or-..."
    }
}
```

## Utilisation

### Interface graphique

1. **Sélectionner un PDF** : Menu "Fichier" → "Ouvrir fichier"
2. **Choisir le mode d'analyse** : Local ou Cloud
3. **Sélectionner le fournisseur** : (si mode cloud)
4. **Lancer l'analyse** : Le traitement démarre automatiquement

### Contrôles disponibles

- **Annulation** : Bouton "Annuler" (uniquement pendant l'extraction)
- **Progression** : Barre de progression et compteur de pages
- **Statut** : Barre de statut en bas de la fenêtre

## Limitations et comportements

### Annulation

- ✅ **Possible pendant l'extraction** : Arrête le traitement page par page
- ❌ **Impossible pendant l'analyse** : Évite les états incohérents
- **Fichier de sortie** : Le texte déjà extrait est conservé

### Performance

- **Mémoire** : Utilisation optimisée (une page à la fois)
- **Vitesse** : Dépend de la complexité du PDF et du fournisseur IA
- **Réseau** : Requêtes IA uniquement après extraction complète

### Gestion d'erreurs

- **Pages corrompues** : Continuent avec OCR de secours
- **Erreurs réseau** : Affichage d'un message d'erreur détaillé
- **Modèle indisponible** : Basculement vers un fournisseur alternatif

## Structure des fichiers de sortie

### Texte extrait

```
output/extracted_text_YYYYMMDD_HHMMSS.txt
```

Contient le texte brut extrait de toutes les pages.

### Résultats d'analyse

- **DataFrame** : Affiché dans l'interface de prévisualisation
- **Fichiers Excel/CSV** : Exportables via le menu "Fichier"
- **Résumé textuel** : Affiché dans la zone de résultats

## Exemples de code

### Extraction manuelle

```python
from utils import iter_pdf_text_pages

# Extraction avec OCR de secours
for page_idx, text in iter_pdf_text_pages("document.pdf", ocr_fallback=True):
    print(f"Page {page_idx + 1}: {len(text)} caractères")
    # Traiter le texte...
```

### Analyse cloud

```python
from cloud_api import CloudVisionAPI

# Initialiser l'API
api = CloudVisionAPI(api_provider='gemini')

# Analyser le texte
prompt = "Extrais les paramètres environnementaux..."
response = api.analyze_text(prompt, provider='gemini')
df = api._extract_parameters(response)
```

## Dépannage

### Problèmes courants

1. **"Fournisseur non supporté"**
   - Vérifiez la configuration dans `cloud_api_config.json`
   - Utilisez les alias corrects ('gemini' → 'google')

2. **"Modèle local non disponible"**
   - Lancez avec `--load-model` pour activer l'analyse locale
   - Ou utilisez un fournisseur cloud

3. **Extraction lente**
   - Activez l'OCR uniquement si nécessaire (`ocr_fallback=False`)
   - Vérifiez la qualité du PDF (texte vs images)

4. **Erreurs d'API**
   - Vérifiez les clés API dans la configuration
   - Contrôlez les quotas et limites de débit

### Logs utiles

```bash
# Logs généraux
tail -f app.log

# Logs d'audit
tail -f logs/audit.log

# Logs d'erreurs
tail -f logs/error.log
```

## Développement

### Tests

```bash
# Test de l'alias Gemini
python test_gemini_alias.py

# Test de l'analyse PDF
python test_pdf_analysis.py

# Tests unitaires
python -m pytest tests/
```

### Extension

Pour ajouter un nouveau fournisseur IA :

1. Ajouter la configuration dans `cloud_api_config.json`
2. Implémenter `_analyze_text_with_nouveau_fournisseur()` dans `CloudVisionAPI`
3. Ajouter le fournisseur à la liste `supported_providers`
4. Tester avec `test_gemini_alias.py`

## Historique des versions

- **v1.0** : Implémentation de base avec threading
- **v1.1** : Ajout de l'alias Gemini et correction du routage cloud
- **v1.2** : Amélioration de la gestion d'erreurs et des logs d'audit
