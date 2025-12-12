# Analyse de Risque Environnemental - Maroc

Ce projet est un outil d'analyse de risque environnemental spécialement conçu pour le contexte marocain. Il permet d'analyser des données environnementales à partir de différents formats de fichiers (Excel, PDF, images, etc.) et d'enrichir ces données avec des informations pertinentes issues du web. L'application utilise des modèles Vision-Language optimisés pour fonctionner sur des machines avec des ressources limitées.

## Lancement Rapide

Plusieurs options sont disponibles pour lancer l'application :

- **Interface graphique** : Double-cliquez sur `lancer_application.bat`
- **Serveur web** : Double-cliquez sur `lancer_serveur_web.bat`
- **Page d'accueil** : Double-cliquez sur `demarrer.bat` pour ouvrir la page d'accueil HTML
- **Raccourcis bureau** : Exécutez `creer_raccourci_bureau.ps1` avec PowerShell pour créer des raccourcis sur votre bureau
- **IA locale** : Le modèle `dots.ocr` est configuré comme IA locale par défaut pour l'analyse d'images et l'extraction de texte. Lancez `lancer_dots_ocr.bat` pour utiliser cette IA locale

Pour plus d'informations, consultez le fichier `GUIDE_LANCEMENT_RAPIDE.md`.

## Fonctionnalités

### Fonctionnalités d'acquisition et d'analyse de données
- Interface graphique conviviale pour l'analyse de données environnementales
- Support de multiples formats de fichiers (Excel, CSV, PDF, images, etc.)
- Extraction de texte et de données à partir de documents et d'images
- Analyse d'images avec des modèles IA Vision-Language (SmolVLM-2B, Moondream-2B, Qwen2-VL, dots.ocr) pour extraire des paramètres environnementaux
- Traitement par lots des images et textes volumineux pour optimiser la consommation mémoire
- Enrichissement automatique des données avec des informations issues du web
- Intégration avec des API externes pour collecter des données environnementales en temps réel

### Fonctionnalités d'analyse de risque et de reporting
- Calcul des scores de risque environnemental (air, eau, sol, humain)
- Génération automatique de recommandations basées sur les scores de risque
- Création de plans d'action priorisés avec estimation des budgets et délais
- Génération de rapports détaillés (HTML, Markdown, PDF)
- Tableau de bord interactif pour visualiser et filtrer les données d'analyse
- Visualisation des données avec graphiques et tableaux

## Structure du Projet

```
projet_1/
│
├── app.py                # Interface graphique (Tkinter)
├── analyse_qwen2vl.py    # Analyse IA avec Qwen2-VL
├── main.py               # Point d'entrée principal avec CLI
├── utils.py              # Fonctions utilitaires (fichiers, logs, etc.)
├── config.py             # Paramètres et chemins
├── model_interface.py    # Interface avec le modèle IA
├── data_processing.py    # Nettoyage et traitement des données
├── gui_components.py     # Widgets personnalisés
├── pipeline.py           # Pipeline d'analyse modulaire
├── server.py             # API web avec Flask
├── cloud_api.py          # Interface avec les API cloud (OpenAI, Azure, Google, Qwen, OpenRouter, Hugging Face, dots.ocr)
├── cloud_api_config.json # Configuration des clés API pour les services cloud
├── install_dots_ocr.py   # Script d'installation du modèle dots.ocr
├── test_dots_ocr.py      # Script de test du modèle dots.ocr
├── GUIDE_DOTS_OCR.md     # Guide d'utilisation du modèle dots.ocr
│
├── Fichiers de lancement:
│   ├── lancer_application.bat      # Lance l'interface graphique
│   ├── lancer_serveur_web.bat      # Lance le serveur web
│   ├── demarrer.bat                # Ouvre la page d'accueil HTML
│   ├── accueil.html                # Page d'accueil pour choisir le mode de lancement
│   ├── creer_raccourci_bureau.ps1  # Crée des raccourcis sur le bureau
│   ├── GUIDE_LANCEMENT_RAPIDE.md   # Guide d'utilisation des méthodes de lancement
│   └── INSTRUCTIONS_RACCOURCIS.md  # Instructions pour créer des raccourcis
│
├── diagnostic_tools/     # Outils de diagnostic pour les API cloud
│   ├── api_diagnostic.py           # Diagnostic pour Google Cloud Vision API
│   ├── cloud_api_tester.py         # Test des API Google, Azure et OpenAI
│   ├── test_qwen_openrouter.py     # Test des API Qwen et OpenRouter
│   └── qwen_openrouter_guide.md    # Guide de résolution des problèmes Qwen/OpenRouter
├── tests/                # Tests unitaires
├── requirements.txt      # Dépendances Python
└── README.md             # Documentation du projet
```

## Installation

1. Clonez ce dépôt sur votre machine locale
2. Assurez-vous d'avoir Python 3.8+ installé
3. Installez les dépendances requises :

```bash
pip install -r requirements.txt
```

4. Installez le modèle de votre choix :

```bash
python install_models.py --model SmolVLM-2B  # Modèle léger par défaut
```

Pour voir la liste des modèles disponibles :

```bash
python install_models.py --list
```

## Analyse d'Images Environnementales

Le système peut analyser des images environnementales (rapports de laboratoire, photos de terrain, certificats d'analyse, etc.) pour en extraire automatiquement des paramètres environnementaux à l'aide de modèles Vision-Langage (VLM).

### Processus d'Extraction des Paramètres

L'extraction des paramètres environnementaux à partir d'images suit un processus en plusieurs étapes :

1. **Prétraitement de l'image** :
   - Correction de perspective et redressement
   - Amélioration du contraste et de la netteté
   - Suppression du bruit et des artefacts
   - Normalisation des couleurs

2. **Reconnaissance Optique de Caractères (OCR)** :
   - Détection des zones de texte
   - Reconnaissance des caractères avec Tesseract OCR
   - Post-traitement pour corriger les erreurs courantes

3. **Analyse par Vision-Langage** :
   - Interprétation du contenu visuel et textuel
   - Identification des tableaux, graphiques et structures de données
   - Extraction des relations entre paramètres, valeurs et unités

4. **Structuration des Données** :
   - Organisation des paramètres extraits en format tabulaire
   - Association des valeurs avec les unités correspondantes
   - Identification des seuils et normes mentionnés

5. **Validation et Enrichissement** :
   - Vérification de la cohérence des données extraites
   - Comparaison avec les plages de valeurs attendues
   - Enrichissement avec des métadonnées contextuelles

### Modèles Vision-Langage Disponibles

Trois modèles sont disponibles pour l'analyse d'images, chacun avec ses caractéristiques spécifiques :

| Modèle | Taille | Vitesse | Précision | Mémoire Requise | Langues Supportées | Cas d'Usage Optimal |
|--------|--------|---------|-----------|-----------------|---------------------|---------------------|
| **SmolVLM-2B** | 2B paramètres | Rapide (2-5s/image) | Modérée (75-80%) | 4-6 GB | FR, EN | Analyses simples, appareils limités |
| **Moondream-2B** | 2B paramètres | Moyenne (4-8s/image) | Bonne (80-85%) | 5-7 GB | FR, EN, AR | Équilibre performance/ressources |
| **Qwen2-VL-7B-Instruct** | 7B paramètres | Lente (10-20s/image) | Excellente (90%+) | 12-16 GB | FR, EN, AR, ES, DE | Analyses complexes, haute précision |

### Optimisations pour les Modèles Locaux

Les modèles locaux sont optimisés pour fonctionner sur des machines avec des ressources limitées :

- **Quantification adaptative** :
  - 4-bit pour les machines avec <8GB RAM
  - 8-bit pour les machines avec 8-16GB RAM
  - 16-bit pour les machines avec >16GB RAM et GPU

- **Chargement intelligent** :
  - Chargement partiel du modèle pour les machines avec peu de RAM
  - Déchargement des couches non essentielles après l'initialisation
  - Partage de mémoire entre modèles pour l'analyse multi-modèle

- **Accélération matérielle** :
  - Utilisation automatique de CUDA si GPU NVIDIA disponible
  - Support de ROCm pour GPU AMD
  - Optimisations CPU avec ONNX Runtime et Intel MKL
  - Support des accélérateurs NPU/TPU si disponibles

### Types d'Images Supportés

Le système est optimisé pour analyser différents types d'images environnementales :

- **Rapports de laboratoire** : Extraction précise des tableaux de résultats d'analyse
- **Certificats d'analyse** : Reconnaissance des paramètres et valeurs certifiés
- **Photos de terrain** : Identification des conditions environnementales visibles
- **Captures d'instruments** : Lecture des valeurs sur les écrans d'appareils de mesure
- **Graphiques et diagrammes** : Interprétation des tendances et valeurs représentées

### Traitement par Lots pour les Images

Pour analyser plusieurs images, le système utilise un traitement par lots avec parallélisation :

```python
# Analyser un lot d'images avec options avancées
python batch_image_analysis.py \
  --input_dir ./images \
  --output_file results.xlsx \
  --model qwen2-vl-7b \
  --batch_size 4 \
  --parallel_workers 2 \
  --confidence_threshold 0.75 \
  --extract_tables True \
  --extract_graphs True \
  --save_annotated_images True \
  --output_format xlsx \
  --language fr
```

### Prompt IA structuré, fallback automatique et historique

#### Extraction tabulaire IA obligatoire (6 colonnes)

Depuis la version 2025-10, l'analyse IA (texte, PDF, OCR, fallback) utilise un prompt directif imposant la génération d'un tableau Markdown structuré avec exactement les colonnes suivantes :
- **Paramètre**
- **Unité**
- **Intervalle acceptable**
- **Valeur mesurée de milieux initial**
- **Rejet de prj**
- **Valeure Mesure+rejet**

L'IA doit parcourir tout le texte importé, extraire tous les paramètres environnementaux, et remplir le tableau même si les informations sont dispersées ou absentes (au moins une ligne "Non disponible" par colonne si rien n'est trouvé). Aucune cellule vide, aucune sortie hors du tableau n'est acceptée.

#### Fallback automatique

En cas d'échec de l'analyse image (provider non supporté, erreur 404, etc.), l'application bascule automatiquement sur l'extraction texte OCR puis applique le même prompt IA structuré.

#### Historique d'analyse systématique

