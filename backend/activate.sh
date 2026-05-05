#!/bin/bash

# Quick activation script for SEND-IT backend virtual environment
# Usage: source activate.sh

if [ ! -d ".venv" ]; then
    echo "Virtual environment not found!"
    echo "Run ./setup_venv.sh to create it."
    return 1
fi

source .venv/bin/activate
echo "✓ Virtual environment activated"
echo "Python: $(python --version)"
echo "Location: $(which python)"
