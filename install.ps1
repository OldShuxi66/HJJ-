[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$PetId = 'hjj',

    [switch]$All
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceRoot = Join-Path $repoRoot 'pets'
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$petsDir = Join-Path $codexHome 'pets'
$requiredFiles = @('pet.json', 'spritesheet.webp')

if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) {
    throw "Pet collection directory not found: $sourceRoot"
}

if ($All -or $PetId -eq 'all') {
    $petDirs = @(Get-ChildItem -LiteralPath $sourceRoot -Directory | Sort-Object Name)
} else {
    $selected = Join-Path $sourceRoot $PetId
    if (-not (Test-Path -LiteralPath $selected -PathType Container)) {
        $available = (Get-ChildItem -LiteralPath $sourceRoot -Directory | Sort-Object Name | ForEach-Object Name) -join ', '
        throw "Unknown PetId '$PetId'. Available IDs: $available"
    }
    $petDirs = @(Get-Item -LiteralPath $selected)
}

function Install-Pet([System.IO.DirectoryInfo]$SourceDir) {
    $id = $SourceDir.Name
    $metadataPath = Join-Path $SourceDir 'pet.json'
    $metadata = $null

    foreach ($name in $requiredFiles) {
        $sourceFile = Join-Path $SourceDir $name
        if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
            throw "Required pet file not found for '$id': $sourceFile"
        }
    }

    $metadata = Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json
    if ($metadata.id -ne $id) {
        throw "Folder and pet.json ID do not match for '$id': $($metadata.id)"
    }

    $targetDir = Join-Path $petsDir $id
    $needsBackup = $false
    if (Test-Path -LiteralPath $targetDir) {
        if (-not (Test-Path -LiteralPath $targetDir -PathType Container)) {
            throw "The install target exists but is not a directory: $targetDir"
        }
        foreach ($name in $requiredFiles) {
            $sourceFile = Join-Path $SourceDir $name
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
        $backupDir = Join-Path $backupRoot ($id + '-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        Copy-Item -LiteralPath $targetDir -Destination $backupDir -Recurse
        Write-Host "Previous $id files backed up to: $(Join-Path $backupDir $id)"
    }

    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    foreach ($name in $requiredFiles) {
        Copy-Item -LiteralPath (Join-Path $SourceDir $name) -Destination (Join-Path $targetDir $name) -Force
    }

    $displayName = if ($metadata.displayName) { $metadata.displayName } else { $id }
    Write-Host "$displayName ($id) installed to: $targetDir"
}

foreach ($petDir in $petDirs) {
    Install-Pet $petDir
}

Write-Host 'Restart Codex or refresh the Pets settings, then select the installed pet.'
