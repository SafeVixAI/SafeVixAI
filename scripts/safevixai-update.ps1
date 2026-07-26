<#
.SYNOPSIS
  SafeVixAI Update Manager — CLI for enterprise update operations.
.DESCRIPTION
  Check for updates, download, install, rollback, and view update history.
  Uses the backend API at $env:SVIX_BACKEND_URL (default: http://localhost:8000).
.EXAMPLE
  .\safevixai-update.ps1 check
  .\safevixai-update.ps1 install 1.1.0
  .\safevixai-update.ps1 history
#>

param(
  [Parameter(Position = 0)]
  [ValidateSet('check', 'download', 'install', 'rollback', 'history', 'channels', 'version', 'sync')]
  [string]$Command = 'check',

  [Parameter(Position = 1)]
  [string]$Version = '',

  [Parameter()]
  [string]$Channel = 'stable',

  [Parameter()]
  [string]$BackendUrl = '',

  [Parameter()]
  [switch]$Json
)

$ErrorActionPreference = 'Stop'

if (-not $BackendUrl) {
  $BackendUrl = if ($env:SVIX_BACKEND_URL) { $env:SVIX_BACKEND_URL } else { 'http://localhost:8000' }
}

$BaseUrl = "$BackendUrl/api/v1/updates"
$Headers = @{ 'Accept' = 'application/json' }
if ($env:SVIX_AUTH_TOKEN) {
  $Headers['Authorization'] = "Bearer $($env:SVIX_AUTH_TOKEN)"
}

function Invoke-Api {
  param([string]$Method, [string]$Uri, [object]$Body)
  $params = @{ Method = $Method; Uri = $Uri; Headers = $Headers; ContentType = 'application/json' }
  if ($Body) { $params['Body'] = ($Body | ConvertTo-Json) }
  try {
    $resp = Invoke-RestMethod @params
    return $resp
  } catch {
    $err = $_.Exception.Response
    $reader = New-Object System.IO.StreamReader($err.GetResponseStream())
    $body = $reader.ReadToEnd() | ConvertFrom-Json
    Write-Error "API Error: $($body.detail)"
    exit 1
  }
}

function Format-JsonOrText {
  param([object]$Data)
  if ($Json) {
    return ($Data | ConvertTo-Json -Depth 5)
  }
  return $Data
}

switch ($Command) {
  'version' {
    $result = Invoke-Api -Method Get -Uri "$BaseUrl/version"
    if ($Json) { return Format-JsonOrText $result }
    Write-Host "SafeVixAI Update Manager" -ForegroundColor Cyan
    Write-Host "Current version: v$($result.current_version)" -ForegroundColor Green
    if ($result.update_available) {
      Write-Host "Update available: v$($result.latest_version) (channel: $($result.channel))" -ForegroundColor Yellow
    } else {
      Write-Host "Status: Up to date" -ForegroundColor Green
    }
    Write-Host "Channel: $($result.channel)"
    Write-Host "Last checked: $($result.last_checked_at)"
    return
  }

  'check' {
    $result = Invoke-Api -Method Get -Uri "$BaseUrl/check?channel=$Channel"
    if ($Json) { return Format-JsonOrText $result }
    if ($result.update_available) {
      Write-Host "✓ Update available: v$($result.latest_version)" -ForegroundColor Yellow
      Write-Host "  Current: v$($result.current_version)"
      Write-Host "  Channel: $($result.channel)"
      if ($result.is_mandatory) { Write-Host "  MANDATORY UPDATE" -ForegroundColor Red }
      if ($result.is_security) { Write-Host "  Security release" -ForegroundColor Red }
    } else {
      Write-Host "✓ Up to date (v$($result.current_version))" -ForegroundColor Green
    }
    return
  }

  'download' {
    $v = if ($Version) { $Version } else {
      $check = Invoke-Api -Method Get -Uri "$BaseUrl/check?channel=$Channel"
      if (-not $check.update_available) { Write-Host "No update available"; return }
      $check.latest_version
    }
    Write-Host "Downloading v$v..." -ForegroundColor Yellow
    $result = Invoke-Api -Method Post -Uri "$BaseUrl/download/$v"
    if ($Json) { return Format-JsonOrText $result }
    Write-Host "✓ $($result.message)" -ForegroundColor Green
    return
  }

  'install' {
    $v = if ($Version) { $Version } else {
      $check = Invoke-Api -Method Get -Uri "$BaseUrl/check?channel=$Channel"
      if (-not $check.update_available) { Write-Host "No update available"; return }
      $check.latest_version
    }
    Write-Host "Installing v$v..." -ForegroundColor Yellow
    $result = Invoke-Api -Method Post -Uri "$BaseUrl/install/$v"
    if ($Json) { return Format-JsonOrText $result }
    Write-Host "✓ $($result.message)" -ForegroundColor Green
    return
  }

  'rollback' {
    $uri = "$BaseUrl/rollback"
    if ($Version) { $uri += "?version=$Version" }
    Write-Host "Rolling back..." -ForegroundColor Yellow
    $result = Invoke-Api -Method Post -Uri $uri
    if ($Json) { return Format-JsonOrText $result }
    Write-Host "✓ $($result.message)" -ForegroundColor Green
    return
  }

  'history' {
    $limit = if ($Version) { [int]$Version } else { 20 }
    $result = Invoke-Api -Method Get -Uri "$BaseUrl/history?limit=$limit&offset=0"
    if ($Json) { return Format-JsonOrText $result }
    Write-Host "Update History (last $limit):" -ForegroundColor Cyan
    foreach ($inst in $result.installations) {
      $color = switch ($inst.status) {
        'installed' { 'Green' }
        'failed' { 'Red' }
        'rolled_back' { 'Yellow' }
        default { 'Gray' }
      }
      $date = if ($inst.completed_at) { $inst.completed_at } else { $inst.created_at }
      Write-Host "  [$($inst.status)] v$($inst.release_version) → $date" -ForegroundColor $color
    }
    Write-Host "Total: $($result.total)"
    return
  }

  'channels' {
    $result = Invoke-Api -Method Get -Uri "$BaseUrl/channels"
    if ($Json) { return Format-JsonOrText $result }
    Write-Host "Available channels:" -ForegroundColor Cyan
    foreach ($ch in $result) {
      Write-Host "  $($ch.display_name) (v$($ch.latest_version), $($ch.release_count) releases)" -ForegroundColor $(if ($ch.channel -eq 'stable') { 'Green' } else { 'White' })
    }
    return
  }

  'sync' {
    Write-Host "Syncing releases from GitHub..." -ForegroundColor Yellow
    $result = Invoke-Api -Method Post -Uri "$BaseUrl/sync"
    if ($Json) { return Format-JsonOrText $result }
    Write-Host "✓ $($result.message)" -ForegroundColor Green
    return
  }
}
