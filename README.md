# Split App

Quick start for local dev and a one-command setup script for new clones.

## Prereqs
- Node.js 20+
- Python 3.12+

## One-time setup
```bash
./scripts/setup.sh
```

## One-time setup (Windows PowerShell)
```powershell
.\scripts\setup.ps1
```

## Run in dev
```bash
npm run dev
```

Backend runs at `http://127.0.0.1:8000`, frontend at the Vite dev URL printed in the terminal.

## Optional: initialize a fresh local DB
```bash
./backend/.venv/bin/python backend/init_db.py
```

## Docker
```bash
docker build -f backend/Dockerfile -t split-app .
docker run --rm -p 8080:8080 split-app
```
