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

```
group-cwk
├─ .dockerignore
├─ backend
│  ├─ crud
│  │  ├─ category.py
│  │  ├─ expenses.py
│  │  ├─ groups.py
│  │  ├─ invites.py
│  │  ├─ settlements.py
│  │  └─ users.py
│  ├─ db.py
│  ├─ Dockerfile
│  ├─ email.py
│  ├─ init_db.py
│  ├─ main.py
│  ├─ models
│  │  ├─ group.py
│  │  └─ user.py
│  └─ requirements.txt
├─ cloudbuild.yaml
├─ dev.db
├─ frontend
│  ├─ index.html
│  ├─ package-lock.json
│  ├─ package.json
│  ├─ public
│  │  └─ vite.svg
│  ├─ README.md
│  ├─ src
│  │  ├─ App.vue
│  │  ├─ assets
│  │  │  └─ vue.svg
│  │  ├─ components
│  │  │  └─ HelloWorld.vue
│  │  ├─ composables
│  │  │  ├─ useAuth.js
│  │  │  ├─ useCategories.js
│  │  │  ├─ useExpenses.js
│  │  │  ├─ useGroups.js
│  │  │  └─ useInvites.js
│  │  ├─ main.js
│  │  ├─ router
│  │  │  └─ index.js
│  │  ├─ services
│  │  │  └─ notifications.js
│  │  ├─ style.css
│  │  └─ views
│  │     ├─ About.vue
│  │     ├─ GroupDetails.vue
│  │     ├─ Groups.vue
│  │     ├─ GroupStats.vue
│  │     ├─ Home.vue
│  │     ├─ Login.vue
│  │     ├─ Register.vue
│  │     └─ Settings.vue
│  └─ vite.config.js
├─ package-lock.json
├─ package.json
├─ README.md
└─ scripts
   ├─ setup.ps1
   └─ setup.sh

```