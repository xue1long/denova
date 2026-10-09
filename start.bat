@echo off
rem Double-click launcher for the Denova dev web UI.
rem Opens a new PowerShell window that runs scripts\start-webui.ps1.

setlocal
set "REPO_ROOT=%~dp0"
set "PS_SCRIPT=%REPO_ROOT%scripts\start-webui.ps1"

if not exist "%PS_SCRIPT%" (
    echo Cannot find "%PS_SCRIPT%". Run this script from the repository root.
    pause
    exit /b 1
)

powershell.exe -NoLogo -NoExit -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
set "RC=%ERRORLEVEL%"

endlocal & exit /b %RC%
