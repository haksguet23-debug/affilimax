@echo off
chcp 65001 >nul 2>&1
cd /d C:\Windows\system32

echo ============================================================
echo    AFFILIMAX - Lancement du Moteur de Gains
echo    Demarrage du serveur + generation SEO + promotion auto
echo ============================================================
echo.

echo [1/3] Demarrage du serveur HTTP sur le port 8765...
start "Affilimax-Server" python -u server.py
timeout /t 3 /nobreak >nul

echo [2/3] Exposition publique (cloudflared tunnel)...
start "Affilimax-Tunnel" C:\Windows\system32\bin\cloudflared.exe tunnel --url http://127.0.0.1:8765 --no-autoupdate
timeout /t 5 /nobreak >nul

echo [3/3] Generation du contenu SEO...
python gain_engine.py --once

echo.
echo ============================================================
echo    SYSTEME DEMARRE !
echo    Dashboard: http://localhost:8765
echo    Status:    http://localhost:8765/status.html
echo    Boutique:  http://localhost:8765/boutique.html
echo.
echo    Pour arreter : ferme les fenetres Python et Cloudflared
echo    Les logs sont dans server_output.log et tunnel_output.log
echo ============================================================
echo.
pause
