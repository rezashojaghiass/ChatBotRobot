# Quick Start Guide

Get your ChatBot Robot running in 5 minutes!

## 🔄 Coming Back After a Break?

**Quick reminder of where things are:**

```bash
# 1. Go to your repository
cd /mnt/nvme/adrian/ChatBotRobot

# 2. Check if Riva is running
docker ps | grep riva-speech

# 3. If not running, start it:
./scripts/start_riva.sh

# 4. Run the voice chat
cd src
python3 voice_chat_riva_aws.py --mode chat --llm llama70b

# That's it! 🚀
```

---

## Prerequisites

- NVIDIA Jetson AGX Xavier with JetPack 5.x
- Microphone (USB recommended)
- Speaker
- Internet connection
- AWS account with Bedrock access

## Step 1: Clone Repository

```bash
cd /mnt/nvme/adrian
git clone https://github.com/rezashojaghiass/ChatBotRobot.git
cd ChatBotRobot
```

## Step 2: Install Dependencies

```bash
# Install Python packages
pip3 install -r requirements.txt

# This installs:
# - nvidia-riva-client (Speech AI)
# - boto3 (AWS SDK)
# - sentence-transformers (RAG)
# - pyaudio (Audio I/O)
```

## Step 3: Set Up Riva

```bash
# Download and install Riva (one-time setup)
# Follow: docs/RIVA_GUIDE.md

# Or use existing installation:
cd /mnt/nvme/adrian/riva_quickstart_arm64_v2.19.0
bash riva_start.sh

# Wait for "Server ready on port 50051"
```

## Step 4: Configure AWS

```bash
# Configure AWS credentials
aws configure
# Enter:
#   Access Key ID: AKIA...
#   Secret Key: ...
#   Region: us-east-1
#   Format: json

# Enable Bedrock models at:
# https://console.aws.amazon.com/bedrock/
# Enable: Llama 3 8B, Llama 3.1 70B
```

## Step 5: Test Audio

```bash
cd src

# List audio devices
python3 list_audio_devices.py

# Test microphone
arecord -f S16_LE -r 16000 -c 1 -d 3 test.wav && aplay test.wav && rm test.wav
# Speak and you should hear yourself

# Test TTS
cd ../scripts
./speak.py "Hello Adrian!"
# Should hear: "Hello Adrian!" in male voice
```

## Step 6: Run Chat Mode

```bash
# Always work from the repository directory
cd /mnt/nvme/adrian/ChatBotRobot/src

# Basic chat with Buzz Lightyear
python3 voice_chat_riva_aws.py --duration 10 --mode chat --llm llama

# Conversation flow:
# 1. Speak: "Hello Buzz!"
# 2. Wait ~2 seconds
# 3. Buzz responds (text + voice)
# 4. Repeat

# Press Ctrl+C to exit
```

## Step 7: Run Quiz Mode (Optional)

```bash
# Still in /mnt/nvme/adrian/ChatBotRobot/src

# Download Madagascar subtitles (see data/README.md)
# Save to: ../data/Madagascar.srt

# Run quiz with RAG
python3 voice_chat_riva_aws.py \
    --duration 10 \
    --mode madagascar_quiz \
    --llm llama70b \
    --rag \
    --quiz_len 10 \
    --topic "the Madagascar movie"

# Quiz flow:
# 1. Buzz asks a question
# 2. Speak your answer
# 3. Buzz grades and gives feedback
# 4. Next question
# ...repeat
```

## Common Commands

### Chat Modes

```bash
# Fast chat (Llama 8B)
python3 voice_chat_riva_aws.py --mode chat --llm llama

# Smart chat (Llama 70B)
python3 voice_chat_riva_aws.py --mode chat --llm llama70b

# Creative chat (Claude)
python3 voice_chat_riva_aws.py --mode chat --llm claude
```

### Quiz Modes

```bash
# Quiz with RAG (accurate questions)
python3 voice_chat_riva_aws.py --mode madagascar_quiz --llm llama70b --rag --topic "the Madagascar movie"

# Quiz without RAG (general questions)
python3 voice_chat_riva_aws.py --mode madagascar_quiz --llm llama --topic "the Madagascar movie"

# Short quiz (5 questions)
python3 voice_chat_riva_aws.py --mode madagascar_quiz --llm llama70b --quiz_len 5 --topic "the Madagascar movie"

# Custom name
python3 voice_chat_riva_aws.py --mode madagascar_quiz --kid_name John --llm llama70b --topic "the Madagascar movie"

# Galaxy science quiz with custom subtitle
python3 voice_chat_riva_aws.py --subtitle ../data/Galaxy_Science.srt --rag --mode madagascar_quiz --llm llama70b --topic "space and galaxies"

# Toy Story quiz
python3 voice_chat_riva_aws.py --subtitle ../data/Toy_Story.srt --rag --mode madagascar_quiz --llm llama70b --topic "Toy Story movie"
```