Après chaque analyse (texte, image, PDF, fallback), le résultat est ajouté à l'historique (`self.recent_analyses`). Cela garantit l'export possible vers Excel/SLRI même après une analyse fallback ou partielle.

### Exemples de Paramètres Extraits

Le système peut extraire une large gamme de paramètres environnementaux à partir d'images, notamment :

- **Eau** : pH, turbidité, conductivité, DBO, DCO, métaux lourds, nitrates, phosphates
- **Air** : PM2.5, PM10, NO₂, SO₂, O₃, COV, CO₂, indice de qualité de l'air
- **Sol** : pH, texture, matière organique, métaux lourds, nutriments, salinité
- **Biologique** : indices biotiques, comptage bactérien, présence d'espèces indicatrices

Chaque paramètre extrait est accompagné d'un score de confiance permettant d'évaluer la fiabilité de l'extraction.

## Traitement par Lots (Batch Processing)

Le système offre des capacités avancées de traitement par lots pour analyser efficacement de grandes quantités de données environnementales provenant de multiples sources.

### Fonctionnalités du Traitement par Lots

- **Multi-format** : Traitement simultané de fichiers Excel, CSV, images et PDF
- **Parallélisation** : Utilisation optimisée des ressources CPU/GPU disponibles
- **Reprise sur erreur** : Capacité à reprendre le traitement après une interruption
- **Journalisation détaillée** : Suivi complet du processus avec niveaux de verbosité configurables
- **Filtrage intelligent** : Sélection des fichiers selon des critères avancés (date, contenu, métadonnées)
- **Agrégation de résultats** : Consolidation automatique des analyses en rapports unifiés

### Utilisation Avancée

```python
# Traitement par lots avec options avancées
python batch_processor.py \
  --input_dir ./data \
  --output_dir ./results \
  --file_type all \
  --recursive True \
  --parallel 4 \
  --max_memory 8G \
  --priority_files "*rapport*.xlsx,*analyse*.xlsx" \
  --exclude_patterns "*backup*,*temp*" \
  --error_handling continue \
  --aggregation_mode consolidated \
  --report_format xlsx,html,pdf \
  --notification_email user@example.com \
  --checkpoint_interval 10 \
  --timeout 3600
```

### Options Disponibles

| Option | Description | Valeur par défaut |
|--------|-------------|-------------------|
| `--input_dir` | Dossier contenant les fichiers à analyser | `./data` |
| `--output_dir` | Dossier où sauvegarder les résultats | `./results` |
| `--file_type` | Type de fichier à traiter (excel, csv, image, pdf, all) | `all` |
| `--recursive` | Rechercher des fichiers dans les sous-dossiers | `False` |
| `--parallel` | Nombre de processus parallèles à utiliser | `2` |
| `--max_memory` | Limite de mémoire par processus (ex: 4G, 8G) | `4G` |
| `--priority_files` | Motifs de fichiers à traiter en priorité (séparés par virgule) | `""` |
| `--exclude_patterns` | Motifs de fichiers à exclure (séparés par virgule) | `"*backup*,*temp*"` |
| `--error_handling` | Comportement en cas d'erreur (stop, continue, retry) | `continue` |
| `--aggregation_mode` | Mode d'agrégation des résultats (individual, consolidated, both) | `both` |
| `--report_format` | Formats de rapport à générer (séparés par virgule) | `xlsx` |
| `--notification_email` | Email pour notifications de fin de traitement | `""` |
| `--checkpoint_interval` | Nombre de fichiers entre points de sauvegarde | `10` |
| `--timeout` | Délai maximum d'exécution en secondes (0 = illimité) | `0` |

### Stratégies d'Optimisation

Le traitement par lots implémente plusieurs stratégies pour optimiser les performances :

1. **Allocation dynamique des ressources** : Ajustement automatique du nombre de processus en fonction de la charge système
2. **Préchargement intelligent** : Chargement anticipé des fichiers suivants pendant le traitement
3. **Mise en cache des modèles** : Réutilisation des modèles chargés entre les fichiers similaires
4. **Traitement par priorité** : Analyse des fichiers les plus importants en premier
5. **Compression adaptative** : Optimisation du stockage des résultats intermédiaires

### Intégration avec les Systèmes Existants

Le traitement par lots peut s'intégrer avec différents systèmes externes :

- **Stockage cloud** : Prise en charge des sources et destinations sur AWS S3, Google Cloud Storage, Azure Blob
- **Bases de données** : Export direct des résultats vers MySQL, PostgreSQL, MongoDB
- **Systèmes de notification** : Alertes via email, Slack, Microsoft Teams
- **Planificateurs** : Intégration avec cron, Windows Task Scheduler, Airflow

### Exemple de Script Personnalisé

```python
from batch_processor import BatchProcessor

# Créer un processeur par lots personnalisé
processor = BatchProcessor(
    input_directory="./data/sites_industriels",
    output_directory="./results/rapport_trimestriel",
    file_types=["excel", "image"],
    recursive=True,
    parallel_processes=4,
    error_handling="retry",
    max_retries=3
)

# Ajouter des filtres personnalisés
processor.add_filter(lambda file: "2023" in file and not "brouillon" in file)

# Définir un gestionnaire d'événements
processor.on_file_complete(lambda file, result: print(f"Traitement terminé pour {file}"))

# Exécuter le traitement
results = processor.process()

# Générer un rapport agrégé
processor.generate_aggregate_report(
    output_file="rapport_consolidé.xlsx",
    include_charts=True,
    group_by="site"
)
```

### Traitement d'Images

- Les grandes images sont divisées en tuiles de taille configurable (par défaut 1024x1024 pixels)
- Les tuiles se chevauchent (par défaut 100 pixels) pour maintenir le contexte entre les sections
- Chaque tuile est analysée séparément, puis les résultats sont combinés

## Analyse de Risque Environnemental

Le cœur du projet est l'analyse de risque environnemental, qui comprend plusieurs étapes :

1. **Collecte de données** : Acquisition de données à partir de fichiers, images et API externes
2. **Calcul des scores de risque** : Évaluation des risques pour l'air, l'eau, le sol et les facteurs humains
3. **Génération de recommandations** : Suggestions automatiques basées sur les scores de risque
4. **Création de plans d'action** : Priorisation des actions avec estimation des budgets et délais
5. **Reporting** : Génération de rapports détaillés dans différents formats

### Méthodologie d'Analyse de Risque

L'analyse de risque environnemental suit une méthodologie rigoureuse basée sur les normes internationales et adaptée au contexte marocain :

- **Identification des dangers** : Détection automatique des paramètres environnementaux critiques
- **Évaluation de l'exposition** : Analyse de la proximité des récepteurs sensibles (populations, écosystèmes)
- **Caractérisation des risques** : Calcul des indices de risque par milieu (air, eau, sol, biologique)
- **Hiérarchisation** : Classification des risques selon leur gravité et probabilité

### Paramètres Environnementaux Analysés

L'application extrait et analyse automatiquement les paramètres environnementaux suivants :

| Milieu | Paramètres clés | Sources de données |
|--------|----------------|--------------------|
| **Air** | PM10, PM2.5, NO2, SO2, O3, CO | Images, API OpenWeatherMap, fichiers Excel |
| **Eau** | pH, conductivité, turbidité, DBO5, DCO, oxygène dissous, métaux lourds | Images, analyses de laboratoire, fichiers Excel |
| **Sol** | pH, matière organique, métaux lourds, hydrocarbures | Images, API SoilGrids, fichiers Excel |
| **Biologique** | Biodiversité, espèces protégées, habitats sensibles | Images, fichiers Excel, API OpenStreetMap |

### Calcul des Scores de Risque

Le module `calculate_risk_scores.py` implémente la méthodologie d'analyse de risque environnemental :

```python
from calculate_risk_scores import calculate_site_risk_scores

# Calculer les scores de risque pour un site
risk_scores = calculate_site_risk_scores(
    site_data,  # DataFrame pandas avec les données du site
    weights={   # Pondérations personnalisées (optionnel)
        "air": 0.3,
        "water": 0.3,
        "soil": 0.2,
        "human": 0.2
    }
)

print(f"Score de risque global: {risk_scores['global_score']}")
print(f"Niveau de risque: {risk_scores['risk_level']}")
```

### Interprétation des Scores de Risque

Les scores de risque sont interprétés selon l'échelle suivante :

| Score | Niveau de risque | Interprétation | Action recommandée |
|-------|-----------------|----------------|---------------------|
| 0-20 | Très faible | Impact environnemental négligeable | Surveillance de routine |
| 21-40 | Faible | Impact limité et localisé | Mesures préventives simples |
| 41-60 | Modéré | Impact significatif mais maîtrisable | Plan d'action à moyen terme |
| 61-80 | Élevé | Impact important nécessitant attention | Mesures correctives prioritaires |
| 81-100 | Très élevé | Impact critique avec risques majeurs | Intervention immédiate requise |

### Génération de Recommandations

Le module `generate_recommendations.py` analyse les scores de risque et génère des recommandations adaptées au contexte spécifique de chaque site :

```python
from generate_recommendations import generate_site_recommendations

# Générer des recommandations basées sur les scores de risque
recommendations = generate_site_recommendations(risk_scores)

# Exporter les recommandations vers Excel
from generate_recommendations import export_recommendations_to_excel
export_recommendations_to_excel(recommendations, "resultats/recommandations.xlsx")
```

#### Catégories de Recommandations

Les recommandations sont organisées en plusieurs catégories pour faciliter leur mise en œuvre :

| Catégorie | Description | Exemples |
|-----------|-------------|----------|
| **Surveillance** | Mesures de suivi et monitoring | Installation de stations de mesure, échantillonnage périodique |
| **Prévention** | Actions pour éviter les risques | Mise en place de systèmes de filtration, zones tampons |
| **Mitigation** | Réduction des impacts existants | Traitement des effluents, phytoremédiation des sols |
| **Conformité** | Respect des normes et réglementations | Mise à niveau des installations, certifications |
| **Urgence** | Interventions immédiates | Confinement des pollutions, alertes sanitaires |

#### Priorisation Intelligente

Le système attribue automatiquement un niveau de priorité à chaque recommandation en fonction de :

- La gravité du risque associé
- L'efficacité estimée de la mesure
- La faisabilité technique et économique
- Les exigences réglementaires marocaines

