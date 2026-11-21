# C++ Adventure - bu bilgisayarda gerekenleri denetler, eksikleri (onay alarak) kurar ve uygulamayı hazırlar.
# Проверяет, что нужно приложению, ставит недостающее (с подтверждением) и готовит приложение.
#
#   kur.bat                -> denetle, eksikleri sorarak kur, bağımlılıkları hazırla, uygulamayı aç
#   kur.bat -CheckOnly     -> yalnızca denetle, hiçbir şey kurma
#   kur.bat -Yes           -> soru sormadan kur
param([switch]$CheckOnly, [switch]$Yes)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Say($tr, $ru, $color = 'Gray') { Write-Host "  $tr" -ForegroundColor $color; if ($ru) { Write-Host "  $ru" -ForegroundColor DarkGray } }
function Ok($text)   { Write-Host "  [OK]    $text" -ForegroundColor Green }
function Miss($text) { Write-Host "  [EKSİK] $text" -ForegroundColor Yellow }
function Ask($tr, $ru) {
  if ($Yes) { return $true }
  $answer = Read-Host "  $tr / $ru [E/y = evet/да, H/n = hayır/нет]"
  return $answer -match '^(e|evet|y|yes|д|да)$'
}
function Refresh-Path {
  $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
  $user = [Environment]::GetEnvironmentVariable('Path', 'User')
  $env:Path = "$machine;$user"
}
function Has-Winget { [bool](Get-Command winget -ErrorAction SilentlyContinue) }
function Winget-Install($id, $extra = @()) {
  $wingetArgs = @('install', '--id', $id, '-e', '--accept-package-agreements', '--accept-source-agreements') + $extra
  & winget @wingetArgs
  Refresh-Path
}

# ---------- denetimler / проверки ----------
function Find-Python {
  foreach ($cmd in @('py', 'python')) {
    $found = Get-Command $cmd -ErrorAction SilentlyContinue
    if (-not $found) { continue }
    if ($found.Source -like '*\WindowsApps\*') { continue }   # Microsoft Store kısayolu, gerçek Python değil
    $pyArgs = if ($cmd -eq 'py') { @('-3') } else { @() }
    try {
      $ver = & $found.Source @pyArgs -c "import sys;print('%d.%d.%d' % sys.version_info[:3])" 2>$null
    } catch { continue }
    if ($ver -and [version]$ver -ge [version]'3.10') { return @{ Path = $found.Source; Args = $pyArgs; Version = $ver } }
  }
  return $null
}

function Find-Compiler {
  if ($env:CPP_ADVENTURE_COMPILER -and (Test-Path $env:CPP_ADVENTURE_COMPILER.Trim('"'))) { return $env:CPP_ADVENTURE_COMPILER.Trim('"') }
  foreach ($name in @('g++', 'clang++')) {
    $found = Get-Command $name -ErrorAction SilentlyContinue
    if ($found) { return $found.Source }
  }
  foreach ($subsystem in @('ucrt64', 'mingw64', 'clang64')) {
    foreach ($name in @('g++.exe', 'clang++.exe')) {
      $candidate = "C:\msys64\$subsystem\bin\$name"
      if (Test-Path $candidate) { return $candidate }
    }
  }
  return $null
}

function Find-WebView2 {
  $client = 'Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'
  foreach ($key in @("HKLM:\SOFTWARE\WOW6432Node\$client", "HKLM:\SOFTWARE\$client", "HKCU:\Software\$client")) {
    try {
      $pv = (Get-ItemProperty -Path $key -Name pv -ErrorAction Stop).pv
      if ($pv -and $pv -ne '0.0.0.0') { return $pv }
    } catch {}
  }
  return $null
}

function Test-Venv { (Test-Path '.venv\Scripts\python.exe') -or (Test-Path '.venv\bin\python.exe') }

function Report {
  Write-Host ''
  Write-Host '  C++ Adventure - gereksinim denetimi / проверка требований' -ForegroundColor Cyan
  Write-Host '  ---------------------------------------------------------'
  $state = @{}
  $state.Windows64 = [Environment]::Is64BitOperatingSystem
  if ($state.Windows64) { Ok 'Windows 64 bit' } else { Miss 'Windows 64 bit gerekli / нужна 64-битная Windows' }
  $state.Python = Find-Python
  if ($state.Python) { Ok "Python $($state.Python.Version)  ($($state.Python.Path))" } else { Miss 'Python 3.10+' }
  $state.Compiler = Find-Compiler
  if ($state.Compiler) { Ok "C++ derleyicisi / компилятор: $($state.Compiler)" } else { Miss 'G++ (MSYS2 UCRT64)' }
  $state.WebView2 = Find-WebView2
  if ($state.WebView2) { Ok "WebView2 Runtime $($state.WebView2)" } else { Miss 'Microsoft Edge WebView2 Runtime' }
  $state.Venv = Test-Venv
  if ($state.Venv) { Ok 'Uygulama bağımlılıkları (.venv) / зависимости приложения' } else { Miss 'Uygulama bağımlılıkları (.venv) / зависимости приложения' }
  Write-Host ''
  return $state
}

