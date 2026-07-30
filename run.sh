#!/bin/bash

# Voicet Runner Script
# This script prepares the environment and starts the Flask application.

set -e

echo "🚀 Preparing to run Voicet..."

# 1. Define paths
PROJECT_ROOT="$(pwd)"
UPLOAD_DIR="$PROJECT_ROOT/Voicet/project/static/uploads"
BREW_PREFIX=$(homebrew --prefix 2>/dev/null || echo "/home/linuxbrew/.linuxbrew")

# Detect OS to set the correct venv bin path
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    VENV_BIN="$PROJECT_ROOT/venv/Scripts"
    PYTHON_EXE="python"
else
    VENV_BIN="$PROJECT_ROOT/venv/bin"
    PYTHON_EXE="/usr/bin/python3"
fi

# 2. Setup Virtual Environment
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_EXE -m venv venv
fi

# 3. Install/Update Dependencies
echo "📥 Checking dependencies..."
"$VENV_BIN/pip" install -q --upgrade pip
"$VENV_BIN/pip" install -q -r requirements.txt

# 4. Create required directories
echo "📁 Ensuring upload directory exists..."
mkdir -p "$UPLOAD_DIR"
touch "$UPLOAD_DIR/.gitkeep"

# 5. Check System Dependencies
echo "🔍 Checking system binaries..."
MISSING_SYS=()
if ! command -v ffmpeg &> /dev/null; then MISSING_SYS+=("ffmpeg"); fi
if ! command -v sox &> /dev/null; then MISSING_SYS+=("sox"); fi

if [ ${#MISSING_SYS[@]} -gt 0 ]; then
    echo "⚠️  Missing system tools: ${MISSING_SYS[*]}"
    echo "Please install them to ensure video and audio processing works correctly."
fi

# 6. Check Vakyansh TTS Models
echo "🔍 Verifying voice models..."
LANGUAGES=("hindi" "kannada" "tamil" "telugu" "odia" "malayalam" "marathi" "gujarati" "bengali" "english")
MISSING_MODELS=()

# Check for transliteration models first
if [ ! -f "$PROJECT_ROOT/VAKYANSH_TTS/tts_infer/translit_models/default_lineup.json" ]; then
    echo "ℹ️  Transliteration models are missing."
    MISSING_MODELS+=("transliteration_base")
fi

for lang in "${LANGUAGES[@]}"; do
    if [ ! -d "$PROJECT_ROOT/VAKYANSH_TTS/tts_infer/translit_models/$lang" ] || [ "$(find "$PROJECT_ROOT/VAKYANSH_TTS/tts_infer/translit_models/$lang" -name "*.pth" -o -name "*.pt" | wc -l)" -eq 0 ]; then
        MISSING_MODELS+=("$lang")
    fi
done

if [ ${#MISSING_MODELS[@]} -gt 0 ]; then
    echo "ℹ️  Some voice models are missing: ${MISSING_MODELS[*]}"
    echo "👉 Run './setup_models.sh' to download the required models."
else
    echo "✅ Voice models verified."
fi

# 7. Start Services (Redis & Celery)
echo "🍃 Starting Redis..."
if ! pgrep redis-server > /dev/null; then
    "$BREW_PREFIX/bin/redis-server" --daemonize yes
    sleep 2
fi

echo "🐝 Starting Celery worker..."
# Kill any existing workers first to avoid conflicts
pkill -f "celery -A project.worker.celery" || true
cd Voicet
"$VENV_BIN/celery" -A project.worker.celery worker --loglevel=info > celery.log 2>&1 &
CELERY_PID=$!

# 8. Start Application
echo "🌐 Starting Flask application..."
export FLASK_APP=project

# Cleanup function to kill background processes on exit
cleanup() {
    echo "🛑 Shutting down..."
    kill $CELERY_PID || true
    # We leave Redis running as it's generally fine, but could kill it if preferred
}
trap cleanup EXIT

"$VENV_BIN/flask" run
