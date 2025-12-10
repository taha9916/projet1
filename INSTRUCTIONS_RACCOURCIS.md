# Instructions pour créer des raccourcis sur le bureau

Ce document explique comment créer des raccourcis sur votre bureau pour lancer rapidement l'application d'analyse de risque environnemental.

## Méthode automatique (recommandée)

1. Faites un clic droit sur le fichier `creer_raccourci_bureau.ps1`
2. Sélectionnez "Exécuter avec PowerShell"
3. Si une fenêtre de sécurité apparaît, cliquez sur "Exécuter"
4. Les raccourcis seront automatiquement créés sur votre bureau

## Méthode manuelle

Si vous préférez créer les raccourcis manuellement :

1. Faites un clic droit sur votre bureau
2. Sélectionnez "Nouveau" > "Raccourci"
3. Dans le champ "Emplacement de l'élément", entrez le chemin complet vers le fichier batch :
   ```
   [Chemin du projet]\lancer_application.bat
   ```
4. Cliquez sur "Suivant"
5. Donnez un nom au raccourci, par exemple "Analyse Risque Environnemental"
6. Cliquez sur "Terminer"

Répétez ces étapes pour créer un raccourci vers `lancer_serveur_web.bat` si nécessaire.

## Utilisation des raccourcis

Une fois les raccourcis créés :

- Double-cliquez sur "Analyse Risque Environnemental" pour lancer l'interface graphique
- Double-cliquez sur "Serveur Web Analyse Risque" pour lancer le serveur web

## Résolution des problèmes

Si vous rencontrez des problèmes lors de l'exécution du script PowerShell :

1. Assurez-vous que PowerShell est installé sur votre système
2. Vous devrez peut-être modifier la politique d'exécution de PowerShell. Ouvrez PowerShell en tant qu'administrateur et exécutez :
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser
   ```
3. Si les raccourcis ne fonctionnent pas, vérifiez que les chemins dans les fichiers batch sont corrects