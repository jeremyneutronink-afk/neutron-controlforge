$ErrorActionPreference = "Stop"

$root = (
    Resolve-Path (
        Join-Path $PSScriptRoot ".."
    )
).Path

Push-Location $root

try {
    Write-Host ""
    Write-Host "Neutron ControlForge release check" -ForegroundColor Cyan

    if (-not $env:VIRTUAL_ENV) {
        Write-Host "Activating .venv..." -ForegroundColor Yellow
        & ".\.venv\Scripts\Activate.ps1"
    }

    Write-Host "1/6 API import" -ForegroundColor Cyan
    python -c "from apps.api.app.main import app; print(app.title)"

    Write-Host "2/6 Migration status" -ForegroundColor Cyan
    alembic current

    Write-Host "3/6 Python compile" -ForegroundColor Cyan
    python -m compileall apps\api\app sdk\python\controlforge

    Write-Host "4/6 Python tests" -ForegroundColor Cyan
    python -m pytest tests -q

    Write-Host "5/6 Dashboard typecheck + lint" -ForegroundColor Cyan
    Push-Location "apps\dashboard"
    try {
        npm run typecheck
        npm run lint
    }
    finally {
        Pop-Location
    }

    Write-Host "6/6 Dashboard production build" -ForegroundColor Cyan
    Push-Location "apps\dashboard"
    try {
        npm run build
    }
    finally {
        Pop-Location
    }

    Write-Host ""
    Write-Host "Release checks passed." -ForegroundColor Green
}
finally {
    Pop-Location
}
