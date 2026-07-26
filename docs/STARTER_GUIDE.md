# Starter Guide

> **For absolute beginners.**  
> **Last updated:** 2026-07-26

---

## What You Need to Know

SafeVixAI is a web app with three parts (called "services"):

| Service | What It Does | Language You'll Write In |
|---------|-------------|--------------------------|
| **Backend** | Handles data, emergency lookups, challan calculations | Python |
| **Chatbot** | Powers the AI assistant | Python |
| **Frontend** | What you see and click in the browser | TypeScript (similar to JavaScript) |

**Prerequisites:**
- Basic programming knowledge (any language)
- Familiarity with the command line (terminal)
- Git basics (clone, commit, push)
- **No prior knowledge of road safety needed**

---

## Setting Up Your Development Environment

### 1. Install Required Software

| Software | Why You Need It | Download |
|----------|----------------|----------|
| Git | Version control | [git-scm.com](https://git-scm.com) |
| Python 3.11+ | Run backend and chatbot | [python.org](https://python.org) |
| Node.js 20+ | Run frontend | [nodejs.org](https://nodejs.org) |
| VS Code | Code editor (recommended) | [code.visualstudio.com](https://code.visualstudio.com) |
| Docker (optional) | Run everything together | [docker.com](https://docker.com) |

### 2. Clone the Repository
Open your terminal (Command Prompt on Windows, Terminal on Mac/Linux):
```bash
git clone https://github.com/SafeVixAI/SafeVixAI.git
cd SafeVixAI
```

This downloads all the code to your computer.

### 3. Set Up the Backend

```bash
cd backend

# Create a virtual environment (isolates Python packages for this project)
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy the example environment file
cp .env.example .env
```

### 4. Set Up the Chatbot Service

```bash
cd ../chatbot_service

# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### 5. Set Up the Frontend

```bash
cd ../frontend

# Install JavaScript dependencies
npm ci

# Copy environment file
cp .env.local.example .env.local
```

### 6. Start Everything

Open **three separate terminal windows**:

**Terminal 1 — Backend:**
```bash
cd backend
.venv\Scripts\activate  # or source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Chatbot:**
```bash
cd chatbot_service
.venv\Scripts\activate  # or source .venv/bin/activate
uvicorn main:app --reload --port 8010
```

**Terminal 3 — Frontend:**
```bash
cd frontend
npm run dev
```

Open http://localhost:3000 in your browser. You should see the SafeVixAI app.

---

## Making Your First Change

### 1. Find Something to Work On
Look for issues labeled `good first issue` in the [GitHub Issues](https://github.com/SafeVixAI/SafeVixAI/issues). These are beginner-friendly tasks.

### 2. Create a Branch
```bash
git checkout -b my-first-contribution
```

### 3. Make a Change
Let's say you want to fix a typo in a comment.

Open `frontend/components/SosButton.tsx` and find:
```typescript
// Actiavte SOS when button is held
```

Change it to:
```typescript
// Activate SOS when button is held
```

### 4. Commit and Push
```bash
git add .
git commit -m "fix: correct typo in SosButton comment"
git push origin my-first-contribution
```

### 5. Create a Pull Request
1. Go to https://github.com/SafeVixAI/SafeVixAI
2. Click "Compare & pull request"
3. Write a short description of your change
4. Click "Create pull request"
5. Wait for a maintainer to review it

Congratulations — you've made your first contribution! 🎉

---

## Understanding the Codebase

### Simple File Map

```
SafeVixAI/
├── backend/         # Python code for the server
│   ├── api/         # API endpoints (what URLs respond to)
│   ├── core/        # Shared utilities (config, database)
│   ├── services/    # Business logic (challan, emergency, etc.)
│   └── tests/       # Tests for the backend
├── chatbot_service/ # Python code for the AI chatbot
│   ├── agent/       # The chatbot brain
│   ├── providers/   # AI model connections (Groq, Gemini, etc.)
│   ├── tools/       # Things the chatbot can do
│   └── rag/         # Document search
├── frontend/        # TypeScript code for the browser app
│   ├── app/         # Pages (URLs users visit)
│   ├── components/  # Reusable UI pieces
│   └── lib/         # Shared utilities
└── docs/            # Documentation
```

### Quick Tips

- **Backend endpoints** are in `backend/api/v1/` — each file handles a group of related URLs
- **Frontend pages** are in `frontend/app/` — each folder is a URL path
- **Reusable components** are in `frontend/components/` — buttons, cards, maps, etc.
- **Chatbot tools** are in `chatbot_service/tools/` — SOS, challan, weather, etc.

---

## Running Tests

```bash
# Backend tests
cd backend
.venv\Scripts\activate
pytest tests/ -v

# Frontend tests (in a different terminal)
cd frontend
npm test

# Chatbot tests
cd chatbot_service
.venv\Scripts\activate
pytest tests/ -v
```

---

## Getting Help

### If Something Doesn't Work

1. **Check common issues**: See [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)
2. **Search existing issues**: https://github.com/SafeVixAI/SafeVixAI/issues
3. **Ask a question**: [GitHub Discussions](https://github.com/SafeVixAI/SafeVixAI/discussions)

### Need a Mentor?

Comment on a `good first issue` saying "I'd like to work on this — could I get a mentor?" A maintainer will help you through your first PR.

---

## What's Next?

- Read [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed contribution guidelines
- Read [STYLE_GUIDE.md](../STYLE_GUIDE.md) for coding conventions
- Explore the [Documentation Site](https://safevixai.github.io/SafeVixAI/) for complete docs
- Check [ROADMAP.md](../ROADMAP.md) for planned features
- Look at [ADOPTERS.md](../ADOPTERS.md) to see who's using SafeVixAI
