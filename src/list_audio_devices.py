#!/usr/bin/env python3
import pyaudio

p = pyaudio.PyAudio()
print("\n=== Available Audio Input Devices ===\n")

for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f"Device {i}: {info['name']}")
        print(f"  Channels: {info['maxInputChannels']}")
        print(f"  Sample Rate: {info['defaultSampleRate']}")
        print()

p.terminate()
