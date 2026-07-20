# ECHO Full Stack Startup Script
# Usage:
#   .\start_echo.ps1          <- full stack (Docker + Ollama + Server)
#   .\start_echo.ps1 quick    <- server only (fastest, no Docker/Ollama)
#   .\start_echo.ps1 nollm    <- Docker + Server, skip Ollama

$mode = $args[0]

Set-Location "c:\Users\Aryan Raj\OneDrive\Desktop\Major\antitrust_sim"
Write-Host "ECHO Startup - $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
Write-Host "Working directory: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# QUICK MODE - just the server
if ($mode -eq "quick") {
    Write-Host "QUICK MODE: Starting API server only..." -ForegroundColor Yellow
    Write-Host "Open Chrome at: http://127.0.0.1:8000" -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop."
    Write-Host ""
    uvicorn api_server:app --port 8000 --reload
    exit
}

# STEP 1: Install Python deps
Write-Host "[1/4] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt -q
Write-Host "      Done." -ForegroundColor Green

# STEP 2: Start PostgreSQL via Docker
Write-Host ""
Write-Host "[2/4] Starting PostgreSQL (Docker)..." -ForegroundColor Yellow
$dockerOK = $false
docker info 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    docker-compose up -d db
    Start-Sleep -Seconds 5
    Write-Host "      PostgreSQL ready on port 5433." -ForegroundColor Green
    $dockerOK = $true
} else {
    Write-Host "      Docker not running - skipping DB. Start Docker Desktop first." -ForegroundColor DarkYellow
}

# STEP 3: Start Ollama + LLaMA 3
Write-Host ""
Write-Host "[3/4] Starting Ollama (LLaMA 3)..." -ForegroundColor Yellow

if ($mode -eq "nollm") {
    Write-Host "      Skipped (nollm mode)." -ForegroundColor DarkYellow
} else {
    $ollamaInstalled = $false
    ollama --version 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $ollamaInstalled = $true
    }

    if ($ollamaInstalled) {
        # Check if already running
        $running = $false
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:11434" -TimeoutSec 2 -ErrorAction Stop
            $running = $true
        } catch {
            $running = $false
        }

        if ($running) {
            Write-Host "      Ollama already running." -ForegroundColor Green
        } else {
            Write-Host "      Starting Ollama server..." -ForegroundColor Gray
            Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
            Start-Sleep -Seconds 3
            Write-Host "      Ollama server started." -ForegroundColor Green
        }

        # Pull llama3 if not present
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

# STEP 4: Start API server
Write-Host ""
Write-Host "[4/4] Starting ECHO API server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  ECHO is running at http://127.0.0.1:8000  " -ForegroundColor Green
Write-Host "  Open Chrome and navigate to that URL.     " -ForegroundColor Green
Write-Host "  Press Ctrl+C to stop the server.          " -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

uvicorn api_server:app --port 8000 --reload
