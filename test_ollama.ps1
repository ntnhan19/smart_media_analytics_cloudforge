# Simple test script for Ollama Vision Models
# Run this from project root

Write-Host "Activating virtual environment..." -ForegroundColor Cyan
.\.venv\Scripts\Activate.ps1

Write-Host "Running Ollama Vision Models test..." -ForegroundColor Cyan
python test_ollama_simple.py

Write-Host "`nTest completed. Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
