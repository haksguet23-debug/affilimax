' ============================================================
' AFFILIMAX - Lanceur du watchdog en arriere-plan (sans console)
' Lance watchdog_import.py avec la fenetre masquee.
' Utilise par la tache planifiee AffilimaxImportWatchdog.
' ============================================================
Option Explicit

Dim fso, baseDir, pythonExe, scriptPath, shell
Set fso = CreateObject("Scripting.FileSystemObject")

' Dossier du script VBS (= dossier affilimax)
baseDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Trouver Python (essayer python, puis py -3)
pythonExe = ""
Dim ws
Set ws = CreateObject("WScript.Shell")
On Error Resume Next
pythonExe = ws.Exec("python --version").StdOut.ReadAll
On Error GoTo 0

scriptPath = baseDir & "\watchdog_import.py"

' Lancer en fenetre masquee
Set shell = CreateObject("WScript.Shell")
shell.Run "cmd /c cd /d """ & baseDir & """ && python watchdog_import.py > " & baseDir & "\rapports_amazon\watchdog_console.log 2>&1", 0, False

WScript.Quit 0
