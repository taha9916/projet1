# SLRI - Analyse par Lieu et Mise à jour Excel

## Description
Ce projet permet de réaliser une analyse environnementale SLRI (Standardiser l'évaluation des risques et impacts) et de mettre à jour automatiquement un fichier Excel SLRI (.xlsm) avec les valeurs mesurées, les intervalles de référence, et les calculs nécessaires.

## Fonctionnalités principales
- **Remplissage automatique** des colonnes D (MIN), E (MAX), F (Valeur mesurée), J (Rejet), K (Valeur Mesure+rejet) dans le fichier Excel SLRI, sans écraser les en-têtes ni les formules.
- **Détection dynamique** des colonnes par analyse des en-têtes (même fusionnés ou multi-lignes).
- **Gestion robuste** des noms de paramètres (accents, majuscules/minuscules, parenthèses, etc.) pour garantir la correspondance entre DataFrame et Excel.
- **Utilisation de win32com** pour manipuler les fichiers Excel natifs (.xlsm) sans corruption.
- **Remplissage des intervalles de référence** (MIN/MAX) selon les normes marocaines/internationales.
- **Protection des formules et de la structure** du fichier Excel d'origine.
- **Logs détaillés** pour tracer les correspondances et les éventuels problèmes de remplissage.

## Utilisation
1. Lancer l'application (`python app.py`).
2. Sélectionner le fichier Excel SLRI à mettre à jour.
3. L'application détecte et remplit automatiquement les colonnes D, E, F, J, K pour chaque paramètre environnemental.
4. Les valeurs manquantes sont complétées par des valeurs de référence si besoin.
5. Le fichier Excel mis à jour conserve ses en-têtes, formules et format.

## Points techniques importants
- **Recherche de paramètres** : la correspondance est faite de façon tolérante (normalisation accent/ponctuation/espaces) pour éviter les erreurs de mapping.
- **Début de recherche à la ligne 2** : pour inclure tous les paramètres, même ceux en haut du tableau.
- **Sauvegarde automatique** d'une copie de sauvegarde avant toute modification.

## Dépendances
- Python 3.8+
- pandas
- win32com (pywin32)

## Contact
Pour toute question ou amélioration : [Votre nom, email]