#### Adaptation au Contexte Marocain

Les recommandations sont spécifiquement adaptées au contexte marocain, prenant en compte :

- Les normes environnementales nationales (lois 11-03, 12-03, 13-03, etc.)
- Les meilleures pratiques locales et internationales
- La disponibilité des technologies et ressources au Maroc
- Les conditions climatiques et géographiques spécifiques

### Création de Plans d'Action

Le module `generate_action_plan.py` transforme les recommandations en plan d'action concret et opérationnel :

```python
from generate_action_plan import generate_action_plan

# Créer un plan d'action à partir des recommandations
action_plan = generate_action_plan(
    "resultats/recommandations.xlsx",  # Fichier de recommandations
    output_file="resultats/plan_action.xlsx",  # Fichier de sortie
    budget_constraints=1000000,  # Budget maximal disponible (optionnel)
    timeframe="12 months"  # Période de mise en œuvre (optionnel)
)

# Le plan d'action inclut :
# - Actions prioritaires par site
# - Estimation des budgets
# - Responsables suggérés
# - Échéanciers recommandés
```

#### Structure du Plan d'Action

Le plan d'action généré est structuré de manière à faciliter sa mise en œuvre et son suivi :

| Section | Contenu | Utilité |
|---------|---------|--------|
| **Vue d'ensemble** | Résumé des risques majeurs et actions clés | Vision globale pour les décideurs |
| **Actions par site** | Liste détaillée des actions par site | Organisation des interventions sur le terrain |
| **Calendrier** | Diagramme de Gantt avec échéanciers | Planification temporelle des actions |
| **Budget** | Estimation des coûts par action et par site | Planification financière |
| **Responsabilités** | Attribution des tâches aux équipes | Clarification des rôles |
| **Indicateurs** | Métriques de suivi pour chaque action | Évaluation de l'efficacité |

#### Algorithme de Priorisation

Le système utilise un algorithme sophistiqué pour prioriser les actions en fonction de multiples critères :

1. **Impact environnemental** : Priorité aux actions réduisant les risques les plus élevés
2. **Rapport coût-efficacité** : Optimisation des ressources financières
3. **Faisabilité technique** : Évaluation de la complexité de mise en œuvre
4. **Contraintes temporelles** : Prise en compte des urgences et des dépendances entre actions
5. **Exigences réglementaires** : Conformité avec la législation marocaine

#### Estimation des Ressources

Pour chaque action, le système estime automatiquement :

- **Budget requis** : Basé sur des références de coûts adaptées au marché marocain
- **Ressources humaines** : Compétences et temps-homme nécessaires
- **Équipements** : Matériel et technologies requis
- **Délais de réalisation** : Durée estimée pour chaque phase d'implémentation

### Génération de Rapports

L'application offre un système avancé de génération de rapports pour communiquer efficacement les résultats de l'analyse de risque environnemental. Plusieurs modules permettent de générer des rapports dans différents formats, adaptés à différents publics et besoins :

```python
# Rapport HTML interactif
from generate_html_report import generate_html_report
generate_html_report(
    "resultats/analyse_risques.xlsx", 
    "rapports/rapport_risques.html",
    include_charts=True,  # Inclure des graphiques interactifs
    language="fr"  # Langue du rapport (fr, en, ar disponibles)
)

# Rapport final combinant analyse et recommandations
from generate_final_report import generate_final_report
generate_final_report(
    "resultats/analyse_risques.xlsx",
    "resultats/recommandations.xlsx",
    "rapports/rapport_final.html",
    template="templates/rapport_officiel.html",  # Template personnalisé
    include_executive_summary=True  # Ajouter un résumé exécutif
)

# Rapport complet avec graphiques et plan d'action
from generate_complete_report import generate_complete_report
generate_complete_report(
    risk_file="resultats/analyse_risques.xlsx",
    recommendations_file="resultats/recommandations.xlsx",
    action_plan_file="resultats/plan_action.xlsx",
    output_dir="rapports",
    formats=["html", "pdf", "docx"],  # Formats de sortie multiples
    include_annexes=True,  # Inclure des annexes techniques
    include_references=True  # Inclure les références réglementaires
)
```

#### Types de Rapports Disponibles

| Type de Rapport | Description | Public cible | Formats |
|-----------------|-------------|--------------|--------|
| **Rapport de Risque** | Analyse détaillée des risques environnementaux | Experts techniques, consultants | HTML, PDF, XLSX |
| **Rapport de Recommandations** | Synthèse des recommandations prioritaires | Décideurs, gestionnaires | HTML, PDF, DOCX |
| **Plan d'Action** | Plan détaillé avec calendrier et budget | Équipes opérationnelles | HTML, PDF, XLSX, MS Project |
| **Rapport Exécutif** | Résumé concis des points clés | Direction, investisseurs | PDF, PPTX |
| **Rapport Réglementaire** | Format adapté aux exigences légales | Autorités environnementales | PDF, DOCX |
| **Tableau de Bord** | Interface interactive pour explorer les données | Tous utilisateurs | HTML, Dashboard |

#### Personnalisation des Rapports

Les rapports peuvent être personnalisés de nombreuses façons :

- **Templates personnalisés** : Utilisation de templates HTML/CSS/Markdown personnalisés
- **Multilinguisme** : Génération de rapports en français, arabe ou anglais
- **Branding** : Intégration de logos, couleurs et styles d'entreprise
- **Niveaux de détail** : Ajustement du niveau de détail technique selon l'audience
- **Visualisations** : Sélection des types de graphiques et visualisations

#### Intégration de Données Contextuelles

Les rapports intègrent automatiquement des informations contextuelles pertinentes :

- **Références réglementaires** : Normes marocaines et internationales applicables
- **Données historiques** : Évolution des paramètres environnementaux dans le temps
- **Comparaisons** : Benchmarking avec des sites similaires ou des moyennes régionales
- **Cartes et images** : Visualisation géographique des risques et impacts

### Tableau de Bord Interactif

Le module `create_dashboard.py` génère un tableau de bord interactif avec Dash et Plotly, offrant une interface visuelle intuitive pour explorer et analyser les données environnementales :

```python
# Lancer le tableau de bord interactif
python create_dashboard.py --port 8050 --debug False --theme light
```

#### Fonctionnalités du Tableau de Bord

Le tableau de bord offre une expérience utilisateur riche avec plusieurs modules interactifs :

- **Vue d'ensemble des risques** : 
  - Carte interactive des sites avec code couleur par niveau de risque
  - Filtres dynamiques par site, niveau de risque et type de milieu
  - Graphiques de distribution et tableaux détaillés
  - Comparaison multi-sites avec analyses statistiques

- **Détails des paramètres environnementaux** :
  - Visualisation détaillée de chaque paramètre par site
  - Comparaison avec les normes et seuils réglementaires
  - Évolution temporelle des paramètres (si données historiques disponibles)
  - Identification des dépassements et anomalies

- **Analyse des recommandations** : 
  - Sélection d'un site pour visualiser ses recommandations spécifiques
  - Filtrage par catégorie, priorité et statut
  - Graphiques de répartition des recommandations
  - Estimation des impacts après mise en œuvre

- **Suivi du plan d'action** : 
  - Vue Gantt interactive du calendrier d'implémentation
  - Filtres par site, priorité, catégorie et statut
  - Suivi budgétaire avec graphiques de consommation
  - Indicateurs de performance clés (KPIs)

- **Module de simulation** :
  - Simulation de l'impact des actions correctives
  - Scénarios "what-if" pour évaluer différentes stratégies
  - Prédiction des évolutions de risque dans le temps

#### Personnalisation et Accessibilité

Le tableau de bord est hautement personnalisable :

- **Thèmes visuels** : Choix entre thème clair, sombre ou personnalisé
- **Langues** : Interface disponible en français, arabe et anglais
- **Exportation** : Export des visualisations en PNG, PDF ou données brutes
- **Responsive** : Adaptation automatique aux différentes tailles d'écran
- **Mode hors ligne** : Possibilité de générer une version statique pour partage

#### Installation et Prérequis

Pour installer les dépendances nécessaires au tableau de bord :

```python
python install_dependencies.py --dashboard-only
```

Le tableau de bord nécessite :
- Python 3.8+
- Dash 2.0+
- Plotly 5.0+
- Pandas 1.3+
- Un navigateur web moderne (Chrome, Firefox, Edge recommandés)

### Flux de Travail Complet

Voici le flux de travail recommandé pour une analyse de risque environnemental complète :

1. **Collecte de données** :
   ```python
   # Collecter des données environnementales pour un site
   from export_api_to_excel import export_environmental_data_to_excel
   export_environmental_data_to_excel("Casablanca", "donnees/casablanca_env_data.xlsx")
   ```

2. **Préparation des données** :
   - Créer un fichier Excel avec les données de tous les sites à analyser
   - Structure requise : voir la section "Structure des Fichiers de Données"

3. **Analyse de risque** :
   ```python
   from calculate_risk_scores import calculate_all_sites_risk_scores
   risk_results = calculate_all_sites_risk_scores("donnees/sites_data.xlsx")
   risk_results.to_excel("resultats/analyse_risques.xlsx")
   ```

4. **Génération de recommandations** :
   ```python
   from generate_recommendations import generate_recommendations_for_all_sites
   generate_recommendations_for_all_sites(
       "resultats/analyse_risques.xlsx",
       "resultats/recommandations.xlsx"
   )
   ```

5. **Création du plan d'action** :
   ```python
   from generate_action_plan import generate_action_plan
   generate_action_plan(
       "resultats/recommandations.xlsx",
       "resultats/plan_action.xlsx"
   )
   ```

6. **Génération de rapports** :
   ```python
   from generate_complete_report import generate_complete_report
   generate_complete_report(
       "resultats/analyse_risques.xlsx",
       "resultats/recommandations.xlsx",
       "resultats/plan_action.xlsx",
       "rapports"
   )
   ```

7. **Visualisation interactive** :
   ```python
   # Lancer le tableau de bord pour explorer les résultats
   python create_dashboard.py
   ```

### Installation et Configuration

#### Installation du Projet

Pour installer le projet et ses dépendances :

```bash
# Cloner le dépôt
git clone https://github.com/votre-utilisateur/analyse-risque-environnemental-maroc.git
cd analyse-risque-environnemental-maroc

# Installer les dépendances pour l'analyse de risque et les rapports
python install_report_dependencies.py

# Installer les dépendances pour le tableau de bord interactif
python install_dependencies.py
```

