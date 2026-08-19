# ============================================================
# ECHO Full Stack Startup Script
# ============================================================
#
# MODES:
#   .\start_echo.ps1            <- full stack (Docker + Server + Embeddings/LLM checks)
#   .\start_echo.ps1 quick      <- server only, no Docker needed
#   .\start_echo.ps1 nollm      <- Docker + Server, skip LLM/embeddings check
#   .\start_echo.ps1 fullrun    <- run ALL simulations + generate figures + start server
#
# ONE-LINER FOR POWERSHELL / VS CODE TERMINAL:
#   cd "c:\Users\Aryan Raj\OneDrive\Desktop\Major\antitrust_sim"; .\start_echo.ps1 fullrun
# ============================================================

$mode = $args[0]

if ($PSScriptRoot) {
    Set-Location $PSScriptRoot
} else {
    Set-Location "c:\Users\Aryan Raj\OneDrive\Desktop\Major\antitrust_sim"
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ECHO: Autonomous Algorithmic Collusion Simulator          " -ForegroundColor Cyan
Write-Host "  Startup Time: $(Get-Date -Format 'HH:mm:ss')               " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Working directory: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# ── QUICK MODE: just the server ───────────────────────────
if ($mode -eq "quick") {
    Write-Host "QUICK MODE: Starting API server directly..." -ForegroundColor Yellow
    Write-Host "Open Chrome / Browser at: http://127.0.0.1:8000" -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop."
    Write-Host ""
    uvicorn api_server:app --port 8000 --reload
    exit
}

# ── STEP 1: Install / Verify Python deps ───────────────────
Write-Host "[1/5] Checking Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt -q
Write-Host "      Dependencies verified." -ForegroundColor Green

# ── STEP 2: Start PostgreSQL via Docker ───────────────────
Write-Host ""
Write-Host "[2/5] Checking PostgreSQL & n8n (Docker)..." -ForegroundColor Yellow
$dockerOK = $false
docker info 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "      Starting containers (db, n8n)..." -ForegroundColor Gray
    # Try 'docker compose' first, fallback to 'docker-compose'
    docker compose up -d db n8n 2>$null
    if ($LASTEXITCODE -ne 0) {
        docker-compose up -d db n8n
    }
    Start-Sleep -Seconds 4
    Write-Host "      PostgreSQL ready on port 5433 (pgvector enabled)." -ForegroundColor Green
    Write-Host "      n8n Workflow Engine at http://localhost:5678" -ForegroundColor Green
    Write-Host "      Running database schema checks..." -ForegroundColor Yellow
    python update_db.py
    $dockerOK = $true
} else {
    Write-Host "      Docker not running - skipping DB. (Run Docker Desktop if you want DB storage)" -ForegroundColor DarkYellow
}

# ── STEP 3: Check LLM & Embedding Providers ─────────────────
Write-Host ""
Write-Host "[3/5] Checking LLM & Embedding Providers..." -ForegroundColor Yellow

$hasGroq = $false
$envFiles = @(".env", "$HOME\.env", "$env:USERPROFILE\.env")
foreach ($ef in $envFiles) {
    if (Test-Path $ef) {
        $content = Get-Content $ef -Raw
        if ($content -match "GROQ_API_KEY") { $hasGroq = $true }
    }
}
if ($env:GROQ_API_KEY) { $hasGroq = $true }

if ($hasGroq) {
    Write-Host "      Groq API key found (LLM agents ready: Allam 2 / Llama 3)." -ForegroundColor Green
} else {
    Write-Host "      GROQ_API_KEY not found. Set it in .env to enable cloud LLM agents." -ForegroundColor DarkYellow
}

