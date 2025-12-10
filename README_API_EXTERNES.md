# Intégration des API Externes pour la Collecte de Données Environnementales

## Présentation

Ce module permet d'enrichir les informations initiales de projet en collectant des données environnementales à partir de diverses API externes. Ces données sont ensuite analysées et intégrées aux résultats de recherche pour fournir une évaluation plus complète des paramètres environnementaux pertinents pour le projet.

## API Intégrées

1. **OpenWeatherMap** - Données météorologiques
   - Température, humidité, précipitations, vent
   - Prévisions et historique météorologique

2. **OpenWeatherMap Air Pollution** - Qualité de l'air
   - Indice de qualité de l'air (AQI)
   - Concentrations de polluants (PM2.5, PM10, O3, NO2, SO2, CO)

3. **SoilGrids** - Données sur les sols
   - Texture du sol
   - pH du sol
   - Teneur en carbone organique
   - Capacité d'échange cationique

4. **FAO AquaStat** - Données sur les ressources en eau
   - Ressources en eau renouvelables
   - Utilisation de l'eau par secteur
   - Stress hydrique et indicateurs de durabilité
   - Données spécifiques par pays (incluant le Maroc)

5. **Banque Mondiale** - Indicateurs environnementaux
   - Émissions de CO2
   - Accès à l'eau potable
   - Indicateurs de développement durable

6. **OpenStreetMap / Overpass API** - Données géographiques
   - Points d'intérêt environnementaux
   - Infrastructures
   - Utilisation des terres

## Configuration

Les paramètres de configuration des API sont stockés dans le fichier `external_api_config.json`. Pour utiliser ces API, vous devez obtenir des clés API pour chaque service et les ajouter à ce fichier.

```json
{
  "openweathermap": {
    "api_key": "VOTRE_CLE_API",
    "url": "https://api.openweathermap.org/data/2.5",
    "air_quality": {
      "enabled": true,
      "standard": "EPA"  // Valeurs possibles: "EPA", "EU", "Morocco"
    }
  },
  "openweathermap_air_pollution": {
    "api_key": "VOTRE_CLE_API",
    "url": "https://api.openweathermap.org/data/2.5/air_pollution"
  },
  "soilgrids": {
    "url": "https://rest.isric.org/soilgrids/v2.0"
  },
  "fao_aquastat": {
    "url": "https://data.apps.fao.org/aquastat/",
    "api_url": "https://fenixservices.fao.org/faostat/api/v1/en/data/",
    "enabled": true
  },
  "worldbank": {
    "url": "https://api.worldbank.org/v2"
  },
  "openstreetmap": {
    "url": "https://nominatim.openstreetmap.org",
    "overpass_url": "https://overpass-api.de/api/interpreter"
  }
}
```

## Utilisation

### Dans l'interface utilisateur

L'interface utilisateur d'informations initiales de projet a été mise à jour pour inclure une option permettant d'activer ou désactiver l'utilisation des API externes. Par défaut, cette option est activée.

Un bouton "Tester les API" a également été ajouté pour vérifier la disponibilité et le bon fonctionnement des API configurées avant de lancer une recherche complète.

### Programmatiquement

Vous pouvez également utiliser les API externes directement dans votre code :

```python
from external_apis import collect_environmental_data_from_apis

# Collecter des données pour une localisation et un type de projet spécifiques
df = collect_environmental_data_from_apis("Paris, France", "Construction résidentielle")

# Afficher les résultats
print(df)
```

Pour tester individuellement chaque API :

```python
from external_apis import ExternalAPIs

# Initialiser la classe ExternalAPIs
apis = ExternalAPIs()

# Tester l'API OpenWeatherMap
weather_data = apis.get_weather_data("Paris, France")
print(weather_data)

# Tester l'API OpenWeatherMap Air Pollution
# Vous pouvez spécifier le standard AQI à utiliser ("EPA", "EU", "Morocco")
air_quality_data = apis.get_air_quality_data("Paris, France", standard="EPA")
print(air_quality_data)

# Tester l'API FAO AquaStat pour les données sur l'eau
# Particulièrement utile pour les projets au Maroc
water_data = apis.get_fao_aquastat_data("MA")  # Code pays pour le Maroc
print(water_data)
```

## Test des API

Un script de test est fourni pour vérifier le bon fonctionnement des API externes :

```
python test_external_apis.py
```

Ce script ouvre une interface graphique permettant de tester les API pour une localisation donnée et d'afficher les résultats.

## Dépannage

### Problèmes courants

1. **Erreur d'authentification** - Vérifiez que vos clés API sont correctement configurées dans le fichier `external_api_config.json`.

2. **Localisation non trouvée** - Assurez-vous que la localisation est correctement orthographiée et qu'elle est reconnue par les services géographiques.

3. **Limite de requêtes atteinte** - Certaines API gratuites ont des limites de requêtes. Vérifiez les quotas de votre compte.

4. **Problèmes de connexion** - Vérifiez votre connexion Internet et assurez-vous que les URL des API sont accessibles.

### Logs

Les erreurs et les avertissements sont enregistrés dans les fichiers de log du projet. Consultez ces fichiers pour plus d'informations sur les problèmes rencontrés.

## Contribution

Pour ajouter de nouvelles API ou améliorer les intégrations existantes, modifiez le fichier `external_apis.py` et mettez à jour la documentation en conséquence.