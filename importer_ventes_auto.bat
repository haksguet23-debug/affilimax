@echo off
REM ============================================================
REM AFFILIMAX - IMPORT AUTOMATIQUE DES VENTES AMAZON (quotidien)
REM ============================================================
REM Ce script importe le dernier rapport Amazon telecharge dans
REM le dossier affilimax\rapports_amazon\ et credite les ventes.
REM
REM A configurer 1 seule fois :
REM   1) Modifie TA_CLE_SECRETE ci-dessous = AMAZON_WEBHOOK_SECRET
REM   2) Cree le dossier affilimax\rapports_amazon\
REM   3) Chaque jour : telecharge le rapport sur partenaires.amazon.fr
REM      (Rapports > Rapports de revenus > Telecharger) et sauvegarde-le
REM      dans affilimax\rapports_amazon\revenus.csv (ecrase l'ancien)
REM   4) Planifie avec le Planificateur de taches Windows (voir plus bas)
REM ============================================================

setlocal EnableDelayedExpansion

REM --- CONFIGURATION (A MODIFIER) ---
set "SECRET=TA_CLE_SECRETE"
set "RAPPORT=%~dp0rapports_amazon\revenus.csv"
set "LOG=%~dp0rapports_amazon\import_log.txt"

echo [%date% %time%] Debut de l'import >> "%LOG%"

if not exist "%RAPPORT%" (
    echo [%date% %time%] PAS DE RAPPORT - telecharge-le sur partenaires.amazon.fr >> "%LOG%"
    echo Aucun rapport trouve dans rapports_amazon\revenus.csv
    exit /b 0
)

echo [%date% %time%] Import de %RAPPORT% >> "%LOG%"
cd /d "%~dp0"

REM --dry-run d'abord pour voir, puis import reel
python import_amazon_report.py "%RAPPORT%" --secret "%SECRET%" >> "%LOG%" 2>&1
set "RESULT=%errorlevel%"

echo [%date% %time%] Termine (code %RESULT%) >> "%LOG%"
echo.
echo ============================================
echo  IMPORT TERMINE - voir rapports_amazon\import_log.txt
echo ============================================
exit /b %RESULT%
