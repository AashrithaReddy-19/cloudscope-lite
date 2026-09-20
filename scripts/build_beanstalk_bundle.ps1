$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$buildRoot = Join-Path $projectRoot ".build\beanstalk"
$bundlePath = Join-Path $projectRoot "cloudscope-backend.zip"

if (-not $buildRoot.StartsWith($projectRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to use a build directory outside the project."
}

if (Test-Path -LiteralPath $buildRoot) {
    Remove-Item -LiteralPath $buildRoot -Recurse -Force
}

New-Item -ItemType Directory -Path $buildRoot | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot "deployment\elasticbeanstalk\Dockerfile") -Destination (Join-Path $buildRoot "Dockerfile")
Copy-Item -LiteralPath (Join-Path $projectRoot "deployment\elasticbeanstalk\start.sh") -Destination (Join-Path $buildRoot "start.sh")
New-Item -ItemType Directory -Path (Join-Path $buildRoot "backend\app\services") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $buildRoot "backend\migrations\versions") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $buildRoot "pricing") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $buildRoot "frontend") -Force | Out-Null
Copy-Item -Path (Join-Path $projectRoot "backend\app\*.py") -Destination (Join-Path $buildRoot "backend\app")
Copy-Item -Path (Join-Path $projectRoot "backend\app\services\*.py") -Destination (Join-Path $buildRoot "backend\app\services")
Copy-Item -Path (Join-Path $projectRoot "backend\migrations\versions\*.py") -Destination (Join-Path $buildRoot "backend\migrations\versions")
Copy-Item -LiteralPath (Join-Path $projectRoot "backend\migrations\env.py") -Destination (Join-Path $buildRoot "backend\migrations\env.py")
Copy-Item -LiteralPath (Join-Path $projectRoot "backend\migrations\script.py.mako") -Destination (Join-Path $buildRoot "backend\migrations\script.py.mako")
Copy-Item -LiteralPath (Join-Path $projectRoot "backend\requirements.txt") -Destination (Join-Path $buildRoot "backend\requirements.txt")
Copy-Item -LiteralPath (Join-Path $projectRoot "backend\alembic.ini") -Destination (Join-Path $buildRoot "backend\alembic.ini")
Copy-Item -LiteralPath (Join-Path $projectRoot "pricing\aws_pricing_catalogue.json") -Destination (Join-Path $buildRoot "pricing\aws_pricing_catalogue.json")
Copy-Item -LiteralPath (Join-Path $projectRoot "frontend\package.json") -Destination (Join-Path $buildRoot "frontend\package.json")
Copy-Item -LiteralPath (Join-Path $projectRoot "frontend\package-lock.json") -Destination (Join-Path $buildRoot "frontend\package-lock.json")
Copy-Item -LiteralPath (Join-Path $projectRoot "frontend\index.html") -Destination (Join-Path $buildRoot "frontend\index.html")
Copy-Item -LiteralPath (Join-Path $projectRoot "frontend\tsconfig.json") -Destination (Join-Path $buildRoot "frontend\tsconfig.json")
Copy-Item -LiteralPath (Join-Path $projectRoot "frontend\vite.config.mjs") -Destination (Join-Path $buildRoot "frontend\vite.config.mjs")
Copy-Item -Path (Join-Path $projectRoot "frontend\src") -Destination (Join-Path $buildRoot "frontend") -Recurse

$forbiddenNames = @(
    ".env",
    "credentials.csv",
    ".git",
    ".terraform",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "tests"
)
$stagedFiles = Get-ChildItem -LiteralPath $buildRoot -Recurse -Force
$forbiddenFiles = @($stagedFiles | Where-Object {
        $relativePath = $_.FullName.Substring($buildRoot.Length + 1)
        $segments = $relativePath -split '[\\/]'
        ($segments | Where-Object { $_ -in $forbiddenNames }).Count -gt 0 -or
        $_.Name -like ".env*" -or
        $_.Extension -in @(".tf", ".tfstate", ".tfvars", ".pem", ".key", ".pyc")
    })

if ($forbiddenFiles.Count -gt 0) {
    throw "Refusing to package forbidden or sensitive files."
}

if (Test-Path -LiteralPath $bundlePath) {
    Remove-Item -LiteralPath $bundlePath -Force
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::Open(
    $bundlePath,
    [System.IO.Compression.ZipArchiveMode]::Create
)

try {
    Get-ChildItem -LiteralPath $buildRoot -Recurse -File |
        Sort-Object FullName |
        ForEach-Object {
            $entryName = $_.FullName.Substring($buildRoot.Length + 1).Replace("\", "/")
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                $archive,
                $_.FullName,
                $entryName,
                [System.IO.Compression.CompressionLevel]::Optimal
            ) | Out-Null
        }
}
finally {
    $archive.Dispose()
}

$verifyArchive = [System.IO.Compression.ZipFile]::OpenRead($bundlePath)
try {
    $entryNames = $verifyArchive.Entries | ForEach-Object { $_.FullName }
    $backslashEntries = @($entryNames | Where-Object { $_.Contains("\") })
    if ($backslashEntries.Count -gt 0) {
        throw "Bundle regression: entries still contain backslash path separators, which Elastic Beanstalk's Linux unzip rejects: $($backslashEntries -join ', ')"
    }
    if ("Dockerfile" -notin $entryNames -or "start.sh" -notin $entryNames) {
        throw "Bundle regression: Dockerfile and start.sh must sit at the archive root."
    }
}
finally {
    $verifyArchive.Dispose()
}

Write-Output "Elastic Beanstalk bundle created at $bundlePath"
Write-Output "Verified: all entries use forward-slash paths; Dockerfile and start.sh are at the archive root."
Write-Output "Terraform will upload this bundle to its private artifact bucket."
