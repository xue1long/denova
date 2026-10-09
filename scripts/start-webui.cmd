@echo off
rem Double-click launcher for the Denova dev web UI.
rem Opens a new PowerShell window running scripts\start-webui.ps1.

setlocal
set "REPO_ROOT=%~dp0.."
pushd "%REPO_ROOT%" >nul

set "PS_SCRIPT=%REPO_ROOT%\scripts\start-webui.ps1"

powershell.exe -NoLogo -NoExit -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
set "RC=%ERRORLEVEL%"

popd >nul
endlocal & exit /b %RC%
