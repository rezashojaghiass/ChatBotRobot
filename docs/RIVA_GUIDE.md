# NVIDIA Riva Installation Guide for Jetson Xavier

Complete guide to install and configure NVIDIA Riva speech AI services on Jetson AGX Xavier.

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Download Riva QuickStart](#download-riva-quickstart)
4. [Configure Riva](#configure-riva)
5. [Download Models](#download-models)
6. [Start Riva Server](#start-riva-server)
7. [Verify Installation](#verify-installation)
8. [Troubleshooting](#troubleshooting)

---

## Overview

**NVIDIA Riva** provides:
- **ASR (Automatic Speech Recognition)**: Speech-to-Text
- **TTS (Text-to-Speech)**: Text-to-Voice
- **NLP (Natural Language Processing)**: Intent recognition, slot filling

**For Jetson Xavier:**
- **Maximum Riva Version**: 2.14.0 (due to JetPack 5.x / L4T R35.x)
- **Client SDK**: Can use 2.19.x (backward compatible)
- **Container**: `nvcr.io/nvidia/riva/riva-speech:2.14.0-l4t-aarch64`

---

## Prerequisites

Before starting, ensure:
- ✅ JetPack 5.x installed (see [SETUP.md](SETUP.md))
- ✅ Docker with GPU support working
- ✅ 30GB+ free disk space (for models)
- ✅ NVIDIA NGC account (free): https://ngc.nvidia.com/

---

## Download Riva QuickStart

### 1. Get NGC API Key

```bash
# Go to https://ngc.nvidia.com/setup/api-key
# Generate API Key
# Copy the key (starts with "nvapi-...")

# Login to NGC
docker login nvcr.io
# Username: $oauthtoken
# Password: <paste your NGC API key>
```

### 2. Download Riva QuickStart Scripts

```bash
cd /mnt/nvme/adrian

# Download Riva QuickStart for ARM64
ngc registry resource download-version "nvidia/riva/riva_quickstart_arm64:2.19.0"

# Or use wget
wget https://ngc.nvidia.com/api/registry/model-scripts/nvidia/riva/riva_quickstart_arm64/versions/2.19.0/files/riva_quickstart_arm64_v2.19.0.tar.gz

# Extract
tar -xzf riva_quickstart_arm64_v2.19.0.tar.gz
cd riva_quickstart_arm64_v2.19.0
```

**Note:** QuickStart version 2.19.0 is just the script package - it will download Riva server 2.14.0 for Xavier.

---

## Configure Riva

### 1. Edit Configuration File

```bash
cd /mnt/nvme/adrian/riva_quickstart_arm64_v2.19.0

# Edit config.sh
nano config.sh
```

**Critical Settings:**

```bash
# Riva server version - MUST BE 2.14.0 for Jetson Xavier
riva_speech_api_image_name="nvcr.io/nvidia/riva/riva-speech:2.14.0-l4t-aarch64"

# Service to enable
service_enabled_asr=true        # Enable ASR (required)
service_enabled_nlp=false       # Disable NLP (optional, saves memory)
service_enabled_tts=true        # Enable TTS (required)
service_enabled_nmt=false       # Disable translation (not needed)

# ASR settings
models_asr=(
    "riv a_quickstart_conformer_en_US_str eaming:v2.14.0"
)

# TTS settings
models_tts=(
    "riva_quickstart_fastpitch_hifigan_en_US_single_female_glow:v2.14.0"
    "riva_quickstart_fastpitch_hifigan_en_US_single_male_glow:v2.14.0"
)

# GPU settings
gpus_to_use="device=0"          # Use GPU 0
riva_target_gpu_family="tegra"  # Jetson platform

# Memory optimization
riva_model_deploy_memlock=false # Reduce memory usage
```

### 2. Model Selection

**ASR Models (choose one):**
- `conformer_en_US_streaming:v2.14.0` - **Recommended**, best accuracy
- `quartznet_en_US:v2.14.0` - Lighter, faster, less accurate

**TTS Voices:**
- `single_male_glow:v2.14.0` - **We use this** (Buzz Lightyear voice)
- `single_female_glow:v2.14.0` - Alternative voice
- Both can be installed

**Recommended Config for This Project:**
```bash
models_asr=("riva_quickstart_conformer_en_US_streaming:v2.14.0")
models_tts=(
    "riva_quickstart_fastpitch_hifigan_en_US_single_male_glow:v2.14.0"
)
```

---

## Download Models

### 1. Initialize Models

```bash
cd /mnt/nvme/adrian/riva_quickstart_arm64_v2.19.0

# Run initialization script
bash riva_init.sh

# This will:
# - Download Riva server container (2.14.0)
# - Download model files (.rmir format)
# - Extract models to ./models/ directory
# 
# Expected download: ~800MB-1.5GB
# Time: 10-30 minutes depending on internet speed
```

**Expected Output:**
```
Downloading riva-speech-server:2.14.0-l4t-aarch64...
Pulling riva-speech container...
Downloading model: riva_quickstart_conformer_en_US_streaming:v2.14.0...
Model downloaded: models/rmir/asr_conformer_en_US_str_offline.rmir (627 MB)
Downloading model: riva_quickstart_fastpitch_hifigan_en_US_single_male_glow:v2.14.0...
Model downloaded: models/rmir/tts_en_US_male.rmir (187 MB)
```

### 2. Deploy Models

```bash
# Build optimized models for Jetson
bash riva_build.sh

# This will:
# - Convert .rmir models to optimized TensorRT engines
# - Create Triton model repository
# - Time: 20-60 minutes (heavy GPU usage)
```

**Expected Output:**
```
Building ASR model...
Optimizing for Tegra platform...
Model built: models/triton/asr_model/...
Building TTS model...
Model built: models/triton/tts_model/...
```

---

## Start Riva Server

### 1. Start Server Container

```bash
cd /mnt/nvme/adrian/riva_quickstart_arm64_v2.19.0

# Start Riva server
bash riva_start.sh

# Server will start in Docker container
# Port: 50051 (gRPC)
# GPU: Will use Xavier GPU 0
```

**Expected Output:**
```
Starting Riva Speech Server...
Container riva-speech is running
Waiting for Riva server to load models...
Server ready on port 50051
```

### 2. Check Server Status

```bash
# Check Docker container
docker ps
# Expected: riva-speech container running

# Check logs
docker logs riva-speech

# Expected: "Riva Speech server started" messages

# Check GPU and memory usage
sudo tegrastats --interval 1000
# Press Ctrl+C after a few seconds
# Expected: Shows GPU usage and memory consumption

# Or use jtop for better visualization
sudo jtop
# Navigate to GPU tab to see Riva memory usage (~2-3GB)
```

### 3. Make Scripts for Easy Control

```bash
cd /mnt/nvme/adrian/ChatBotRobot/scripts

# Create start script
cat > start_riva.sh << 'EOF'
#!/bin/bash
cd /mnt/nvme/adrian/riva_quickstart_arm64_v2.19.0
bash riva_start.sh
EOF

# Create stop script
cat > stop_riva.sh << 'EOF'
#!/bin/bash
cd /mnt/nvme/adrian/riva_quickstart_arm64_v2.19.0
docker stop riva-speech
EOF

# Make executable
chmod +x start_riva.sh stop_riva.sh
```

**Usage:**
```bash
# Start Riva
./scripts/start_riva.sh

# Stop Riva
./scripts/stop_riva.sh
```

---

## Verify Installation

### 1. Test ASR (Speech-to-Text)

```bash
cd /mnt/nvme/adrian/ChatBotRobot/src

# Run ASR test
python3 asr_test.py

# Speak into microphone: "Hello, how are you?"
# Expected output: Transcribed text appears on screen
```

### 2. Test TTS (Text-to-Speech)

```bash
# Test TTS with Python
python3 << EOF
import riva.client

auth = riva.client.Auth(uri='localhost:50051')
tts = riva.client.SpeechSynthesisService(auth)

resp = tts.synthesize(
    "To infinity and beyond!",
    voice_name="English-US.Male-1",
    language_code="en-US",
    encoding=riva.client.AudioEncoding.LINEAR_PCM,
    sample_rate_hz=16000
)

with open("test_tts.wav", "wb") as f:
    f.write(resp.audio)

print("TTS audio saved to test_tts.wav")
EOF

# Play audio
aplay test_tts.wav
# Expected: Hear "To infinity and beyond!" in male voice
```

### 3. Check Available Models

```bash
# List models via gRPC
docker exec riva-speech curl -s localhost:8000/v2/models
# Expected: JSON output with asr, tts models listed
```

---

## Troubleshooting

### Container Won't Start

**Problem:** Error starting riva-speech container

```bash
# Check Docker GPU access
docker run --rm --runtime nvidia nvcr.io/nvidia/l4t-base:r35.4.1 cat /proc/device-tree/model
# Should show: Jetson AGX Xavier

# If error, reinstall NVIDIA Container Runtime
sudo apt install nvidia-container-runtime
sudo systemctl restart docker
```

### Wrong Riva Version

**Problem:** Riva 2.15+ downloads instead of 2.14.0

**Solution:** Edit `config.sh`:
```bash
riva_speech_api_image_name="nvcr.io/nvidia/riva/riva-speech:2.14.0-l4t-aarch64"
```

**Verify:**
```bash
docker images | grep riva
# Should show: riva-speech  2.14.0-l4t-aarch64
```

### Model Build Fails

**Problem:** riva_build.sh crashes with OOM (Out of Memory)

**Solutions:**
```bash
# 1. Close other applications
pkill chrome
pkill firefox

# 2. Increase swap space
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 3. Build one model at a time
# Edit config.sh and enable only ASR, build, then enable TTS
```

### gRPC Connection Refused

**Problem:** Client can't connect to server

**Checks:**
```bash
# 1. Is container running?
docker ps | grep riva-speech

# 2. Is port open?
netstat -tulpn | grep 50051

# 3. Check firewall
sudo ufw status
sudo ufw allow 50051/tcp

# 4. Restart server
cd /mnt/nvme/adrian/riva_quickstart_arm64_v2.19.0
bash riva_stop.sh
bash riva_start.sh
```

### TTS Voice Not Found

**Problem:** Error: "Voice English-US.Male-1 not found"

**Solution:**
```bash
# List available voices
docker exec riva-speech curl -s localhost:8000/v2/models | grep tts

# Use correct voice name
# - English-US.Male-1 (if male model installed)
# - English-US.Female-1 (if female model installed)
```

### High Latency

**Problem:** ASR/TTS response is slow

**Solutions:**
```bash
# 1. Check GPU usage
sudo tegrastats --interval 1000
# Press Ctrl+C after checking
# Look for GR3D (GPU) usage - if not at 100%, good

# 2. Optimize Jetson power mode
sudo nvpmodel -m 0  # MAXN mode (maximum performance)
sudo jetson_clocks   # Lock clocks to max

# 3. Reduce batch size in config.sh
asr_decoder_batching_config="max_batch_size: 1"
```

### ALSA Warnings

**Problem:** `ALSA lib ... Unknown PCM ...` warnings

**Solution:** These are harmless warnings, audio still works. To suppress:
```bash
# Add to ~/.bashrc
export ALSA_CARD=2  # Replace 2 with your device number
```

---

## Performance Tuning

### Jetson Power Modes

```bash
# Check current mode
sudo nvpmodel -q

# Set maximum performance
sudo nvpmodel -m 0  # Mode 0 = MAXN (8-core, 15W)

# Lock clocks to maximum
sudo jetson_clocks

# Verify
sudo tegrastats
```

### Model Optimization

**For faster ASR:**
- Use QuartzNet instead of Conformer (less accurate but 2x faster)

**For lower memory:**
- Enable only one TTS voice
- Disable NLP service
- Set `riva_model_deploy_memlock=false`

### Expected Performance

**On Jetson AGX Xavier:**
- ASR latency: ~0.29 RTF (real-time factor)
- TTS latency: <0.5 seconds
- Memory usage: ~2-3GB GPU, ~1GB RAM
- First request: ~2-3 seconds (model warmup)
- Subsequent: <1 second

---

## Persistence

### Auto-start Riva on Boot

```bash
# Create systemd service
sudo nano /etc/systemd/system/riva-speech.service

# Add content:
[Unit]
Description=Riva Speech Server
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=nvidia
WorkingDirectory=/mnt/nvme/adrian/riva_quickstart_arm64_v2.19.0
ExecStart=/bin/bash /mnt/nvme/adrian/riva_quickstart_arm64_v2.19.0/riva_start.sh
ExecStop=/usr/bin/docker stop riva-speech
Restart=always

[Install]
WantedBy=multi-user.target

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable riva-speech
sudo systemctl start riva-speech

# Check status
sudo systemctl status riva-speech
```

---

## Additional Resources

- [Riva Documentation](https://docs.nvidia.com/deeplearning/riva/user-guide/docs/)
- [Riva on Jetson](https://docs.nvidia.com/deeplearning/riva/user-guide/docs/quick-start-guide-jetson.html)
- [NGC Catalog](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/riva/resources/riva_quickstart_arm64)
- [Riva Forum](https://forums.developer.nvidia.com/c/ai/riva/)

---

**Next:** [AWS_BEDROCK.md](AWS_BEDROCK.md) - Configure AWS Bedrock
