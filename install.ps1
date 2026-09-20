$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceDir = Join-Path $repoRoot 'pet/hjj'
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$petsDir = Join-Path $codexHome 'pets'
$targetDir = Join-Path $petsDir 'hjj'
$requiredFiles = @('pet.json', 'spritesheet.webp')

foreach ($name in $requiredFiles) {
    $sourceFile = Join-Path $sourceDir $name
    if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
        throw "Required pet file not found: $sourceFile"
    }
}

$needsBackup = $false
if (Test-Path -LiteralPath $targetDir) {
    if (-not (Test-Path -LiteralPath $targetDir -PathType Container)) {
        throw "The HJJ install target exists but is not a directory: $targetDir"
    }
    foreach ($name in $requiredFiles) {
        $sourceFile = Join-Path $sourceDir $name
        $targetFile = Join-Path $targetDir $name
        if (-not (Test-Path -LiteralPath $targetFile -PathType Leaf)) {
            $needsBackup = $true
            continue
        }
        $sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $sourceFile).Hash
        $targetHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $targetFile).Hash
        if ($sourceHash -ne $targetHash) { $needsBackup = $true }
    }
}

if ($needsBackup) {
    $backupRoot = Join-Path $codexHome 'pet-backups'
    $backupDir = Join-Path $backupRoot ('hjj-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Copy-Item -LiteralPath $targetDir -Destination $backupDir -Recurse
    Write-Host "Previous HJJ files backed up to: $(Join-Path $backupDir 'hjj')"
}

New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
foreach ($name in $requiredFiles) {
    Copy-Item -LiteralPath (Join-Path $sourceDir $name) -Destination (Join-Path $targetDir $name) -Force
}

Write-Host "HJJ installed to: $targetDir"
Write-Host 'Restart Codex or refresh the Pets settings, then select HJJ.'
