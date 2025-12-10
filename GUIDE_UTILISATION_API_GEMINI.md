# Guide d'utilisation de l'API Gemini

## Introduction

Ce guide explique comment configurer et utiliser correctement l'API Gemini dans l'application d'analyse de risque environnemental. Il couvre les différentes méthodes d'utilisation, la résolution des problèmes courants et les bonnes pratiques.

## Configuration de l'API Gemini

### Méthode 1: Interface graphique au démarrage

L'application vérifie automatiquement la configuration de l'API Gemini au démarrage. Si aucune clé API n'est configurée, une boîte de dialogue s'affiche pour vous permettre d'entrer votre clé API.

### Méthode 2: Utilisation de l'interface de configuration

Vous pouvez configurer l'API Gemini à tout moment en exécutant le script suivant :

```bash
python corriger_interface_gemini.py
```

Cette interface vous permet de :
- Vérifier la configuration actuelle
- Tester la validité de votre clé API
- Mettre à jour votre clé API
- Activer ou désactiver l'API Gemini

### Méthode 3: Ligne de commande

Vous pouvez également configurer l'API Gemini en utilisant le script en ligne de commande :

```bash
python mettre_a_jour_cle_api_gemini.py --update VOTRE_CLE_API
```

Autres options disponibles :
- `--test` : Tester la clé API actuelle
- `--test-key VOTRE_CLE_API` : Tester une nouvelle clé API sans la sauvegarder
- `--enable` : Activer l'API Gemini
- `--disable` : Désactiver l'API Gemini
- `--show` : Afficher la configuration actuelle

### Méthode 4: Variable d'environnement

Vous pouvez définir la clé API Gemini en utilisant la variable d'environnement `GEMINI_API_KEY` :

```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY="VOTRE_CLE_API"

# Windows (CMD)
set GEMINI_API_KEY=VOTRE_CLE_API

# Linux/macOS
export GEMINI_API_KEY="VOTRE_CLE_API"
```

## Utilisation de l'API Gemini dans votre code

### Méthode 1: Utilisation de la bibliothèque officielle

```python
import google.generativeai as genai

# Configurer l'API avec votre clé
genai.configure(api_key="VOTRE_CLE_API")

# Créer un modèle génératif
model = genai.GenerativeModel('gemini-pro')

# Générer du contenu
response = model.generate_content("Bonjour, comment ça va?")
print(response.text)
```

### Méthode 2: Utilisation de l'intégration du projet

```python
from gemini_integration import initialize_gemini_api

# Initialiser l'API Gemini (utilise la configuration sauvegardée)
gemini_api, config = initialize_gemini_api()

# Vérifier si l'initialisation a réussi
if gemini_api:
    # Générer du contenu
    response = gemini_api.generate_content("Bonjour, comment ça va?")
    print(response['text'])
else:
    print("Impossible d'initialiser l'API Gemini.")
```

### Méthode 3: Utilisation directe de la classe GeminiAPI

```python
from gemini_api import GeminiAPI

# Initialiser directement avec votre clé API
gemini_api = GeminiAPI(api_key="VOTRE_CLE_API")

# Générer du contenu
response = gemini_api.generate_content("Bonjour, comment ça va?")
print(response['text'])
```

## Analyse d'images environnementales avec Gemini

```python
from gemini_integration import analyze_environmental_image_with_gemini

# Analyser une image environnementale
results = analyze_environmental_image_with_gemini(
    image_path="chemin/vers/votre/image.jpg",
    use_ocr=True  # Utiliser l'OCR pour extraire le texte de l'image
)

# Afficher les résultats
print(f"Type d'environnement: {results['type_environnement']}")
print(f"Polluants: {', '.join(results['polluants'])}")
print(f"Risques: {', '.join(results['risques'])}")
print(f"Recommandations: {', '.join(results['recommandations'])}")
```

## Résolution des problèmes courants

### Problème: "google-generativeai n'existe pas"

**Solution**: Le nom correct du package est `google.generativeai`, pas `google-generativeai`. Utilisez:

```python
import google.generativeai as genai
```

### Problème: "Clé API invalide"

**Solutions**:
1. Vérifiez que votre clé API est correcte et active
2. Assurez-vous que la clé API est correctement formatée (sans espaces supplémentaires)
3. Testez votre clé API avec le script de diagnostic:
   ```bash
   python corriger_probleme_cle_api_gemini.py --verifier-cle VOTRE_CLE_API
   ```

### Problème: "API Gemini désactivée"

**Solution**: Activez l'API Gemini avec l'une des méthodes suivantes:
1. Via l'interface graphique: `python corriger_interface_gemini.py`
2. Via la ligne de commande: `python mettre_a_jour_cle_api_gemini.py --enable`

### Problème: "Quota dépassé"

**Solutions**:
1. Attendez que votre quota soit réinitialisé
2. Demandez une augmentation de quota sur la console Google Cloud
3. Utilisez une autre clé API

## Bonnes pratiques

1. **Sécurité**: Ne partagez jamais votre clé API et ne la stockez pas en clair dans votre code
2. **Gestion des erreurs**: Implémentez toujours une gestion des erreurs robuste
3. **Fallback**: Prévoyez une solution de repli en cas d'indisponibilité de l'API Gemini
4. **Mise en cache**: Mettez en cache les résultats pour éviter des appels API inutiles
5. **Monitoring**: Surveillez votre utilisation de l'API pour éviter de dépasser votre quota

## Ressources supplémentaires

- [Documentation officielle de l'API Gemini](https://ai.google.dev/docs/gemini_api)
- [Console Google Cloud pour gérer vos clés API](https://console.cloud.google.com/)
- [Exemples d'utilisation de l'API Gemini](https://github.com/google-gemini/gemini-api-samples)

## Support

Si vous rencontrez des problèmes avec l'API Gemini, vous pouvez:
1. Exécuter le script de diagnostic: `python corriger_probleme_cle_api_gemini.py`
2. Consulter les logs de l'application pour plus de détails sur les erreurs
3. Contacter l'équipe de support technique