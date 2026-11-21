@echo off
rem C++ Adventure: gerekenleri denetler ve eksikleri kurar (checks requirements, installs what is missing).
rem   kur.bat            denetle ve kur (check and install)
rem   kur.bat -CheckOnly yalnizca denetle (check only)
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\check-and-install.ps1" %*
set "CODE=%errorlevel%"
pause
exit /b %CODE%
