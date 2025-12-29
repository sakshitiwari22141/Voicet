# Voicet 🚀

Voicet is an automated video dubbing tool that translates and re-voices videos into multiple Indian languages. It leverages state-of-the-art AI models for transcription, translation, and text-to-speech.

---

## 🤖 How it works?
1. **Listen**: Transcribes the original audio using **Whisper**.
2. **Translate**: Translates text to the target language using **NLLB-200**.
3. **Speak**: Generates native-sounding audio using **Vakyansh** Indian language models.
4. **Mix**: Synchronizes and muxes the new audio into the video using **FFmpeg** and **Sox**.

---

## 🛠️ System Requirements

- **Linux** (Ubuntu/Debian recommended) or **Windows** (via Git Bash)
- **RAM**: 8GB Minimum (16GB+ recommended for smoother model loading)
- **Disk Space**: ~10GB for models
- **System Binaries**: `ffmpeg` and `sox` must be installed and in your PATH.

---

## 🚀 Quick Start (Automated)

The easiest way to get started is using the runner script:

```bash
sh run.sh
```

This script will:
1. Create a virtual environment and install Python dependencies.
2. Check for system binaries (`ffmpeg`, `sox`).
3. Verify if the required voice models are present.
4. Start the Flask application.

If it's your first time, you **must** download the voice models separately (see below).

---

## 📥 Manual Setup

### 1. Install System Dependencies

**Linux:**
```bash
sudo apt update && sudo apt install ffmpeg sox unzip wget
```

**Windows:**
1. Download `ffmpeg` from [ffmpeg.org](https://ffmpeg.org/download.html).
2. Download `sox` for Windows.
3. Add both directories to your **System Environment Variables (PATH)**.

### 2. Download Voice Models
The models for Hindi, Tamil, Telugu, etc., are quite large (~10GB total). Run the following to download everything:

```bash
sh setup_models.sh
```

---

## 🖥️ Usage

1. Run `sh run.sh` and open `http://127.0.0.1:5000` in your browser.
2. Upload a video (mp4, avi, mkv) or provide a YouTube URL.
3. Select your target language and voice gender.
4. Wait for processing—the dubbed video will download automatically once finished!

---

## 📝 Tips & Troubleshooting

### Torch 2.6 Weights Error
If you see a `Weights only load failed` error, the code includes a monkeypatch for PyTorch 2.6+ to allow loading older model formats safely. This is handled automatically.

### Cleaning Temporary Files
The processing generates many small `.wav` files. To clean them up:
```bash
sh clean_temp.sh
```

### Accuracy & Performance
- **Model Size**: We use `nllb-200-distilled-1.3B` for speed. For higher accuracy, you can edit `voicet.py` to use the `3.3B` version if you have enough RAM/VRAM.
- **Background Noise**: Clean audio leads to better results. Noisy backgrounds might cause Whisper to skip words.

For more details, see our [Accuracy Log](docs/ACCURACY_LOG.md).

---

## 📸 Interface
![Voicet Homepage](Voicet-Homepage.png)
