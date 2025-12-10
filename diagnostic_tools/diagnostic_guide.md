# Guide de diagnostic pour l'application d'analyse de risque environnemental

Ce guide vous aidera à diagnostiquer et résoudre les problèmes courants rencontrés lors de l'utilisation de l'application d'analyse de risque environnemental, notamment :

1. L'erreur 403 Forbidden avec l'API Google Cloud Vision
2. Les problèmes d'extraction de paramètres environnementaux

Les outils de diagnostic disponibles sont :

- `api_diagnostic.py` - Diagnostic des problèmes d'API Google Cloud Vision
- `cloud_api_tester.py` - Test des API cloud alternatives
- `parameter_extractor.py` - Extraction améliorée des paramètres environnementaux
- `fix_api_issues.py` - Correction automatique des problèmes d'API
- `fix_extraction_issues.py` - Correction des problèmes d'extraction de paramètres
- `run_diagnostic.py` - Interface unifiée pour tous les outils

## Diagnostic de l'erreur 403 Forbidden avec l'API Google Cloud Vision

L'erreur 403 Forbidden indique un problème d'autorisation avec l'API Google Cloud Vision. Voici comment diagnostiquer et résoudre ce problème :

### Étape 1 : Exécuter l'outil de diagnostic API

```bash
python diagnostic_tools/api_diagnostic.py --api-key VOTRE_CLE_API
```

Cet outil va :
- Tester la validité de votre clé API
- Vérifier si l'API Vision est activée dans votre projet Google Cloud
- Analyser l'erreur 403 pour déterminer la cause probable
- Proposer des solutions adaptées

### Étape 2 : Vérifier l'activation de l'API Vision

Si le diagnostic indique que l'API Vision n'est pas activée :

