# Outils de diagnostic pour l'application d'analyse de risque environnemental

Ce répertoire contient des outils de diagnostic pour identifier et résoudre les problèmes courants rencontrés dans l'application d'analyse de risque environnemental.

## Nouvelles améliorations pour l'extraction des paramètres environnementaux

Des améliorations ont été apportées pour résoudre les problèmes d'extraction des données tabulaires des réponses de l'API Cloud:

### Problème résolu

Le système original rencontrait des difficultés pour extraire correctement les données tabulaires des réponses de l'API Cloud, principalement en raison de:

1. Problèmes d'encodage des caractères accentués (ex: `ParamÃ¨tre` au lieu de `Paramètre`)
2. Validation trop stricte des en-têtes de tableau
3. Manque de flexibilité dans la détection des tableaux mal formatés
4. Absence de logs détaillés pour le débogage

Ces problèmes entraînaient l'affichage fréquent du message d'erreur "Aucune donnée structurée n'a été extraite de la réponse" dans les logs de l'application.

### Solution implémentée

Les améliorations suivantes ont été apportées:

1. **Normalisation des textes**: Ajout d'une fonction `normalize_text()` qui supprime les accents et convertit en minuscules pour une comparaison plus souple des en-têtes
2. **Détection améliorée des tableaux**: Recherche de tableaux bien formatés et mal formatés avec une tolérance accrue
3. **Mappage flexible des noms de colonnes**: Utilisation de la normalisation pour faire correspondre les en-têtes avec différentes variantes (avec/sans accents, majuscules/minuscules)
4. **Logs détaillés**: Ajout de logs pour faciliter le débogage
5. **Extraction alternative**: Méthodes alternatives pour extraire les données si la structure du tableau est incomplète

### Nouveaux fichiers

1. **improved_cloud_api_extraction.py**: Contient la version améliorée de la fonction `_extract_parameters`
2. **test_improved_extraction.py**: Script de test pour vérifier le fonctionnement de la nouvelle fonction avec différents exemples
3. **integrate_improved_extraction.py**: Script pour intégrer la fonction améliorée dans le système existant

### Comment utiliser

#### Option 1: Tester la fonction améliorée

Pour tester la fonction améliorée sans modifier le système existant:

```bash
python test_improved_extraction.py
```

Cela exécutera une série de tests avec différents formats de tableaux et affichera les résultats.

#### Option 2: Intégrer la fonction améliorée

Pour intégrer la fonction améliorée dans le système existant:

```bash
python integrate_improved_extraction.py
```

Ce script:
1. Recherche le fichier `cloud_api.py` dans le projet
2. Crée une sauvegarde du fichier original
3. Remplace la fonction `_extract_parameters` par la version améliorée
4. Ajoute les imports et fonctions nécessaires

**Note**: Une sauvegarde du fichier original est automatiquement créée avant toute modification.

## Outils disponibles

### 1. API Diagnostic (`api_diagnostic.py`)

Cet outil permet de diagnostiquer les problèmes liés à l'API Google Cloud Vision, notamment les erreurs 403 Forbidden.

**Fonctionnalités :**
- Test de la validité de la clé API Google Cloud Vision
- Vérification de l'activation de l'API Vision dans le projet Google Cloud
- Analyse détaillée des erreurs 403 pour déterminer les causes probables
- Suggestions de solutions pour résoudre les problèmes d'API

**Utilisation :**
```bash
python api_diagnostic.py --api-key YOUR_API_KEY
```

### 2. Extracteur de paramètres amélioré (`parameter_extractor.py`)

Cet outil améliore l'extraction des paramètres environnementaux à partir de fichiers texte en utilisant des techniques avancées de traitement du langage naturel et des expressions régulières.

**Fonctionnalités :**
- Détection améliorée des paramètres environnementaux avec des expressions régulières avancées
- Prise en compte des variations de noms et d'unités pour chaque paramètre
- Extraction à partir de données structurées (tableaux, listes)
- Analyse statistique du contenu du texte
- Suggestions pour améliorer l'extraction

**Utilisation :**
```bash
python parameter_extractor.py --file chemin/vers/fichier.txt --output-excel resultats.xlsx
```

### 3. Testeur d'API Cloud (`cloud_api_tester.py`)

Cet outil permet de tester la connectivité et la configuration des différentes API cloud utilisées par l'application (Google Cloud Vision, Azure Computer Vision, OpenAI).

**Fonctionnalités :**
- Test de l'API Google Cloud Vision
- Test de l'API Azure Computer Vision
- Test de l'API OpenAI
- Analyse détaillée des erreurs
- Recommandations pour résoudre les problèmes

**Utilisation :**
```bash
python cloud_api_tester.py --all
```

### 4. Correcteur de problèmes d'API (`fix_api_issues.py`)