#### Structure des Fichiers de Données

Le projet attend certains fichiers Excel avec une structure spécifique :

- **analyse_risques.xlsx** : Données brutes des sites avec indicateurs environnementaux
  - Colonnes requises : `site_id`, `site_name`, `latitude`, `longitude`, `air_quality`, `water_quality`, etc.

- **recommandations.xlsx** : Généré automatiquement, contient les recommandations par site
  - Colonnes : `site_id`, `recommendation_id`, `category`, `description`, `priority`, etc.

- **plan_action.xlsx** : Plan d'action généré à partir des recommandations
  - Colonnes : `action_id`, `site_id`, `description`, `responsible`, `deadline`, `budget`, `status`, etc.

### Traitement de Texte

- Les textes longs sont divisés en morceaux de taille configurable (par défaut 1000 caractères)
- Les morceaux se chevauchent (par défaut 100 caractères) pour maintenir le contexte
- Chaque morceau est analysé séparément, puis les résultats sont combinés et dédupliqués

Ces optimisations permettent d'analyser des documents et images de grande taille sans dépasser les limites de mémoire.

## Utilisation

### Interface Graphique

Pour lancer l'application avec l'interface graphique :

```bash
python main.py gui
```

Ou directement :

```bash
python app.py
```

Pour démarrer l'application sans charger le modèle IA (économie de mémoire) :

```bash
python app.py --no-load-model
```

### Analyse SLRI (Standardiser l'évaluation des risques et impacts)

Le système intègre la méthodologie SLRI officielle pour une évaluation standardisée, interactive et exportable des risques environnementaux.

#### Fonctionnalités SLRI Avancées
- **Évaluation multi-phases** : Pré-construction, Construction, Exploitation, Démantèlement
- **Analyse par milieux** : Physique (eau/sol/air), Biologique, Humain
- **Scoring automatisé** : Système de notation 0-2 avec calculs multi-critères
- **Facteurs temporels/spatiaux** : Durée × Étendue × Fréquence
- **Classification des risques** : Faible, Moyen, Fort, Très grave
- **Navigation par onglets** : Synthèse + 1 onglet par phase dans l'interface principale
- **Tableaux interactifs et exportables** : Tous les résultats SLRI sont présentés sous forme de tableaux (Treeview) avec export Excel/CSV
- **Conformité structurelle** : Les tableaux SLRI respectent la structure officielle du fichier Excel SLRI de référence

#### Utilisation de l'analyse SLRI

- Lancement via le menu **Analyse > Analyse SLRI par phases**
- Saisie des coordonnées et du type de projet
- Résultats affichés dans la page d'accueil sous forme d'onglets :
    - **Synthèse globale** (tableau exportable)
    - **Phases** (Pré-construction, Construction, Exploitation, Démantèlement)
        - Scores par milieu (eau, sol, air)
        - Paramètres détaillés avec conformité ✓/✗
        - Risques majeurs identifiés
    - **Boutons d'export Excel/CSV** sur chaque tableau

##### Exemple visuel de tableau SLRI exporté

| Paramètre       | Valeur mesurée | Unité | Score | Classification | Conforme |
|----------------|---------------|-------|-------|----------------|----------|
| pH             | 7.2           |      | 0.0   | FAIBLE         | ✓        |
| Plomb (Pb)     | 0.015         | mg/L | 2.0   | TRÈS GRAVE     | ✗        |
| DBO5           | 4.8           | mg/L | 0.0   | FAIBLE         | ✓        |
| ...            | ...           | ...   | ...   | ...            | ...      |

- Chaque tableau peut être exporté individuellement en Excel ou CSV.
- Les résultats sont conformes à la matrice SLRI officielle et directement utilisables pour le reporting réglementaire ou la documentation de projet.

#### Structure des données SLRI

```
SLRI/
├── Standardiser-levaluation-des-risques-et-impacts.xlsx  # Fichier Excel maître
├── matrice d'impacts.txt                                 # Matrice d'identification
├── Echelles.txt                                         # Système de notation
├── PRE CONSTRUCTION.txt                                 # Phase pré-construction
├── CONSTRUCTION.txt                                     # Phase construction
├── exploitation.txt                                     # Phase exploitation
├── démantalement.txt                                   # Phase démantèlement
└── a8bf5757-476b-43d5-a344-767ecfb19b88_image.png     # Diagramme méthodologique
```

#### Utilisation de l'analyse SLRI

L'analyse SLRI s'intègre automatiquement lors de la récupération de données environnementales :

```python
from slri_integration import SLRIAnalyzer, integrate_slri_with_main_system

# Analyse SLRI pour des coordonnées données
coordinates = (34.0209, -6.8416)  # Latitude, Longitude
slri_results = integrate_slri_with_main_system(coordinates, "SLRI")

# Accès aux résultats
if "error" not in slri_results:
    phases_scores = slri_results["statistiques_globales"]["scores_par_phase"]
    risques_majeurs = slri_results["statistiques_globales"]["risques_majeurs"]
    recommendations = slri_results["statistiques_globales"]["recommandations"]
```

#### Paramètres évalués par milieu

**Milieu Physique - Eau :**
- Température, pH, Turbidité, Conductivité
- DBO5, DCO, Oxygène dissous
- Nitrates, Nitrites, Ammoniac
- Phosphore total, Azote total
- Métaux lourds (Pb, Cd, Cr, Cu, Zn, Ni, Hg, As)
- Hydrocarbures (HCT, HAP)

**Milieu Physique - Sol :**
- pH, Perméabilité, Matière organique
- Carbone organique, Métaux lourds
- Azote total, Phosphore total

**Milieu Physique - Air :**
- Poussières totales, PM10, PM2.5
- SO₂, NOx, CO, O₃ (ozone)

**Milieu Biologique :**
- Flore : Biodiversité terrestre et marine
- Faune : Mammifères, amphibiens, reptiles
- Statuts de protection et présence sur site

#### Système de scoring SLRI

```
Score paramètre (0-2) :
├── 0 : Conforme aux normes
├── 1 : Dépassement léger (≤10%)
└── 2 : Dépassement important (>10%)

Score temporel-spatial :
Durée (0-4) × Étendue (0-3) × Fréquence (0-4)

Amplitude finale :
├── 0-4   : Faible
├── 5-8   : Moyen
├── 9-12  : Fort
└── 13+   : Très grave
```

#### Export des résultats

Les résultats SLRI peuvent être exportés vers Excel avec :

```python
slri_analyzer = SLRIAnalyzer("SLRI")
slri_data = slri_analyzer.load_slri_data()
assessment = slri_analyzer.generate_global_assessment(slri_data)
slri_analyzer.export_to_excel(assessment, "rapport_slri.xlsx")
```

## Surveillance Continue des Sites Existants

Le système intègre un module complet de **surveillance continue** pour le suivi automatisé et l'efficacité opérationnelle des sites environnementaux.

### 🧩 Fonctionnalités Combinées

#### Traitement par Lots (Batch Processing)
- **Analyse périodique automatisée** des dossiers de rapports mensuels
- **Planification flexible** : quotidienne, hebdomadaire, mensuelle
- **Traitement parallèle** de multiples fichiers (Excel, CSV, PDF, images)
- **Reprise sur erreur** et journalisation détaillée
- **Filtrage intelligent** par patterns de fichiers et dates

#### Tableau de Bord Interactif Avancé
- **KPI temps réel** : taux de conformité, alertes actives, tendances globales
- **Visualisation des tendances** temporelles pour eau, air, sol
- **Alertes visuelles** avec code couleur (🔴 critique, 🟡 attention, ✅ conforme)
- **Navigation intuitive** par onglets (Eau, Air, Sol, Actions)
- **Export interactif** des graphiques et données

#### Comparaison Temporelle des Plans d'Action
- **Analyse évolutive** : janvier vs juin, avant/après interventions
- **Métriques de performance** : taux de completion, utilisation budgétaire
- **Identification automatique** des nouvelles actions et actions terminées
- **Recommandations intelligentes** basées sur l'évolution
- **Visualisations comparatives** avec graphiques d'évolution

#### Alertes Automatiques
- **Seuils configurables** par paramètre et par milieu (eau/air/sol)
- **Notifications multi-canaux** : email, webhook (Slack/Teams)
- **Criticité adaptative** : attention, critique, très grave
- **Historique des alertes** avec traçabilité complète
- **Escalade automatique** selon les règles métier

### ⚙️ Workflow Automatisé

#### Configuration Initiale
```json
{
  "sites": {
    "site_industriel": {
      "name": "Site Industriel Exemple",
      "coordinates": [34.0209, -6.8416],
      "monitoring_frequency": "daily",
      "data_directory": "./surveillance/site_industriel",
      "thresholds": {
        "water": {
          "pH": {"min": 6.5, "max": 8.5, "critical": true},
          "Plomb": {"max": 0.01, "critical": true},
          "DBO5": {"max": 25, "critical": true}
        },
        "air": {
          "PM2.5": {"max": 25, "critical": true},
          "PM10": {"max": 50, "critical": true}
        }
      }
    }
  }
}
```

#### Démarrage du Système
```bash
# Démarrer la surveillance automatique
python site_monitoring.py

# Ou via l'interface graphique
Menu Surveillance > 🔄 Démarrer surveillance automatique
```

#### Lancement du Tableau de Bord
```bash
# Tableau de bord avancé (port 8051)
python monitoring_dashboard.py

# Ou via l'interface graphique
Menu Surveillance > 📊 Tableau de bord avancé
```

#### Comparaison de Plans d'Action
```bash
# En ligne de commande
python action_plan_comparison.py plan_janvier.xlsx plan_juin.xlsx

# Ou via l'interface graphique
Menu Surveillance > 🔄 Comparer plans d'action
```

### 🎯 Utilisation Pratique

#### Surveillance Automatique
1. **Configuration** : Définir sites et seuils via `Menu Surveillance > ⚙️ Configurer surveillance`
2. **Démarrage** : Lancer via `Menu Surveillance > 🔄 Démarrer surveillance automatique`
3. **Monitoring** : Consulter le tableau de bord sur `http://localhost:8051`
4. **Alertes** : Recevoir notifications automatiques par email/webhook

