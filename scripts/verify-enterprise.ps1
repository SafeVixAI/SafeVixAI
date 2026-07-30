# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

<#
.SYNOPSIS
  Enterprise OSPO completion verification script for SafeVixAI.
  Checks all implemented gaps across backend, chatbot, frontend, and docs.
#>

$ErrorActionPreference = "Stop"
$exitCode = 0
$report = @()

function Check-Item {
    param($Name, $Condition)
    if (& $Condition) {
        $report += "  [PASS] $Name"
    } else {
        $report += "  [FAIL] $Name"
        $exitCode = 1
    }
}

Write-Host "=== SafeVixAI Enterprise OSPO Verification ===" -ForegroundColor Cyan
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"

# ════════════════════════════════════════════════════════════
# Phase 1: Chatbot Service Endpoints
# ════════════════════════════════════════════════════════════
Write-Host "-- Phase 1: Chatbot Service --" -ForegroundColor Yellow

Check-Item "Metrics endpoint module" { Test-Path "chatbot_service/core/metrics.py" }
Check-Item "Metrics test file" { Test-Path "chatbot_service/tests/test_metrics.py" }
Check-Item "Version endpoint file" { Test-Path "chatbot_service/api/version.py" }
Check-Item "Version endpoint registered" {
    $init = Get-Content "chatbot_service/api/__init__.py" -Raw
    $init -match "from api.version import router as version_router"
}
Check-Item "Version tests exist" { Test-Path "chatbot_service/tests/test_version.py" }
Check-Item "Speech v1 router exists" {
    $speech = Get-Content "chatbot_service/api/speech.py" -Raw
    $speech -match "router_v1"
}
Check-Item "Admin v1 router exists" {
    $admin = Get-Content "chatbot_service/api/admin.py" -Raw
    $admin -match "router_v1"
}
Check-Item "API versioning tests exist" { Test-Path "chatbot_service/tests/test_api_versioning.py" }
Check-Item "Admin v1 registered in __init__" {
    $init = Get-Content "chatbot_service/api/__init__.py" -Raw
    $init -match "admin_router_v1" -and $init -match "speech_router_v1"
}

# ════════════════════════════════════════════════════════════
# Phase 2: Backend Probes
# ════════════════════════════════════════════════════════════
Write-Host "`n-- Phase 2: Backend Probes --" -ForegroundColor Yellow

Check-Item "Probes module exists" { Test-Path "backend/api/v1/probes.py" }
Check-Item "Probes registered in __init__" {
    $init = Get-Content "backend/api/v1/__init__.py" -Raw
    $init -match "from api.v1.probes import router as probes_router"
}
Check-Item "Probes tests exist" { Test-Path "backend/tests/test_probes.py" }
Check-Item "Startup flag wired in main.py" {
    $main = Get-Content "backend/main.py" -Raw
    $main -match "from api.v1.probes import set_startup_complete"
}
Check-Item "readyz endpoint" {
    $probes = Get-Content "backend/api/v1/probes.py" -Raw
    $probes -match "@router.get\('/readyz'\)"
}
Check-Item "livez endpoint" {
    $probes = Get-Content "backend/api/v1/probes.py" -Raw
    $probes -match "@router.get\('/livez'\)"
}
Check-Item "startupz endpoint" {
    $probes = Get-Content "backend/api/v1/probes.py" -Raw
    $probes -match "@router.get\('/startupz'\)"
}

# ════════════════════════════════════════════════════════════
# Phase 3: Frontend Updates
# ════════════════════════════════════════════════════════════
Write-Host "`n-- Phase 3: Frontend Updates --" -ForegroundColor Yellow

Check-Item "PWA update hook exists" { Test-Path "frontend/hooks/useServiceWorkerUpdate.ts" }
Check-Item "PWA update hook tests exist" { Test-Path "frontend/hooks/__tests__/useServiceWorkerUpdate.test.ts" }
Check-Item "PWA update prompt component exists" { Test-Path "frontend/components/updates/PwaUpdatePrompt.tsx" }
Check-Item "PWA update prompt tests exist" { Test-Path "frontend/components/updates/__tests__/PwaUpdatePrompt.test.tsx" }
Check-Item "PWA prompt integrated in layout.tsx" {
    $layout = Get-Content "frontend/app/layout.tsx" -Raw
    $layout -match "PwaUpdatePrompt"
}
Check-Item "Release notes page exists" { Test-Path "frontend/app/release-notes/page.tsx" }
Check-Item "Release notes tests exist" { Test-Path "frontend/tests/release-notes.test.tsx" }
Check-Item "ReleaseNotesViewer component" { Test-Path "frontend/components/updates/ReleaseNotesViewer.tsx" }
Check-Item "ReleaseNotesModal component" { Test-Path "frontend/components/updates/ReleaseNotesModal.tsx" }
Check-Item "Release Notes link in UpdateBanner" {
    $banner = Get-Content "frontend/components/updates/UpdateBanner.tsx" -Raw
    $banner -match "Release Notes"
}
Check-Item "CLI update script" { Test-Path "frontend/scripts/update.mjs" }
Check-Item "CLI update script entry in package.json" {
    $pkg = Get-Content "frontend/package.json" -Raw
    $pkg -match '"update":'
}

