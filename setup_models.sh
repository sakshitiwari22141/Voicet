#!/bin/bash

# setup_models.sh - Automated model setup for Voicet (All Languages)

set -e

echo "🚀 Starting Voicet Model Setup for all languages..."

# Define base path
BASE_DIR="VAKYANSH_TTS/tts_infer/translit_models"
mkdir -p "$BASE_DIR"

# 0. Download Transliteration models (Required for XlitEngine)
if [ ! -f "VAKYANSH_TTS/tts_infer/translit_models/default_lineup.json" ]; then
    echo "📥 Downloading Transliteration models..."
    cd VAKYANSH_TTS/tts_infer
    wget -q --show-progress https://storage.googleapis.com/vakyansh-open-models/translit_models.zip
    unzip -o translit_models.zip
    rm translit_models.zip
    cd ../..
fi

# Function to download and extract models
download_model() {
    local lang=$1
    local gender=$2
    local model_type=$3 # glow or hifi
    local url=$4
    local target_dir="$BASE_DIR/$lang/$gender/${model_type}_ckp"

    if [ -d "$target_dir" ] && [ "$(ls -A "$target_dir")" ]; then
        echo "✅ $lang $gender $model_type already exists. Skipping."
        return
    fi

    echo "📥 Downloading $lang $gender $model_type..."
    mkdir -p "$target_dir"
    local temp_file=$(mktemp)
    wget -q --show-progress -O "$temp_file" "$url"
    
    echo "📦 Extracting $lang $gender $model_type..."
    unzip -q -j "$temp_file" -d "$target_dir"
    rm "$temp_file"
}

# 1. Hindi
download_model "hindi" "female" "glow" "https://storage.googleapis.com/vakyansh-open-models/tts/hindi/hi-IN/female_voice_0/glow.zip"
download_model "hindi" "female" "hifi" "https://storage.googleapis.com/vakyansh-open-models/tts/hindi/hi-IN/female_voice_0/hifi.zip"
download_model "hindi" "male" "glow" "https://storage.googleapis.com/vakyansh-open-models/tts/hindi/hi-IN/male_voice_1/glow.zip"
download_model "hindi" "male" "hifi" "https://storage.googleapis.com/vakyansh-open-models/tts/hindi/hi-IN/male_voice_1/hifi.zip"

# 2. Kannada
download_model "kannada" "female" "glow" "https://storage.googleapis.com/vakyansh-open-models/tts/kannada/kn-IN/female_voice_0/fe_glow.zip"
download_model "kannada" "female" "hifi" "https://storage.googleapis.com/vakyansh-open-models/tts/kannada/kn-IN/ma_fe_hifi/ma_fe_hifi.zip"
download_model "kannada" "male" "glow" "https://storage.googleapis.com/vakyansh-open-models/tts/kannada/kn-IN/male_voice_1/ma_glow.zip"
download_model "kannada" "male" "hifi" "https://storage.googleapis.com/vakyansh-open-models/tts/kannada/kn-IN/ma_fe_hifi/ma_fe_hifi.zip"

# 3. Tamil
download_model "tamil" "female" "glow" "https://storage.googleapis.com/vakyansh-open-models/tts/tamil/ta-IN/female_voice_0/glow.zip"
download_model "tamil" "female" "hifi" "https://storage.googleapis.com/vakyansh-open-models/tts/tamil/ta-IN/ma_fe_hifi/hifi.zip"
download_model "tamil" "male" "glow" "https://storage.googleapis.com/vakyansh-open-models/tts/tamil/ta-IN/male_voice_1/glow.zip"
download_model "tamil" "male" "hifi" "https://storage.googleapis.com/vakyansh-open-models/tts/tamil/ta-IN/ma_fe_hifi/hifi.zip"