#### Analyse des Tendances
1. **Sélection** : `Menu Surveillance > 📈 Analyser tendances`
2. **Paramètres** : Choisir site et période (7j, 30j, 90j, 1an)
3. **Résultats** : Tableau avec tendances 📈📉➡️ par paramètre
4. **Export** : Sauvegarde Excel/CSV des analyses

#### Comparaison Temporelle
1. **Fichiers** : Sélectionner 2 plans d'action (Excel/CSV)
2. **Analyse** : Comparaison automatique des métriques clés
3. **Recommandations** : Suggestions d'amélioration automatiques
4. **Rapport** : Export Excel complet avec graphiques

### ✅ Avantages Opérationnels

#### Gain de Temps Massif
- **Automatisation complète** : pas de relance manuelle mensuelle
- **Traitement parallèle** : analyse simultanée de centaines de fichiers
- **Détection proactive** : alertes avant problèmes critiques
- **Reporting automatisé** : rapports Excel/CSV générés automatiquement

#### Suivi Visuel Intuitif
- **Tableaux de bord temps réel** avec actualisation automatique
- **Indicateurs visuels clairs** : 🔴🟡✅ pour état des paramètres
- **Graphiques de tendances** interactifs (Plotly/Dash)
- **Navigation par onglets** dans l'interface principale

#### Réactivité via Alertes
- **Notifications instantanées** dès dépassement de seuils
- **Escalade automatique** selon criticité (attention → critique → très grave)
- **Historique complet** des alertes avec traçabilité
- **Intégration Slack/Teams** pour équipes distribuées

#### Analyse Comparative Avancée
- **Évolution temporelle** : progression/régression des actions
- **Métriques de performance** : completion rate, budget utilization
- **Recommandations IA** basées sur patterns historiques
- **Benchmarking automatique** entre périodes

### 📊 Métriques et KPI Surveillés

| Catégorie | Métriques Clés | Alertes |
|-----------|---------------|---------|
| **Conformité** | Taux de paramètres conformes (%) | < 80% = 🟡, < 60% = 🔴 |
| **Tendances** | Évolution mensuelle des paramètres | Dégradation > 10% = 🟡 |
| **Actions** | Taux de completion des plans | < 50% = 🟡, < 30% = 🔴 |
| **Budget** | Utilisation budgétaire (%) | > 90% = 🟡, > 100% = 🔴 |
| **Délais** | Actions en retard | > 5 actions = 🟡, > 10 = 🔴 |

### 📁 Structure des Fichiers de Surveillance

```
surveillance/
├── config/
│   └── monitoring_config.json         # Configuration globale
├── site_exemple/
│   ├── results_20240911_103045.json   # Résultats d'analyse
│   ├── alerts_history.json            # Historique alertes
│   └── trends_analysis.json           # Analyse tendances
├── comparisons/
│   ├── comparison_20240911_144530.json # Résultats comparaison
│   └── comparison_report_20240911.xlsx # Rapport Excel
└── logs/
    └── monitoring.log                  # Logs système
```

### Résolution des problèmes courants

#### Configuration de l'API Gemini

- **Erreur "'str' object has no attribute 'items'"** : Cette erreur peut survenir lors de la sauvegarde de la configuration Gemini. Elle est due à une gestion incorrecte du type de données. Pour résoudre ce problème :
  1. Utilisez le script de correction automatique : `python corriger_probleme_cle_api_gemini.py --fix-str-items`
  2. Ou assurez-vous d'utiliser la dernière version de l'application
  3. Vérifiez que les fichiers `app.py` et `gemini_integration.py` contiennent les vérifications de type appropriées
  4. Redémarrez l'application après avoir effectué les modifications

- **Clé API non reconnue** : Vérifiez que votre clé API est correctement formatée et active dans la console Google Cloud. Vous pouvez utiliser `python corriger_probleme_cle_api_gemini.py --verifier` pour diagnostiquer les problèmes de clé API.

Pour plus de détails sur la configuration et la résolution des problèmes liés à l'API Gemini, consultez :
- [Guide d'utilisation de l'API Gemini](README_GEMINI_API.md)

#### Blocage de l'onglet "Info par Lieu"

- **Problème** : L'onglet "Info par Lieu" pouvait se bloquer indéfiniment lors de la récupération des données par coordonnées géographiques, affichant une barre de progression figée.
- **Cause** : Ce problème était dû à des erreurs non capturées dans les appels aux API externes (notamment SoilGrids et OpenWeatherMap) qui arrêtaient le thread de récupération sans réinitialiser l'interface. De plus, l'absence de timeout sur les requêtes réseau pouvait causer un blocage en cas de non-réponse du serveur.
- **Solution** :
  1. **Correction des API externes** : Les erreurs de logique et de nom de variable dans le module `external_apis.py` ont été corrigées pour éviter les plantages silencieux.
  2. **Ajout d'un Watchdog** : Un mécanisme de surveillance (watchdog) a été implémenté dans `app.py`. Si une récupération de données dépasse 60 secondes, l'interface est automatiquement réinitialisée pour éviter un blocage permanent.
  3. **Amélioration de la robustesse** : La gestion de l'état "occupé" a été renforcée pour empêcher des lancements multiples et garantir que l'interface redevient toujours utilisable, même en cas d'erreur.

- [Guide de résolution du problème de configuration Gemini](GUIDE_RESOLUTION_PROBLEME_GEMINI.md)

Vous pouvez également utiliser le script de diagnostic et correction automatique :
```bash
# Diagnostic complet et correction automatique de tous les problèmes
python corriger_probleme_cle_api_gemini.py --diagnostic-complet

# Correction spécifique du problème 'str' object has no attribute 'items'
python corriger_probleme_cle_api_gemini.py --fix-str-items

# Vérification de la clé API
python corriger_probleme_cle_api_gemini.py --verifier

# Configuration d'une nouvelle clé API
python corriger_probleme_cle_api_gemini.py --cle "VOTRE_NOUVELLE_CLE_API"
```

### Bonnes Pratiques et Conseils d'Utilisation

#### Optimisation des Analyses

- **Données de qualité** : La précision de l'analyse dépend directement de la qualité des données d'entrée. Assurez-vous de collecter des données fiables et à jour.

- **Pondérations personnalisées** : Ajustez les pondérations des facteurs de risque en fonction du contexte spécifique de votre région ou industrie :
  ```python
  custom_weights = {
      "air": 0.35,  # Plus d'importance à la qualité de l'air
      "water": 0.30,
      "soil": 0.20,
      "human": 0.15
  }
  calculate_site_risk_scores(site_data, weights=custom_weights)
  ```

- **Validation croisée** : Comparez les résultats de l'analyse automatique avec des évaluations d'experts pour valider la méthodologie.

#### Personnalisation des Rapports

- **Modèles de rapport** : Créez des modèles de rapport personnalisés pour différents publics (technique, direction, autorités) :
  ```python
  generate_complete_report(
      risk_file="resultats/analyse_risques.xlsx",
      recommendations_file="resultats/recommandations.xlsx",
      action_plan_file="resultats/plan_action.xlsx",
      output_dir="rapports",
      template="templates/rapport_technique.md"  # Template personnalisé
  )
  ```

- **Intégration de données externes** : Enrichissez vos rapports avec des données contextuelles supplémentaires (réglementations locales, normes industrielles, etc.).

#### Suivi des Plans d'Action

- **Mises à jour régulières** : Mettez à jour régulièrement le statut des actions dans le fichier Excel du plan d'action.

- **Analyse de progression** : Utilisez le tableau de bord pour suivre la progression des actions au fil du temps :
  ```python
  # Comparer les plans d'action à différentes dates
  from action_plan_analysis import compare_action_plans
  compare_action_plans(
      "historique/plan_action_janvier.xlsx",
      "historique/plan_action_juin.xlsx",
      output_file="rapports/progression_actions.xlsx"
  )
  ```

#### Dépannage Courant

- **Problèmes d'API** : Si les APIs externes ne répondent pas, vérifiez votre connexion Internet et les quotas d'API.

- **Erreurs de génération de rapport** : Pour les problèmes avec la génération de PDF, assurez-vous que Pandoc est correctement installé :
  ```bash
  # Vérifier l'installation de Pandoc
  pandoc --version
  ```

- **Performances du tableau de bord** : Pour améliorer les performances avec de grands ensembles de données, utilisez l'option de prétraitement :
  ```python
  python create_dashboard.py --preprocess-data
  ```

### Ligne de Commande

Le programme offre plusieurs options en ligne de commande :

#### Traiter un fichier unique

```bash
python main.py file chemin/vers/fichier.xlsx --format xlsx
```

Options de format disponibles : `xlsx`, `csv`, `json`

#### Traiter un lot de fichiers

```bash
python main.py batch chemin/vers/dossier --format xlsx --file-types .xlsx .pdf .jpg
```

Options disponibles :
- `--output-dir` : Spécifier un répertoire de sortie personnalisé
- `--format` : Format de sortie (xlsx, csv, json)
- `--file-types` : Liste des extensions de fichiers à traiter

#### Lancer le serveur web

```bash
python main.py server --host 127.0.0.1 --port 5000
```

#### Lancer l'interface graphique

```bash
python main.py gui
```

Ou simplement :

```bash
python main.py
```

### API Web

Une fois le serveur lancé, vous pouvez utiliser l'API web :

- `GET /` - Page d'accueil de l'API
- `POST /analyze` - Analyser un fichier (multipart/form-data avec champ 'file')
- `GET /results` - Lister les fichiers de résultats disponibles
- `GET /results/<filename>` - Télécharger un fichier de résultats

Exemple avec curl :

```bash
curl -F "file=@chemin/vers/fichier.xlsx" -F "format=json" http://localhost:5000/analyze
```

### Utilisation Programmatique

Vous pouvez également utiliser le pipeline d'analyse directement dans votre code :

```python
from pipeline import AnalysisPipeline
from cloud_api import CloudVisionAPI

# Initialiser le pipeline avec modèle local
pipeline = AnalysisPipeline()

# Analyser un fichier avec le modèle local
result = pipeline.process_file("chemin/vers/fichier.xlsx", output_format="df")

# Traiter un lot de fichiers
results = pipeline.process_batch("chemin/vers/dossier", output_format="xlsx")

# Utiliser les API cloud
cloud_api = CloudVisionAPI(api_provider="openai")  # ou "azure", "google", "qwen", "openrouter"
result = cloud_api.analyze_image("chemin/vers/image.jpg", prompt="Identifiez les risques environnementaux dans cette image")
```

