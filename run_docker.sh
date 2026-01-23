#!/bin/bash
set -e

echo "🚀 Starting Voicet in Docker..."

# Define model directory path in container
MODEL_DIR="/app/VAKYANSH_TTS/tts_infer/translit_models"

# Check if model directory is empty (meaning volume is mounted but empty)
if [ -z "$(ls -A $MODEL_DIR)" ]; then
   echo "⚠️  Model directory $MODEL_DIR is empty."
   echo "ℹ️  Ideally, you should run ./setup_models.sh on your host setup to populate ./model_storage first."
   echo "    However, we can attempt to run setup inside the container if you wish, but it won't persist if the volume isn't mapped correctly."
   # Uncomment the line below if you want to auto-setup inside container (not recommended for "lightweight" goal if volume not permanent)
   # ./setup_models.sh
else
   echo "✅ Models detected in $MODEL_DIR."
fi

# Ensure upload directory exists
mkdir -p /app/Voicet/project/static/uploads

# Start the application
echo "🌐 Starting Flask App..."
cd Voicet
flask run --host=0.0.0.0
