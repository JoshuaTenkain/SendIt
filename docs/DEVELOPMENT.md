# SEND-IT Development Guide

## Local Development Setup

This guide covers setting up the SEND-IT platform for local development without Docker.

---

## Prerequisites

### Required Software

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **PostgreSQL 15+** - [Download](https://www.postgresql.org/download/)
- **Git** - [Download](https://git-scm.com/downloads/)

### Verify Installation

```bash
python3 --version  # Should be 3.11 or higher
node --version     # Should be 18 or higher
psql --version     # Should be 15 or higher
git --version
```

---

## Backend Setup (Python/FastAPI)

### 1. Navigate to Backend Directory

```bash
cd backend
```

### 2. Create Virtual Environment

**Option A: Using Setup Script (Recommended)**

```bash
# macOS/Linux
chmod +x setup_venv.sh
./setup_venv.sh

# Windows
setup_venv.bat
```

**Option B: Manual Setup**

```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Windows
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Activate Virtual Environment

**macOS/Linux:**
```bash
source .venv/bin/activate

# Or use the helper script
source activate.sh
```

**Windows:**
```bash
.venv\Scripts\activate
```

**Verify activation:**
```bash
which python  # Should point to .venv/bin/python
python --version
```

### 4. Setup PostgreSQL Database

**Create database and user:**

```bash
# Start PostgreSQL (macOS with Homebrew)
brew services start postgresql@15

# Create database
createdb sendit

# Create user with password
createuser sendit -P
# Enter password: sendit123

# Grant privileges
psql -d sendit -c "GRANT ALL PRIVILEGES ON DATABASE sendit TO sendit;"
```

**Alternative: Using psql directly**

```bash
psql postgres
```

```sql
CREATE DATABASE sendit;
CREATE USER sendit WITH PASSWORD 'sendit123';
GRANT ALL PRIVILEGES ON DATABASE sendit TO sendit;
\q
```

### 5. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Database
DATABASE_URL=postgresql://sendit:sendit123@localhost:5432/sendit

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS
CORS_ORIGINS=http://localhost:3000

# PayFast (Sandbox)
PAYFAST_MERCHANT_ID=10000100
PAYFAST_MERCHANT_KEY=46f0cd694581a
PAYFAST_PASSPHRASE=your-passphrase
PAYFAST_MODE=sandbox
PAYFAST_RETURN_URL=http://localhost:3000/payment/success
PAYFAST_CANCEL_URL=http://localhost:3000/payment/cancel
PAYFAST_NOTIFY_URL=http://localhost:8000/webhooks/payfast
```

### 6. Run Database Migrations

```bash
alembic upgrade head
```

### 7. Seed Test Data (Optional)

```bash
python scripts/seed_data.py
```

This creates:
- Test user: `test@send-it.local` / `pass123`
- Admin user: `admin@send-it.local` / `admin123`
- Sample addresses
- Mock courier

### 8. Start Development Server

```bash
# With auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Makefile
make dev
```

**Server will be available at:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Frontend Setup (Next.js/React)

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure Environment Variables

```bash
cp .env.example .env.local
```

Edit `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Start Development Server

```bash
npm run dev
```

**Server will be available at:**
- Frontend: http://localhost:3000

---

## Using Makefile (Backend)

The backend includes a Makefile for common tasks:

```bash
# Show all available commands
make help

# Create virtual environment
make venv

# Install dependencies
make install

# Run development server
make dev

# Run tests
make test

# Run linters
make lint

# Auto-format code
make format

# Run migrations
make migrate

# Seed database
make seed

# Clean cache files
make clean
```

---

## Development Workflow

### Daily Workflow

1. **Activate virtual environment:**
   ```bash
   cd backend
   source .venv/bin/activate  # or source activate.sh
   ```

2. **Start backend:**
   ```bash
   make dev
   # or
   uvicorn app.main:app --reload
   ```

3. **Start frontend (new terminal):**
   ```bash
   cd frontend
   npm run dev
   ```

4. **Access application:**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Before Committing

```bash
# Run linters
cd backend && make lint
cd frontend && npm run lint

# Run tests
cd backend && make test

# Format code
cd backend && make format
cd frontend && npm run lint:fix
```

---

## Virtual Environment Management

### Activating

**macOS/Linux:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\activate
```

**Verify activation:**
```bash
which python  # Should show .venv path
echo $VIRTUAL_ENV  # Should show .venv path
```

### Deactivating

```bash
deactivate
```

### Recreating Virtual Environment

```bash
# Remove existing
rm -rf .venv

# Create new
./setup_venv.sh
```

### Installing New Packages

```bash
# Activate venv first
source .venv/bin/activate

# Install package
pip install package-name

# Update requirements.txt
pip freeze > requirements.txt
```

---

## Database Management

### Creating Migrations

```bash
# Auto-generate migration
alembic revision --autogenerate -m "Description of changes"

# Review generated migration in alembic/versions/

# Apply migration
alembic upgrade head
```

### Rolling Back Migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Rollback all
alembic downgrade base
```

### Database Reset

```bash
# Drop and recreate database
dropdb sendit
createdb sendit

# Run migrations
alembic upgrade head

# Seed data
python scripts/seed_data.py
```

---

## Testing

### Running Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_signup

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x
```

### Writing Tests

```python
# tests/test_example.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_example():
    response = client.get("/health")
    assert response.status_code == 200
```

---

## Linting & Formatting

### Backend (Python)

```bash
cd backend

# Check linting
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Check formatting
black --check .

# Format code
black .

# Type checking
mypy app/

# All in one
make lint
make format
```

### Frontend (TypeScript)

```bash
cd frontend

# Check linting
npm run lint

# Auto-fix linting issues
npm run lint:fix

# Type checking
npm run type-check
```

---

## Troubleshooting

### Virtual Environment Issues

**Problem:** `command not found: python`

**Solution:**
```bash
# Ensure venv is activated
source .venv/bin/activate

# Verify
which python
```

**Problem:** `ModuleNotFoundError`

**Solution:**
```bash
# Ensure venv is activated and dependencies installed
source .venv/bin/activate
pip install -r requirements.txt
```

### Database Issues

**Problem:** `could not connect to server`

**Solution:**
```bash
# Start PostgreSQL
brew services start postgresql@15  # macOS
sudo systemctl start postgresql    # Linux
```

**Problem:** `database "sendit" does not exist`

**Solution:**
```bash
createdb sendit
```

### Port Already in Use

**Problem:** `Address already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn app.main:app --reload --port 8001
```

### Frontend Build Errors

**Problem:** `Module not found`

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

## IDE Setup

### VS Code

**Recommended Extensions:**
- Python (Microsoft)
- Pylance
- Ruff
- Black Formatter
- ESLint
- Prettier

**Settings (.vscode/settings.json):**
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  }
}
```

### PyCharm

1. **Configure Python Interpreter:**
   - Settings → Project → Python Interpreter
   - Add Interpreter → Existing
   - Select: `backend/.venv/bin/python`

2. **Enable Black:**
   - Settings → Tools → Black
   - Check "On save"

3. **Enable Ruff:**
   - Settings → Tools → External Tools
   - Add Ruff configuration

---

## Environment Variables Reference

### Backend (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@localhost:5432/db` |
| `SECRET_KEY` | JWT signing key | `your-secret-key` |
| `CORS_ORIGINS` | Allowed origins | `http://localhost:3000` |
| `PAYFAST_MERCHANT_ID` | PayFast merchant ID | `10000100` |
| `PAYFAST_MODE` | sandbox/production | `sandbox` |

### Frontend (.env.local)

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

---

## Quick Reference

### Backend Commands

```bash
# Virtual environment
source .venv/bin/activate
deactivate

# Development
make dev
make test
make lint
make format

# Database
make migrate
make seed
alembic upgrade head
alembic downgrade -1

# Cleanup
make clean
```

### Frontend Commands

```bash
# Development
npm run dev
npm run build
npm run start

# Quality
npm run lint
npm run lint:fix
npm run type-check
```

---

## Next Steps

1. ✅ Set up virtual environment
2. ✅ Configure database
3. ✅ Run migrations
4. ✅ Seed test data
5. ✅ Start development servers
6. 🚀 Start coding!

For production deployment, see [DEPLOYMENT.md](./DEPLOYMENT.md)

For API documentation, see [API.md](./API.md)
