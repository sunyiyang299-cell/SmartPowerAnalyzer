param([string]$OutputDirectory)
$ErrorActionPreference='Stop'
if (-not $OutputDirectory) { $OutputDirectory=Join-Path (Split-Path $PSScriptRoot -Parent) 'build/inno-tool' }
$OutputDirectory=[IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Force $OutputDirectory | Out-Null
$download=Join-Path $OutputDirectory 'innosetup-6.7.3.exe'
Invoke-WebRequest 'https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe' -OutFile $download
$expected='9c73c3bae7ed48d44112a0f48e66742c00090bdb5bef71d9d3c056c66e97b732'
if ((Get-FileHash -LiteralPath $download -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) { throw 'Inno Setup download hash mismatch' }
$signature=Get-AuthenticodeSignature -LiteralPath $download
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Pyrsys') { throw 'Inno Setup publisher signature is not valid' }
$compiler=Join-Path $OutputDirectory 'compiler'
$argsInstall=@('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CURRENTUSER','/PORTABLE=1','/NOICONS',('/DIR="'+$compiler+'"'))
$process=Start-Process -FilePath $download -ArgumentList $argsInstall -WindowStyle Hidden -Wait -PassThru
if ($process.ExitCode -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $compiler 'ISCC.exe'))) { throw 'Portable Inno Setup tool extraction failed' }
Write-Output (Join-Path $compiler 'ISCC.exe')
