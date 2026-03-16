# 🤖 ChatBotRobot - Voice-Enabled AI Assistant for Jetson Xavier

An interactive, real-time voice-controlled AI system featuring quiz mode and conversational chat, powered by NVIDIA Riva ASR/TTS and AWS Bedrock LLMs, deployed on Jetson AGX Xavier edge device.

## 🎯 Features

- **Real-time Voice Interaction**: Speech-to-Text → AI Response → Text-to-Speech pipeline
- **Multiple AI Models**: Llama 3 8B, Llama 3.1 70B, Claude 3.5 Sonnet support
- **Madagascar Quiz Mode**: Interactive quiz with progressive difficulty and RAG-enhanced context
- **Voice Activity Detection (VAD)**: Auto-stops recording after user finishes speaking (3s grace period, then 0.5s silence threshold)
- **RAG (Retrieval-Augmented Generation)**: Uses movie subtitles for accurate context
- **Buzz Lightyear Persona**: Enthusiastic, kid-friendly character interactions
- **Edge AI Deployment**: Runs entirely on Jetson Xavier with <2s latency

## 📋 Table of Contents

- [Hardware Requirements](#hardware-requirements)
- [Software Requirements](#software-requirements)
- [Quick Start](#quick-start)
- [Detailed Setup Guide](#detailed-setup-guide)
- [Usage Examples](#usage-examples)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🖥️ Hardware Requirements

- **NVIDIA Jetson AGX Xavier** (8GB unified memory)
- **Microphone**: Rode Wireless GO II or any USB audio device
- **Speaker**: Built-in or USB speaker
- **Storage**: 250GB+ NVMe SSD recommended (models + datasets)
- **Network**: Internet connection for AWS Bedrock API

## 📦 Software Requirements

### Core System
- **JetPack**: 5.x (L4T R35.6.3)
- **CUDA**: 11.4
- **Docker**: 20.10+
- **Python**: 3.8+

### Python Libraries
```bash
nvidia-riva-client==2.14.0
boto3==1.37.38
pyaudio
sentence-transformers
numpy
```

### Cloud Services
- **AWS Account** with Bedrock access
- **IAM User** with `AmazonBedrockFullAccess` policy

## 🚀 Quick Start

**Prerequisites**: 
- Docker must be installed and running ✓ (Already on your system)
- NVIDIA Docker runtime configured ✓ (Already enabled in daemon.json)
- Riva models downloaded ✓ (Already in /mnt/nvme/reza_backup/riva_quickstart_arm64_v2.14.0)
- Python dependencies installed ✓

### First Time Setup (One-time only)

```bash
# 1. Clone repository
git clone https://github.com/rezashojaghiass/ChatBotRobot.git
cd ChatBotRobot

# 2. Install Python dependencies
pip3 install -r requirements.txt

# 3. Set Jetson to MAXN power mode for optimal GPU memory allocation
sudo nvpmodel -m 0
sudo jetson_clocks

# 4. Configure AWS credentials
aws configure

# 5. Install NVIDIA Riva (see docs/RIVA_GUIDE.md for detailed instructions)
# - Download Riva QuickStart for ARM64
# - Configure config.sh with desired models
# - Run riva_init.sh to download models (~10GB)
# - This is a one-time setup
# ✓ ALREADY DONE - Located at: /mnt/nvme/reza_backup/riva_quickstart_arm64_v2.14.0

# 6. Configure speaker volume
aplay -l  # List audio devices to find card number
amixer -c 1 set Headphone 100% unmute  # Replace '1' with your card number
```

**System Info (Your Setup)**
- JetPack: R35.6.3 ✓
- Docker: 26.1.3 with NVIDIA runtime ✓
- GPU: Confirmed working with TensorRT acceleration ✓
- Storage: 2.9GB internal | 137GB /mnt/nvme ✓

### Running the Quiz (Every Time)

#### Step 1: Start Riva Docker Container with GPU

```bash
# Navigate to Riva installation directory
cd /mnt/nvme/reza_backup/riva_quickstart_arm64_v2.14.0

# Start the container with GPU enabled
bash start_riva_v2_14.sh
# This runs the official startup script which:
# - Removes any existing riva-speech container
# - Starts new container with --gpus all flag (GPU acceleration enabled)
# - Maps ports: gRPC (50051), HTTP (50000)
# - Mounts prebuilt models from /data/models
# - Enables ASR (Speech-to-Text) and TTS (Text-to-Speech) services
# - Disables NLP service to save GPU memory
# - Expected output: "✓ Riva server is running with GPU"
```

**Alternative: Manual Docker Command (if script not available)**
```bash
RIVA_DIR="/mnt/nvme/reza_backup/riva_quickstart_arm64_v2.14.0"
MODEL_REPO="$RIVA_DIR/model_repository/prebuilt"
IMAGE="nvcr.io/nvidia/riva/riva-speech:2.14.0-l4t-aarch64"
CONTAINER="riva-speech"
PORT_GRPC=50051
PORT_HTTP=50000

# Remove any existing container
sudo docker rm -f $CONTAINER &> /dev/null

# Start with GPU enabled
sudo docker run -d \
        --gpus all \
        --init \
        --ipc=host \
        --device /dev/bus/usb \
        --device /dev/snd \
        -p $PORT_GRPC:$PORT_GRPC \
        -p $PORT_HTTP:$PORT_HTTP \
        -v $MODEL_REPO:/data/models \
        --ulimit memlock=-1 \
        --ulimit stack=67108864 \
        --name $CONTAINER \
        $IMAGE \
        bash -c "/opt/riva/bin/start-riva --asr_service=true --tts_service=true --nlp_service=false"

# Wait and verify
sleep 5
docker ps | grep $CONTAINER && echo "✓ Riva server is running" || echo "✗ Failed"
```

#### Step 2: Verify Riva is Running

```bash
# Check container is up
docker ps | grep riva-speech

# Check logs to confirm models loaded
docker logs riva-speech 2>&1 | grep -E "successfully loaded|listening on"

# Expected output should include:
# - "successfully loaded 'conformer-en-US-asr-streaming'" 
# - "Riva Conversational AI Server listening on 0.0.0.0:50051"

# Test Riva is responding (Python test)
python3 << 'EOF'
import riva.client
auth = riva.client.Auth(uri="localhost:50051")
tts = riva.client.SpeechSynthesisService(auth)
resp = tts.synthesize("Hello, Riva is working", language_code="en-US", sample_rate_hz=16000)
print("✓ Riva TTS working!" if resp.audio else "✗ TTS failed")
EOF
```

#### Step 3: Run Madagascar Quiz

**Option A: Using the Bash Script (Recommended - Auto-detects speaker)**

```bash
# Navigate to ChatBotRobot directory
cd /home/reza/ChatBotRobot

# Run with default settings (Adrian, Llama 70B, 5 questions, RAG enabled)
bash scripts/madagascar_quiz.sh

# Run with custom settings
bash scripts/madagascar_quiz.sh --quiz-len 3 --llm llama70b --duration 10 --topic "space and galaxies"

# View all available options
bash scripts/madagascar_quiz.sh --help
```

**Script Benefits**:
- ✓ Automatically detects KT USB Audio speaker by name (survives USB replug)
- ✓ Auto-stops recording when user finishes speaking (VAD enabled)
- ✓ RAG-enhanced context from Madagascar movie subtitles
- ✓ Simplified command-line interface with sensible defaults

**Script Options**:
```
--quiz-len <N>          Number of questions (default: 5)
--llm <model>           LLM: 'llama' (8B), 'llama70b' (70B), 'claude' (default: llama70b)
--duration <secs>       Max recording time (default: 10)
--topic <topic>         Quiz topic (default: "the Madagascar movie")
--no-rag                Disable RAG (uses basic facts instead of subtitles)
--no-vad                Disable voice activity detection (record full duration)
--output-device <N>     Force specific audio device (rarely needed)
--help                  Show this help message
```

**Option B: Using Python Directly (Advanced)**

```bash
# Navigate to source code directory
cd /home/reza/ChatBotRobot/src

# Run with auto-detection (recommended)
python3 voice_chat_riva_aws.py --duration 10 --mode madagascar_quiz --llm llama70b --rag --quiz_len 6 --topic "the Madagascar movie"

# Note: Output device is automatically detected. No need to specify --output-device
# The system finds "KT USB Audio" by name, ensuring it works even after USB replug
```

#### Step 4: Stop Riva (When Done)

```bash
# Stop the Riva container gracefully
docker stop riva-speech

# Verify it's stopped
docker ps | grep riva-speech  # Should return nothing

# Remove container to save disk space (optional)
docker rm riva-speech
```

### Docker & GPU Verification Checklist

Before running Riva each time, verify:

```bash
# 1. Check system resources
tegrastats  # Should show ~6-8GB free RAM, CPU temps <50°C

# 2. Verify Docker is running
docker ps  # Should work without timeout

# 3. Confirm GPU acceleration is configured
docker info | grep nvidia  # Should show NVIDIA runtime

# 4. Check Jetson is in MAXN power mode (optimal for inference)
nvpmodel -q  # Should show "NVPmodel: ARMv8 Processor [mode: 0]"
# If not in mode 0, run: sudo nvpmodel -m 0 && sudo jetson_clocks

# 5. Check available disk space
df -h /mnt/nvme  # Should have >50GB free (for Riva models)
```

### Common Docker Issues

**Problem: "Cannot connect to Docker daemon"**
```bash
sudo systemctl restart docker
# Or manually start: sudo dockerd &
```

**Problem: "NVIDIA runtime not found"**
```bash
# This is already configured, but if needed:
docker run --rm --gpus all nvidia/cuda:11.4.0-base-ubuntu20.04 nvidia-smi
```

**Problem: Container exits immediately**
```bash
docker logs riva-speech  # Check error messages
# Most common: Out of memory - run: sudo jetson_clocks first
```

**Problem: "Port 50051 already in use"**
```bash
# Kill existing Riva
docker rm -f riva-speech
# Or use different ports: -p 50052:50051 -p 50001:50000
```


## 📖 Detailed Setup Guide

See [docs/SETUP.md](docs/SETUP.md) for complete installation instructions including:
- Initial Jetson Xavier setup
- VNC remote desktop configuration
- Riva ASR/TTS installation
- AWS Bedrock configuration
- Audio device setup

## 💻 Usage Examples

**Working directory: Always run from `/home/reza/ChatBotRobot/src`**

```bash
cd /home/reza/ChatBotRobot/src
```

### Chat Mode (Buzz Lightyear)
```bash
python3 voice_chat_riva_aws.py --duration 10 --mode chat --llm llama
```
**Tip**: Use `--llm llama` for fast responses (8B model), `--llm llama70b` for better quality

### Madagascar Quiz Mode
```bash
# With RAG (uses subtitles - RECOMMENDED for accuracy)
python3 voice_chat_riva_aws.py --duration 10 --mode madagascar_quiz --llm llama70b --rag --quiz_len 10 --topic "the Madagascar movie"

# Without RAG (uses LLM knowledge only)
python3 voice_chat_riva_aws.py --duration 10 --mode madagascar_quiz --llm llama --topic "the Madagascar movie"
```

### Custom Topic Quiz (e.g., Space Science)
```bash
# With RAG (knowledge file can be .srt, .pdf, or .txt)
python3 voice_chat_riva_aws.py --subtitle ../data/Galaxy_Science.pdf --rag --mode madagascar_quiz --llm llama70b --topic "space and galaxies" --quiz_len 10

# Without specifying file (auto-uses Madagascar.srt)
python3 voice_chat_riva_aws.py --rag --mode madagascar_quiz --llm llama70b --topic "any movie or topic" --quiz_len 10
```

### Custom Announcements
```bash
# Run from repository root
cd /home/reza/ChatBotRobot
python3 scripts/speak.py "Bravo Adrian for tidying up your toys!"
```

### All CLI Options
```bash
--duration 10              # Max recording time in seconds
--mode chat               # Mode: 'chat' or 'madagascar_quiz'
--llm llama               # LLM: 'llama' (8B-fast), 'llama70b' (70B-best), 'claude'
--rag                     # Enable RAG with subtitle context (recommended for quiz)
--quiz_len 10             # Number of quiz questions
--kid_name Adrian         # Child's name for personalization
--topic "Madagascar movie" # Quiz topic (movie title or subject)
--no-vad                  # Disable voice activity detection (always record full duration)
--subtitle <path>         # Knowledge file (.srt, .pdf, .txt) - defaults to Madagascar.srt
--output-device 25        # Audio output device index (run: python3 list_audio_devices.py)
```

**Note on Voice Activity Detection (VAD):**
- By default, the system has a 3-second grace period before VAD activates
- After the grace period, it waits for 0.5 seconds of silence to auto-stop recording
- This ensures you have time to think and speak naturally without interruption
- Use `--no-vad` flag if you prefer manual timing or want to record the full duration

## 📁 Project Structure

```
ChatBotRobot/
├── README.md                          # This file
├── docs/
│   ├── SETUP.md                       # Complete setup guide
│   ├── RIVA_GUIDE.md                  # Riva installation details
│   ├── AWS_BEDROCK.md                 # AWS configuration
│   ├── RAG_IMPLEMENTATION.md          # RAG system details
│   └── AUDIO_SETUP.md                 # Audio device configuration
├── src/
│   ├── voice_chat_riva_aws.py         # Main application
│   ├── voice_chat_riva.py             # Local LLM version
│   ├── asr_test.py                    # ASR testing script
│   └── list_audio_devices.py          # Audio device discovery
├── scripts/
│   ├── setup.sh                       # One-command setup
│   ├── start_riva.sh                  # Start Riva container
│   ├── stop_riva.sh                   # Stop Riva container
│   └── speak.py                       # TTS utility script
├── data/
│   └── Madagascar.720p.CHD.en.srt     # Movie subtitles (not included)
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Git ignore rules
└── LICENSE                            # MIT License

```

## 📚 Documentation

- **[SETUP.md](docs/SETUP.md)**: Complete installation guide from scratch
- **[RIVA_GUIDE.md](docs/RIVA_GUIDE.md)**: NVIDIA Riva setup and troubleshooting
- **[AWS_BEDROCK.md](docs/AWS_BEDROCK.md)**: AWS Bedrock configuration and model selection
- **[RAG_IMPLEMENTATION.md](docs/RAG_IMPLEMENTATION.md)**: How RAG works with embeddings
- **[AUDIO_SETUP.md](docs/AUDIO_SETUP.md)**: Audio device configuration and testing

## 🛠️ Troubleshooting

### Riva Container Won't Start

```bash
# Check GPU and memory usage on Jetson
sudo tegrastats

# Verify Jetson is in MAXN mode (required for Riva)
nvpmodel -q  # Should show "mode: 0"
# If not: sudo nvpmodel -m 0 && sudo jetson_clocks

# Check Docker can access GPU
docker run --rm --gpus all nvidia/cuda:11.4.0-base-ubuntu20.04 tegrastats --interval 1000 --logfile /dev/stdout

# View Riva container logs for errors
docker logs riva-speech 2>&1 | tail -50

# Check if port is already in use
sudo lsof -i :50051  # gRPC port
sudo lsof -i :50000  # HTTP port

# Force stop and remove existing container
docker rm -f riva-speech
```

### Docker & GPU Configuration Status

**Current Setup (Verified Working):**
```
✓ Docker Version: 26.1.3 with NVIDIA runtime enabled
✓ Architecture: aarch64 (ARM64) - Correct for Jetson Xavier
✓ NVIDIA Runtime: Configured as default in /etc/docker/daemon.json
✓ Docker Data Storage: /mnt/nvme/docker (NVMe drive)
✓ Riva Version: 2.14.0-l4t-aarch64 (Latest for JetPack R35)
✓ NVIDIA Runtime Configuration:
    - Default runtime: nvidia
    - Runtime path: nvidia-container-runtime
✓ Model Status: TensorRT + ONNX Runtime models fully loaded
✓ GPU Models Loaded:
    - Conformer ASR (Speech-to-Text)
    - FastPitch + HiFiGAN TTS (Text-to-Speech)
    - All running on GPU device 0 (Unified Memory)
```

### Riva Service Status Verification

### Audio Issues
```bash
# List audio devices
python3 src/list_audio_devices.py
# Test microphone
arecord -l
```

### AWS Bedrock Errors
- **ThrottlingException**: Increase cooldown or request quota increase
- **ValidationException**: Check model ID and inference profile

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for more solutions.

## 🎓 Technical Details

### Audio Device Detection & Playback Fixes

**Problem: Hardcoded USB Device Indices**
- USB audio devices (microphones, speakers) get assigned different device indices when unplugged/replugged
- Previous code used hardcoded indices, causing failures after USB reconnection
- Example: Speaker was at device 25, but code looked for device 0

**Solution: Name-Based Device Detection**
```python
# Instead of: output_device_index = 0  ❌ Fails after USB replug
# We now: find_output_device_by_name("KT USB Audio")  ✅ Always works
```
- Searches for devices by name substring match (case-insensitive)
- Returns device index at runtime
- Survives USB unplugs and replugs
- Implemented in both `voice_chat_riva_aws.py` and `riva_speech.py`

**Problem: Audio Playback at 2-3x Speed**
- Riva synthesizes mono audio (1 channel)
- Code was opening stereo stream (2 channels) and writing mono data to it
- PyAudio interpreted mono data as half the duration → 2x speed playback

**Solution: Use Mono for Playback**
```python
# Before: channels=2  ❌ Plays at 2x speed
# After:  channels=1  ✅ Normal speed
```
- Changed all TTS playback to mono (1 channel)
- Matches Riva's output format exactly
- No data loss or quality reduction

**Tested & Verified**
- ✅ Device detection survives USB replug
- ✅ Audio plays at normal speed (not 2-3x fast)
- ✅ Works with auto-detected device indices
- ✅ Both ChatBotRobot and Humanoid apps fixed

### Architecture
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Microphone │───▶│  Riva ASR    │───▶│   LLM       │
│ (48kHz)     │    │  (16kHz)     │    │  (Bedrock)  │
└─────────────┘    └──────────────┘    └─────────────┘
                                              │
                                              ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Speaker   │◀───│  Riva TTS    │◀───│   RAG       │
│             │    │  (Male-1)    │    │  (Optional) │
└─────────────┘    └──────────────┘    └─────────────┘
```

### Performance Metrics
- **ASR Latency**: ~0.29x real-time factor
- **LLM Response**: 1-3 seconds (Llama 70B)
- **TTS Latency**: <0.5 seconds
- **End-to-End**: <2 seconds total
- **Memory Usage**: ~3GB (Riva) + ~100MB (RAG)

### Technologies
- **Edge AI**: NVIDIA Jetson AGX Xavier
- **ASR/TTS**: NVIDIA Riva 2.14.0
- **LLMs**: Meta Llama 3/3.1, Anthropic Claude
- **Cloud**: AWS Bedrock
- **RAG**: Sentence-BERT (all-MiniLM-L6-v2)
- **Vector Search**: Cosine similarity with NumPy
- **Audio**: PyAudio, ALSA

## 📊 Resume/Portfolio Highlights

This project demonstrates:
- ✅ Large Language Models (LLMs) integration
- ✅ Retrieval-Augmented Generation (RAG)
- ✅ Real-time speech processing (ASR/TTS)
- ✅ Edge AI deployment on resource-constrained hardware
- ✅ AWS cloud services (Bedrock)
- ✅ Vector embeddings and semantic search
- ✅ Voice User Interface (VUI) design
- ✅ Production-grade error handling
- ✅ Docker containerization
- ✅ Python development (boto3, numpy, transformers)

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 👤 Author

**Reza Shojaghias**
- GitHub: [@rezashojaghiass](https://github.com/rezashojaghiass)
- Project: ChatBotRobot

## 🙏 Acknowledgments

- NVIDIA for Riva speech AI services
- AWS for Bedrock LLM access
- Meta for Llama models
- Anthropic for Claude models

## 📞 Support

For issues and questions:
- Open an [issue](https://github.com/rezashojaghiass/ChatBotRobot/issues)
- See [documentation](docs/)

---

**Star ⭐ this repo if you find it helpful!**
