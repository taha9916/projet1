# Script PowerShell pour créer un raccourci sur le bureau

# Chemin du projet
$projetPath = $PSScriptRoot

# Chemin du bureau
$desktopPath = [Environment]::GetFolderPath("Desktop")

# Créer un raccourci pour l'application GUI
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$desktopPath\Analyse Risque Environnemental.lnk")
$Shortcut.TargetPath = "$projetPath\lancer_application.bat"
$Shortcut.WorkingDirectory = "$projetPath"
$Shortcut.Description = "Lancer l'application d'analyse de risque environnemental"
$Shortcut.IconLocation = "$env:SystemRoot\System32\SHELL32.dll,43"
$Shortcut.Save()

# Créer un raccourci pour le serveur web
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$desktopPath\Serveur Web Analyse Risque.lnk")
$Shortcut.TargetPath = "$projetPath\lancer_serveur_web.bat"
$Shortcut.WorkingDirectory = "$projetPath"
$Shortcut.Description = "Lancer le serveur web d'analyse de risque environnemental"
$Shortcut.IconLocation = "$env:SystemRoot\System32\SHELL32.dll,44"
$Shortcut.Save()

# Créer un raccourci pour dots.ocr (IA locale)
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$desktopPath\dots.ocr - IA Locale.lnk")
$Shortcut.TargetPath = "$projetPath\lancer_dots_ocr.bat"
$Shortcut.WorkingDirectory = "$projetPath"
$Shortcut.Description = "Lancer dots.ocr comme IA locale pour l'analyse d'images"
$Shortcut.IconLocation = "$env:SystemRoot\System32\SHELL32.dll,70"
$Shortcut.Save()

Write-Host "Raccourcis créés avec succès sur le bureau!" -ForegroundColor Green
Write-Host "Appuyez sur une touche pour continuer..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")