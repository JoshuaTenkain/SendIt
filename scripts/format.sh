#!/bin/bash

# SEND-IT Auto-formatting Script
# Automatically fix formatting issues

set -e

echo "======================================"
echo "  SEND-IT Auto-Formatter"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Backend formatting
echo -e "${YELLOW}[1/2] Backend Formatting${NC}"
echo "--------------------------------------"

cd backend

echo "Running Ruff auto-fix..."
ruff check --fix .
echo -e "${GREEN}✓ Ruff fixes applied${NC}"

echo ""
echo "Running Black formatter..."
black .
echo -e "${GREEN}✓ Black formatting applied${NC}"

cd ..

echo ""
echo -e "${YELLOW}[2/2] Frontend Formatting${NC}"
echo "--------------------------------------"

cd frontend

echo "Running ESLint auto-fix..."
npm run lint:fix
echo -e "${GREEN}✓ ESLint fixes applied${NC}"

cd ..

echo ""
echo "======================================"
echo -e "${GREEN}  ✓ All Formatting Complete!${NC}"
echo "======================================"
