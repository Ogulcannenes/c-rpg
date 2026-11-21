@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python 3.10 veya uzeri bulunamadi.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" if not exist ".venv\bin\python.exe" python -m venv .venv
if errorlevel 1 exit /b 1
if exist ".venv\Scripts\python.exe" set "CPP_PY=.venv\Scripts\python.exe"
if exist ".venv\bin\python.exe" set "CPP_PY=.venv\bin\python.exe"
if not defined CPP_PY (
  echo Python sanal ortami olusturulamadi.
  exit /b 1
)
"%CPP_PY%" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
"%CPP_PY%" -m pip install -r requirements-desktop.lock.txt
if errorlevel 1 exit /b 1
echo Masaustu bagimliliklari hazir.
endlocal