#### Journalisation des Actions

```python
from logger import setup_logging, AuditLogger

# Configurer le logging
logger = setup_logging()

# Journaliser les actions importantes
audit_logger = AuditLogger()
audit_logger.log_action(
    action="Traitement fichier",
    user="nom_utilisateur",
    ip="adresse_ip",
    fichier="chemin/vers/fichier.xlsx"
)
```

## Dépendances Principales

- pandas - Pour la manipulation des données
- tkinter - Pour l'interface graphique
- transformers - Pour l'utilisation du modèle Qwen2-VL
- PIL (Pillow) - Pour le traitement d'images
- pdfplumber - Pour l'extraction de texte à partir de PDF
- pytesseract - Pour l'OCR (reconnaissance optique de caractères)
- requests & beautifulsoup4 - Pour la récupération de données web
- Flask - Pour l'API web
- matplotlib - Pour la visualisation des données

## Performances et Optimisations

### Matériel Recommandé

| Composant | Minimum | Recommandé | Optimal |
|-----------|---------|------------|--------|
| **CPU** | Intel Core i5 / AMD Ryzen 5 (4 cœurs) | Intel Core i7 / AMD Ryzen 7 (8 cœurs) | Intel Core i9 / AMD Ryzen 9 / Threadripper (16+ cœurs) |
| **RAM** | 8 Go | 16 Go | 32+ Go |
| **GPU** | Intégré ou NVIDIA GTX 1650 (4 Go VRAM) | NVIDIA RTX 3060 / AMD RX 6700 (8+ Go VRAM) | NVIDIA RTX 4070+ / A5000+ (16+ Go VRAM) |
| **Stockage** | SSD 256 Go (10 Go libre) | SSD 512 Go (50 Go libre) | SSD NVMe 1 To+ (100+ Go libre) |
| **Réseau** | 10 Mbps (pour API cloud) | 50+ Mbps (pour API cloud) | 100+ Mbps avec faible latence |

### Architecture d'Optimisation

Le système implémente une architecture d'optimisation multiniveau pour maximiser les performances :

#### 1. Optimisations de Calcul

- **Quantification Adaptative** :
  - Conversion automatique des modèles en précision réduite (FP16, INT8, INT4)
  - Sélection dynamique du niveau de quantification selon le matériel disponible
  - Calibration spécifique pour préserver la précision sur les données environnementales

- **Parallélisation Intelligente** :
  - Distribution optimale des charges de travail entre CPU et GPU
  - Parallélisation des opérations indépendantes avec ThreadPoolExecutor
  - Pipeline de traitement asynchrone pour maximiser l'utilisation des ressources
  - Équilibrage de charge dynamique basé sur la complexité des tâches

- **Accélération Matérielle** :
  - Support CUDA pour GPU NVIDIA avec optimisations spécifiques
  - Utilisation de TensorRT pour l'inférence accélérée
  - Support des instructions AVX2/AVX512 sur CPU compatibles
  - Détection et utilisation des NPU/TPU si disponibles

#### 2. Optimisations de Mémoire

- **Gestion Avancée de la Mémoire** :
  - Chargement progressif des modèles et données volumineuses
  - Déchargement automatique des composants non utilisés
  - Pagination intelligente pour les grands ensembles de données
  - Compression des structures de données intermédiaires

- **Mise en Cache Stratégique** :
  - Cache multi-niveau (mémoire, disque, réseau)
  - Préchargement prédictif basé sur les modèles d'utilisation
  - Invalidation sélective pour maintenir la cohérence des données
  - Persistance configurable entre les sessions

- **Optimisation des E/S** :
  - Lectures/écritures asynchrones pour les opérations sur disque
  - Bufferisation optimisée pour les flux de données
  - Compression à la volée des données persistantes
  - Stratégies de lecture anticipée pour les fichiers volumineux

#### 3. Optimisations Algorithmiques

- **Traitement Adaptatif** :
  - Ajustement dynamique de la résolution d'image selon la complexité
  - Sélection automatique des algorithmes selon les caractéristiques des données
  - Échantillonnage intelligent pour les grands ensembles de données
  - Arrêt précoce pour les calculs convergents

- **Réduction de Dimensionnalité** :
  - Application sélective de PCA/t-SNE pour les données à haute dimension
  - Filtrage des caractéristiques non pertinentes
  - Agrégation intelligente des paramètres corrélés
  - Compression sémantique des représentations textuelles

### Métriques de Performance

| Opération | Configuration Minimale | Configuration Recommandée | Configuration Optimale |
|-----------|------------------------|---------------------------|------------------------|
| **Analyse d'un fichier Excel** | 30-60 secondes | 10-20 secondes | 3-8 secondes |
| **Analyse d'une image** (modèle local) | 15-30 secondes | 5-10 secondes | 1-3 secondes |
| **Analyse d'une image** (API cloud) | 5-10 secondes | 3-5 secondes | 1-2 secondes |
| **Génération de rapport** (standard) | 20-40 secondes | 10-15 secondes | 3-8 secondes |
| **Génération de rapport** (complet) | 60-120 secondes | 30-60 secondes | 15-30 secondes |
| **Traitement par lots** (100 fichiers) | 45-90 minutes | 15-30 minutes | 5-15 minutes |

### Modes d'Optimisation Configurables

L'application propose plusieurs modes d'optimisation préconfigurés :

- **Mode Économie** : Minimise l'utilisation des ressources, adapté aux machines limitées
- **Mode Équilibré** : Compromis entre performance et consommation de ressources (défaut)
- **Mode Performance** : Maximise la vitesse d'exécution en utilisant toutes les ressources disponibles
- **Mode Cloud** : Décharge les calculs intensifs vers les API cloud quand c'est possible

Configuration via le fichier `config/performance.json` :

```json
{
  "optimization_mode": "balanced",
  "max_memory_usage": 0.7,  // 70% de la RAM disponible
  "max_gpu_memory": 0.8,    // 80% de la VRAM disponible
  "parallel_processes": "auto",  // Détection automatique
  "cache_strategy": {
    "enabled": true,
    "max_size_gb": 2,
    "ttl_seconds": 3600
  },
  "quantization": {
    "enabled": true,
    "precision": "auto"  // auto, fp16, int8, int4
  },
  "io_optimization": {
    "async_loading": true,
    "compression": true,
    "buffer_size_mb": 64
  },
  "adaptive_processing": {
    "enabled": true,
    "complexity_threshold": 0.7
  }
}
```

### Conseils d'Optimisation pour Utilisateurs

1. **Prétraitement des Données** :
   - Nettoyer les données Excel avant l'analyse (supprimer les lignes/colonnes vides)
   - Redimensionner les images volumineuses à max 1920x1080 pixels
   - Convertir les PDF en images pour une analyse plus rapide

2. **Configuration Système** :
   - Fermer les applications gourmandes en ressources avant l'analyse
   - Désactiver les économiseurs d'écran et mises en veille pendant les longs traitements
   - Maintenir les pilotes GPU à jour pour les meilleures performances

3. **Stratégies de Traitement** :
   - Diviser les grands ensembles de données en lots plus petits
   - Utiliser le mode cloud pour les analyses complexes sur machines limitées
   - Planifier les traitements par lots pendant les périodes de faible utilisation

## Intégration des API Cloud

L'application prend en charge plusieurs API cloud pour l'analyse d'images et l'extraction de paramètres environnementaux :

| API | Description | Avantages | Configuration |
|-----|-------------|-----------|---------------|
| OpenAI Vision | API Vision d'OpenAI | Haute précision, multilingue | Clé API OpenAI |
| Azure Computer Vision | API Vision d'Azure | Bonne détection d'objets, OCR | Clé API Azure + Endpoint |
| Google Cloud Vision | API Vision de Google | Excellente reconnaissance de texte | Clé API Google (JSON) |
| Qwen Vision | API Vision de Qwen | Optimisée pour le chinois et l'anglais | Clé API Qwen |
| OpenRouter (Qwen3 32B) | Proxy vers Qwen3 32B | Modèle très puissant | Clé API OpenRouter |

## API Externes pour les Données Environnementales

L'application utilise plusieurs API gratuites pour récupérer automatiquement des données environnementales et les intégrer dans les analyses :

### Sources de Données Environnementales

| API | Type de Données | Utilisation dans l'Analyse | Couverture Maroc | Clé nécessaire | Gratuit |
|-----|----------------|----------------------------|-------------------|----------------|--------|
| **OpenWeatherMap** | Météo, qualité de l'air (PM10, PM2.5, NO2, SO2, O3, CO), précipitations, UV | Contextualisation des mesures, corrélation avec les paramètres environnementaux | Excellente (résolution 500m-1km) | ✅ Oui | ✅ 1000/jour |
| **SoilGrids** | Composition du sol, pH, texture, carbone organique | Analyse des risques liés au sol, interprétation des contaminants | Bonne (résolution 250m) | ❌ Non | ✅ Oui |
| **OpenStreetMap** | Utilisation des terres, infrastructures, hydrographie | Identification des sources potentielles de pollution, analyse de proximité | Très bonne (zones urbaines), Moyenne (zones rurales) | ❌ Non | ✅ Oui |
| **World Bank Climate** | Données climatiques historiques, projections | Analyse des tendances, prévisions d'impact à long terme | Bonne (niveau régional) | ❌ Non | ✅ Oui |
| **GeoNames** | Données administratives, toponymie | Contextualisation géographique, rapports régionaux | Excellente | ✅ Oui (simple) | ✅ Oui |
| **NASA POWER** | Rayonnement solaire, température | Analyse des facteurs climatiques influençant les paramètres environnementaux | Bonne (résolution 50km) | ❌ Non | ✅ Oui |
| **FAO AquaStat** | Ressources en eau, irrigation | Analyse des risques liés à l'eau, contexte hydrique | Moyenne (niveau national) | ❌ Non | ✅ Oui |

### Exemples d'utilisation des API externes