1. Connectez-vous à la [Console Google Cloud](https://console.cloud.google.com/)
2. Sélectionnez votre projet
3. Allez dans "API et services" > "Bibliothèque"
4. Recherchez "Vision API"
5. Cliquez sur "Activer"

### Étape 3 : Vérifier la facturation

Si le diagnostic indique un problème de facturation :

1. Allez dans "Facturation" dans la Console Google Cloud
2. Vérifiez que la facturation est activée pour votre projet
3. Assurez-vous que votre mode de paiement est valide

### Étape 4 : Tester les API alternatives

Si vous ne parvenez pas à résoudre le problème avec Google Cloud Vision, vous pouvez tester les API alternatives :

```bash
python diagnostic_tools/cloud_api_tester.py --all
```

Cet outil testera toutes les API configurées (Google, Azure, OpenAI) et vous indiquera laquelle fonctionne le mieux.

### Étape 5 : Utiliser l'outil de correction automatique des problèmes d'API

Pour résoudre automatiquement les problèmes d'API, vous pouvez utiliser l'outil `fix_api_issues.py` :

```bash
python diagnostic_tools/fix_api_issues.py --api-key VOTRE_CLE_API --test-alternatives --update-config
```

Cet outil va :
- Vérifier la validité de votre clé API
- Tester la connectivité avec l'API Google Cloud Vision
- Analyser les erreurs 403 et proposer des solutions
- Tester les API alternatives (Azure, OpenAI)
- Mettre à jour automatiquement la configuration avec l'API fonctionnelle

Options disponibles :
- `--api-key` : Spécifier une clé API Google Cloud Vision à tester
- `--test-alternatives` : Tester les API alternatives (Azure, OpenAI)
- `--update-config` : Mettre à jour la configuration avec l'API fonctionnelle
- `--open-console` : Ouvrir la console Google Cloud dans le navigateur
- `--output` : Spécifier un fichier de sortie pour le rapport JSON

## Diagnostic des problèmes d'extraction de paramètres environnementaux

Si l'application affiche le message "Aucun paramètre environnemental n'a pu être extrait du texte", suivez ces étapes :

### Étape 1 : Analyser le fichier avec l'extracteur de paramètres amélioré

```bash
python diagnostic_tools/parameter_extractor.py --file CHEMIN_VERS_VOTRE_FICHIER.txt --output-excel resultats.xlsx
```

Cet outil va :
- Analyser le contenu du fichier en profondeur
- Utiliser des expressions régulières avancées pour détecter les paramètres
- Générer un rapport détaillé avec des statistiques et des suggestions

### Étape 2 : Examiner le rapport d'extraction

Le rapport d'extraction vous indiquera :
- Les paramètres trouvés (s'il y en a)
- Les mots-clés environnementaux détectés
- Les sections du texte qui pourraient contenir des informations pertinentes
- Des suggestions pour améliorer l'extraction

### Étape 3 : Améliorer le fichier source (si nécessaire)

Si le rapport suggère des améliorations, vous pouvez :

1. Ajouter des mots-clés spécifiques dans le fichier
2. Structurer les données sous forme de tableau ou de liste
3. Utiliser des formulations plus explicites pour les paramètres environnementaux

Exemples de formulations efficaces :
- "La température mesurée est de 25°C"
- "pH : 7.2"
- "Conductivité : 500 µS/cm"

### Étape 4 : Utiliser l'outil de correction des problèmes d'extraction

Pour diagnostiquer et corriger automatiquement les problèmes d'extraction de paramètres, vous pouvez utiliser l'outil `fix_extraction_issues.py` :

```bash
python diagnostic_tools/fix_extraction_issues.py --file "EIE HUB TARFAYA GREEN AMMONIA v2.txt" --suggest-improvements --output-report rapport_extraction.txt
```

Cet outil va :
- Analyser en profondeur le contenu du fichier
- Identifier les problèmes d'extraction de paramètres
- Détecter les structures de données et les formats
- Suggérer des améliorations pour faciliter l'extraction
- Générer un rapport détaillé avec des recommandations

Options disponibles :
- `--file` : Spécifier le fichier texte à analyser
- `--output-excel` : Générer un rapport Excel avec les paramètres extraits
- `--output-report` : Générer un rapport texte avec les analyses et suggestions
- `--analyze-only` : Analyser uniquement sans appliquer de corrections
- `--suggest-improvements` : Générer des suggestions pour améliorer l'extraction

### Étape 5 : Essayer le mode d'analyse local

Si le mode cloud ne parvient pas à extraire les paramètres, essayez le mode local :

1. Dans l'application, allez dans "Configuration" > "Mode d'analyse"
2. Sélectionnez "Local"
3. Analysez à nouveau votre fichier

## Exemple de workflow complet pour résoudre les deux problèmes

### Méthode manuelle (étape par étape)

1. Diagnostiquer l'erreur API :
   ```bash
   python diagnostic_tools/api_diagnostic.py
   ```

2. Tester les API alternatives :
   ```bash
   python diagnostic_tools/cloud_api_tester.py --all
   ```

3. Corriger les problèmes d'API :
   ```bash
   python diagnostic_tools/fix_api_issues.py --test-alternatives --update-config
   ```

4. Analyser le fichier problématique :
   ```bash
   python diagnostic_tools/parameter_extractor.py --file "EIE HUB TARFAYA GREEN AMMONIA v2.txt"
   ```

5. Corriger les problèmes d'extraction :
   ```bash
   python diagnostic_tools/fix_extraction_issues.py --file "EIE HUB TARFAYA GREEN AMMONIA v2.txt" --suggest-improvements
   ```

6. Appliquer les suggestions du rapport d'extraction

7. Réessayer l'analyse dans l'application

### Méthode automatique (tout-en-un)

Vous pouvez également utiliser l'outil `run_diagnostic.py` qui exécute automatiquement tous les outils nécessaires :

```bash
python diagnostic_tools/run_diagnostic.py full --api-key VOTRE_CLE_API --file "EIE HUB TARFAYA GREEN AMMONIA v2.txt" --output-report rapport.txt
```

Cet outil va :
1. Diagnostiquer les problèmes d'API
2. Tester les API alternatives
3. Corriger automatiquement les problèmes d'API (si nécessaire)
4. Analyser l'extraction de paramètres
5. Corriger les problèmes d'extraction (si nécessaire)
6. Générer un rapport complet

## Conseils supplémentaires

- **Pour les erreurs API** : Vérifiez toujours que votre connexion internet fonctionne correctement et que vous n'avez pas de proxy ou de pare-feu qui bloque les requêtes.

- **Pour l'extraction de paramètres** : Les fichiers PDF convertis en texte peuvent perdre leur formatage, ce qui rend l'extraction plus difficile. Essayez d'utiliser directement le fichier PDF si possible.

- **Pour les deux problèmes** : Consultez les fichiers de log (app.log) pour obtenir plus d'informations sur les erreurs.