param(
    [switch]$OneFile,
    [switch]$Installer,
    [switch]$SkipDependencyInstall
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Get-PythonCommand {
    $preferredPython = "C:\Users\psing\AppData\Local\Programs\Python\Python311\python.exe"
    if (Test-Path $preferredPython) {
        return $preferredPython
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        return (Get-Command python).Source
    }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        return "py"
    }

    throw "Python was not found. Install Python 3.11+ and retry."
}

function Get-InnoSetupCompiler {
    $knownPaths = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
    )

    foreach ($path in $knownPaths) {
        if (Test-Path $path) {
            return $path
        }
    }

    $command = Get-Command ISCC -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    return $null
}

function Copy-ZipFromSourceDirectory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourceDirectory,
        [Parameter(Mandatory = $true)]
        [string]$DestinationZipPath
    )

    $tempZipPath = Join-Path $env:TEMP ("{0}.zip" -f [System.Guid]::NewGuid().ToString("N"))
    Compress-Archive -Path (Join-Path $SourceDirectory "*") -DestinationPath $tempZipPath -Force
    Copy-Item -Force -Path $tempZipPath -Destination $DestinationZipPath
    Remove-Item -Force $tempZipPath
}

function New-ScriptInstallerPackage {
    param(
        [Parameter(Mandatory = $true)]
        [string]$BuildFolder,
        [Parameter(Mandatory = $true)]
        [string]$ProjectDistPath,
        [Parameter(Mandatory = $true)]
        [string]$Timestamp
    )

    $tempPackageRoot = Join-Path $env:TEMP "BreaktimeRestaurant-Setup-$Timestamp"
    $packageRoot = Join-Path $ProjectDistPath "BreaktimeRestaurant-Setup-$Timestamp"
    $appTarget = Join-Path $tempPackageRoot "app"

    if (Test-Path $tempPackageRoot) {
        Remove-Item -Recurse -Force $tempPackageRoot
    }

    if (Test-Path $packageRoot) {
        Remove-Item -Recurse -Force $packageRoot
    }

    New-Item -ItemType Directory -Force -Path $tempPackageRoot | Out-Null
    New-Item -ItemType Directory -Force -Path $appTarget | Out-Null

    Copy-Item -Recurse -Force -Path (Join-Path $BuildFolder "*") -Destination $appTarget

    foreach ($installerFile in @(
        "Install-BreaktimeRestaurant.cmd",
        "Install-BreaktimeRestaurant.ps1",
        "Uninstall-BreaktimeRestaurant.ps1",
        "README.txt"
    )) {
        Copy-Item -Force `
            -Path (Join-Path $PSScriptRoot "installer\$installerFile") `
            -Destination (Join-Path $tempPackageRoot $installerFile)
    }

    $zipPath = "$packageRoot.zip"
    if (Test-Path $zipPath) {
        Remove-Item -Force $zipPath
    }

    Copy-Item -Recurse -Force -Path $tempPackageRoot -Destination $packageRoot
    Copy-ZipFromSourceDirectory -SourceDirectory $tempPackageRoot -DestinationZipPath $zipPath

    return @{
        Folder = $packageRoot
        Zip = $zipPath
    }
}

