#!/usr/bin/env python3
"""
Audio Recording Script - Records voice to a WAV file
Uses PyAudio to capture audio from your RODE Wireless GO microphone
"""

import pyaudio
import wave
import sys
from datetime import datetime

def record_audio(filename=None, duration=10, sample_rate=44100, chunk_size=1024):
    """
    Records audio from the default audio device to a WAV file.
    
    Args:
        filename (str): Output WAV file path. If None, uses timestamp.
        duration (int): Recording duration in seconds (default: 10)
        sample_rate (int): Sample rate in Hz (default: 44100)
        chunk_size (int): Buffer size (default: 1024)
    """
    
    # Default filename with timestamp
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
    
    # Audio parameters
    channels = 2  # Stereo (USB device requires stereo)
    sample_width = 2  # 16-bit audio
    
    print(f"🎤 Recording Audio")
    print(f"  Duration: {duration} seconds")
    print(f"  Sample Rate: {sample_rate} Hz")
    print(f"  Output: {filename}")
    print()
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    try:
        # Open audio stream
        stream = p.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk_size
        )
        
        print("Recording... (Press Ctrl+C to stop)")
        
        # Collect audio frames
        frames = []
        num_frames = int(sample_rate / chunk_size * duration)
        
        for i in range(num_frames):
            try:
                data = stream.read(chunk_size, exception_on_overflow=False)
                frames.append(data)
                
                # Progress indicator
                progress = (i + 1) / num_frames * 100
                print(f"  Progress: {progress:.1f}%", end='\r')
            except KeyboardInterrupt:
                print("\n✋ Recording stopped by user")
                break
        
        print()
        
        # Stop stream
        stream.stop_stream()
        stream.close()
        
        # Write to WAV file
        print(f"Saving to {filename}...")
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))
        
        file_size_kb = len(b''.join(frames)) / 1024
        print(f"✅ Recording saved successfully!")
        print(f"  File: {filename}")
        print(f"  Size: {file_size_kb:.1f} KB")
        
        return filename
        
    finally:
        p.terminate()


if __name__ == "__main__":
    # Command line arguments
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = None
    
    if len(sys.argv) > 2:
        try:
            duration = int(sys.argv[2])
        except ValueError:
            duration = 10
    else:
        duration = 10
    
    # Record audio
    record_audio(filename=filename, duration=duration)
