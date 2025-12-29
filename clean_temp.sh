#!/bin/bash

# clean_temp.sh - Utility to clean up temporary audio and video files

echo "🧹 Cleaning up temporary files..."

# Clean up temporary wav files in root
find . -maxdepth 1 -name "temp_*.wav" -delete
find . -maxdepth 1 -name "output.wav" -delete
find . -maxdepth 1 -name "output.mp4" -delete

# Clean up uploads directory (optional, uncomment if you want to clear processed videos)
# echo "📁 Cleaning uploads directory..."
# rm -rf Voicet/project/static/uploads/*

echo "✅ Done! All clean now."