Cet outil permet de diagnostiquer et corriger automatiquement les problèmes liés à l'API Google Cloud Vision, notamment les erreurs 403 Forbidden.

**Fonctionnalités :**
- Vérification de la validité de la clé API
- Test de connectivité avec l'API Google Cloud Vision
- Analyse détaillée des erreurs 403 et proposition de solutions
- Test des API alternatives (Azure, OpenAI)
- Mise à jour automatique de la configuration avec l'API fonctionnelle
- Ouverture de la console Google Cloud pour activer l'API ou la facturation

**Utilisation :**
```bash
python fix_api_issues.py --api-key YOUR_API_KEY --test-alternatives --update-config
```

### 5. Correcteur de problèmes d'extraction (`fix_extraction_issues.py`)

Cet outil permet de diagnostiquer et corriger les problèmes d'extraction de paramètres environnementaux à partir de fichiers texte.

**Fonctionnalités :**
- Analyse approfondie du contenu du fichier
- Identification des problèmes d'extraction de paramètres
- Détection des structures de données et des formats
- Suggestions d'améliorations pour faciliter l'extraction
- Génération de rapports détaillés avec des recommandations

**Utilisation :**
```bash
python fix_extraction_issues.py --file "EIE HUB TARFAYA GREEN AMMONIA v2.txt" --suggest-improvements
```

### 6. Interface unifiée (`run_diagnostic.py`)

Cet outil fournit une interface unifiée pour exécuter tous les outils de diagnostic en une seule commande.

**Fonctionnalités :**
- Exécution de tous les outils de diagnostic en séquence
- Diagnostic complet des problèmes d'API et d'extraction
- Correction automatique des problèmes détectés
- Génération de rapports détaillés

**Utilisation :**
```bash
python run_diagnostic.py full --api-key YOUR_API_KEY --file chemin/vers/fichier.txt
```

Ou pour exécuter un outil spécifique :
```bash
python run_diagnostic.py api --api-key YOUR_API_KEY
python run_diagnostic.py extract --file chemin/vers/fichier.txt
python run_diagnostic.py test-api --all
python run_diagnostic.py fix-api --api-key YOUR_API_KEY --test-alternatives
python run_diagnostic.py fix-extract --file chemin/vers/fichier.txt --suggest-improvements
```

## Résolution des problèmes courants

### Erreur 403 avec l'API Google Cloud Vision

Si vous rencontrez une erreur 403 Forbidden avec l'API Google Cloud Vision, suivez ces étapes :

1. Vérifiez que la clé API est correctement saisie dans la configuration
2. Assurez-vous que l'API Vision est activée dans votre projet Google Cloud :
   - Accédez à la console Google Cloud : https://console.cloud.google.com
   - Sélectionnez votre projet
   - Allez dans 'API et services' > 'Bibliothèque'
   - Recherchez 'Vision API' et activez-la
3. Vérifiez que la facturation est activée pour votre projet Google Cloud
4. Vérifiez les quotas et restrictions de votre clé API
5. Essayez d'utiliser un autre fournisseur d'API (Azure ou OpenAI) comme alternative

### Problème d'extraction de paramètres environnementaux

Si l'application n'arrive pas à extraire des paramètres environnementaux d'un fichier texte, essayez ces solutions :

1. Vérifiez que le fichier texte contient effectivement des informations environnementales
2. Utilisez l'outil `parameter_extractor.py` pour analyser le fichier et obtenir des suggestions d'amélioration
3. Essayez d'utiliser le mode d'analyse local si le mode cloud ne parvient pas à extraire les paramètres
4. Ajoutez des mots-clés spécifiques dans le fichier pour faciliter l'extraction, par exemple :
   - "température: 25°C"
   - "pH: 7.2"
   - "conductivité: 500 µS/cm"
5. Structurez les données sous forme de tableau ou de liste pour faciliter l'extraction

## Exemple de workflow de diagnostic

1. Exécutez l'outil de diagnostic API pour vérifier la configuration de l'API Google Cloud Vision :
   ```bash
   python api_diagnostic.py --api-key YOUR_API_KEY
   ```

2. Si des problèmes sont détectés avec l'API, suivez les recommandations du rapport de diagnostic

3. Testez l'extraction de paramètres avec l'outil d'extraction amélioré :
   ```bash
   python parameter_extractor.py --file votre_fichier.txt --output-excel resultats.xlsx
   ```

4. Consultez le rapport d'extraction pour identifier les problèmes et appliquer les suggestions

5. Testez toutes les API cloud disponibles pour trouver la meilleure alternative :
   ```bash
   python cloud_api_tester.py --all
   ```

6. Configurez l'application pour utiliser l'API qui fonctionne le mieux dans votre cas