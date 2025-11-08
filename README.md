# TIMEMACHINE AI – Backend

FastAPI service that stores TIMEMACHINE AI users and exposes health/user APIs while preparing a clean integration point for future LangChain workflows.

## Tech Stack
- FastAPI + Uvicorn
- SQLAlchemy ORM with SQLite by default (`app/data/app.db`)
- Pydantic v2 + `pydantic-settings` for configuration management
- Optional LangChain + OpenAI bindings (see `app/services/langchain.py`)

## Getting Started
1. **Install dependencies**
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure the environment**
   ```bash
   cp .env.example .env
   # edit .env as needed
   ```
   | Variable | Description |
   | --- | --- |
   | `PROJECT_NAME` | FastAPI title (default `TIMEMACHINE-AI API`) |
   | `API_PREFIX` | Root path for all routers (`/api`) |
   | `DATABASE_URL` | SQLAlchemy URL (ships with SQLite) |
   | `LANGCHAIN_MODEL` | Model identifier passed to LangChain |
   | `LANGCHAIN_API_KEY` | Required when calling LangChain/OpenAI |
   | `LANGCHAIN_TRACING` | Enable LangSmith tracing (`true` / `false`) |

3. **Run the server**
   ```bash
   uvicorn app.main:app --reload
   ```
   The liveness probe is available at `http://localhost:8000/api/health/live`.

## Project Layout
```
app/
├── api/                 # Routers, dependencies, health probe
├── core/                # Config and security helpers
├── db/                  # SQLAlchemy engine/session setup
├── models/              # ORM models (User)
├── repositories/        # Data-access layer (UserRepository)
├── schemas/             # Pydantic schemas / DTOs
└── services/            # LangChain orchestration helpers
```

## Useful Commands
```bash
# Run FastAPI with production settings
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Format imports / run lint (example)
python -m compileall app
```

## API Surface (current)
- `GET /api/health/live` – liveness
- `GET /api/health/ready` – readiness + LangChain info
- `POST /api/users` – create a user (email uniqueness enforced)
- `GET /api/users` – list users with pagination (`skip`, `limit`)
- `GET /api/users/{user_id}` – fetch single user

Extend routes via `app/api/routes` and encapsulate new data logic inside repositories/services to keep endpoints slim.
