#!/usr/bin/env python3
"""
Simple TTS utility script for one-off announcements.
Usage: python3 speak.py "Message to speak"

Fixed: Uses PyAudio instead of deprecated riva.client.AudioPlayer
"""

import sys
import riva.client
import pyaudio

def speak(text, voice="English-US.Male-1", sample_rate=22050):
    """Speak text using Riva TTS."""
    try:
        # Connect to Riva server
        auth = riva.client.Auth(uri='localhost:50051')
        tts_service = riva.client.SpeechSynthesisService(auth)
        
        # Synthesize speech
        print(f"Speaking: {text}")
        resp = tts_service.synthesize(
            text=text,
            voice_name=voice,
            language_code="en-US",
            encoding=riva.client.AudioEncoding.LINEAR_PCM,
            sample_rate_hz=sample_rate
        )
        
        # Play audio using PyAudio (AudioPlayer is deprecated)
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            output=True
        )
        stream.write(resp.audio)
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        print("Done!")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure Riva server is running:")
        print("  cd /mnt/nvme/adrian/riva_quickstart_arm64_v2.19.0")
        print("  bash riva_start.sh")
        return 1
    
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 speak.py 'Text to speak'")
        print("Example: python3 speak.py 'Hello Adrian!'")
        sys.exit(1)
    
    message = ' '.join(sys.argv[1:])
    sys.exit(speak(message))
