' ============================================================
' AFFILIMAX - Lanceur du watchdog pour le dossier Demarrage
' ============================================================
' Copie automatique dans AppData\...\Startup par
' install_tache_import.bat (demarrage auto SANS droits admin).
' Chemin python absolu + CurrentDirectory : robuste.
' ============================================================
Option Explicit

Dim baseDir, pythonExe, shell
baseDir   = "C:\Users\leordi\affilimax"
pythonExe = "C:\Users\leordi\AppData\Local\Programs\Python\Python311\python.exe"

Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = baseDir
shell.Run """" & pythonExe & """ """ & baseDir & "\watchdog_import.py""", 0, False

WScript.Quit 0
