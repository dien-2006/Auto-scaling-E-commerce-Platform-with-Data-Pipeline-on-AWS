param([switch]$SkipBuild)
$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Push-Location $repoRoot
try {
    $composeArgs = @('compose', '-f', 'docker-compose.yaml', '-f', 'docker-compose.otp.yaml')
    # Capture resolved settings privately; never print config output (it contains secrets).
    $resolved = & docker @composeArgs config --format json
    if ($LASTEXITCODE -ne 0) { throw 'Compose configuration is invalid' }
    $config = ($resolved -join [Environment]::NewLine) | ConvertFrom-Json
    $backendImage = [string]$config.services.backend.image
    $frontendImage = [string]$config.services.frontend.image
    if ($backendImage -notmatch '^coco-backend:([A-Za-z0-9][A-Za-z0-9_.-]{0,127})$') {
        throw 'Expected a versioned coco-backend image'
    }
    $releaseTag = $Matches[1]
    if ($frontendImage -ne ('coco-frontend:' + $releaseTag)) { throw 'Image versions do not match' }
    $outputDir = [System.IO.Path]::GetFullPath((Join-Path $repoRoot ('artifacts/docker/' + $releaseTag)))
    $allowedRoot = [System.IO.Path]::GetFullPath((Join-Path $repoRoot 'artifacts/docker')) + [System.IO.Path]::DirectorySeparatorChar
    if (-not $outputDir.StartsWith($allowedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Invalid export location'
    }
    $backendTar = Join-Path $outputDir ('coco-backend-' + $releaseTag + '.tar')
    $frontendTar = Join-Path $outputDir ('coco-frontend-' + $releaseTag + '.tar')
    if ((Test-Path -LiteralPath $backendTar) -or (Test-Path -LiteralPath $frontendTar)) {
        throw 'Archive already exists. Use a new COCO_IMAGE_TAG or keep the existing release.'
    }
    if (-not $SkipBuild) {
        & docker @composeArgs build backend frontend
        if ($LASTEXITCODE -ne 0) { throw 'Application image build failed' }
    }
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    $records = @()
    foreach ($item in @(@{Image=$backendImage;Path=$backendTar}, @{Image=$frontendImage;Path=$frontendTar})) {
        & docker image save --output $item.Path $item.Image
        if ($LASTEXITCODE -ne 0) { throw 'Docker image export failed' }
        $inspection = & docker image inspect $item.Image
        if ($LASTEXITCODE -ne 0) { throw 'Docker image inspection failed' }
        $details = (($inspection -join [Environment]::NewLine) | ConvertFrom-Json)[0]
        $records += [ordered]@{
            image=$item.Image; id=$details.Id; platform=($details.Os + '/' + $details.Architecture)
            archive=[System.IO.Path]::GetFileName($item.Path)
            bytes=(Get-Item -LiteralPath $item.Path).Length
            sha256=(Get-FileHash -LiteralPath $item.Path -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
    $encoding = New-Object System.Text.UTF8Encoding($false)
    $manifest = [ordered]@{version=$releaseTag; images=$records}
    [System.IO.File]::WriteAllText((Join-Path $outputDir 'manifest.json'), ($manifest | ConvertTo-Json -Depth 5), $encoding)
    $checksums = ($records | ForEach-Object { $_.sha256 + '  ' + $_.archive }) -join [Environment]::NewLine
    [System.IO.File]::WriteAllText((Join-Path $outputDir 'SHA256SUMS.txt'), $checksums + [Environment]::NewLine, $encoding)
    foreach ($name in @('docker-compose.yaml','docker-compose.otp.yaml','.env.example')) {
        Copy-Item -LiteralPath (Join-Path $repoRoot $name) -Destination (Join-Path $outputDir $name)
    }
    Copy-Item -LiteralPath (Join-Path $repoRoot 'docs/docker-release.md') -Destination (Join-Path $outputDir 'README.md')
    Write-Output ('Exported two application images to: ' + $outputDir)
    Write-Output 'No private env, credentials or database data are included.'
} finally {
    Pop-Location
}