### Audio Settings

```bash
# Without VAD (manual stop)
python3 voice_chat_riva_aws.py --no-vad --duration 5

# Longer recording time
python3 voice_chat_riva_aws.py --duration 15

# Custom subtitle file
python3 voice_chat_riva_aws.py --subtitle /path/to/subtitles.srt --rag
```

### Utility Scripts

**Important: Run these from the repository directory!**

```bash
# Always start from the repo
cd /mnt/nvme/adrian/ChatBotRobot

# Speak a message
./scripts/speak.py "Bravo Adrian!"

# Start Riva server
./scripts/start_riva.sh

# Stop Riva server
./scripts/stop_riva.sh

# Test ASR
python3 src/asr_test.py

# List audio devices
python3 src/list_audio_devices.py
```

## Troubleshooting

### "Connection refused" Error
```bash
# Riva server not running
./scripts/start_riva.sh
# Wait 10 seconds for models to load
```

### "AccessDeniedException" Error
```bash
# AWS credentials not configured
aws configure

# Or check IAM permissions
# Go to: AWS Console → IAM → Users → bedrock-user
# Ensure: AmazonBedrockFullAccess policy attached
```

### No Audio / No Microphone
```bash
# Check audio devices
python3 src/list_audio_devices.py
arecord -l

# See detailed guide:
cat docs/AUDIO_SETUP.md
```

### Poor Audio Quality
```bash
# Set Jetson to max performance
sudo nvpmodel -m 0
sudo jetson_clocks

# Check microphone volume
alsamixer
# Increase Master and Mic volumes
```

### Quiz Questions Don't Match Movie
```bash
# Need RAG enabled
python3 voice_chat_riva_aws.py --rag --mode madagascar_quiz

# Need subtitle file
# See: data/README.md for how to get subtitles
```

## Next Steps

- **Full Documentation**: See [docs/SETUP.md](docs/SETUP.md) for complete setup
- **Riva Guide**: [docs/RIVA_GUIDE.md](docs/RIVA_GUIDE.md) for Riva installation
- **AWS Setup**: [docs/AWS_BEDROCK.md](docs/AWS_BEDROCK.md) for Bedrock configuration
- **RAG Details**: [docs/RAG_IMPLEMENTATION.md](docs/RAG_IMPLEMENTATION.md) for how RAG works
- **Audio Config**: [docs/AUDIO_SETUP.md](docs/AUDIO_SETUP.md) for audio troubleshooting

## CLI Reference

```bash
python3 voice_chat_riva_aws.py [OPTIONS]

Options:
  --duration SECONDS       Max recording time (default: 10)
  --mode MODE             'chat' or 'madagascar_quiz'
  --llm MODEL             'llama' (8B), 'llama70b' (70B), or 'claude'
  --rag                   Enable RAG with subtitles
  --quiz_len N            Number of quiz questions (default: 10)
  --kid_name NAME         Child's name (default: Adrian)
  --topic TOPIC           Quiz topic (default: "the Madagascar movie")
  --no-vad                Disable voice activity detection
  --subtitle PATH         Custom subtitle file path

Examples:
  # Chat with Llama 8B
  python3 voice_chat_riva_aws.py --mode chat --llm llama
  
  # Madagascar quiz with RAG
  python3 voice_chat_riva_aws.py --mode madagascar_quiz --llm llama70b --rag --topic "the Madagascar movie"
  
  # Galaxy science quiz
  python3 voice_chat_riva_aws.py --subtitle ../data/Galaxy_Science.srt --mode madagascar_quiz --llm llama70b --rag --topic "space and galaxies" --quiz_len 5
```

## Performance Tips

1. **Use Llama 8B for chat** (fast, responsive)
2. **Use Llama 70B for quiz** (accurate, smart)
3. **Enable VAD** for natural conversations (auto-stops when you stop speaking)
4. **Set Jetson to max performance**:
   ```bash
   sudo nvpmodel -m 0
   sudo jetson_clocks
   ```
5. **Use wired microphone** (lower latency than Bluetooth)

## Cost Estimate

**Typical usage (1 hour/day):**
- Chat mode (Llama 8B): ~$5-10/month
- Quiz mode (Llama 70B): ~$15-25/month

**Per session:**
- 10-minute chat: ~$0.02-0.05
- 10-question quiz: ~$0.05-0.10

See [docs/AWS_BEDROCK.md](docs/AWS_BEDROCK.md) for detailed pricing.

## Support

- **Issues**: https://github.com/rezashojaghiass/ChatBotRobot/issues
- **Documentation**: See [docs/](docs/) folder
- **Examples**: See [README.md](README.md)

---

**Enjoy your ChatBot Robot! 🤖🚀**

*To infinity and beyond!*