# ════════════════════════════════════════════════════════════
# Phase 4: Documentation
# ════════════════════════════════════════════════════════════
Write-Host "`n-- Phase 4: Documentation --" -ForegroundColor Yellow

Check-Item "Tutorials index exists" { Test-Path "docs/tutorials/index.md" }
Check-Item "SOS tutorial exists" { Test-Path "docs/tutorials/sos-setup.md" }
Check-Item "Challan tutorial exists" { Test-Path "docs/tutorials/challan-integration.md" }
Check-Item "Chatbot tutorial exists" { Test-Path "docs/tutorials/chatbot-customization.md" }
Check-Item "SYSTEM_DESIGN.md exists" { Test-Path "docs/SYSTEM_DESIGN.md" }
Check-Item "DEVELOPER_GUIDE.md exists" { Test-Path "docs/DEVELOPER_GUIDE.md" }

Check-Item "mkdocs.yml Tutorials nav sub-menu (not flat)" {
    $mkdocs = Get-Content "mkdocs.yml" -Raw
    $mkdocs -match "Tutorials:" -and $mkdocs -match "SOS Setup:" -and $mkdocs -match "Challan Integration:" -and $mkdocs -match "Chatbot Customization:"
}
Check-Item "mkdocs.yml CLI Reference nav entry" {
    $mkdocs = Get-Content "mkdocs.yml" -Raw
    $mkdocs -match "CLI Reference:"
}
Check-Item "mkdocs.yml has System Design nav entry" {
    $mkdocs = Get-Content "mkdocs.yml" -Raw
    $mkdocs -match "System Design: SYSTEM_DESIGN.md"
}
Check-Item "mkdocs.yml has Developer Guide nav entry" {
    $mkdocs = Get-Content "mkdocs.yml" -Raw
    $mkdocs -match "Developer Guide: DEVELOPER_GUIDE.md"
}
Check-Item "mkdocs.yml has mike version selector" {
    $mkdocs = Get-Content "mkdocs.yml" -Raw
    $mkdocs -match "provider: mike"
}

# ════════════════════════════════════════════════════════════
# Phase 5: Templates & Scaffolding
# ════════════════════════════════════════════════════════════
Write-Host "`n-- Phase 5: Templates --" -ForegroundColor Yellow

Check-Item "cookiecutter config exists" { Test-Path "templates/project-scaffold/cookiecutter.json" }
Check-Item "README template exists" { Test-Path "templates/project-scaffold/{{cookiecutter.project_name}}/README.md" }
Check-Item "Makefile template exists" { Test-Path "templates/project-scaffold/{{cookiecutter.project_name}}/Makefile" }
Check-Item "docker-compose template exists" { Test-Path "templates/project-scaffold/{{cookiecutter.project_name}}/docker-compose.yml" }
Check-Item "backend init template exists" { Test-Path "templates/project-scaffold/{{cookiecutter.project_name}}/backend/__init__.py" }
Check-Item "frontend package template exists" { Test-Path "templates/project-scaffold/{{cookiecutter.project_name}}/frontend/package.json" }
Check-Item "tests init template exists" { Test-Path "templates/project-scaffold/{{cookiecutter.project_name}}/tests/__init__.py" }
Check-Item "docs index template exists" { Test-Path "templates/project-scaffold/{{cookiecutter.project_name}}/docs/index.md" }

# ════════════════════════════════════════════════════════════
# Summary
# ════════════════════════════════════════════════════════════
Write-Host "`n-- Results --" -ForegroundColor Cyan
$report | ForEach-Object { Write-Host $_ }
$passCount = ($report | Where-Object { $_ -match "\[PASS\]" }).Count
$failCount = ($report | Where-Object { $_ -match "\[FAIL\]" }).Count
Write-Host "`n$passCount passed, $failCount failed" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
if ($exitCode -ne 0) { exit $exitCode }
