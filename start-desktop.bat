@echo off
setlocal
cd /d "%~dp0"
rem Development launcher. The installed app is started from its Start menu shortcut instead.
if exist "%~dp0data\adventure.db" set "CPP_ADVENTURE_LEGACY_DB=%~dp0data\adventure.db"
if exist "dist\CppAdventure\CppAdventure.exe" (
  start "" "%~dp0dist\CppAdventure\CppAdventure.exe"
  exit /b 0
)
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" desktop.py
  exit /b %errorlevel%
)
if exist ".venv\bin\python.exe" (
  ".venv\bin\python.exe" desktop.py
  exit /b %errorlevel%
)
where python >nul 2>nul
if errorlevel 1 (
  echo Python bulunamadi. Python 3.10 veya uzeri gereklidir.
  pause
  exit /b 1
)
python -c "import webview" >nul 2>nul
if errorlevel 1 (
  echo Masaustu arayuzu ilk kez kuruluyor. Internet baglantisi gerekir.
  call setup-desktop.bat
  if errorlevel 1 exit /b 1
  if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" desktop.py
  ) else (
    ".venv\bin\python.exe" desktop.py
  )
) else (
  python desktop.py
)
endlocal