function New-InnoInstaller {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CompilerPath,
        [Parameter(Mandatory = $true)]
        [string]$BuildFolder,
        [Parameter(Mandatory = $true)]
        [string]$ProjectDistPath,
        [Parameter(Mandatory = $true)]
        [string]$Timestamp,
        [Parameter(Mandatory = $true)]
        [string]$Version
    )

    $outputBaseFilename = "BreaktimeRestaurant-Setup-$Timestamp"
    $issPath = Join-Path $PSScriptRoot "installer\BreaktimeRestaurant.iss"
    $installerPath = Join-Path $ProjectDistPath "$outputBaseFilename.exe"

    & $CompilerPath `
        "/DMyAppSource=$BuildFolder" `
        "/DMyAppOutput=$ProjectDistPath" `
        "/DMyAppVersion=$Version" `
        "/DMyAppOutputBaseFilename=$outputBaseFilename" `
        $issPath | Out-Host

    return $installerPath
}

$pythonCmd = Get-PythonCommand
$releaseVersion = Get-Date -Format "yyyy.MM.dd.HHmm"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$projectDistPath = Join-Path $PSScriptRoot "dist"
$workPath = Join-Path $env:TEMP "BreaktimeRestaurant-pyinstaller-build"
$stagingDistPath = Join-Path $env:TEMP "BreaktimeRestaurant-pyinstaller-dist"
$iconPngPath = Join-Path $PSScriptRoot "app_icon.png"
$iconIcoPath = Join-Path $PSScriptRoot "app_icon.ico"
$buildInstaller = [bool]$Installer
$buildOneFile = [bool]$OneFile -and -not $buildInstaller

if ($buildInstaller -and $OneFile) {
    Write-Host "Installer releases use the onedir build as the source package. Ignoring -OneFile."
}

if (-not $SkipDependencyInstall) {
    & $pythonCmd -m pip install --disable-pip-version-check -r requirements.txt
}

if (Test-Path $iconPngPath) {
    & $pythonCmd -c "from pathlib import Path; from PIL import Image; source = Path(r'$iconPngPath'); target = Path(r'$iconIcoPath'); image = Image.open(source).convert('RGBA'); image.save(target, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])"
}

$pyInstallerArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--windowed",
    "--workpath", $workPath,
    "--distpath", $stagingDistPath,
    "--name", "BreaktimeRestaurant",
    "--icon", "app_icon.ico"
)

if ($buildOneFile) {
    $pyInstallerArgs += "--onefile"
} else {
    $pyInstallerArgs += "--onedir"
}

foreach ($dataFile in @(
    "app_icon.png",
    "background.jpg",
    "bg.png",
    "logo.png",
    "user.png",
    "lock.png",
    "phone.png",
    "calendar.png",
    "check.png",
    "breaktime_restaurant.db"
)) {
    if (Test-Path (Join-Path $PSScriptRoot $dataFile)) {
        $pyInstallerArgs += "--add-data"
        $pyInstallerArgs += "$dataFile;."
    }
}

$pyInstallerArgs += "main.py"

& $pythonCmd @pyInstallerArgs

New-Item -ItemType Directory -Force -Path $projectDistPath | Out-Null

Write-Host ""
if ($buildOneFile) {
    $stagedFile = Join-Path $stagingDistPath "BreaktimeRestaurant.exe"
    $finalFile = Join-Path $projectDistPath "BreaktimeRestaurant-$timestamp.exe"
    Copy-Item -Force $stagedFile $finalFile
    Write-Host "Build complete."
    Write-Host "Output file: $finalFile"
    return
}

$stagedFolder = Join-Path $stagingDistPath "BreaktimeRestaurant"
$finalFolder = Join-Path $projectDistPath "BreaktimeRestaurant-$timestamp"
$zipPath = "$finalFolder.zip"

Copy-Item -Recurse -Force $stagedFolder $finalFolder
Copy-ZipFromSourceDirectory -SourceDirectory $stagedFolder -DestinationZipPath $zipPath

Write-Host "Build complete."
Write-Host "Output folder: $finalFolder"
Write-Host "Zip file: $zipPath"

if (-not $buildInstaller) {
    return
}

$innoCompiler = Get-InnoSetupCompiler
if ($innoCompiler) {
    $installerPath = New-InnoInstaller `
        -CompilerPath $innoCompiler `
        -BuildFolder $stagedFolder `
        -ProjectDistPath $projectDistPath `
        -Timestamp $timestamp `
        -Version $releaseVersion

    Write-Host "Installer file: $installerPath"
    return
}

$scriptInstaller = New-ScriptInstallerPackage `
    -BuildFolder $stagedFolder `
    -ProjectDistPath $projectDistPath `
    -Timestamp $timestamp

Write-Host "Installer package folder: $($scriptInstaller.Folder)"
Write-Host "Installer package zip: $($scriptInstaller.Zip)"
Write-Host "Inno Setup was not found, so a script-based installer package was created instead."
