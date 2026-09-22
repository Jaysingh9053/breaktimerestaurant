# Breaktime Restaurant Deployment

This project is a PyQt6 desktop application. The repo now supports both portable releases and installer-style releases from the same PowerShell build script.

## Prerequisites

- Windows
- Python 3.11 or newer
- PowerShell

## Build Commands

Portable folder build:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

This creates:

- `dist\BreaktimeRestaurant-<timestamp>\`
- `dist\BreaktimeRestaurant-<timestamp>.zip`

Portable single-file build:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -OneFile
```

This creates:

- `dist\BreaktimeRestaurant-<timestamp>.exe`

Installer-oriented release:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Installer
```

This always builds the standard onedir release first, then:

- If Inno Setup 6 is installed, it creates `dist\BreaktimeRestaurant-Setup-<timestamp>.exe`
- If Inno Setup is not installed, it creates a self-contained installer package folder and zip:
  - `dist\BreaktimeRestaurant-Setup-<timestamp>\`
  - `dist\BreaktimeRestaurant-Setup-<timestamp>.zip`

The fallback package can be installed by opening it and running `Install-BreaktimeRestaurant.cmd`.

## Optional Flags

- `-SkipDependencyInstall`
  Skips `pip install -r requirements.txt` when the machine already has the required packages.

## First Run Behavior

- Static assets are loaded from the packaged bundle.
- The SQLite database is copied on first launch to `%LOCALAPPDATA%\BreaktimeRestaurant\breaktime_restaurant.db`.
- After that, the app keeps using the writable copy in `%LOCALAPPDATA%`, so user data is preserved across launches.

## Installer Behavior

- The fallback installer installs the app for the current Windows user under `%LOCALAPPDATA%\Programs\BreaktimeRestaurant`.
- It creates Start Menu and Desktop shortcuts.
- Uninstall removes the app binaries and shortcuts, but leaves `%LOCALAPPDATA%\BreaktimeRestaurant` in place so restaurant data is not deleted.

## Notes

- During local development, the app still uses the database file in the project folder.
- If you want a fresh packaged database, replace `breaktime_restaurant.db` before building.
- PyInstaller work files are staged in `%TEMP%`, which avoids cleanup failures in OneDrive-synced folders.
