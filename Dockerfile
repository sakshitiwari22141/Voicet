# Use an official PyTorch image with CUDA support
# This tag assumes PyTorch 2.4.0 with CUDA 12.1.
# If this specific tag doesn't exist, we might need to adjust, but this is the target.
FROM pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime

# Set working directory
WORKDIR /app

# Install system dependencies
# ffmpeg and sox are required for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    sox \
    libsox-fmt-all \
    wget \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
# Upgrade pip first to ensure compatibility
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set environment variables
ENV FLASK_APP=project
ENV FLASK_RUN_HOST=0.0.0.0
# Ensure Python outputs are sent straight to terminal (e.g. logs) without buffering
ENV PYTHONUNBUFFERED=1

# Expose the Flask port
EXPOSE 5000

# The entrypoint will be handled by the docker-compose command or a script
CMD ["./run_docker.sh"]
