# Start backend for local E2E (mock GigaChat, no network).
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\..\backend"

$env:E2E_MOCK_GIGACHAT = "1"
$env:DATABASE_URL = "sqlite:///./data/e2e.db"
$env:FRONTEND_ORIGIN = "http://127.0.0.1:5173"

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