```python
# Récupérer des données environnementales complètes
from external_apis import ExternalAPIs

# Initialiser les API externes
apis = ExternalAPIs()

# Récupérer les données météo pour une localisation
weather_data = apis.get_weather_data(
    "Rabat, Maroc",
    parameters=["temperature", "humidity", "air_quality", "precipitation"],
    time_period="daily"  # Options: hourly, daily, monthly
)
print(f"Température: {weather_data['Température'][0]}{weather_data['Température'][1]}")
print(f"Humidité: {weather_data['Humidité'][0]}{weather_data['Humidité'][1]}")

# Récupérer les données de qualité de l'air
air_data = apis.get_air_quality_data("Rabat", "Morocco")
print(f"PM2.5: {air_data['PM2.5'][0]} {air_data['PM2.5'][1]}")
print(f"PM10: {air_data['PM10'][0]} {air_data['PM10'][1]}")

# Récupérer les données du sol
soil_data = apis.get_soil_data(
    34.0209, -6.8416,  # Coordonnées de Rabat
    depth=30,  # profondeur en cm
    properties=["ph", "clay", "sand", "organic_carbon"]
)
print(f"pH du sol: {soil_data['pH sol']}")

# Récupérer les points d'intérêt environnementaux à proximité
poi_data = apis.get_nearby_features(
    34.0209, -6.8416,  # Coordonnées de Rabat
    radius=5000,  # 5km autour de Rabat
    categories=["industrial", "agricultural", "water_bodies"]
)
print(f"Points d'eau à proximité: {poi_data['Points d\'eau']}")
print(f"Habitations à proximité: {poi_data['Habitations']}")

# Obtenir les données sur les ressources en eau
water_resources = apis.get_water_resources(
    region="Marrakech-Safi",
    resource_type="groundwater",  # Options: groundwater, surface_water, precipitation
    time_period="annual"  # Options: monthly, annual, historical
)
```

### Enrichissement Intelligent des Données

Le système utilise ces API externes pour :

1. **Compléter les données manquantes** : Estimation des paramètres non mesurés basée sur des modèles prédictifs
2. **Contextualiser les mesures** : Interprétation des valeurs en fonction des conditions météorologiques et géographiques
3. **Analyser les tendances** : Comparaison avec les données historiques pour identifier les évolutions
4. **Évaluer les impacts potentiels** : Modélisation des effets sur les écosystèmes et la santé humaine
5. **Adapter les recommandations** : Personnalisation en fonction du contexte local marocain

### Configuration des API externes

Les clés API et autres paramètres sont configurés dans le fichier `external_api_config.json` :

```json
{
  "openweathermap": {
    "api_key": "votre_clé_api",
    "units": "metric",
    "language": "fr",
    "cache_duration": 3600
  },
  "soilgrids": {
    "resolution": "250m",
    "cache_duration": 86400
  },
  "worldbank": {
    "country_code": "MA"
  },
  "nasa_power": {
    "parameters": ["T2M", "PRECTOT", "RH2M", "ALLSKY_SFC_SW_DWN"],
    "cache_duration": 86400
  },
  "proxy": {
    "enabled": false,
    "http": "http://proxy.example.com:8080",
    "https": "https://proxy.example.com:8080"
  },
  "fallback": {
    "enabled": true,
    "use_cached": true,
    "max_cache_age": 604800
  }
}
```

