param(
    [string]$DistributionPath = '',
    [string]$SetupPath = ''
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$dist = if ($DistributionPath) { [System.IO.Path]::GetFullPath($(if ([System.IO.Path]::IsPathRooted($DistributionPath)) { $DistributionPath } else { Join-Path $root $DistributionPath })) } else { Join-Path $root 'dist' }
$build = Join-Path $root 'build'
$payload = Join-Path $build 'installer-payload.zip'
$stub = Join-Path $build 'installer-stub.exe'
$output = if ($SetupPath) { [System.IO.Path]::GetFullPath($(if ([System.IO.Path]::IsPathRooted($SetupPath)) { $SetupPath } else { Join-Path $root $SetupPath })) } else { Join-Path $dist 'C++Adventure-Setup.exe' }
if (-not (Test-Path (Join-Path $dist 'CppAdventure\CppAdventure.exe'))) { throw 'Run build-windows.bat before creating the setup package.' }
New-Item -ItemType Directory -Force -Path $build | Out-Null
if (Test-Path -LiteralPath $payload) { Remove-Item -LiteralPath $payload -Force }
Compress-Archive -Path @((Join-Path $dist 'CppAdventure'), (Join-Path $root 'installer\install.ps1')) -DestinationPath $payload -CompressionLevel Optimal
g++ -municode -mwindows -static -static-libgcc -static-libstdc++ (Join-Path $root 'installer\installer_stub.cpp') -o $stub -lshell32
if ($LASTEXITCODE -ne 0) { throw 'Could not compile the Windows setup launcher.' }
& python (Join-Path $root 'build_sfx.py') $stub $payload $output
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $output)) { throw 'Could not assemble the Windows setup executable.' }
Write-Host "Setup package created: $output"
