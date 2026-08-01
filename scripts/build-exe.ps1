# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
<#
.SYNOPSIS
    Builds the standalone Windows .exe binary for SafeVixAI CLI & Update Manager.
.DESCRIPTION
    Uses PyInstaller to bundle scripts/safevixai_update.py into a single-file executable.
    Outputs to release-binaries/safevixai-cli-windows-x64.exe with SHA256 checksum.
#>

[CmdletBinding()]
param (
    [switch]$SkipDeps
)

$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " SafeVixAI Windows Executable Builder    " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

if (-not $SkipDeps) {
    Write-Host "[1/3] Checking and installing build dependencies..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    pip install pyinstaller httpx
}

Write-Host "[2/3] Compiling standalone executable via PyInstaller..." -ForegroundColor Yellow
pyinstaller --onefile --name safevixai-cli-windows-x64 scripts/safevixai_update.py

Write-Host "[3/3] Packaging binary and computing SHA256 checksum..." -ForegroundColor Yellow
if (-not (Test-Path -Path "release-binaries")) {
    New-Item -ItemType Directory -Path "release-binaries" | Out-Null
}

Copy-Item "dist/safevixai-cli-windows-x64.exe" "release-binaries/" -Force

$hash = (Get-FileHash "release-binaries/safevixai-cli-windows-x64.exe" -Algorithm SHA256).Hash
"$hash  safevixai-cli-windows-x64.exe" | Out-File -Encoding ascii "release-binaries/safevixai-cli-windows-x64.exe.sha256"

Write-Host ""
Write-Host "Build complete successfully!" -ForegroundColor Green
Write-Host "Executable: release-binaries/safevixai-cli-windows-x64.exe" -ForegroundColor Green
Write-Host "SHA256:     $hash" -ForegroundColor Green
