# ============================================================
# ECHO — Full Stack Startup Script
# ============================================================
# Starts: PostgreSQL (Docker) + Ollama (LLaMA 3) + API Server
#
# HOW TO USE:
#   Open VS Code terminal (Ctrl+`) and run:
#   .\start_echo.ps1
#
# MODES:
#   .\start_echo.ps1            → full stack (Docker + Ollama + Server)
#   .\start_echo.ps1 -Quick     → server only, no Docker/Ollama needed
#   .\start_echo.ps1 -NoLLM     → Docker + Server, skip Ollama
# ============================================================

param(
    [switch]$Quick,   # Skip Docker and Ollama, just run the API server
    [switch]$NoLLM    # Skip Ollama (no LLM mode), but still start Docker DB
)

$projectRoot = "c:\Users\Aryan Raj\OneDrive\Desktop\Major\antitrust_sim"
Set-Location $projectRoot

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║    ECHO — Full Stack Startup                 ║" -ForegroundColor Cyan
Write-Host "║    Antitrust Simulation Platform             ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── QUICK MODE: just the API server ──────────────────────
if ($Quick) {
    Write-Host "⚡ QUICK MODE — Starting API server only" -ForegroundColor Yellow
    Write-Host "   (Heuristic + RL + DQN modes available. No LLM, no DB logging)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Opening dashboard at http://127.0.0.1:8000 ..." -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
    Write-Host ""
    uvicorn api_server:app --port 8000 --reload
    exit 0
}

# ── STEP 1: Check prerequisites ───────────────────────────
Write-Host "[ 1/5 ] Checking prerequisites..." -ForegroundColor Yellow

# Python
python --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Python not found. Install Python 3.11 from python.org" -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ Python OK" -ForegroundColor Green

# Docker
docker --version 2>$null
$dockerOK = ($LASTEXITCODE -eq 0)
if ($dockerOK) {
    Write-Host "  ✓ Docker OK" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Docker not found — DB logging will be disabled" -ForegroundColor Yellow
    Write-Host "    Install from https://docker.com/products/docker-desktop" -ForegroundColor Gray
}

# Ollama
ollama --version 2>$null
$ollamaOK = ($LASTEXITCODE -eq 0)
if ($ollamaOK) {
    Write-Host "  ✓ Ollama OK" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Ollama not found — LLM mode will be disabled" -ForegroundColor Yellow
    Write-Host "    Install from https://ollama.com" -ForegroundColor Gray
}

# ── STEP 2: Install Python dependencies ───────────────────
Write-Host ""
Write-Host "[ 2/5 ] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt -q
Write-Host "  ✓ Dependencies installed" -ForegroundColor Green

# ── STEP 3: Start PostgreSQL via Docker ───────────────────
Write-Host ""
Write-Host "[ 3/5 ] Starting PostgreSQL database..." -ForegroundColor Yellow

if ($dockerOK) {
    # Check if Docker Desktop is actually running
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ⚠ Docker is installed but not running." -ForegroundColor Yellow
        Write-Host "    Please start Docker Desktop, then run this script again." -ForegroundColor Gray
        Write-Host "    Continuing without database (no DB logging)..." -ForegroundColor Gray
    } else {
        # Start the DB container
        docker-compose up -d db 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ PostgreSQL container started (port 5433)" -ForegroundColor Green
            Write-Host "    Connection: postgresql://echo_user:echo_pass_2026@localhost:5433/echo" -ForegroundColor Gray
            # Wait for DB to be ready
            Write-Host "  ⏳ Waiting for DB to be ready..." -ForegroundColor Gray
            Start-Sleep -Seconds 5
        } else {
            Write-Host "  ⚠ docker-compose failed — continuing without DB" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  ⚠ Skipped (Docker not installed)" -ForegroundColor Gray
}

# ── STEP 4: Start Ollama + pull LLaMA 3 ──────────────────
Write-Host ""
Write-Host "[ 4/5 ] Starting Ollama (LLaMA 3 model)..." -ForegroundColor Yellow

if ($ollamaOK -and -not $NoLLM) {
    # Check if Ollama is already running
    $ollamaRunning = $false
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:11434" -TimeoutSec 2 -ErrorAction SilentlyContinue
        $ollamaRunning = ($resp.StatusCode -eq 200)
    } catch {}

    if ($ollamaRunning) {
        Write-Host "  ✓ Ollama already running on port 11434" -ForegroundColor Green
    } else {
        Write-Host "  Starting Ollama server..." -ForegroundColor Gray
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 3
        Write-Host "  ✓ Ollama server started" -ForegroundColor Green
    }

    # Check if llama3 model is downloaded
    $models = ollama list 2>$null
    if ($models -match "llama3") {
        Write-Host "  ✓ llama3 model ready" -ForegroundColor Green
    } else {
        Write-Host "  📥 Downloading llama3 model (~4.7 GB, first time only)..." -ForegroundColor Yellow
        Write-Host "     This will take a few minutes. Please wait..." -ForegroundColor Gray
        ollama pull llama3
        Write-Host "  ✓ llama3 downloaded and ready" -ForegroundColor Green
    }
} elseif ($NoLLM) {
    Write-Host "  ⚠ Skipped (--NoLLM flag set)" -ForegroundColor Gray
} else {
    Write-Host "  ⚠ Skipped (Ollama not installed)" -ForegroundColor Gray
}

# ── STEP 5: Start the ECHO API Server ─────────────────────
Write-Host ""
Write-Host "[ 5/5 ] Starting ECHO API server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✓ ECHO is running at http://127.0.0.1:8000  ║" -ForegroundColor Green
Write-Host "║                                              ║" -ForegroundColor Green

if ($ollamaOK -and -not $NoLLM) {
    Write-Host "║  Modes available:                            ║" -ForegroundColor Green
    Write-Host "║    ✓ Heuristic  ✓ RL  ✓ DQN  ✓ LLM (Llama3) ║" -ForegroundColor Green
} else {
    Write-Host "║  Modes available:                            ║" -ForegroundColor Green
    Write-Host "║    ✓ Heuristic  ✓ RL  ✓ DQN  (no LLM)       ║" -ForegroundColor Green
}

Write-Host "║                                              ║" -ForegroundColor Green
Write-Host "║  Open Chrome and go to:                     ║" -ForegroundColor Green
Write-Host "║  → http://127.0.0.1:8000                    ║" -ForegroundColor Green
Write-Host "║                                              ║" -ForegroundColor Green
Write-Host "║  Press Ctrl+C to stop the server.           ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

uvicorn api_server:app --port 8000 --reload
