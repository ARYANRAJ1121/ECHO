# ============================================================
# ECHO — Complete Project Startup Script
# Run this from: c:\Users\Aryan Raj\OneDrive\Desktop\Major\antitrust_sim
# 
# HOW TO USE:
#   1. Open VS Code terminal (Ctrl+`)
#   2. Paste this entire block and press Enter
# ============================================================

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   ECHO — Antitrust Simulation Startup    ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Navigate to project root ──
$projectRoot = "c:\Users\Aryan Raj\OneDrive\Desktop\Major\antitrust_sim"
Set-Location $projectRoot
Write-Host "✓ Working directory: $projectRoot" -ForegroundColor Green

# ── Check Python ──
Write-Host ""
Write-Host "Checking Python..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Python not found. Install Python 3.11 first." -ForegroundColor Red
    exit 1
}

# ── Install dependencies ──
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt -q
Write-Host "✓ Dependencies OK" -ForegroundColor Green

# ── Run real-world data validation (gasoline + amazon) ──
Write-Host ""
Write-Host "Running real-world data validation (FRED + Amazon)..." -ForegroundColor Yellow
python -m analysis.real_data
Write-Host "✓ Validation data computed → analysis/data/validation_report.json" -ForegroundColor Green

# ── Run a quick DQN simulation (100 rounds) ──
Write-Host ""
Write-Host "Running DQN simulation (100 rounds)..." -ForegroundColor Yellow
python run_simulation.py --mode dqn --rounds 100
Write-Host "✓ Simulation complete" -ForegroundColor Green

# ── Start API server in background ──
Write-Host ""
Write-Host "Starting ECHO dashboard server on http://127.0.0.1:8000 ..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the server when done." -ForegroundColor Gray
Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Open Chrome → http://127.0.0.1:8000   ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

uvicorn api_server:app --port 8000