Pour OpenWeatherMap, vous devez obtenir une clé API gratuite sur [leur site](https://openweathermap.org/api) et l'ajouter au fichier de configuration.

### Configuration des API Cloud

Les clés API sont configurées dans le fichier `cloud_api_config.json`. Vous pouvez également les configurer via l'interface graphique en cliquant sur "Configurer les clés API" dans le menu Configuration.

### Mode d'Analyse Configurable

L'application permet de choisir entre deux modes d'analyse :

- **Mode Local** : Utilise les modèles installés localement (SmolVLM, Moondream, Qwen2-VL)
- **Mode Cloud** : Utilise les API cloud (OpenAI, Azure, Google, Qwen, OpenRouter)

Vous pouvez configurer le mode par défaut dans les paramètres de l'application ou choisir à chaque analyse.

### Outils de Diagnostic

Des outils de diagnostic sont disponibles pour tester et résoudre les problèmes liés aux API cloud :

```bash
# Test des API Google, Azure et OpenAI
python diagnostic_tools/cloud_api_tester.py

# Test des API Qwen et OpenRouter
python diagnostic_tools/test_qwen_openrouter.py --qwen-key VOTRE_CLE_API_QWEN --openrouter-key VOTRE_CLE_API_OPENROUTER

# Diagnostic spécifique pour Google Cloud Vision
python diagnostic_tools/api_diagnostic.py
```

Un guide détaillé de résolution des problèmes pour les API Qwen et OpenRouter est disponible dans `diagnostic_tools/qwen_openrouter_guide.md`.

## Bonnes Pratiques de Développement

### Gestion des Encodages
- Utilisation systématique de l'encodage UTF-8 pour tous les fichiers texte
- Normalisation des caractères spéciaux dans les requêtes web pour éviter les erreurs d'encodage
- Configuration explicite de l'encodage UTF-8 pour les fichiers de log

### Système de Logging Avancé
- Système de logging centralisé et configurable via le module `logger.py`
- Niveaux de log différenciés selon l'importance des messages
- Rotation des fichiers de log pour éviter une croissance excessive
- Journal d'audit séparé pour les actions importantes (traitement de fichiers, erreurs critiques)
- Enregistrement des informations utilisateur et adresse IP pour les actions sensibles

### Gestion de la Configuration
- Configuration centralisée dans le fichier `config.py`
- Sauvegarde des préférences utilisateur dans `app_config.json`
- Configuration des API cloud dans `cloud_api_config.json`
- Interface graphique pour modifier les configurations sans éditer les fichiers

### Structure du Code
- Architecture modulaire avec séparation claire des responsabilités
- Pipeline d'analyse flexible supportant différents types de fichiers et formats de sortie
- Composants d'interface utilisateur réutilisables dans le module `gui_components.py`
- API web RESTful pour l'intégration avec d'autres systèmes
- Tests unitaires pour assurer la qualité du code
- Gestion des erreurs robuste avec messages explicites

## Sécurité et Confidentialité

Le système implémente une architecture de sécurité multicouche pour protéger les données environnementales sensibles tout au long du cycle de traitement.

### Architecture de Sécurité

#### 1. Sécurité des Données

- **Chiffrement des Données au Repos** :
  - Chiffrement AES-256 pour toutes les données stockées localement
  - Rotation automatique des clés de chiffrement
  - Stockage sécurisé des clés de chiffrement avec isolation

- **Sécurité des Données en Transit** :
  - Communications TLS 1.3 pour toutes les interactions réseau
  - Vérification des certificats pour les API externes
  - Tunneling sécurisé pour les transferts de données volumineuses

- **Anonymisation et Pseudonymisation** :
  - Détection automatique des informations sensibles (coordonnées GPS précises, noms d'entreprises)
  - Techniques d'anonymisation configurables (hachage, masquage, agrégation)
  - Options de pseudonymisation pour les analyses nécessitant des identifiants

#### 2. Contrôle d'Accès

- **Authentification Multi-facteurs** :
  - Support de l'authentification par mot de passe renforcé
  - Intégration optionnelle avec les systèmes d'authentification d'entreprise
  - Verrouillage temporaire après tentatives infructueuses

- **Autorisation Granulaire** :
  - Contrôle d'accès basé sur les rôles (RBAC)
  - Permissions spécifiques pour visualisation, édition et administration
  - Isolation des données entre différents projets et utilisateurs

- **Gestion des Sessions** :
  - Expiration automatique des sessions inactives
  - Invalidation des sessions à la déconnexion
  - Limitation du nombre de sessions simultanées

#### 3. Protection des API

- **Gestion Sécurisée des Clés API** :
  - Stockage chiffré des clés API dans un coffre-fort sécurisé
  - Rotation périodique automatique des clés
  - Isolation des clés par service et par environnement

- **Limitation des Requêtes** :
  - Contrôle du débit des requêtes vers les API externes
  - Détection des comportements anormaux
  - Mécanismes anti-abus pour prévenir l'utilisation excessive

### Confidentialité des Données

#### Modes de Confidentialité

L'application propose plusieurs modes de confidentialité configurables :

| Mode | Description | Cas d'Usage |
|------|-------------|------------|
| **Standard** | Équilibre entre fonctionnalités et confidentialité | Analyses générales |
| **Élevé** | Minimisation des données partagées avec les services externes | Données sensibles |
| **Local uniquement** | Aucune donnée envoyée à des services externes | Données hautement confidentielles |
| **Conformité réglementaire** | Paramètres adaptés aux exigences légales spécifiques | Rapports officiels |

#### Paramètres de Confidentialité

Configuration via le fichier `config/privacy.json` :

```json
{
  "privacy_mode": "standard",
  "data_retention": {
    "raw_data_days": 30,
    "processed_results_days": 365,
    "logs_days": 90
  },
  "anonymization": {
    "enabled": true,
    "gps_precision_reduction": true,
    "organization_names": "hash",
    "personal_identifiers": "remove"
  },
  "external_services": {
    "allow_cloud_apis": true,
    "allow_geolocation": true,
    "allow_weather_data": true,
    "allow_regulatory_lookups": true
  },
  "audit": {
    "log_data_access": true,
    "log_analysis_parameters": true,
    "log_export_operations": true
  }
}
```

### Audit et Journalisation

Le système maintient des journaux d'audit détaillés pour toutes les opérations sensibles :

- **Journalisation des Accès** :
  - Enregistrement de toutes les tentatives d'accès (réussies et échouées)
  - Suivi des sessions utilisateur et des actions effectuées
  - Horodatage précis et informations contextuelles

- **Journalisation des Opérations** :
  - Suivi de toutes les analyses et traitements effectués
  - Enregistrement des paramètres utilisés et des résultats générés
  - Traçabilité complète des modifications apportées aux données

- **Alertes de Sécurité** :
  - Détection des comportements anormaux ou suspects
  - Notification en cas d'accès inhabituels ou de tentatives d'intrusion
  - Rapports périodiques sur l'état de la sécurité du système

### Conformité Réglementaire

Le système est conçu pour faciliter la conformité avec les réglementations pertinentes :

- **RGPD (Europe)** : Fonctionnalités de protection des données personnelles
- **Loi 09-08 (Maroc)** : Conformité avec la loi marocaine sur la protection des données
- **ISO 14001** : Support pour les exigences de gestion environnementale
- **ISO 27001** : Alignement avec les normes de sécurité de l'information

#### Gestion des Données Personnelles (RGPD)

Le système intègre des fonctionnalités spécifiques pour la gestion des données personnelles conformément au RGPD :

- **Inventaire des Données** : Cartographie automatique des données personnelles traitées
- **Droits des Personnes Concernées** : Outils pour faciliter l'exercice des droits (accès, rectification, effacement)
- **Registre de Traitement** : Documentation automatique des activités de traitement
- **Minimisation des Données** : Collecte limitée aux données strictement nécessaires
- **Durées de Conservation** : Gestion automatisée des durées de conservation avec suppression programmée

#### Mesures Techniques et Organisationnelles

```python
# Exemple d'utilisation du module de conformité RGPD
from compliance import GDPRCompliance

# Initialisation avec les paramètres de conformité
gdpr = GDPRCompliance(
    data_controller="Nom de l'entreprise",
    dpo_contact="dpo@example.com",
    legal_basis="Intérêt légitime",
    retention_period=365  # jours
)

# Enregistrement d'une activité de traitement
gdpr.register_processing_activity(
    name="Analyse environnementale du site X",
    purpose="Évaluation des risques environnementaux",
    data_categories=["Coordonnées GPS", "Noms des responsables"],
    recipients=["Équipe interne", "Autorités environnementales"]
)

# Génération d'un rapport de conformité
gdpr.generate_compliance_report(output_format="pdf")
```

### Sécurité des API et Intégrations

Le système implémente plusieurs niveaux de protection pour les API internes et externes :

- **Authentification API** :
  - Authentification par jetons JWT avec rotation automatique
  - Validation des signatures pour toutes les requêtes API
  - Support pour OAuth 2.0 pour les intégrations tierces

- **Sécurisation des Points d'Accès** :
  - Limitation du taux de requêtes par IP et par utilisateur
  - Protection contre les attaques par force brute
  - Filtrage des requêtes malveillantes par WAF (Web Application Firewall)

- **Validation des Données** :
  - Validation stricte des entrées pour prévenir les injections
  - Échappement contextuel pour les sorties
  - Vérification des types et formats de données

#### Configuration de la Sécurité API

```json
{
  "api_security": {
    "jwt": {
      "secret_rotation_days": 30,
      "token_expiration_minutes": 60,
      "refresh_token_expiration_days": 7
    },
    "rate_limiting": {
      "requests_per_minute": 60,
      "burst": 10,
      "throttling_response": "429"
    },
    "cors": {
      "allowed_origins": ["https://example.com"],
      "allowed_methods": ["GET", "POST"],
      "allow_credentials": true
    },
    "input_validation": {
      "strict_mode": true,
      "sanitize_inputs": true,
      "max_request_size_kb": 1024
    }
  }
}
```

### Gestion des Vulnérabilités

- **Analyse de Vulnérabilités** :
  - Scans automatiques des dépendances via OWASP Dependency-Check
  - Analyse statique du code pour détecter les failles de sécurité
  - Tests de pénétration périodiques

- **Processus de Correction** :
  - Système de notification immédiate pour les vulnérabilités critiques
  - Procédure de correction accélérée pour les failles de sécurité
  - Suivi documenté des vulnérabilités et des correctifs

- **Mises à Jour de Sécurité** :
  - Vérification automatique des mises à jour de sécurité
  - Déploiement prioritaire des correctifs de sécurité
  - Historique des mises à jour de sécurité appliquées

### Sauvegarde et Récupération des Données

Le système intègre une stratégie complète de sauvegarde et de récupération des données :

- **Politique de Sauvegarde** :
  - Sauvegardes automatiques quotidiennes des données critiques
  - Sauvegardes différentielles hebdomadaires
  - Sauvegardes complètes mensuelles avec conservation longue durée
  - Chiffrement de bout en bout des sauvegardes

- **Mécanismes de Récupération** :
  - Restauration granulaire au niveau des fichiers individuels
  - Restauration complète du système avec conservation des relations
  - Procédure de récupération après sinistre documentée
  - Tests périodiques de restauration pour valider l'intégrité

- **Continuité d'Activité** :
  - Mode hors ligne permettant de continuer le travail en cas de panne réseau
  - Synchronisation automatique à la reconnexion
  - Mécanismes de reprise sur erreur pour les traitements longs

#### Configuration des Sauvegardes

```python
# Exemple d'utilisation du module de sauvegarde
from backup import BackupManager

# Initialisation du gestionnaire de sauvegarde
backup_mgr = BackupManager(
    backup_dir="/path/to/secure/backup",
    encryption_enabled=True,
    compression_level=9
)

# Configuration des politiques de sauvegarde
backup_mgr.configure(
    daily_retention=7,      # Conserver 7 jours de sauvegardes quotidiennes
    weekly_retention=4,     # Conserver 4 semaines de sauvegardes hebdomadaires
    monthly_retention=12,   # Conserver 12 mois de sauvegardes mensuelles
    critical_data_paths=[
        "data/environmental_measurements",
        "data/risk_analysis",
        "reports/generated"
    ]
)

# Exécution d'une sauvegarde manuelle
backup_id = backup_mgr.create_backup(
    backup_type="full",
    include_user_settings=True,
    include_logs=True
)

# Restauration depuis une sauvegarde
backup_mgr.restore_from_backup(
    backup_id=backup_id,
    target_dir="/path/to/restore",
    selective_paths=["data/risk_analysis"]
)
```

### Bonnes Pratiques de Sécurité

1. **Pour les Administrateurs** :
   - Activer l'authentification multi-facteurs
   - Effectuer des sauvegardes régulières et chiffrées
   - Maintenir le système et ses dépendances à jour
   - Réaliser des audits de sécurité périodiques
   - Configurer correctement les pare-feu et les règles d'accès réseau
   - Mettre en place une politique de gestion des incidents de sécurité

2. **Pour les Utilisateurs** :
   - Utiliser des mots de passe forts et uniques
   - Se déconnecter après utilisation sur des postes partagés
   - Vérifier les paramètres de confidentialité avant chaque analyse sensible
   - Signaler immédiatement tout comportement suspect
   - Maintenir à jour les navigateurs et systèmes d'exploitation
   - Être vigilant face aux tentatives de phishing

## Mises à jour récentes (2025-11 → 2025-12)

- **SLRI Excel Updater**
  - Correspondance des paramètres plus robuste (suppression des accents, espaces, parenthèses, tirets).
  - Recherche des paramètres dès la ligne 2 pour inclure les premières lignes du tableau SLRI.
  - Remplissage sécurisé des colonnes D (MIN), E (MAX), F (Valeur mesurée), J (Rejet), K (Mesure+rejet) sans écraser les formules.
  - Journalisation claire: paramètres trouvés/non trouvés avec la ligne cible.

- **Analyse PDF/Texte volumineux**
  - Découpage automatique du texte en morceaux (par taille ou tokens selon le fournisseur) avec chevauchement pour préserver le contexte.
  - Agrégation des réponses en un résultat unique, utilisable pour l'export et la mise à jour SLRI.
  - Réduction des erreurs liées aux limites de contexte des modèles cloud.

- **Fournisseurs IA et modèles**
  - Alias `gemini` → fournisseur `google`. Utiliser des modèles valides: `gemini-1.5-pro` (recommandé) ou `gemini-1.0-pro`.
  - Fallback possible vers `openrouter_qwen` si le fournisseur principal échoue.
  - Messages d'erreur plus explicites (ex: 404 modèle introuvable, 400 contexte trop long).

- **Interface**
  - Intégration d'une interface SLRI simplifiée dans l'application (onglets résultats, export, historique).

## Configuration API rapide

Avant d'utiliser l'IA cloud, configurez vos clés et modèles dans `external_api_config.json` (ou `cloud_api_config.json`) et/ou via variables d'environnement.

Exemple minimal (à adapter):

```json
{
  "active_provider": "google",
  "providers": {
    "google": { "model": "gemini-1.5-pro", "api_key_env": "GEMINI_API_KEY" },
    "openrouter_qwen": { "model": "qwen2.5-7b-instruct", "api_key_env": "OPENROUTER_API_KEY" }
  },
  "nlp": {
    "chunking": { "enabled": true, "target_tokens": 120000, "overlap_tokens": 1000 }
  }
}
```

Variables d'environnement utiles:

- `GEMINI_API_KEY`
- `OPENROUTER_API_KEY`

## Dépannage (Gemini/PDF)

- **Erreur 404: modèle introuvable**
  - Cause: nom de modèle invalide ou non supporté.
  - Solution: utiliser `gemini-1.5-pro` ou `gemini-1.0-pro`, vérifier la version d'API et la liste des modèles supportés.

- **Erreur 400: contexte trop long**
  - Cause: le texte envoyé dépasse la fenêtre de contexte du modèle.
  - Solutions: activer le découpage (chunking), réduire le nombre de pages, ou traiter par lots (ex: 30–50 pages). Ajuster `target_tokens`/`overlap_tokens`.

- **Avertissements pdfminer (non critiques)**
  - Messages du type `Cannot set gray non-stroke color ...` peuvent être ignorés ou masqués en réduisant le niveau de logs.

## Bonnes pratiques SLRI Excel

- La recherche de correspondance supprime accents/espaces/parenthèses/tirets côté DataFrame et côté Excel.
- Les formules existantes ne sont pas écrasées (ex: colonne K si formule → conservée).
- Les en-têtes sont protégés (filtrage par mots-clés). Les paramètres sont recherchés en colonnes A/B/C.
- En cas de paramètre non trouvé, un avertissement est journalisé avec la version normalisée du nom.

## Exemple: découpage de texte en blocs

Selon le fournisseur, le découpage peut être basé sur caractères ou estimation de tokens.

```python
def split_text(text, max_len=120000, overlap=1000):
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_len)
        chunks.append(text[start:end])
        start = max(0, end - overlap)
    return chunks
```

Ensuite, chaque bloc est envoyé à l'API puis les résultats sont agrégés avant l'export SLRI.

## Contribution

Les contributions à ce projet sont les bienvenues. Veuillez suivre ces étapes pour contribuer :

1. Forkez le projet
2. Créez votre branche de fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Poussez vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.