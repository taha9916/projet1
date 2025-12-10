# Guide de diagnostic et résolution des problèmes pour les API Qwen et OpenRouter

## Introduction

Ce guide vous aidera à diagnostiquer et résoudre les problèmes courants rencontrés lors de l'utilisation des API Qwen Vision et OpenRouter dans l'application d'analyse de risque environnemental.

## 1. Problèmes d'authentification

### API Qwen Vision

#### Symptômes
- Message d'erreur: "401 Client Error: Unauthorized for url"
- Message d'erreur: "Erreur lors de l'analyse de l'image avec qwen"

#### Solutions
1. **Vérifiez votre clé API**:
   - Assurez-vous que la clé API Qwen est correctement configurée dans le fichier `cloud_api_config.json`
   - La clé API ne doit pas contenir d'espaces ou de caractères spéciaux non autorisés
   - Vérifiez que la clé n'a pas expiré sur le portail Qwen

2. **Vérifiez l'URL de l'API**:
   - L'URL correcte pour l'API Qwen Vision est: `https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation`
   - Assurez-vous qu'il n'y a pas d'erreur de frappe dans l'URL

3. **Vérifiez votre quota**:
   - Connectez-vous au portail Qwen pour vérifier si vous avez dépassé votre quota d'utilisation
   - Si nécessaire, augmentez votre quota ou attendez qu'il se renouvelle

### API OpenRouter

#### Symptômes
- Message d'erreur: "401 Client Error: Unauthorized for url"
- Message d'erreur: "Erreur lors de l'analyse de l'image avec OpenRouter"

#### Solutions
1. **Vérifiez votre clé API**:
   - Assurez-vous que la clé API OpenRouter est correctement configurée dans le fichier `cloud_api_config.json`
   - La clé API doit commencer par `sk-or-v1-`
   - Vérifiez que la clé n'a pas expiré sur le portail OpenRouter

2. **Vérifiez l'URL de l'API**:
   - L'URL correcte pour l'API OpenRouter est: `https://openrouter.ai/api/v1/chat/completions`
   - Assurez-vous qu'il n'y a pas d'erreur de frappe dans l'URL

3. **Vérifiez vos crédits**:
   - Connectez-vous à votre compte OpenRouter pour vérifier si vous avez suffisamment de crédits
   - Si nécessaire, rechargez vos crédits

## 2. Problèmes de format de requête

### API Qwen Vision

#### Symptômes
- Message d'erreur: "400 Client Error: Bad Request for url"
- Message d'erreur contenant "invalid request format"

#### Solutions
1. **Vérifiez le format de l'image**:
   - Assurez-vous que l'image est dans un format pris en charge (JPEG, PNG)
   - Vérifiez que l'image n'est pas corrompue
   - Essayez avec une image de taille plus petite (moins de 5 MB)

2. **Vérifiez le format de la requête**:
   - Assurez-vous que le format de la requête est correct selon la documentation Qwen
   - Vérifiez que le modèle spécifié existe et est disponible (`qwen3-32b-vl`)

### API OpenRouter

#### Symptômes
- Message d'erreur: "400 Client Error: Bad Request for url"
- Message d'erreur contenant "invalid request format"

#### Solutions
1. **Vérifiez le format de l'image**:
   - Assurez-vous que l'image est dans un format pris en charge (JPEG, PNG)
   - Vérifiez que l'image n'est pas corrompue
   - Essayez avec une image de taille plus petite (moins de 5 MB)

2. **Vérifiez le format de la requête**:
   - Assurez-vous que le format de la requête est correct selon la documentation OpenRouter
   - Vérifiez que le modèle spécifié existe et est disponible (`qwen/qwen3-32b:free`)
   - Assurez-vous que les champs `type` sont correctement définis dans le contenu du message

## 3. Problèmes de réseau

#### Symptômes
- Message d'erreur: "Connection refused"
- Message d'erreur: "Timeout"
- Message d'erreur: "Network error"

#### Solutions
1. **Vérifiez votre connexion Internet**:
   - Assurez-vous que vous êtes connecté à Internet
   - Vérifiez si d'autres services en ligne fonctionnent correctement

2. **Vérifiez votre pare-feu ou proxy**:
   - Assurez-vous que votre pare-feu n'empêche pas les connexions aux API
   - Si vous utilisez un proxy, vérifiez qu'il est correctement configuré

3. **Vérifiez la disponibilité des services**:
   - Vérifiez si les services Qwen ou OpenRouter ne sont pas en maintenance
   - Consultez les pages de statut des services si disponibles

## 4. Utilisation de l'outil de diagnostic

L'application inclut un outil de diagnostic spécifique pour les API Qwen et OpenRouter. Pour l'utiliser:

```bash
python diagnostic_tools/test_qwen_openrouter.py --qwen-key VOTRE_CLE_API_QWEN
```

ou

```bash
python diagnostic_tools/test_qwen_openrouter.py --openrouter-key VOTRE_CLE_API_OPENROUTER
```

Cet outil effectuera un test complet de l'API et fournira des informations détaillées sur les erreurs éventuelles.

## 5. Alternatives en cas de problème persistant

Si vous rencontrez des problèmes persistants avec les API Qwen ou OpenRouter, vous pouvez:

1. **Utiliser une autre API cloud**:
   - L'application prend en charge plusieurs fournisseurs d'API (OpenAI, Azure, Google)
   - Configurez et utilisez une autre API en attendant de résoudre les problèmes

2. **Utiliser le mode local**:
   - L'application peut fonctionner en mode local avec le modèle SmolVLM
   - Activez le mode local dans le menu Configuration > Mode d'analyse

## 6. Mise à jour des configurations

Si vous avez modifié les fichiers de configuration, assurez-vous de redémarrer l'application pour que les changements prennent effet.

## 7. Journalisation et débogage

Pour obtenir plus d'informations sur les erreurs:

1. **Consultez les fichiers de log**:
   - Vérifiez le fichier `app.log` pour les messages d'erreur détaillés
   - Les erreurs spécifiques aux API sont enregistrées avec leur code et message

2. **Activez le mode débogage**:
   - Lancez l'application avec l'option `--debug` pour obtenir des logs plus détaillés:
   ```bash
   python app.py --debug
   ```

## Contact et support

Si vous ne parvenez pas à résoudre les problèmes après avoir suivi ce guide, vous pouvez:

1. Ouvrir une issue sur le dépôt GitHub du projet
2. Contacter l'équipe de support technique
3. Consulter la documentation officielle des API:
   - [Documentation Qwen](https://help.aliyun.com/document_detail/2400395.html)
   - [Documentation OpenRouter](https://openrouter.ai/docs)