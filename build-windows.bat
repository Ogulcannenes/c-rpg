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
for /f "usebackq delims=" %%v in (`"%CPP_PY%" installer\app_version.py`) do set "APP_VERSION=%%v"
if not defined APP_VERSION (
  echo Surum okunamadi.
  exit /b 1
)
rem Inno Setup gives a real uninstaller and closes a running copy; without it the older self-extracting setup is built.
set "ISCC="
for %%p in ("%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" "%ProgramFiles%\Inno Setup 6\ISCC.exe" "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe") do if exist %%p set "ISCC=%%~p"
if defined ISCC (
  "%ISCC%" /Qp /DAppVersion=%APP_VERSION% installer\CppAdventure.iss
  if errorlevel 1 exit /b 1
  echo Kurulum:  dist\C++Adventure-Setup-%APP_VERSION%.exe
) else (
  echo Inno Setup 6 bulunamadi; eski tek dosyalik kurulum paketleniyor.
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0package-installer.ps1"
  if errorlevel 1 exit /b 1
  echo Kurulum:  dist\C++Adventure-Setup.exe
)
echo Uygulama: dist\CppAdventure\CppAdventure.exe  (surum %APP_VERSION%)
endlocal
