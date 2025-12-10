# Guide de résolution du problème de configuration Gemini

Ce guide explique comment résoudre le problème spécifique d'erreur `'str' object has no attribute 'items'` qui peut survenir lors de la sauvegarde de la configuration de l'API Gemini dans l'application d'analyse de risque environnemental.

## Description du problème

### Symptômes

Lorsque vous tentez de sauvegarder la configuration de l'API Gemini via l'interface graphique, vous pouvez rencontrer l'erreur suivante :

```
Impossible de sauvegarder la configuration: 'str' object has no attribute 'items'
```

Cette erreur se produit généralement dans la boîte de dialogue de configuration des clés API, après avoir entré une clé API Gemini et cliqué sur le bouton "Sauvegarder".

### Cause

Le problème est dû à une gestion incorrecte du type de données de la configuration Gemini dans le code de l'application. Plus précisément :

1. La configuration Gemini est parfois traitée comme une chaîne de caractères (string) au lieu d'un dictionnaire
2. Le code tente d'appeler la méthode `.items()` sur cette chaîne, ce qui provoque l'erreur
3. Il manque des vérifications de type appropriées avant de manipuler la configuration

## Solutions

### Solution 1 : Utiliser le script de correction automatique

L'application inclut un script de diagnostic et de correction automatique qui peut résoudre ce problème spécifique :

```bash
# Correction spécifique du problème 'str' object has no attribute 'items'
python corriger_probleme_cle_api_gemini.py --fix-str-items

# Ou exécuter un diagnostic complet qui corrigera tous les problèmes détectés
python corriger_probleme_cle_api_gemini.py --diagnostic-complet
```

Ce script vérifiera si le fichier de configuration Gemini contient une simple chaîne au lieu d'un dictionnaire JSON et le corrigera automatiquement.

### Solution 2 : Mettre à jour l'application

Si vous utilisez une version officielle de l'application, assurez-vous de la mettre à jour vers la dernière version qui inclut la correction de ce problème.

### Solution 3 : Corriger manuellement le code

Si vous utilisez une version personnalisée ou si la mise à jour n'est pas possible, vous pouvez corriger manuellement le code :

#### Étape 1 : Modifier le fichier `app.py`

Localisez le code qui gère la sauvegarde de la configuration Gemini dans `app.py` (généralement autour des lignes 550-600) et assurez-vous qu'il contient une vérification de type appropriée :

```python
# Vérifier si gemini_config est un dictionnaire
if gemini_config and isinstance(gemini_config, dict):
    # Créer un dictionnaire complet avec des valeurs par défaut
    complete_gemini_config = {
        "api_key": gemini_config.get("api_key", ""),
        "default_models": gemini_config.get("default_models", {
            "text": "gemini-pro",
            "vision": "gemini-pro-vision"
        }),
        "max_tokens": gemini_config.get("max_tokens", 2048)
    }
    
    # Sauvegarder la configuration complète
    try:
        save_gemini_config(complete_gemini_config)
        sg.popup("Configuration Gemini sauvegardée avec succès.")
        logger.info("Configuration Gemini sauvegardée avec succès.")
    except Exception as e:
        sg.popup_error(f"Impossible de sauvegarder la configuration: {str(e)}")
        logger.error(f"Erreur lors de la sauvegarde de la configuration Gemini: {str(e)}")
else:
    # Gérer le cas où gemini_config n'est pas un dictionnaire
    sg.popup_error("Erreur: La configuration Gemini n'est pas dans un format valide.")
    logger.error(f"Erreur de type pour gemini_config: {type(gemini_config)}")
```

#### Étape 2 : Modifier le fichier `gemini_integration.py`

Localisez la fonction `save_gemini_config` dans `gemini_integration.py` et assurez-vous qu'elle contient des vérifications de type et une gestion d'erreurs robuste :

```python
def save_gemini_config(config):
    """Sauvegarde la configuration de l'API Gemini dans un fichier JSON."""
    try:
        # Vérifier que config est un dictionnaire
        if not isinstance(config, dict):
            raise TypeError(f"La configuration doit être un dictionnaire, pas {type(config)}")
        
        # Vérifier que les clés requises sont présentes
        if "api_key" not in config:
            raise ValueError("La clé 'api_key' est requise dans la configuration")
        
        # Charger la configuration existante si elle existe
        existing_config = {}
        config_path = os.path.join(os.path.dirname(__file__), "gemini_api_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    existing_config = json.load(f)
            except Exception as e:
                logger.warning(f"Impossible de charger la configuration existante: {str(e)}")
        
        # Fusionner avec la configuration existante
        merged_config = {**existing_config, **config}
        
        # Ajouter des valeurs par défaut si nécessaire
        if "default_models" not in merged_config:
            merged_config["default_models"] = {
                "text": "gemini-pro",
                "vision": "gemini-pro-vision"
            }
        
        if "max_tokens" not in merged_config:
            merged_config["max_tokens"] = 2048
        
        # Sauvegarder la configuration
        with open(config_path, "w") as f:
            json.dump(merged_config, f, indent=4)
        
        logger.info("Configuration de l'API Gemini sauvegardée avec succès.")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de la configuration Gemini: {str(e)}")
        raise
```

### Solution 3 : Utiliser une variable d'environnement

Si vous ne parvenez pas à résoudre le problème via l'interface graphique, vous pouvez contourner le problème en définissant directement la clé API via une variable d'environnement :

```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY="VOTRE_CLE_API"

# Windows (CMD)
set GEMINI_API_KEY=VOTRE_CLE_API

# Linux/macOS
export GEMINI_API_KEY="VOTRE_CLE_API"
```

## Vérification de la correction

Après avoir appliqué l'une des solutions ci-dessus :

1. Redémarrez l'application
2. Ouvrez l'interface de configuration des clés API
3. Entrez votre clé API Gemini
4. Cliquez sur "Sauvegarder"

Si la correction a fonctionné, vous devriez voir un message de confirmation indiquant que la configuration a été sauvegardée avec succès, sans aucune erreur.

## Support supplémentaire

Si vous continuez à rencontrer des problèmes après avoir suivi ce guide, vous pouvez :

1. Consulter les logs de l'application pour obtenir plus de détails sur l'erreur
2. Exécuter le script de diagnostic complet : `python corriger_probleme_cle_api_gemini.py --diagnostic-complet`
3. Vérifier la validité de votre clé API : `python corriger_probleme_cle_api_gemini.py --verifier`
4. Contacter l'équipe de support technique

## Prévention des problèmes futurs

Pour éviter des problèmes similaires à l'avenir :

1. Toujours vérifier les types de données avant de les manipuler
2. Implémenter une gestion d'erreurs robuste
3. Utiliser des valeurs par défaut appropriées
4. Maintenir l'application à jour avec les dernières corrections de bugs