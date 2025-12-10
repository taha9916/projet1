@echo off
echo Lancement de dots.ocr comme IA locale...
echo.

:: Vérifier si Python est installé
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python n'est pas installé ou n'est pas dans le PATH.
    echo Veuillez installer Python 3.8 ou supérieur.
    pause
    exit /b 1
)

:: Vérifier l'installation de dots.ocr
echo Vérification de l'installation de dots.ocr...
python verifier_dots_ocr.py

:: Vérifier si le modèle dots.ocr est installé
if not exist "models\dots_ocr" (
    echo Installation du modèle dots.ocr...
    python install_dots_ocr.py
    if %errorlevel% neq 0 (
        echo Erreur lors de l'installation du modèle dots.ocr.
        pause
        exit /b 1
    )
)

:: Proposer un test rapide
echo.
echo Voulez-vous effectuer un test rapide de dots.ocr ? (O/N)
set /p choix=Votre choix: 

if /i "%choix%"=="O" (
    echo.
    echo Lancement du test rapide de dots.ocr...
    python tester_dots_ocr.py
    echo.
)

:: Afficher les options disponibles
echo.
echo Options disponibles:
echo 1. Analyser une image:           python demo_dots_ocr_local.py chemin/vers/image.jpg
echo 2. Extraire données de rapport:  python demo_extraction_rapports.py chemin/vers/rapport.pdf --type environnement --format markdown
echo 3. Test rapide:                  python tester_dots_ocr.py
echo 4. Vérifier l'installation:      python verifier_dots_ocr.py
echo.

python -c "import os; print('Répertoire de travail actuel:', os.getcwd())"
echo.

cmd /k