$ollamaOK = $false
if ($mode -eq "nollm") {
    Write-Host "      Local Ollama skipped (nollm mode)." -ForegroundColor DarkYellow
} else {
    ollama --version 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $running = $false
        try {
            Invoke-WebRequest -Uri "http://localhost:11434" -TimeoutSec 2 -ErrorAction Stop | Out-Null
            $running = $true
        } catch { $running = $false }

        if ($running) {
            Write-Host "      Ollama server is running on http://localhost:11434." -ForegroundColor Green
            $ollamaOK = $true
        } else {
            Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
            Start-Sleep -Seconds 2
            Write-Host "      Ollama server started." -ForegroundColor Green
            $ollamaOK = $true
        }

        # Check for nomic-embed-text for vector memory & NLP clustering
        $modelList = ollama list 2>$null
        if ($modelList -match "nomic-embed-text") {
            Write-Host "      nomic-embed-text embedding model ready." -ForegroundColor Green
        } else {
            Write-Host "      Pulling nomic-embed-text for vector embeddings..." -ForegroundColor Yellow
            ollama pull nomic-embed-text
        }
    } else {
        Write-Host "      Ollama not installed (optional for local embeddings / RAG memory)." -ForegroundColor Gray
    }
}

# ── FULL RUN MODE: simulations + figures + server ─────────
if ($mode -eq "fullrun") {
    Write-Host ""
    Write-Host "[4/5] Running simulations + generating publication figures..." -ForegroundColor Yellow
    Write-Host ""

    if ($dockerOK) {
        Write-Host "      [4a] Heuristic agents (100 rounds, scale-invariant)..." -ForegroundColor Gray
        python run_simulation.py --dataset gasoline --mode dummy --rounds 100 --db
        Write-Host "           Done." -ForegroundColor Green

        Write-Host "      [4b] Q-Learning RL agents (300 rounds)..." -ForegroundColor Gray
        python run_simulation.py --dataset gasoline --mode rl --rounds 300 --db
        Write-Host "           Done." -ForegroundColor Green

        Write-Host "      [4c] DQN Neural Network agents (200 rounds)..." -ForegroundColor Gray
        python run_simulation.py --dataset gasoline --mode dqn --rounds 200 --db
        Write-Host "           Done." -ForegroundColor Green

        if ($hasGroq) {
            Write-Host "      [4d] LLM agents (50 rounds - Groq Allam 2)..." -ForegroundColor Gray
            python run_simulation.py --dataset gasoline --mode llm --rounds 50 --db
            Write-Host "           Done." -ForegroundColor Green
        } else {
            Write-Host "      [4d] LLM agents - SKIPPED (GROQ_API_KEY not configured)" -ForegroundColor DarkYellow
        }

        # Generate Figures from real DB data
        Write-Host ""
        Write-Host "      [4e] Generating figures from database data..." -ForegroundColor Gray
        python -m analysis.plots --all
        Write-Host "           Done." -ForegroundColor Green
    } else {
        Write-Host "      DB simulations skipped (Docker not running)." -ForegroundColor DarkYellow
        Write-Host "      Generating Figures 1-7 from baseline calibrated parameters..." -ForegroundColor Gray
        python -m analysis.generate_all_figures
    }

    # Generate Figures 8-10 from real empirical data (BLS FRED + Amazon)
    Write-Host ""
    Write-Host "      [4f] Fetching real market validation data (Figs 8-10)..." -ForegroundColor Gray
    python -m analysis.real_data
    Write-Host "           Done." -ForegroundColor Green

    Write-Host ""
    Write-Host "      All figures saved to: analysis\figures\" -ForegroundColor Green
    Write-Host ""
}

# ── STEP 5: Start API server ──────────────────────────────
Write-Host ""
if ($mode -eq "fullrun") {
    Write-Host "[5/5] Starting ECHO API server & interactive dashboard..." -ForegroundColor Yellow
} else {
    Write-Host "[4/4] Starting ECHO API server & interactive dashboard..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  ECHO Dashboard  ->  http://127.0.0.1:8000                " -ForegroundColor Green
Write-Host "  API Docs        ->  http://127.0.0.1:8000/docs           " -ForegroundColor Green
if ($dockerOK) {
    Write-Host "  n8n Pipeline    ->  http://localhost:5678                 " -ForegroundColor Green
}
Write-Host "  Open your browser at http://127.0.0.1:8000              " -ForegroundColor Green
Write-Host "  Press Ctrl+C to stop.                                    " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

uvicorn api_server:app --port 8000 --reload
