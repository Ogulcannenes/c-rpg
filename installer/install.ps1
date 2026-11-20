$ErrorActionPreference = 'Stop'
$installRoot = if ($env:CPP_ADVENTURE_INSTALL_ROOT) { $env:CPP_ADVENTURE_INSTALL_ROOT } else { Join-Path $env:LOCALAPPDATA 'Programs\CppAdventure' }
$shortcutRoot = $env:CPP_ADVENTURE_SHORTCUT_ROOT
$startMenu = if ($shortcutRoot) { Join-Path $shortcutRoot 'StartMenu\C++ Adventure' } else { Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\C++ Adventure' }
$desktop = if ($shortcutRoot) { Join-Path $shortcutRoot 'Desktop' } else { [Environment]::GetFolderPath('Desktop') }
New-Item -ItemType Directory -Force -Path $installRoot, $startMenu, $desktop | Out-Null
$appSource = Join-Path $PSScriptRoot 'CppAdventure'
Copy-Item -Path (Join-Path $appSource '*') -Destination $installRoot -Recurse -Force
$appData = if ($env:CPP_ADVENTURE_DATA_ROOT) { $env:CPP_ADVENTURE_DATA_ROOT } else { Join-Path $env:LOCALAPPDATA 'CppAdventure' }
if ($env:CPP_ADVENTURE_LEGACY_DB -and (Test-Path -LiteralPath $env:CPP_ADVENTURE_LEGACY_DB)) {
    New-Item -ItemType Directory -Force -Path $appData | Out-Null
    $legacyPointer = Join-Path $appData 'legacy_db_path.txt'
    if (-not (Test-Path -LiteralPath $legacyPointer)) { Set-Content -LiteralPath $legacyPointer -Value $env:CPP_ADVENTURE_LEGACY_DB -Encoding UTF8 }
}
$shell = New-Object -ComObject WScript.Shell
foreach ($shortcutPath in @((Join-Path $startMenu 'C++ Adventure.lnk'), (Join-Path $desktop 'C++ Adventure.lnk'))) {
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = Join-Path $installRoot 'CppAdventure.exe'
    $shortcut.WorkingDirectory = $installRoot
    $shortcut.Description = 'Local C++ learning adventure'
    $shortcut.Save()
}
Write-Host 'C++ Adventure installed for this Windows user.'
