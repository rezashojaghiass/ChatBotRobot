#!/bin/bash

################################################################################
# Simple Voice Assistant Script
################################################################################
# 
# A conversational AI powered by Llama 70B with speech input/output
# Uses RIVA for ASR (Automatic Speech Recognition) and TTS (Text-to-Speech)
# 
# Features:
#   - Natural conversation with Llama 70B LLM
#   - No RAG context (pure LLM conversation)
#   - Buzz Lightyear persona greets users with their name (Adrian by default)
#   - Voice Activity Detection (VAD) with 3-second grace period
#   - Automatic response via speaker
#
# Requirements:
#   - AWS Bedrock access configured (aws configure)
#   - RIVA services running (./scripts/start_riva.sh)
#   - Python dependencies installed (pip3 install -r requirements.txt)
#
################################################################################

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# Configuration Variables
# ============================================================================
# These variables store the user-provided options or defaults
DURATION=10
LLM="llama70b"
OUTPUT_DEVICE=""
NO_VAD=""

# Script directory - get absolute path to ChatBotRobot root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ============================================================================
# Function: usage()
# ============================================================================
# Display help text with usage examples and available options
usage() {
    cat << EOF
${BLUE}🤖 Simple Voice Assistant${NC}

A conversational AI powered by Llama 70B with speech input/output

${GREEN}Usage:${NC}
    ./voice_assistant.sh [options]

${GREEN}Options:${NC}
    --llm <model>           LLM to use: 'llama' (8B-fast), 'llama70b' (70B), 'claude' (default: llama70b)
    --duration <secs>       Max recording time per message (default: 10)
    --no-vad                Disable voice activity detection (record full duration)
    --output-device <N>     Audio output device index (default: 0, run: python3 list_audio_devices.py)
    --help                  Display this help message

${GREEN}Examples:${NC}
    # Default - chat with Llama 70B
    ./voice_assistant.sh

    # Use faster Llama 8B model
    ./voice_assistant.sh --llm llama

    # Use Claude 3.5 Sonnet
    ./voice_assistant.sh --llm claude

    # Extended recording time for longer messages
    ./voice_assistant.sh --duration 15

${GREEN}Notes:${NC}
    • VAD (Voice Activity Detection): 3-second grace period, then auto-stops after 0.5s silence
    • Just speak naturally - no special commands needed
    • Type Ctrl+C to exit the conversation
    • Ensure AWS credentials are configured (aws configure)
    • RIVA services must be running (start_riva.sh)

EOF
}

# ============================================================================
# Function: Parse command-line arguments
# ============================================================================
# Loop through all provided arguments and set configuration variables
# Supports: --llm, --duration, --no-vad, --output-device, --help
while [[ $# -gt 0 ]]; do
    case $1 in
        --llm)
            LLM="$2"
            shift 2
            ;;
        --duration)
            DURATION="$2"
            shift 2
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

# ============================================================================
# Validation: Check if voice_chat_riva_aws.py exists
# ============================================================================
# Ensure we can find the main Python application
if [ ! -f "$SCRIPT_DIR/src/voice_chat_riva_aws.py" ]; then
    echo -e "${YELLOW}Error: Could not find voice_chat_riva_aws.py${NC}"
    echo "Make sure you're running this script from the ChatBotRobot directory"
    exit 1
fi

# ============================================================================
# Health Check: Verify RIVA services are accessible
# ============================================================================
# Try to connect to RIVA gRPC server; warn if not available
# User can continue anyway, but RIVA must be running for actual use
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

# ============================================================================
# Display Configuration Summary
# ============================================================================
# Show the user what settings will be used for this session
echo -e "${GREEN}🎙️  Voice Assistant Configuration:${NC}"
echo "  LLM: $LLM"
echo "  Max Recording: ${DURATION}s"
echo "  VAD: $([ -z "$NO_VAD" ] && echo 'Enabled (3s grace + 0.5s silence)' || echo 'Disabled')"
echo "  Output Device: $OUTPUT_DEVICE"
echo ""

# ============================================================================
# Build Python Command
# ============================================================================
# Construct the full command with all parameters to pass to voice_chat_riva_aws.py
# This is a conversational chat mode (not quiz, no RAG) with Buzz Lightyear persona
CMD="python3 $SCRIPT_DIR/src/voice_chat_riva_aws.py"
CMD="$CMD --duration $DURATION"
CMD="$CMD --mode chat"
CMD="$CMD --llm $LLM"
if [ -n "$OUTPUT_DEVICE" ]; then
    CMD="$CMD --output-device $OUTPUT_DEVICE"
fi

if [ -n "$NO_VAD" ]; then
    CMD="$CMD $NO_VAD"
fi

# ============================================================================
# Launch Voice Assistant
# ============================================================================
# Start the main Python application in chat mode
# User can now speak naturally and receive AI responses via speaker
echo -e "${BLUE}🎤 Starting Voice Assistant...${NC}"
echo -e "${YELLOW}Speak naturally. I'm listening!${NC}"
echo -e "${YELLOW}Press Ctrl+C to exit.${NC}"
echo ""

eval $CMD
