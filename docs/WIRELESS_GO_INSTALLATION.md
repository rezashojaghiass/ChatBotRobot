# RODE Wireless GO II Installation Guide

## Overview
This guide covers installing and configuring the RODE Wireless GO II (dual wireless microphone system) on your NVIDIA Jetson Xavier for audio recording and playback.

## Problem & Solution

### The Problem
The RODE Wireless GO II receiver hub appeared in the system's USB device list (`lsusb`) but **was NOT showing as an audio input device** in ALSA or PyAudio, even though the hardware was connected and the USB audio driver was loaded.

This was caused by **the receiver hub being powered off**. The device firmware only exposes audio input/output endpoints when the hardware is actively powered on.

### Root Cause
The RODE Wireless GO II receiver hub has these requirements:
1. **Must be powered on** via USB or its battery
2. **Wireless microphones must be synced/paired** to the receiver
3. **USB audio driver** (`snd_usb_audio`) must be loaded on Xavier

When powered off, the device appears in `lsusb` but doesn't expose any audio endpoints to ALSA.

### The Solution
1. **Ensure receiver is powered ON** - Check for LED indicators on the hub
2. **Verify wireless mics are paired** - They should auto-pair on startup
3. **Load USB audio driver** (if not already loaded): `sudo modprobe snd_usb_audio`
4. **Check device detection**: `python3 src/list_audio_devices.py` should show:
   ```
   Device 25: Wireless GO II RX: USB Audio (hw:3,0)
     Channels: 2
     Sample Rate: 48000.0
   ```

### Result
Once powered on and paired, your RODE Wireless GO II:
- ✅ Appears in ALSA as **"Wireless GO II RX: USB Audio"** (Device 25)
- ✅ Shows 2 input channels at 48000 Hz sample rate
- ✅ Can record audio from the wireless microphones
- ✅ Can be used with PyAudio and audio applications for voice recording

## Prerequisites
- RODE Wireless GO II receiver hub + 2 wireless transmitter microphones
- USB connection to Jetson Xavier (via USB-A or USB-C adapter)
- Power source for receiver (USB power or internal battery charged)
- USB audio driver support (`snd_usb_audio`)

## Installation Steps

### CRITICAL: Power On the Receiver
⚠️ **The receiver hub MUST be powered on for audio input to work!**

Check for LED indicators on the physical receiver hub. The device should show power lights when active. If powered off, audio input will NOT be detected by the operating system.

### 1. Verify USB Connection
Confirm your RODE Wireless GO II receiver is connected via USB:

```bash
lsusb | grep -i rode
```

Expected outputs:
```
Bus 001 Device 004: ID 19f7:002a RODE Microphones         (Transmitter)
Bus 001 Device 007: ID 31b2:1002 KTMicro KT USB Audio      (Receiver Hub)
```

### 2. Load USB Audio Driver
Load the USB audio kernel module:

```bash
sudo modprobe snd_usb_audio
```

### 3. Verify Receiver Is Detected
Check if the receiver appears as an input device:

```bash
python3 src/list_audio_devices.py
```

Should show:
```
Device 25: Wireless GO II RX: USB Audio (hw:3,0)
  Channels: 2
  Sample Rate: 48000.0
```

### 4. Make Driver Persistent
To ensure the USB audio driver loads automatically on boot:

```bash
echo "snd_usb_audio" | sudo tee -a /etc/modules
```

This adds the module to the system's persistent module list.

## Verification

### Check Audio Input Devices
Run the audio device detection script to verify the RODE receiver is recognized:

```bash
cd /home/reza/ChatBotRobot
python3 src/list_audio_devices.py
```

Look for: `Device 25: Wireless GO II RX: USB Audio (hw:3,0)`

### Check with ALSA
View all capture devices:

```bash
arecord -l
```

The RODE receiver should NOT appear in arecord (as it doesn't have traditional ALSA capture), but PyAudio should detect it.

### Record Audio from RODE
Record 5 seconds from the wireless microphones:

```bash
cd /home/reza/ChatBotRobot
python3 src/record_audio.py "test.wav" 5 25
```

### Play Back Recording
Play the recording through your speaker (device 25 = speaker output):

```bash
python3 src/play_audio.py "test.wav"
```

## Usage

### Recording from RODE Wireless Microphones
```bash
python3 src/record_audio.py "recording.wav" 10 25
```
- Records 10 seconds
- Device 25 = Wireless GO II receiver
- Output: stereo WAV file

### Playing Audio
```bash
python3 src/play_audio.py "recording.wav"
```
- Uses default speaker (device 25)
- Supports automatic sample rate conversion

## Troubleshooting

### "Device Not Appearing in Audio List"
**Solution**: Ensure the receiver hub is POWERED ON!

1. Check for LED lights on the physical receiver
2. Verify power via USB cable or charged battery
3. Restart the Xavier after powering on receiver
4. Run `python3 src/list_audio_devices.py` again

### USB Module Not Loading
If `sudo modprobe snd_usb_audio` fails:

```bash
# Check if module is already loaded
lsmod | grep snd_usb

# If builtin (Jetson Xavier), it should be automatic
```

### Microphones Not Transmitting
If receiver is on but no audio is recorded:

1. **Check wireless mics have power** - Look for LED indicators on transmitters
2. **Check pairing** - Mics may need to be re-paired with receiver
3. **Move mics closer** - Try moving within 5-10 feet of receiver to test
4. **Restart transmitters** - Toggle power off/on on the wireless mics

### Permission Issues
Add your user to the audio group:

```bash
sudo usermod -a -G audio $USER
# Log out and back in for changes to take effect
```

## Device Information

| Property | Value |
|----------|-------|
| Device Model | RODE Wireless GO II |
| Receiver Vendor ID | 31b2 |
| Receiver Product ID | 1002 |
| Receiver USB Name | KTMicro KT USB Audio |
| Input Channels | 2 (stereo) |
| Sample Rate | 48000 Hz |
| PyAudio Device Index | 25 |
| Transmitter Vendor ID | 19f7 |
| Transmitter Product ID | 002a |
| Range | 200m line of sight |
