@echo off
setlocal
cd /d "%~dp0"
call "%~dp0setup-desktop.bat"
if errorlevel 1 exit /b 1
if exist ".venv\Scripts\python.exe" set "CPP_PY=.venv\Scripts\python.exe"
if exist ".venv\bin\python.exe" set "CPP_PY=.venv\bin\python.exe"
if not defined CPP_PY (
  echo Python sanal ortami bulunamadi.
  exit /b 1
)
"%CPP_PY%" -m PyInstaller --noconfirm --clean --distpath dist --workpath build CppAdventure.spec
if errorlevel 1 exit /b 1
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0package-installer.ps1"
if errorlevel 1 exit /b 1
echo Uygulama: dist\CppAdventure\CppAdventure.exe
echo Kurulum:  dist\C++Adventure-Setup.exe
endlocal
