# 🤖 ChatBotRobot - Voice-Enabled AI Assistant for Jetson Xavier

An interactive, real-time voice-controlled AI system featuring quiz mode and conversational chat, powered by NVIDIA Riva ASR/TTS and AWS Bedrock LLMs, deployed on Jetson AGX Xavier edge device.

## 🎯 Features

- **Real-time Voice Interaction**: Speech-to-Text → AI Response → Text-to-Speech pipeline
- **Multiple AI Models**: Llama 3 8B, Llama 3.1 70B, Claude 3.5 Sonnet support
- **Madagascar Quiz Mode**: Interactive quiz with progressive difficulty and RAG-enhanced context
- **Voice Activity Detection (VAD)**: Auto-stops recording when user stops speaking (0.5s silence)
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
nvidia-riva-client==2.19.1
boto3==1.37.38
pyaudio
sentence-transformers
numpy
```

### Cloud Services
- **AWS Account** with Bedrock access
- **IAM User** with `AmazonBedrockFullAccess` policy

## 🚀 Quick Start

```bash
# 1. Clone repository
git clone https://github.com/rezashojaghiass/ChatBotRobot.git
cd ChatBotRobot

# 2. Run setup script
./scripts/setup.sh

# 3. Configure AWS credentials
aws configure

# 4. Start Riva server
./scripts/start_riva.sh

# 5. Run Madagascar quiz
cd src
python3 voice_chat_riva_aws.py --duration 10 --mode madagascar_quiz --llm llama70b --rag --quiz_len 6 --topic "the Madagascar movie"
```

## 📖 Detailed Setup Guide

See [docs/SETUP.md](docs/SETUP.md) for complete installation instructions including:
- Initial Jetson Xavier setup
- VNC remote desktop configuration
- Riva ASR/TTS installation
- AWS Bedrock configuration
- Audio device setup

## 💻 Usage Examples

### Chat Mode (Buzz Lightyear)
```bash
python3 voice_chat_riva_aws.py --duration 10 --mode chat --llm llama70b
```

### Madagascar Quiz Mode
```bash
# With RAG (uses subtitles)
python3 voice_chat_riva_aws.py --duration 10 --mode madagascar_quiz --llm llama70b --rag --quiz_len 10 --topic "the Madagascar movie"

# Without RAG (basic facts)
python3 voice_chat_riva_aws.py --duration 10 --mode madagascar_quiz --llm llama --topic "the Madagascar movie"
```

### Custom Topic Quiz (e.g., Space Science)
```bash
# Galaxy science quiz with custom subtitle file
python3 voice_chat_riva_aws.py --subtitle ../data/Galaxy_Science.srt --rag --mode madagascar_quiz --llm llama70b --topic "space and galaxies" --quiz_len 10

# Toy Story quiz
python3 voice_chat_riva_aws.py --subtitle ../data/Toy_Story.srt --rag --mode madagascar_quiz --llm llama70b --topic "Toy Story movie" --quiz_len 10
```

### Custom Announcements
```bash
python3 scripts/speak.py "Bravo Adrian for tidying up your toys!"
```

### All CLI Options
```bash
--duration 10              # Max recording time (seconds)
--mode chat               # Mode: chat or madagascar_quiz
--llm llama70b            # LLM: llama (8B), llama70b (70B), claude
--rag                     # Enable RAG with subtitle context
--quiz_len 10             # Number of quiz questions
--kid_name Adrian         # Child's name
--topic "Madagascar movie" # Quiz topic (any subject!)
--no-vad                  # Disable voice activity detection
--subtitle <path>         # Custom subtitle file path
```

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
# Check CUDA
nvidia-smi
# Verify Docker can access GPU
docker run --rm --gpus all nvidia/cuda:11.4.0-base-ubuntu20.04 nvidia-smi
```

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
