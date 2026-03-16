#!/usr/bin/env python3
"""
Audio Playback Script - Plays WAV files through audio devices
Uses aplay for better hardware support and automatic sample rate conversion
"""

import pyaudio
import wave
import sys
import os
import subprocess


def play_audio(filename, device_index=None, use_aplay=True):
    """
    Plays a WAV file through the specified audio device.
    Uses aplay for better hardware compatibility and sample rate conversion.
    
    Args:
        filename (str): Path to WAV file to play
        device_index (int): PyAudio device index (optional, for fallback)
        use_aplay (bool): Use aplay command instead of PyAudio (default: True)
    """
    
    # Check file exists
    if not os.path.exists(filename):
        print(f"❌ Error: File '{filename}' not found")
        sys.exit(1)
    
    print(f"🔊 Audio Playback")
    print(f"  File: {filename}")
    if device_index is not None:
        print(f"  Device: {device_index}")
    else:
        print(f"  Device: Default (plughw:0,0 - KT USB Audio)")
    print()
    
    # Read WAV file info
    try:
        with wave.open(filename, 'rb') as wf:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            sample_rate = wf.getframerate()
            num_frames = wf.getnframes()
            duration = num_frames / sample_rate
            
            print(f"  Channels: {channels}")
            print(f"  Sample Rate: {sample_rate} Hz")
            print(f"  Duration: {duration:.1f} seconds")
            print()
        
        # Use aplay command for better hardware support
        if use_aplay:
            print("▶️  Playing with aplay...")
            
            # Build aplay command with sample rate conversion
            cmd = ['aplay', '-D', 'plughw:0,0', filename]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                print()
                if result.returncode == 0:
                    print("✅ Playback completed!")
                else:
                    print(f"⚠️  aplay returned code {result.returncode}")
                    if result.stderr:
                        print(f"Error: {result.stderr}")
                    print("\nFalling back to PyAudio...")
                    play_audio_pyaudio(filename, device_index)
            except FileNotFoundError:
                print("⚠️  aplay not found, falling back to PyAudio...")
                play_audio_pyaudio(filename, device_index)
        else:
            play_audio_pyaudio(filename, device_index)
                
    except wave.Error as e:
        print(f"❌ Error reading WAV file: {e}")
        sys.exit(1)
    except OSError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def play_audio_pyaudio(filename, device_index=None):
    """Fallback PyAudio playback method"""
    with wave.open(filename, 'rb') as wf:
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        sample_rate = wf.getframerate()
        num_frames = wf.getnframes()
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        try:
            # Open output stream
            stream = p.open(
                format=p.get_format_from_width(sample_width),
                channels=channels,
                rate=sample_rate,
                output=True,
                output_device_index=device_index,
                frames_per_buffer=1024
            )
            
            print("▶️  Playing with PyAudio...")
            
            # Play audio
            chunk_size = 1024
            frames_played = 0
            
            while True:
                data = wf.readframes(chunk_size)
                if not data:
                    break
                
                stream.write(data)
                frames_played += chunk_size
                
                # Progress indicator
                progress = min(100, (frames_played / num_frames) * 100)
                print(f"  Progress: {progress:.1f}%", end='\r')
            
            print()
            
            # Stop stream
            stream.stop_stream()
            stream.close()
            
            print("✅ Playback completed!")
            
        finally:
            p.terminate()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 play_audio.py <filename> [device_index]")
        print()
        print("Example:")
        print("  python3 play_audio.py test_recording.wav")
        print("  python3 play_audio.py test_recording.wav 0")
        print()
        print("Note: Uses aplay with plughw:0,0 (KT USB Audio) by default")
        print("      Supports automatic sample rate conversion")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    device_index = None
    if len(sys.argv) > 2:
        try:
            device_index = int(sys.argv[2])
        except ValueError:
            print(f"❌ Error: Device index must be a number")
            sys.exit(1)
    
    play_audio(filename, device_index)

