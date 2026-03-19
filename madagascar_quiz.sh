#!/bin/bash

# Madagascar Quiz Runner Script
# Interactive voice-based quiz using AWS Bedrock LLM and RIVA ASR/TTS
# Usage: ./madagascar_quiz.sh [options]

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
QUIZ_LENGTH=5
LLM="llama70b"
DURATION=10
TOPIC="the Madagascar movie"
RAG_ENABLED=true
OUTPUT_DEVICE=""
NO_VAD=""

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Function to display usage
usage() {
    cat << EOF
${BLUE}🎬 Madagascar Quiz Runner${NC}

Interactive voice-based quiz with AI responses using RIVA and AWS Bedrock

${GREEN}Usage:${NC}
    ./madagascar_quiz.sh [options]

${GREEN}Options:${NC}
    --quiz-len <N>          Number of questions (default: 5)
    --llm <model>           LLM to use: 'llama' (8B), 'llama70b' (70B), 'claude' (default: llama70b)
    --duration <secs>       Max recording time (default: 10)
    --topic <topic>         Quiz topic (default: "the Madagascar movie")
    --no-rag                Disable RAG context from subtitles
    --no-vad                Disable voice activity detection (record full duration)
    --output-device <N>     Audio output device index (default: 0, run: python3 list_audio_devices.py)
    --help                  Display this help message

${GREEN}Examples:${NC}
    # Basic quiz with defaults
    ./madagascar_quiz.sh

    # 10 questions with Claude LLM
    ./madagascar_quiz.sh --quiz-len 10 --llm claude

    # Custom topic without RAG
    ./madagascar_quiz.sh --topic "Penguins of Madagascar" --no-rag

    # Extended recording time with fast model
    ./madagascar_quiz.sh --duration 15 --llm llama

${GREEN}Notes:${NC}
    • VAD (Voice Activity Detection): 3-second grace period, then auto-stops after 0.5s silence
    • RAG uses Madagascar.srt subtitle file for context
    • Ensure AWS credentials are configured (aws configure)
    • RIVA services must be running (start_riva.sh)

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --quiz-len)
            QUIZ_LENGTH="$2"
            shift 2
            ;;
        --llm)
            LLM="$2"
            shift 2
            ;;
        --duration)
            DURATION="$2"
            shift 2
            ;;
        --topic)
            TOPIC="$2"
            shift 2
            ;;
        --no-rag)
            RAG_ENABLED=false
            shift
            ;;
        --no-vad)
            NO_VAD="--no-vad"
            shift
            ;;
        --output-device)
            OUTPUT_DEVICE="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo -e "${YELLOW}Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

# Verify we're in the right directory
if [ ! -f "$SCRIPT_DIR/src/voice_chat_riva_aws.py" ]; then
    echo -e "${YELLOW}Error: Could not find voice_chat_riva_aws.py${NC}"
    echo "Make sure you're running this script from the ChatBotRobot directory"
    exit 1
fi

# Check if RIVA is running
echo -e "${BLUE}🔍 Checking RIVA services...${NC}"
if ! timeout 2 python3 -c "import grpc; grpc.aio.secure_channel('localhost:50051', grpc.ssl_channel_credentials())" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  RIVA services may not be running${NC}"
    echo "Start RIVA with: ./scripts/start_riva.sh"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Display configuration
echo -e "${GREEN}📋 Quiz Configuration:${NC}"
echo "  Questions: $QUIZ_LENGTH"
echo "  LLM: $LLM"
echo "  Topic: $TOPIC"
echo "  RAG Context: $([ "$RAG_ENABLED" = true ] && echo 'Enabled' || echo 'Disabled')"
echo "  VAD: $([ -z "$NO_VAD" ] && echo 'Enabled (3s grace + 0.5s silence)' || echo 'Disabled')"
echo "  Max Recording: ${DURATION}s"
echo "  Output Device: $OUTPUT_DEVICE"
echo ""

# Build the command
CMD="python3 $SCRIPT_DIR/src/voice_chat_riva_aws.py"
CMD="$CMD --duration $DURATION"
CMD="$CMD --mode madagascar_quiz"
CMD="$CMD --llm $LLM"
CMD="$CMD --quiz_len $QUIZ_LENGTH"
CMD="$CMD --topic \"$TOPIC\""
if [ -n "$OUTPUT_DEVICE" ]; then
    CMD="$CMD --output-device $OUTPUT_DEVICE"
fi

if [ "$RAG_ENABLED" = true ]; then
    CMD="$CMD --rag"
fi

if [ -n "$NO_VAD" ]; then
    CMD="$CMD $NO_VAD"
fi

# Run the quiz
echo -e "${BLUE}🎤 Starting Madagascar Quiz...${NC}"
echo -e "${YELLOW}Speak clearly. Wait for the question, then give your answer.${NC}"
echo -e "${YELLOW}The system will wait 3 seconds before auto-stopping after you finish speaking.${NC}"
echo ""

eval $CMD
