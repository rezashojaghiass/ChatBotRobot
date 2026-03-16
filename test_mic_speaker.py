#!/usr/bin/env python3
"""
Simple microphone record and speaker playback test
"""

import pyaudio
import numpy as np

def test_mic_speaker():
    p = pyaudio.PyAudio()
    
    # Device 5 = Microphone (APE hw:2,0)
    # Device 0 = Speaker (KT USB Audio)
    MIC_DEVICE = 5
    SPEAKER_DEVICE = 0
    SAMPLE_RATE = 48000
    DURATION = 5
    
    print("=" * 60)
    print("Microphone → Speaker Test")
    print("=" * 60)
    
    # Record
    print(f"\n🎤 Recording for {DURATION} seconds from device {MIC_DEVICE}...")
    print("   (Speak clearly into the microphone)\n")
    
    stream_in = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        input_device_index=MIC_DEVICE,
        frames_per_buffer=1024
    )
    
    frames = []
    for i in range(0, int(SAMPLE_RATE / 1024 * DURATION)):
        data = stream_in.read(1024, exception_on_overflow=False)
        frames.append(data)
        print(f"\r   Recording... {i+1}/{int(SAMPLE_RATE / 1024 * DURATION)}", end="")
    
    stream_in.stop_stream()
    stream_in.close()
    print("\n✅ Recording complete\n")
    
    # Play back
    audio_data = b''.join(frames)
    print(f"🔊 Playing back through device {SPEAKER_DEVICE}...")
    
    stream_out = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        output=True,
        output_device_index=SPEAKER_DEVICE,
        frames_per_buffer=1024
    )
    
    # Play in chunks
    chunk_size = 1024 * 2
    for i in range(0, len(audio_data), chunk_size):
        chunk = audio_data[i:i+chunk_size]
        stream_out.write(chunk)
        print(f"\r   Playing... {i//chunk_size + 1}/{len(audio_data)//chunk_size + 1}", end="")
    
    stream_out.stop_stream()
    stream_out.close()
    p.terminate()
    
    print("\n✅ Playback complete")
    print("\n" + "=" * 60)
    print("Did you hear your voice from the speaker? (Y/N)")
    print("=" * 60)

if __name__ == "__main__":
    test_mic_speaker()
