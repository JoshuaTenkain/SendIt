#!/bin/bash

# SEND-IT Linting Script
# Run all linters for backend and frontend

set -e

echo "======================================"
echo "  SEND-IT Code Quality Check"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Backend linting
echo -e "${YELLOW}[1/2] Backend Linting${NC}"
echo "--------------------------------------"

cd backend

echo "Running Ruff..."
if ruff check .; then
    echo -e "${GREEN}✓ Ruff passed${NC}"
else
    echo -e "${RED}✗ Ruff failed${NC}"
    exit 1
fi

echo ""
echo "Running Black..."
if black --check .; then
    echo -e "${GREEN}✓ Black passed${NC}"
else
    echo -e "${RED}✗ Black failed (run 'black .' to fix)${NC}"
    exit 1
fi

echo ""
echo "Running MyPy..."
if mypy app/ --ignore-missing-imports; then
    echo -e "${GREEN}✓ MyPy passed${NC}"
else
    echo -e "${YELLOW}⚠ MyPy warnings (non-blocking)${NC}"
fi

cd ..

echo ""
echo -e "${YELLOW}[2/2] Frontend Linting${NC}"
echo "--------------------------------------"

cd frontend

echo "Running ESLint..."
if npm run lint; then
    echo -e "${GREEN}✓ ESLint passed${NC}"
else
    echo -e "${RED}✗ ESLint failed (run 'npm run lint:fix' to fix)${NC}"
    exit 1
fi

echo ""
echo "Running TypeScript type check..."
if npm run type-check; then
    echo -e "${GREEN}✓ TypeScript passed${NC}"
else
    echo -e "${YELLOW}⚠ TypeScript warnings (non-blocking)${NC}"
fi

cd ..

echo ""
echo "======================================"
echo -e "${GREEN}  ✓ All Linting Passed!${NC}"
echo "======================================"
