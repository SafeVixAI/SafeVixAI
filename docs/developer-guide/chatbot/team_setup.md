# Chatbot Team — Setup & Workflow Guide

Welcome to the SafeVixAI Chatbot development team. To ensure a smooth collaboration and protect the stability of the `SafeVixAI` platform, please follow these standardized workflow rules.

## 1. Local Environment Setup
Before writing any code, prepare your local environment in the `chatbot_service/` folder.
- **Python**: Ensure you have Python 3.11+ installed.
- **Install Dependencies**:
  ```bash
  pip install -r requirements.txt
  ```
- **Environment Variables**:
  - Copy `.env.example` to `.env`
  - Add your API keys for the LLM providers (Groq, Gemini, etc.). **NEVER commit the `.env` file.**

## 2. GitHub Workflow (Branching)
**CRITICAL RULE**: Do not push directly to the `main` or `develop` branches.

### Step-by-Step Contribution:
1. **Pull the latest changes** from the upstream repository.
   ```bash
   git checkout develop
   git pull origin develop
   ```
2. **Create a feature branch** using the `chatbot/` prefix.
   ```bash
   git checkout -b chatbot/your-feature-name
   ```
3. **Commit your changes** with descriptive messages.
   ```bash
   git add .
   git commit -m "feat: add vectorstore rebuild endpoint"
   ```
4. **Push your branch** to GitHub (not `main`).
   - If it's the first time pushing this branch:
     ```bash
     git push -u origin chatbot/your-feature-name
     ```
   - For subsequent pushes:
     ```bash
     git push
     ```
5. **Create a Pull Request (PR)** on GitHub, targeting the `develop` branch.
6. **Request Review**: Assign a teammate to review your PR before merging.

## 3. Module Ownership
To avoid merge conflicts, ensure you are working on the module assigned to you.
- **Member A**: Providers (13 provider files), Memory (Redis conversation, 24h TTL), API endpoints.
- **Member B**: RAG (ChromaDB, LocalHashEmbeddingFunction, top_k=5), Agent (ChatEngine — 8 modules: graph.py, intent_detector.py, safety_checker.py, context_assembler.py, governance.py, state.py, __init__.py), 13 Tools.
- **Member C**: Frontend UI/Voice (Web Speech API, IndicSeamless), Multi-language (14 languages, Sarvam routing), Speech endpoints (`POST /speech/translate`, `GET /speech/status`).

## 4. Testing
Run the existing tests in the `/tests` folder before pushing to ensure you haven't introduced any regressions.
```bash
pytest tests/ -q
```
**pytest config**: `asyncio_mode = strict` — async tests **require** `@pytest.mark.asyncio` decorator.
**Current state**: 892/892 tests passing, 95% coverage.

## 5. Documentation
If you add a new feature or change an API, update the corresponding file in the `chatbot_docs/` folder to keep the documentation current.