# 4. Telugu
download_model "telugu" "female" "glow" "https://storage.googleapis.com/vakyansh-open-models/tts/telugu/te-IN/female_voice_0/glow.zip"
download_model "telugu" "female" "hifi" "https://storage.googleapis.com/vakyansh-open-models/tts/telugu/te-IN/ma_fe_hifi/hifi.zip"
download_model "telugu" "male" "glow" "https://storage.googleapis.com/vakyansh-open-models/tts/telugu/te-IN/male_voice_1/glow.zip"
download_model "telugu" "male" "hifi" "https://storage.googleapis.com/vakyansh-open-models/tts/telugu/te-IN/ma_fe_hifi/hifi.zip"

# 5. Odia
download_model "odia" "female" "glow" "https://storage.googleapis.com/vakyansh-open-models/tts/odia/or-IN/female_voice_0/glow.zip"
download_model "odia" "female" "hifi" "https://storage.googleapis.com/vakyansh-open-models/tts/odia/or-IN/ma_fe_hifi/hifi.zip"
download_model "odia" "male" "glow" "https://storage.googleapis.com/vakyansh-open-models/tts/odia/or-IN/male_voice_1/glow.zip"
download_model "odia" "male" "hifi" "https://storage.googleapis.com/vakyansh-open-models/tts/odia/or-IN/ma_fe_hifi/hifi.zip"

# 6. Malayalam
download_model "malayalam" "female" "glow" "https://storage.googleapis.com/vakyansh-open-models/tts/malayalam/ml-IN/female_voice_0/glow.zip"
download_model "malayalam" "female" "hifi" "https://storage.googleapis.com/vakyansh-open-models/tts/malayalam/ml-IN/female_voice_0/hifi.zip"
download_model "malayalam" "male" "glow" "https://storage.googleapis.com/vakyansh-open-models/tts/malayalam/ml-IN/male_voice_1/glow.zip"
download_model "malayalam" "male" "hifi" "https://storage.googleapis.com/vakyansh-open-models/tts/malayalam/ml-IN/male_voice_1/hifi.zip"

# 7. Marathi
download_model "marathi" "female" "glow" "https://storage.googleapis.com/vakyansh-open-models/tts/marathi/mr-IN/female_voice_0/glow.zip"
download_model "marathi" "female" "hifi" "https://storage.googleapis.com/vakyansh-open-models/tts/marathi/mr-IN/female_voice_0/hifi.zip"

# 8. Gujarati
download_model "gujarati" "male" "glow" "https://storage.googleapis.com/vakyansh-open-models/tts/gujarati/gu-IN/male_voice_1/glow.zip"
download_model "gujarati" "male" "hifi" "https://storage.googleapis.com/vakyansh-open-models/tts/gujarati/gu-IN/male_voice_1/hifi.zip"

# 9. Bengali
download_model "bengali" "female" "glow" "https://storage.googleapis.com/vakyansh-open-models/tts/bengali/bn-IN/female_voice_0/glow.zip"
download_model "bengali" "female" "hifi" "https://storage.googleapis.com/vakyansh-open-models/tts/bengali/bn-IN/female_voice_0/hifi.zip"
download_model "bengali" "male" "glow" "https://storage.googleapis.com/vakyansh-open-models/tts/bengali/bn-IN/male_voice_1/glow.zip"
download_model "bengali" "male" "hifi" "https://storage.googleapis.com/vakyansh-open-models/tts/bengali/bn-IN/male_voice_1/hifi.zip"

# 10. English (IN)
download_model "english" "female" "glow" "https://storage.googleapis.com/vakyansh-open-models/tts/english/en-IN/female_voice_0/glow.zip"
download_model "english" "female" "hifi" "https://storage.googleapis.com/vakyansh-open-models/tts/hindi/hi-IN/female_voice_0/hifi.zip"
download_model "english" "male" "glow" "https://storage.googleapis.com/vakyansh-open-models/tts/english/en-IN/male_voice_1/glow.zip"
download_model "english" "male" "hifi" "https://storage.googleapis.com/vakyansh-open-models/tts/hindi/hi-IN/male_voice_1/hifi.zip"

echo "✅ All set! Models are ready to use."
