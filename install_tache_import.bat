@echo off
REM ============================================================
REM AFFILIMAX - INSTALLATION DES TACHES PLANIFIEES WINDOWS
REM ============================================================
REM Cree 2 taches :
REM   1. AffilimaxImportWatchdog : au demarrage de session, lance le
REM      watchdog en arriere-plan (fenetre cachee). Surveille le dossier
REM      rapports_amazon\ : tout CSV depose est importe automatiquement.
REM   2. AffilimaxImportQuotidien : tous les jours a 09h30, importe
REM      rapports_amazon\revenus.csv s'il existe (filet de securite).
REM
REM Usage : double-cliquer sur ce fichier, ou :
REM    install_tache_import.bat
REM ============================================================

setlocal

REM --- Emplacement du projet (dossier de ce script) ---
set "BASE=%~dp0"
REM Retirer le \ final pour schtasks
if "%BASE:~-1%"=="\" set "BASE=%BASE:~0,-1%"

REM --- Tache 1 : Watchdog au demarrage (fenetre cachee) ---
echo.
echo [1/2] Creation de la tache "AffilimaxImportWatchdog" (demarrage)...

schtasks /Create /TN "AffilimaxImportWatchdog" /TR "wscript.exe \"%BASE%\launch_watchdog_hidden.vbs\"" /SC ONLOGON /RL LIMITED /F
if errorlevel 1 (
    echo   ERREUR: tache watchdog non creee. Lance en admin ? sinon, clique droit > Executer en tant qu'administrateur.
)

REM --- Tache 2 : Import quotidien (filet de securite) ---
echo.
echo [2/2] Creation de la tache "AffilimaxImportQuotidien" (09h30 tous les jours)...

schtasks /Create /TN "AffilimaxImportQuotidien" /TR "\"%BASE%\importer_ventes_auto.bat\"" /SC DAILY /ST 09:30 /RL LIMITED /F
if errorlevel 1 (
    echo   ERREUR: tache quotidienne non creee.
)

echo.
echo ============================================================
echo  Installation terminee. Verifier avec :
echo    schtasks /Query /TN AffilimaxImportWatchdog
echo    schtasks /Query /TN AffilimaxImportQuotidien
echo ============================================================
pause
