# Guide de correction de l'erreur "VLModel object has no attribute load_model"

Ce guide vous explique comment corriger l'erreur "VLModel object has no attribute load_model" qui apparaît lors de l'utilisation de l'application d'analyse de risque environnemental.

## Description du problème

Lorsque vous lancez l'application et tentez d'analyser un fichier, vous pouvez rencontrer l'erreur suivante :

```
Impossible de charger le modèle local: 'VLModel' object has no attribute 'load_model'
```

Cette erreur se produit car la classe `VLModel` utilisée dans l'application ne possède pas la méthode `load_model` nécessaire pour charger le modèle d'analyse.

## Solutions

Vous avez plusieurs options pour résoudre ce problème :

### Solution 1 : Utiliser le script de correction automatique

Un script de correction automatique a été créé pour faciliter la résolution de ce problème. Pour l'utiliser :

1. Ouvrez une invite de commande (cmd) ou PowerShell
2. Naviguez vers le répertoire du projet
3. Exécutez la commande suivante :

```bash
python fix_vlmodel_error.py --patch-app
```

Ce script modifiera automatiquement le fichier `app.py` pour utiliser l'adaptateur `VLModelAdapter` à la place de la classe `VLModel` défectueuse.

### Solution 2 : Correction manuelle

Si vous préférez corriger le problème manuellement, suivez ces étapes :

1. Ouvrez le fichier `app.py` dans un éditeur de texte
2. Recherchez la ligne suivante :
   ```python
   from model_interface import analyze_environmental_image, VLModel
   ```
   Et remplacez-la par :
   ```python
   from model_interface import analyze_environmental_image
   from vlmodel_adapter import create_vlmodel_adapter, VLModelAdapter
   ```

3. Recherchez la ligne suivante :
   ```python
   self.model = VLModel(model_path)
   ```
   Et remplacez-la par :
   ```python
   self.model = create_vlmodel_adapter(model_path)
   ```

4. Sauvegardez le fichier et redémarrez l'application

### Solution 3 : Utiliser l'interface graphique corrigée

Si vous avez accès à l'interface graphique corrigée, vous pouvez simplement l'utiliser à la place de l'interface standard :

1. Exécutez le script `integration_gui_dots_ocr.py` au lieu de `app.py` :

```bash
python integration_gui_dots_ocr.py
```

Cette interface utilise déjà l'adaptateur `VLModelAdapter` et ne rencontrera pas l'erreur.

## Vérification de la correction

Pour vérifier que la correction a bien été appliquée :

1. Lancez l'application
2. Sélectionnez un fichier à analyser
3. Cliquez sur le bouton "Analyser"

Si l'analyse démarre sans afficher l'erreur "VLModel object has no attribute load_model", la correction a réussi.

## Informations techniques

L'erreur est corrigée en utilisant un adaptateur qui implémente la méthode `load_model` manquante dans la classe `VLModel`. Cet adaptateur est défini dans le fichier `vlmodel_adapter.py` et fournit une interface compatible avec celle attendue par l'application.

La fonction `create_vlmodel_adapter` crée une instance de l'adaptateur configurée avec les paramètres appropriés pour le modèle utilisé dans l'application.

## Support

Si vous rencontrez des difficultés avec cette correction ou si vous avez d'autres questions, consultez le fichier `GUIDE_DEPANNAGE_ERREUR_VLMODEL.md` pour des informations plus détaillées sur le problème et ses solutions.