# AI Employee - Full Workflow Startup (PowerShell)
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AI Employee - Full Workflow Startup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location (Join-Path $PSScriptRoot "..")

# Activate virtual environment
& ".\venv-win\Scripts\Activate.ps1"

# Start the workflow
Write-Host "Starting all watchers..." -ForegroundColor Green
python src\workflow\start_workflow.py @args
