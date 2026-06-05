# KNB AI System -- Script de deploiement (Windows PowerShell 5.1)
# Deploie le client sur Vercel, le serveur sur Vercel, l'AI service sur Render
# Usage: .\deploy.ps1

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host ""
Write-Host "=== KNB AI System -- Deploiement ===" -ForegroundColor Cyan
Write-Host ""

# ── Verification des outils ────────────────────────────────────────────────────
function Require-Tool($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Host "[MANQUANT] $name n'est pas installe." -ForegroundColor Red
        return $false
    }
    return $true
}

$hasVercel = Require-Tool "vercel"
$hasGit    = Require-Tool "git"

if (-not $hasGit) {
    Write-Host "Git est requis. Installez-le depuis https://git-scm.com" -ForegroundColor Red
    exit 1
}

# ── Installer Vercel CLI si absent ────────────────────────────────────────────
if (-not $hasVercel) {
    Write-Host "[...] Installation de Vercel CLI..." -ForegroundColor Yellow
    npm install -g vercel
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERREUR] Impossible d'installer Vercel CLI" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Vercel CLI installe" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== ETAPE 1 : Build du client ===" -ForegroundColor Cyan
Set-Location (Join-Path $root "client")
npm install
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERREUR] Build client echoue" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Client build reussi" -ForegroundColor Green

Write-Host ""
Write-Host "=== ETAPE 2 : Deploiement du client sur Vercel ===" -ForegroundColor Cyan
Write-Host "Variables a configurer dans Vercel Dashboard:" -ForegroundColor Yellow
Write-Host "  VITE_FIREBASE_API_KEY       = AIzaSyAU7JO7kEchFaLnW4TfPJQz6Z7RtRlObVE" -ForegroundColor White
Write-Host "  VITE_FIREBASE_AUTH_DOMAIN   = knb-ai-system.firebaseapp.com" -ForegroundColor White
Write-Host "  VITE_FIREBASE_PROJECT_ID    = knb-ai-system" -ForegroundColor White
Write-Host "  VITE_API_URL                = (URL de votre serveur deploye)" -ForegroundColor White
Write-Host "  VITE_WS_URL                 = (URL de votre serveur deploye)" -ForegroundColor White
Write-Host ""
vercel --cwd (Join-Path $root "client") --prod
Write-Host "[OK] Client deploye sur Vercel" -ForegroundColor Green

Write-Host ""
Write-Host "=== ETAPE 3 : Deploiement du serveur sur Vercel ===" -ForegroundColor Cyan
Write-Host "Variables a configurer dans Vercel Dashboard (serveur):" -ForegroundColor Yellow
Write-Host "  FIREBASE_PROJECT_ID    = knb-ai-system" -ForegroundColor White
Write-Host "  FIREBASE_CLIENT_EMAIL  = firebase-adminsdk-fbsvc@knb-ai-system.iam.gserviceaccount.com" -ForegroundColor White
Write-Host "  FIREBASE_PRIVATE_KEY   = (contenu du champ private_key du fichier JSON)" -ForegroundColor White
Write-Host "  AI_SERVICE_PUBLIC_URL  = (URL de votre AI service sur Render)" -ForegroundColor White
Write-Host "  CORS_ORIGINS           = (URL de votre client Vercel)" -ForegroundColor White
Write-Host ""
vercel --cwd (Join-Path $root "server") --prod

Write-Host ""
Write-Host "=== ETAPE 4 : AI Service (Render) ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "L'AI service Python ne peut pas tourner sur Vercel (trop lourd)." -ForegroundColor Yellow
Write-Host "Deploiement GRATUIT sur Render.com :" -ForegroundColor White
Write-Host ""
Write-Host "  1. Allez sur https://dashboard.render.com/select-repo" -ForegroundColor White
Write-Host "  2. Choisissez votre repo GitHub" -ForegroundColor White
Write-Host "  3. Render detectera render.yaml automatiquement" -ForegroundColor White
Write-Host "  4. Ajoutez les variables d'environnement:" -ForegroundColor White
Write-Host "     GROQ_API_KEY       = gsk_qxpIiM..." -ForegroundColor Gray
Write-Host "     GEMINI_API_KEY     = (depuis aistudio.google.com)" -ForegroundColor Gray
Write-Host "     FIREBASE_CLIENT_EMAIL  = firebase-adminsdk-fbsvc@knb-ai-system.iam.gserviceaccount.com" -ForegroundColor Gray
Write-Host "     FIREBASE_PRIVATE_KEY   = (contenu du champ private_key du fichier JSON)" -ForegroundColor Gray
Write-Host ""

Write-Host "=== DEPLOIEMENT TERMINE ===" -ForegroundColor Green
Write-Host ""
Write-Host "Architecture de production:" -ForegroundColor Cyan
Write-Host "  Client  -> Vercel (gratuit, CDN mondial)" -ForegroundColor White
Write-Host "  Serveur -> Vercel Serverless (gratuit, 100GB-heures/mois)" -ForegroundColor White
Write-Host "  AI Service -> Render Free (gratuit, redemarrage apres 15 min inactivite)" -ForegroundColor White
Write-Host ""
Write-Host "LLMs gratuits configures (dans l'ordre de priorite):" -ForegroundColor Cyan
Write-Host "  1. Groq     -> llama-3.3-70b-versatile (14 400 req/jour)" -ForegroundColor White
Write-Host "  2. Gemini   -> gemini-2.0-flash-exp    (1 500 req/jour)" -ForegroundColor White
Write-Host "  3. Mistral  -> mistral-small-latest    (tier gratuit)" -ForegroundColor White
Write-Host "  4. OpenRouter -> mistral-7b:free       (modeles communautaires)" -ForegroundColor White
Write-Host ""
