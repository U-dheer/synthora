#!/bin/bash

# RAG Service Startup Script

echo "🚀 Starting RAG Service..."
echo "================================"

# Navigate to RAG service directory
cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH="$(pwd)"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Copying from .env.example..."
    cp .env.example .env
fi

# Start the service
echo "📦 Loading dependencies (this may take a minute on first run)..."
python -m app.main

