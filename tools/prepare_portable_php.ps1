param(
    [string] $TargetDir = "runtime/php"
)

$ErrorActionPreference = "Stop"

$phpCommand = Get-Command php -ErrorAction SilentlyContinue
if (-not $phpCommand) {
    throw "PHP nao encontrado no PATH. Instale PHP 8.1+ ou use o workflow do GitHub Actions."
}

$sourceDir = Split-Path -Parent $phpCommand.Source
$targetPath = Resolve-Path -LiteralPath "." | Select-Object -ExpandProperty Path
$targetPath = Join-Path $targetPath $TargetDir

if (Test-Path -LiteralPath $targetPath) {
    Remove-Item -LiteralPath $targetPath -Recurse -Force
}

New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
Copy-Item -Path (Join-Path $sourceDir "*") -Destination $targetPath -Recurse -Force

$iniPath = Join-Path $targetPath "php.ini"
if (-not (Test-Path -LiteralPath $iniPath)) {
    $productionIni = Join-Path $targetPath "php.ini-production"
    $developmentIni = Join-Path $targetPath "php.ini-development"

    if (Test-Path -LiteralPath $productionIni) {
        Copy-Item -LiteralPath $productionIni -Destination $iniPath -Force
    } elseif (Test-Path -LiteralPath $developmentIni) {
        Copy-Item -LiteralPath $developmentIni -Destination $iniPath -Force
    } else {
        New-Item -ItemType File -Path $iniPath -Force | Out-Null
    }
}

$ini = Get-Content -LiteralPath $iniPath -Raw
$ini = $ini -replace '(?m)^\s*;?\s*extension_dir\s*=.*$', 'extension_dir = "ext"'

if ($ini -notmatch '(?m)^\s*extension_dir\s*=') {
    $ini = $ini.TrimEnd() + "`r`nextension_dir = `"ext`"`r`n"
}

Set-Content -LiteralPath $iniPath -Value $ini -Encoding ASCII

& (Join-Path $targetPath "php.exe") -v | Out-Host
Write-Host "Runtime PHP portatil copiado para $targetPath"
