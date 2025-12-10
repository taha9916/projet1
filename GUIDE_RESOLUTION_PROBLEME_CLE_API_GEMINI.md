# Guide de résolution des problèmes de clé API Gemini

## Problème observé

Vous avez configuré une clé API Gemini, mais vous recevez un message d'erreur indiquant qu'aucune clé API n'est configurée pour Gemini ou que la clé API ne fonctionne pas correctement.

## Solutions possibles

### 1. Vérifier la configuration actuelle

Utilisez le script `mettre_a_jour_cle_api_gemini.py` pour vérifier votre configuration actuelle :

```bash
python mettre_a_jour_cle_api_gemini.py --show
```

Cela affichera les informations de configuration actuelles, y compris si une clé API est définie et si l'API est activée.

### 2. Tester la validité de votre clé API

Utilisez le script `mettre_a_jour_cle_api_gemini.py` pour tester si votre clé API actuelle est valide :

```bash
python mettre_a_jour_cle_api_gemini.py --test
```

Ou utilisez le nouveau script de diagnostic :

```bash
python corriger_probleme_cle_api_gemini.py --verifier
```

### 3. Mettre à jour votre clé API

Si votre clé API est invalide ou n'est pas configurée, vous pouvez la mettre à jour avec :

```bash
python mettre_a_jour_cle_api_gemini.py --api_key "VOTRE_NOUVELLE_CLE_API"
```

Ou utilisez le script de correction :

```bash
python corriger_probleme_cle_api_gemini.py --cle "VOTRE_NOUVELLE_CLE_API"
```

### 4. Activer l'API Gemini

Assurez-vous que l'API Gemini est activée dans la configuration :

```bash
python mettre_a_jour_cle_api_gemini.py --enable
```

### 5. Vérifier la variable d'environnement

Vérifiez si la variable d'environnement `GEMINI_API_KEY` est définie :

```bash
python corriger_probleme_cle_api_gemini.py --env
```

## Diagnostic complet et correction automatique

Pour effectuer un diagnostic complet et corriger automatiquement les problèmes courants :

```bash
python corriger_probleme_cle_api_gemini.py
```

Ce script vérifiera :
1. La configuration actuelle dans le fichier `gemini_api_config.json`
2. La présence et la validité de la variable d'environnement `GEMINI_API_KEY`
3. Vous proposera de corriger les problèmes détectés

## Problèmes courants et solutions

### La clé API est invalide

- Vérifiez que vous avez copié la clé API complète sans espaces supplémentaires
- Assurez-vous que la clé API commence par "AIza"
- Vérifiez que votre clé API est activée dans la console Google Cloud
- Assurez-vous que l'API Gemini est activée pour votre projet Google Cloud

### L'API est désactivée dans la configuration

- Activez l'API avec `python mettre_a_jour_cle_api_gemini.py --enable`

### Erreur de quota ou de facturation

- Vérifiez que votre compte Google Cloud dispose d'un mode de paiement valide
- Vérifiez que vous n'avez pas dépassé votre quota d'utilisation de l'API Gemini

### Problèmes de réseau

- Vérifiez votre connexion Internet
- Si vous utilisez un proxy ou un VPN, assurez-vous qu'ils n'interfèrent pas avec les requêtes à l'API Gemini

## Obtenir une nouvelle clé API Gemini

Si votre clé API ne fonctionne pas, vous pouvez en obtenir une nouvelle en suivant ces étapes :

1. Accédez à la [console Google Cloud](https://console.cloud.google.com/)
2. Créez un nouveau projet ou sélectionnez un projet existant
3. Activez l'API Gemini pour votre projet
4. Créez une clé API dans la section "Identifiants"
5. Copiez la clé API et utilisez-la dans l'application