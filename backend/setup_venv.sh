#!/bin/bash

# SEND-IT Backend - Virtual Environment Setup Script
# This script creates and configures a Python virtual environment

set -e

echo "======================================"
echo "  SEND-IT Backend Setup"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Found Python $PYTHON_VERSION${NC}"
echo ""

# Check if virtual environment already exists
if [ -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists.${NC}"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf .venv
    else
        echo "Using existing virtual environment."
        echo ""
        echo -e "${GREEN}To activate the virtual environment, run:${NC}"
        echo "  source .venv/bin/activate"
        exit 0
    fi
fi

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv .venv
echo -e "${GREEN}✓ Virtual environment created${NC}"
echo ""

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Install requirements
echo -e "${YELLOW}Installing dependencies from requirements.txt...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}Error: requirements.txt not found${NC}"
    exit 1
fi

echo ""
echo "======================================"
echo -e "${GREEN}  ✓ Setup Complete!${NC}"
echo "======================================"
echo ""
echo "To activate the virtual environment:"
echo -e "  ${YELLOW}source .venv/bin/activate${NC}"
echo ""
echo "To deactivate:"
echo -e "  ${YELLOW}deactivate${NC}"
echo ""
echo "To run the development server:"
echo -e "  ${YELLOW}uvicorn app.main:app --reload${NC}"
echo ""
