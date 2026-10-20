param(
    [string]$Python = "python",
    [string]$DistRoot = "",
    [string]$BuildRoot = "",
    [string]$ReleaseRoot = "",
    [string]$Iscc = "",
    [switch]$Installer
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
if (-not $DistRoot) { $DistRoot=Join-Path $root 'dist' }
if (-not $BuildRoot) { $BuildRoot=Join-Path $root 'build/pyinstaller' }
if (-not $ReleaseRoot) { $ReleaseRoot=Join-Path $root 'release' }
$DistRoot=[IO.Path]::GetFullPath($DistRoot)
$BuildRoot=[IO.Path]::GetFullPath($BuildRoot)
$ReleaseRoot=[IO.Path]::GetFullPath($ReleaseRoot)
Push-Location $root
try {
    & $Python -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Dependency check failed' }
    & $Python tools/generate_icon.py
    if ($LASTEXITCODE -ne 0) { throw 'Icon generation failed' }
    & $Python -m PyInstaller --noconfirm --clean --distpath $DistRoot --workpath $BuildRoot packaging/SmartPowerAnalyzer.spec
    if ($LASTEXITCODE -ne 0) { throw 'EXE build failed' }
    $package=Join-Path $DistRoot 'SmartPowerAnalyzer'
    $verification=Join-Path $BuildRoot ('frozen-verification-'+[Guid]::NewGuid().ToString('N'))
    & $Python tools/verify_frozen.py $package $verification
    if ($LASTEXITCODE -ne 0) { throw 'Real EXE verification failed; installer not built' }
    New-Item -ItemType Directory -Force $ReleaseRoot | Out-Null
    if ($Installer) {
        if (-not $Iscc) { $Iscc=(Get-Command ISCC.exe -ErrorAction SilentlyContinue).Source }
        if (-not $Iscc -or -not (Test-Path -LiteralPath $Iscc)) { throw 'Inno Setup ISCC.exe is required for -Installer' }
        & $Iscc ('/DDistDir='+$package) ('/DReleaseDir='+$ReleaseRoot) packaging/SmartPowerAnalyzer.iss
        if ($LASTEXITCODE -ne 0) { throw 'Installer compilation failed' }
    }
    & $Python tools/render_manual.py docs/USER_MANUAL_V1.0.md (Join-Path $ReleaseRoot 'USER_MANUAL_V1.0.pdf')
    if ($LASTEXITCODE -ne 0) { throw 'User manual PDF generation failed' }
    $notesSource=Join-Path $root 'release/RELEASE_NOTES_V1.0.md'
    $notesTarget=Join-Path $ReleaseRoot 'RELEASE_NOTES_V1.0.md'
    if ([IO.Path]::GetFullPath($notesSource) -ne [IO.Path]::GetFullPath($notesTarget)) { Copy-Item -LiteralPath $notesSource -Destination $notesTarget -Force }
    & $Python tools/make_release.py $package $ReleaseRoot
    if ($LASTEXITCODE -ne 0) { throw 'Release archive/hash verification failed' }
} finally { Pop-Location }
