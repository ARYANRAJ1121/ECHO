# ============================================================
# ECHO Full Stack Startup Script
# ============================================================
#
# MODES:
#   .\start_echo.ps1            <- full stack (Docker + Ollama + Server)
#   .\start_echo.ps1 quick      <- server only, no Docker/Ollama needed
#   .\start_echo.ps1 nollm      <- Docker + Server, skip Ollama
#   .\start_echo.ps1 fullrun    <- run ALL simulations + generate figures + start server
#
# ONE-LINER FOR VS CODE TERMINAL (paste this):
#   cd "c:\Users\Aryan Raj\OneDrive\Desktop\Major\antitrust_sim"; .\start_echo.ps1 fullrun
# ============================================================

$mode = $args[0]

Set-Location "c:\Users\Aryan Raj\OneDrive\Desktop\Major\antitrust_sim"
Write-Host ""
Write-Host "ECHO Startup  $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
Write-Host "Working directory: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# ── QUICK MODE: just the server ───────────────────────────
if ($mode -eq "quick") {
    Write-Host "QUICK MODE: Starting API server only..." -ForegroundColor Yellow
    Write-Host "Open Chrome at: http://127.0.0.1:8000" -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop."
    Write-Host ""
    uvicorn api_server:app --port 8000 --reload
    exit
}

# ── STEP 1: Install Python deps ───────────────────────────
Write-Host "[1/5] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt -q
Write-Host "      Done." -ForegroundColor Green

# ── STEP 2: Start PostgreSQL via Docker ───────────────────
Write-Host ""
Write-Host "[2/5] Starting PostgreSQL (Docker)..." -ForegroundColor Yellow
$dockerOK = $false
docker info 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    docker-compose up -d db n8n
    Start-Sleep -Seconds 6
    Write-Host "      PostgreSQL ready on port 5433." -ForegroundColor Green
    Write-Host "      n8n Workflow Engine at http://localhost:5678" -ForegroundColor Green
    Write-Host "      Running database schema migration..." -ForegroundColor Yellow
    python update_db.py
    $dockerOK = $true
} else {
    Write-Host "      Docker not running - skipping DB. Start Docker Desktop first." -ForegroundColor DarkYellow
}

# ── STEP 3: Start Ollama + LLaMA 3 ───────────────────────
Write-Host ""
Write-Host "[3/5] Starting Ollama (LLaMA 3)..." -ForegroundColor Yellow

$ollamaOK = $false
if ($mode -eq "nollm") {
    Write-Host "      Skipped (nollm mode)." -ForegroundColor DarkYellow
} else {
    ollama --version 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $ollamaOK = $true
        $running = $false
        try {
            Invoke-WebRequest -Uri "http://localhost:11434" -TimeoutSec 2 -ErrorAction Stop | Out-Null
            $running = $true
        } catch { $running = $false }

        if ($running) {
            Write-Host "      Ollama already running." -ForegroundColor Green
        } else {
            Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
            Start-Sleep -Seconds 3
            Write-Host "      Ollama server started." -ForegroundColor Green
        }

        $modelList = ollama list 2>$null
        if ($modelList -match "llama3") {
            Write-Host "      llama3 model ready." -ForegroundColor Green
        } else {
            Write-Host "      Downloading llama3 (~4.7 GB, first time only)..." -ForegroundColor Yellow
            ollama pull llama3
            Write-Host "      llama3 downloaded." -ForegroundColor Green
        }
    } else {
        Write-Host "      Ollama not installed - LLM mode unavailable." -ForegroundColor DarkYellow
        Write-Host "      Install from: https://ollama.com" -ForegroundColor Gray
    }
}

# ── FULL RUN MODE: simulations + figures + server ─────────
if ($mode -eq "fullrun") {
    Write-Host ""
    Write-Host "[4/5] Running ALL simulations + generating figures..." -ForegroundColor Yellow
    Write-Host "      This will take ~10-15 minutes. Go get a coffee." -ForegroundColor Gray
    Write-Host ""

    if ($dockerOK) {
        # Run all 4 agent modes on the baseline 'gasoline' dataset and save to DB
        # To test all datasets, wrap this block in: foreach ($ds in "gasoline","amazon","airlines","crypto","rideshare") { ... }
        Write-Host "      [4a] Heuristic agents (100 rounds)..." -ForegroundColor Gray
        python run_simulation.py --dataset gasoline --mode dummy --rounds 100 --db
        Write-Host "           Done." -ForegroundColor Green

        Write-Host "      [4b] Q-Learning RL agents (300 rounds)..." -ForegroundColor Gray
        python run_simulation.py --dataset gasoline --mode rl --rounds 300 --db
        Write-Host "           Done." -ForegroundColor Green

        Write-Host "      [4c] DQN agents (200 rounds)..." -ForegroundColor Gray
        python run_simulation.py --dataset gasoline --mode dqn --rounds 200 --db
        Write-Host "           Done." -ForegroundColor Green

        if ($ollamaOK) {
            Write-Host "      [4d] LLM agents (50 rounds - Llama 3)..." -ForegroundColor Gray
            python run_simulation.py --dataset gasoline --mode llm --rounds 50 --db
            Write-Host "           Done." -ForegroundColor Green
        } else {
            Write-Host "      [4d] LLM agents - SKIPPED (Ollama not available)" -ForegroundColor DarkYellow
        }

        # Generate Figures 1-7 from real DB data
        Write-Host ""
        Write-Host "      [4e] Generating Figures 1-7 from real simulation data..." -ForegroundColor Gray
        python -m analysis.plots --all
        Write-Host "           Done." -ForegroundColor Green
    } else {
        Write-Host "      DB simulations SKIPPED (Docker not running)." -ForegroundColor DarkYellow
        Write-Host "      Generating Figures 1-7 from synthetic data instead..." -ForegroundColor Gray
        python -m analysis.generate_all_figures
    }

    # Generate Figures 8-10 from real empirical data (FRED + Amazon)
    Write-Host ""
    Write-Host "      [4f] Fetching real gasoline + Amazon data (Figs 8-10)..." -ForegroundColor Gray
    python -m analysis.real_data
    Write-Host "           Done." -ForegroundColor Green

    Write-Host ""
    Write-Host "      All figures saved to: analysis\figures\" -ForegroundColor Green
    Write-Host ""
}

# ── STEP 5: Start API server ──────────────────────────────
Write-Host ""
if ($mode -eq "fullrun") {
    Write-Host "[5/5] Starting ECHO API server..." -ForegroundColor Yellow
} else {
    Write-Host "[4/4] Starting ECHO API server..." -ForegroundColor Yellow
}
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  ECHO Dashboard  ->  http://127.0.0.1:8000                " -ForegroundColor Green
Write-Host "  n8n Pipeline    ->  http://localhost:5678                 " -ForegroundColor Green
Write-Host "  Open Chrome and navigate to http://127.0.0.1:8000        " -ForegroundColor Green
Write-Host "  Press Ctrl+C to stop.                                    " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

uvicorn api_server:app --port 8000 --reload

# ── HOW TO RUN ────────────────────────────────────────────
# Full stack (Docker + Ollama + Server):
#   .\start_echo.ps1
#
# FULL RUN - simulations + real figures + server (use before demo/viva):
#   .\start_echo.ps1 fullrun
#
# Server only (fastest, no Docker/Ollama):
#   .\start_echo.ps1 quick
#
# Docker + Server, skip Ollama:
#   .\start_echo.ps1 nollm
# ─────────────────────────────────────────────────────────