# KNB AI System -- Dev Launcher (Windows PowerShell 5.1)
# Usage: .\start-dev.ps1
# Opens 3 separate terminals: AI Service (8000), Server (8080), Client (5173)

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host ""
Write-Host "=== KNB AI System -- Demarrage local ===" -ForegroundColor Cyan
Write-Host ""

# ── 1. AI Service (Python / FastAPI on port 8000) ─────────────────────────────
$aiDir  = Join-Path $root "ai-services"
$python = Join-Path $aiDir ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "[WARN] Virtualenv introuvable: $python" -ForegroundColor Yellow
    Write-Host "       Creez-le avec: python -m venv ai-services\.venv" -ForegroundColor Yellow
    Write-Host "       Puis: ai-services\.venv\Scripts\pip install -r ai-services\requirements.txt" -ForegroundColor Yellow
} else {
    Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command",
        "`$host.UI.RawUI.WindowTitle = 'KNB AI Service :8000'; " +
        "Set-Location '$aiDir'; " +
        "Write-Host '=== KNB AI Service (port 8000) ===' -ForegroundColor Cyan; " +
        "& '$python' -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    )
    Write-Host "[OK] AI Service   --> http://localhost:8000" -ForegroundColor Cyan
}

# ── 2. Node Server (Express / Socket.IO on port 8080) ─────────────────────────
$serverDir = Join-Path $root "server"

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "`$host.UI.RawUI.WindowTitle = 'KNB Server :3001'; " +
    "Set-Location '$serverDir'; " +
    "Write-Host '=== KNB Server (port 3001) ===' -ForegroundColor Green; " +
    "npx tsx src/index.ts"
)
Write-Host "[OK] Server        --> http://localhost:3001" -ForegroundColor Green

# ── 3. Vite Client (port 5173) ────────────────────────────────────────────────
$clientDir = Join-Path $root "client"

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "`$host.UI.RawUI.WindowTitle = 'KNB Client :5173'; " +
    "Set-Location '$clientDir'; " +
    "Write-Host '=== KNB Client (port 5173) ===' -ForegroundColor Yellow; " +
    "npx vite"
)
Write-Host "[OK] Client        --> http://localhost:5173" -ForegroundColor Yellow

Write-Host ""
Write-Host ""
Write-Host "3 fenetres ouvertes. Fermez-les ou Ctrl+C pour arreter chaque service." -ForegroundColor Gray
Write-Host ""
Write-Host "NOTE: Le port 8080 est pris par Apache/XAMPP sur cette machine." -ForegroundColor Yellow
Write-Host "      Le serveur KNB utilise le port 3001 a la place." -ForegroundColor Yellow
Write-Host ""
