#!/usr/bin/env python3
"""
Simple TTS utility script for one-off announcements.
Usage: python3 speak.py "Message to speak"

Fixed: Uses PyAudio with device 1 and 48000Hz sample rate
"""

import sys
import riva.client
import pyaudio

def speak(text, voice="English-US.Male-1", sample_rate=48000):
    """Speak text using Riva TTS."""
    try:
        # Connect to Riva server
        auth = riva.client.Auth(uri='localhost:50051')
        tts_service = riva.client.SpeechSynthesisService(auth)
        
        # Synthesize speech at 48000Hz (USB Audio native rate)
        print(f"Speaking: {text}")
        resp = tts_service.synthesize(
            text=text,
            voice_name=voice,
            language_code="en-US",
            encoding=riva.client.AudioEncoding.LINEAR_PCM,
            sample_rate_hz=sample_rate
        )
        
        # Play audio using PyAudio on KT USB Audio (device 0)
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            output=True,
            output_device_index=0  # KT USB Audio
        )
        stream.write(resp.audio)
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        print("Done!")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure Riva server is running:")
        print("  cd /mnt/nvme/reza_backup/riva_quickstart_arm64_v2.14.0")
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
