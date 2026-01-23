#!/bin/bash
set -e

# Configuration
MODEL_STORAGE="model_storage"
OLD_MODEL_DIR="VAKYANSH_TTS/tts_infer/translit_models"
UPLOAD_DIR="Voicet/project/static/uploads"

echo "🚀 Starting Voicet Docker Setup..."

# 1. Ensure Upload Directory Exists
if [ ! -d "$UPLOAD_DIR" ]; then
    echo "📁 Creating upload directory..."
    mkdir -p "$UPLOAD_DIR"
fi

# 2. Handle Model Storage
echo "🔍 Checking model storage..."
mkdir -p "$MODEL_STORAGE"

# Check if model_storage is empty
if [ -z "$(ls -A $MODEL_STORAGE)" ]; then
    echo "⚠️  Model storage is empty."
    
    # Check if models exist in the old location (inside repo)
    if [ -d "$OLD_MODEL_DIR" ] && [ -n "$(ls -A $OLD_MODEL_DIR)" ]; then
        echo "📦 Found models in project directory. Moving to $MODEL_STORAGE to save space..."
        # Use rsync or mv. Mv is faster.
        # Ensure the destination supports the move or copy+delete
        cp -r "$OLD_MODEL_DIR"/* "$MODEL_STORAGE"/
        rm -rf "$OLD_MODEL_DIR"/* # Clean up old location to prevent build context bloat
    else
        echo "⬇️  No models found. Downloading now (this may take 10GB+)..."
        # Run the existing setup script
        ./setup_models.sh
        
        # Move them to storage
        echo "📦 Moving downloaded models to external storage..."
        cp -r "$OLD_MODEL_DIR"/* "$MODEL_STORAGE"/
        rm -rf "$OLD_MODEL_DIR"/*
    fi
else
    echo "✅ Models found in $MODEL_STORAGE."
fi

# 3. Launch Docker
echo "🐳 Launching Docker Container..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker."
    exit 1
fi

docker compose up --build