# ---------- kurulumlar / установка ----------
function Install-Python {
  if (-not (Has-Winget)) { Say 'winget yok. Python''u elle kur: https://www.python.org/downloads/ (Add python.exe to PATH işaretli)' 'winget нет. Установи Python вручную (отметь Add python.exe to PATH).' Yellow; return }
  if (-not (Ask 'Python 3.12 kurulsun mu?' 'Установить Python 3.12?')) { return }
  Winget-Install 'Python.Python.3.12' @('--scope', 'user')
}

function Install-Compiler {
  $bash = 'C:\msys64\usr\bin\bash.exe'
  if (-not (Test-Path $bash)) {
    if (-not (Has-Winget)) { Say 'winget yok. MSYS2''yi elle kur: https://www.msys2.org' 'winget нет. Установи MSYS2 вручную: https://www.msys2.org' Yellow; return }
    if (-not (Ask 'MSYS2 (G++ için, ~500 MB) kurulsun mu?' 'Установить MSYS2 (для G++, ~500 МБ)?')) { return }
    Winget-Install 'MSYS2.MSYS2'
    if (-not (Test-Path $bash)) { Say 'MSYS2 C:\msys64 içine kurulamadı; https://www.msys2.org adresinden elle kur.' 'MSYS2 не установлен в C:\msys64; установи вручную.' Yellow; return }
  } elseif (-not (Ask 'MSYS2 var; G++ paketi kurulsun mu?' 'MSYS2 есть; установить пакет G++?')) { return }
  Say 'G++ indiriliyor (birkaç dakika sürebilir)...' 'Загрузка G++ (может занять несколько минут)...'
  $env:MSYSTEM = 'UCRT64'; $env:CHERE_INVOKING = '1'
  & $bash -lc 'pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-gcc'
  if ($LASTEXITCODE -ne 0) {
    # Yeni kurulmuş MSYS2'de paket veritabanı önce güncellenmeli.
    & $bash -lc 'pacman -Sy --noconfirm && pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-gcc'
  }
}

function Install-WebView2 {
  if (-not (Has-Winget)) { Say 'winget yok. WebView2''yi elle kur: https://go.microsoft.com/fwlink/p/?LinkId=2124703' 'winget нет. Установи WebView2 вручную по ссылке выше.' Yellow; return }
  if (-not (Ask 'WebView2 Runtime kurulsun mu?' 'Установить WebView2 Runtime?')) { return }
  Winget-Install 'Microsoft.EdgeWebView2Runtime'
}

function Install-AppDependencies($python) {
  if (-not (Ask 'Uygulama bağımlılıkları (.venv) hazırlansın mı? İnternet gerekir.' 'Подготовить зависимости приложения (.venv)? Нужен интернет.')) { return }
  if (-not (Test-Venv)) { & $python.Path @($python.Args + @('-m', 'venv', '.venv')) }
  $venvPy = if (Test-Path '.venv\Scripts\python.exe') { '.venv\Scripts\python.exe' } else { '.venv\bin\python.exe' }
  & $venvPy -m pip install --upgrade pip
  & $venvPy -m pip install -r requirements-desktop.lock.txt
  if ($LASTEXITCODE -ne 0) { Say 'Bağımlılıklar kurulamadı; internet bağlantısını kontrol et.' 'Не удалось установить зависимости; проверь интернет.' Red }
}

# ---------- akış / порядок ----------
$state = Report
if ($CheckOnly) {
  $missing = @('Python', 'Compiler', 'WebView2', 'Venv') | Where-Object { -not $state[$_] }
  if (@($missing).Count -eq 0) { Say 'Her şey hazır.' 'Всё готово.' Green } else { Say "Eksik: $($missing -join ', ')  ->  kur.bat ile kurabilirsin." "Не хватает: $($missing -join ', ')  ->  запусти kur.bat." Yellow }
  exit ([int](@($missing).Count -gt 0))
}
if (-not $state.Windows64) { exit 1 }

if (-not $state.Python)   { Install-Python }
if (-not $state.WebView2) { Install-WebView2 }
if (-not $state.Compiler) { Install-Compiler }
$python = Find-Python
if ($python -and -not (Test-Venv)) { Install-AppDependencies $python }

$state = Report
if (-not $state.Compiler) {
  Say 'Not: Derleyici olmadan dersler ve sorular çalışır, kod görevleri çalışmaz.' 'Примечание: без компилятора работают уроки и вопросы, но не задания с кодом.' Yellow
}
if (-not ($state.Python -and $state.WebView2 -and $state.Venv)) {
  Say 'Kurulum tamamlanamadı; yukarıdaki EKSİK satırlarına bak ve kur.bat''ı yeniden çalıştır.' 'Установка не завершена; смотри строки EKSİK выше и запусти kur.bat снова.' Red
  exit 1
}
Say 'Hazır! Uygulamayı açmak için: start-desktop.bat' 'Готово! Запуск приложения: start-desktop.bat' Green
if (Ask 'Uygulama şimdi açılsın mı?' 'Открыть приложение сейчас?') {
  Start-Process -FilePath (Join-Path $Root 'start-desktop.bat') -WorkingDirectory $Root
}
exit 0
