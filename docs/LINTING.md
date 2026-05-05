# SEND-IT Linting & Code Quality Guide

## Overview

This project uses automated linting and formatting tools to maintain code quality and consistency across the codebase.

---

## Backend (Python)

### Tools Used

1. **Ruff** - Fast Python linter (replaces flake8, isort, pyupgrade)
2. **Black** - Code formatter
3. **MyPy** - Static type checker

### Configuration Files

- `.ruff.toml` - Ruff configuration
- `pyproject.toml` - Black and MyPy configuration

### Running Linters

**Check code quality:**
```bash
cd backend

# Run all linters
ruff check .
black --check .
mypy app/ --ignore-missing-imports
```

**Auto-fix issues:**
```bash
cd backend

# Fix linting issues
ruff check --fix .

# Format code
black .
```

### Ruff Rules

- **Line length:** 120 characters
- **Target Python:** 3.11
- **Enabled rules:**
  - E/W: pycodestyle errors and warnings
  - F: pyflakes
  - I: isort (import sorting)
  - B: flake8-bugbear
  - C4: flake8-comprehensions
  - UP: pyupgrade

### Common Issues

**Import sorting:**
```python
# Bad
import os
from app.models import User
import sys

# Good (Ruff will fix)
import os
import sys

from app.models import User
```

**Line length:**
```python
# Bad
def very_long_function_name_with_many_parameters(param1, param2, param3, param4, param5, param6, param7, param8):
    pass

# Good (Black will format)
def very_long_function_name_with_many_parameters(
    param1, param2, param3, param4, 
    param5, param6, param7, param8
):
    pass
```

---

## Frontend (TypeScript/React)

### Tools Used

1. **ESLint** - JavaScript/TypeScript linter
2. **TypeScript Compiler** - Type checking

### Configuration Files

- `.eslintrc.json` - ESLint configuration
- `tsconfig.json` - TypeScript configuration

### Running Linters

**Check code quality:**
```bash
cd frontend

# Run ESLint
npm run lint

# Run TypeScript type check
npm run type-check
```

**Auto-fix issues:**
```bash
cd frontend

# Fix ESLint issues
npm run lint:fix
```

### ESLint Rules

- **Extends:** next/core-web-vitals, next/typescript
- **Custom rules:**
  - Unused variables: warning
  - Explicit any: warning
  - React hooks deps: warning

### Common Issues

**Unused variables:**
```typescript
// Bad
const [data, setData] = useState(null);
// 'setData' is never used

// Good
const [data] = useState(null);
```

**Missing dependencies:**
```typescript
// Bad
useEffect(() => {
  fetchData(userId);
}, []); // Missing 'userId' dependency

// Good
useEffect(() => {
  fetchData(userId);
}, [userId]);
```

**Unescaped entities:**
```typescript
// Bad
<p>Don't use quotes like this</p>

// Good
<p>Don&apos;t use quotes like this</p>
```

---

## Docker Integration

### Run Linters in Docker

**Using Docker Compose:**
```bash
# Run all linters
docker compose --profile lint up

# Run backend linting only
docker compose --profile lint up backend-lint

# Run frontend linting only
docker compose --profile lint up frontend-lint
```

**Using dedicated compose file:**
```bash
docker compose -f docker-compose.lint.yml up
```

### Linting in CI/CD

Linting runs automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**GitHub Actions workflow:** `.github/workflows/lint.yml`

---

## Quick Scripts

### Lint Everything

```bash
# Make script executable
chmod +x scripts/lint.sh

# Run all linters
./scripts/lint.sh
```

### Auto-format Everything

```bash
# Make script executable
chmod +x scripts/format.sh

# Auto-fix all formatting
./scripts/format.sh
```

---

## IDE Integration

### VS Code

**Install extensions:**
- Python (Microsoft)
- Pylance
- Ruff
- ESLint
- Prettier

**Settings (.vscode/settings.json):**
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### PyCharm / WebStorm

**Configure Ruff:**
1. Settings → Tools → External Tools
2. Add new tool: Ruff
3. Program: `ruff`
4. Arguments: `check $FilePath$`

**Configure Black:**
1. Settings → Tools → Black
2. Enable "On save"

**Configure ESLint:**
1. Settings → Languages & Frameworks → JavaScript → Code Quality Tools → ESLint
2. Enable "Automatic ESLint configuration"
3. Enable "Run eslint --fix on save"

---

## Pre-commit Hooks

### Install pre-commit

```bash
pip install pre-commit
```

### Create .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        files: \.(js|ts|tsx)$
        types: [file]
```

### Install hooks

```bash
pre-commit install
```

Now linting runs automatically before each commit!

---

## Ignoring Linting Rules

### Backend (Python)

**Ignore specific line:**
```python
# noqa: E501
very_long_line_that_exceeds_limit = "This line is too long but we need it"

# ruff: noqa
import unused_module  # Won't be flagged
```

**Ignore entire file:**
```python
# ruff: noqa
# This file is excluded from linting
```

### Frontend (TypeScript)

**Ignore specific line:**
```typescript
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const data: any = fetchData();

// @ts-ignore
const legacyCode = oldLibrary();
```

**Ignore entire file:**
```typescript
/* eslint-disable */
// This file is excluded from linting
```

---

## Continuous Improvement

### Code Quality Metrics

Track these metrics over time:
- Linting errors count
- Type coverage percentage
- Code complexity scores
- Test coverage

### Best Practices

1. **Run linters before committing**
2. **Fix warnings, not just errors**
3. **Don't ignore rules without reason**
4. **Keep configuration up to date**
5. **Review linting in code reviews**

---

## Troubleshooting

### Ruff not found

```bash
cd backend
pip install ruff
```

### ESLint errors in node_modules

Add to `.eslintignore`:
```
node_modules/
.next/
out/
```

### MyPy import errors

Add to `pyproject.toml`:
```toml
[[tool.mypy.overrides]]
module = "problematic_module.*"
ignore_missing_imports = true
```

### Black and Ruff conflict

Black takes precedence for formatting. Ruff handles linting.

---

## Summary

**Backend:**
- ✅ Ruff for linting
- ✅ Black for formatting
- ✅ MyPy for type checking

**Frontend:**
- ✅ ESLint for linting
- ✅ TypeScript for type checking

**Integration:**
- ✅ Docker Compose profiles
- ✅ GitHub Actions CI/CD
- ✅ Pre-commit hooks
- ✅ IDE integration

**Commands:**
```bash
# Quick lint check
./scripts/lint.sh

# Quick format
./scripts/format.sh

# Docker lint
docker compose --profile lint up
```

---

**Maintain high code quality with automated linting!** 🎯
