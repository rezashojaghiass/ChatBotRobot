# Audio Setup and Configuration Guide

Complete guide for configuring audio devices on Jetson Xavier for voice interaction.

## Table of Contents
1. [Audio Hardware Overview](#audio-hardware-overview)
2. [List Audio Devices](#list-audio-devices)
3. [Configure Microphone](#configure-microphone)
4. [Configure Speaker](#configure-speaker)
5. [Test Audio](#test-audio)
6. [Troubleshooting](#troubleshooting)

---

## Audio Hardware Overview

### Recommended Setup
- **Microphone**: Rode Wireless GO II RX (USB)
  - Sample Rate: 48kHz (auto-resampled to 16kHz)
  - Channels: Stereo (auto-converted to mono)
  - Latency: <10ms
  
- **Speaker**: Any USB or 3.5mm audio output
  - Sample Rate: 16kHz (Riva TTS output)
  
### Supported Devices
- ✅ USB microphones (Rode, Blue Yeti, etc.)
- ✅ USB headsets
- ✅ 3.5mm microphone (built-in jack)
- ✅ Bluetooth audio (with some latency)
- ✅ HDMI audio output

---

## List Audio Devices

### Using Python Script

```bash
cd /mnt/nvme/adrian/ChatBotRobot/src

# List all audio devices
python3 list_audio_devices.py
```

**Example Output:**
```
=== PyAudio Device List ===

Device 0: HDA NVidia: HDMI 0 (hw:0,3)
  Max Input Channels: 0
  Max Output Channels: 8
  Default Sample Rate: 44100.0

Device 1: HDA NVidia: HDMI 1 (hw:0,7)
  Max Input Channels: 0
  Max Output Channels: 8
  Default Sample Rate: 44100.0

Device 2: Wireless GO II RX: USB Audio (hw:2,0)
  Max Input Channels: 2
  Max Output Channels: 0
  Default Sample Rate: 48000.0
  ✓ Input device (microphone)

Device 3: USB PnP Sound Device: USB Audio (hw:3,0)
  Max Input Channels: 0
  Max Output Channels: 2
  Default Sample Rate: 44100.0
  ✓ Output device (speaker)
```

**Notes:**
- Devices with `Max Input Channels > 0` are microphones
- Devices with `Max Output Channels > 0` are speakers
- `hw:X,Y` is the ALSA hardware address (X=card, Y=device)

### Using ALSA Commands

```bash
# List input devices (microphones)
arecord -l

# Expected output:
# **** List of CAPTURE Hardware Devices ****
# card 2: RX [Wireless GO II RX], device 0: USB Audio [USB Audio]
#   Subdevices: 1/1
#   Subdevice #0: subdevice #0

# List output devices (speakers)
aplay -l

# Expected output:
# **** List of PLAYBACK Hardware Devices ****
# card 0: NVidia [HDA NVidia], device 3: HDMI 0 [HDMI 0]
#   Subdevices: 1/1
#   Subdevice #0: subdevice #0
```

---

## Configure Microphone

### Automatic Configuration (Default)

The voice chat application auto-detects the first USB microphone:

```python
# In voice_chat_riva_aws.py
# PyAudio automatically finds input device
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,  # Mono
    rate=16000,  # 16kHz
    input=True,
    frames_per_buffer=1024
)
```

### Manual Device Selection

If you have multiple microphones:

```python
# Modify voice_chat_riva_aws.py
DEVICE_INDEX = 2  # Change to your device number

stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    input_device_index=DEVICE_INDEX,  # Add this line
    frames_per_buffer=1024
)
```

### Set Default ALSA Device

```bash
# Create ~/.asoundrc file
nano ~/.asoundrc

# Add content (replace card 2 with your device number):
pcm.!default {
    type hw
    card 2
    device 0
}

ctl.!default {
    type hw
    card 2
}

# Save and exit (Ctrl+X, Y, Enter)

# Test
arecord -f S16_LE -r 16000 -c 1 -d 5 test.wav
aplay test.wav
```

### Adjust Microphone Volume

```bash
# Launch ALSA mixer
alsamixer

# Navigate:
# - F6: Select sound card (choose your microphone)
# - Up/Down arrows: Adjust volume
# - M: Mute/Unmute
# - ESC: Exit

# Or use command line:
amixer -c 2 set Mic 80%  # Set to 80% (replace 2 with your card number)
```

---

## Configure Speaker

### Automatic Configuration

Riva TTS automatically outputs to the default audio device.

### Change Default Output

```bash
# Set default ALSA playback device
nano ~/.asoundrc

# Add (or modify existing):
pcm.!default {
    type hw
    card 0  # Change to your speaker card number
    device 3
}

ctl.!default {
    type hw
    card 0
}
```

### Adjust Speaker Volume

```bash
# ALSA mixer
alsamixer
# F6: Select sound card
# Adjust Master volume

# Or command line:
amixer -c 0 set Master 75%  # Set to 75%
```

### Use PulseAudio (Optional)

```bash
# Install PulseAudio (if not installed)
sudo apt install pulseaudio pavucontrol

# Start PulseAudio
pulseaudio --start

# GUI volume control
pavucontrol
# Navigate to "Playback" tab to adjust volume
# Navigate to "Input Devices" tab to select microphone

# List PulseAudio devices
pactl list short sinks    # Speakers
pactl list short sources  # Microphones

# Set default sink (speaker)
pactl set-default-sink <sink-name>

# Set default source (microphone)
pactl set-default-source <source-name>
```

---

## Test Audio

### Test Microphone

```bash
cd /mnt/nvme/adrian/ChatBotRobot/src

# Record 5 seconds
arecord -D hw:2,0 -f S16_LE -r 16000 -c 1 -d 5 test_mic.wav

# Speak into microphone: "Testing one two three"

# Play back
aplay test_mic.wav

# If you hear your voice clearly: ✓ Microphone works!

# Clean up
rm test_mic.wav
```

### Test Speaker/TTS

```bash
# Use TTS utility script
./scripts/speak.py "Testing speaker output"

# Should hear: "Testing speaker output" in male voice

# Or test with Python:
python3 << EOF
import riva.client

auth = riva.client.Auth(uri='localhost:50051')
tts = riva.client.SpeechSynthesisService(auth)

resp = tts.synthesize(
    "Hello Adrian, testing one two three",
    voice_name="English-US.Male-1",
    language_code="en-US",
    encoding=riva.client.AudioEncoding.LINEAR_PCM,
    sample_rate_hz=16000
)

player = riva.client.AudioPlayer(sample_rate_hz=16000)
player.push(resp.audio)
player.wait()
EOF
```

### Test ASR (Speech Recognition)

```bash
cd /mnt/nvme/adrian/ChatBotRobot/src

# Run ASR test script
python3 asr_test.py

# Speak clearly: "Hello Buzz Lightyear"
# Expected output: Transcription appears on screen
```

### Full Integration Test

```bash
# Start Riva server (if not running)
./scripts/start_riva.sh

# Test chat mode
cd src
python3 voice_chat_riva_aws.py --duration 5 --mode chat --llm llama

# Say: "Hello Buzz"
# Expected:
# 1. ASR transcribes: "Hello Buzz"
# 2. LLM responds (text printed)
# 3. TTS speaks response
# 4. Wait for next input

# Press Ctrl+C to exit
```

---

## Troubleshooting

### No Audio Devices Detected

**Problem:** `python3 list_audio_devices.py` shows no devices

**Solutions:**
```bash
# 1. Check USB connection
lsusb
# Should show your USB microphone/speaker

# 2. Reload ALSA
sudo alsa force-reload

# 3. Restart audio services
pulseaudio -k  # Kill PulseAudio
pulseaudio --start  # Restart

# 4. Check kernel modules
lsmod | grep snd
# Should show: snd_usb_audio, snd_hda_intel, etc.

# If missing:
sudo modprobe snd-usb-audio
```

### ALSA Warnings

**Warning:** `ALSA lib pcm.c:2664:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.rear`

**Solution:**
```bash
# These warnings are harmless, audio still works

# To suppress, add to ~/.asoundrc:
pcm.!default {
    type hw
    card 2
}

# Or set environment variable:
export ALSA_CARD=2  # Add to ~/.bashrc
```

### Audio Crackling/Distortion

**Problem:** Poor audio quality, crackling sounds

**Solutions:**
```bash
# 1. Increase buffer size
# In voice_chat_riva_aws.py:
frames_per_buffer=2048  # Increase from 1024

# 2. Check CPU usage
htop
# If CPU at 100%, close other apps

# 3. Set Jetson to max performance
sudo nvpmodel -m 0
sudo jetson_clocks

# 4. Disable power management on USB
echo 'on' | sudo tee /sys/bus/usb/devices/*/power/level
```

### Microphone Not Recording

**Problem:** arecord produces empty file or silence

**Solutions:**
```bash
# 1. Check microphone is not muted
alsamixer
# Select microphone, press 'M' to unmute

# 2. Increase microphone gain
amixer -c 2 set Mic 100%
amixer -c 2 set 'Mic Boost' 100%

# 3. Test different sample rate
arecord -D hw:2,0 -f S16_LE -r 48000 -c 2 -d 5 test.wav
# Try native sample rate (48kHz, stereo)

# 4. Check permissions
ls -l /dev/snd/
# Should show crw-rw---- with group 'audio'

# Add user to audio group:
sudo usermod -aG audio $USER
newgrp audio
```

### Speaker No Output

**Problem:** TTS runs but no sound

**Solutions:**
```bash
# 1. Check volume
alsamixer
# Master volume should be >0 and unmuted

# 2. Test different output
aplay -l  # List devices
aplay -D hw:0,3 test.wav  # Try specific device

# 3. Check HDMI audio
# If using HDMI monitor with speakers:
# Right-click volume icon → Sound Settings → Output → Select HDMI

# 4. Test with speaker-test
speaker-test -c 2 -r 48000 -D hw:0,3
# Should hear pink noise
```

### High Latency

**Problem:** Delay between speaking and transcription

**Solutions:**
```bash
# 1. Reduce VAD silence threshold
# In voice_chat_riva_aws.py:
silence_threshold = 0.5  # Already optimal

# 2. Reduce buffer size
frames_per_buffer=512  # Smaller = lower latency, more CPU

# 3. Use wired microphone (Bluetooth has ~100-300ms latency)

# 4. Optimize Jetson
sudo nvpmodel -m 0  # Max performance mode
```

### Sample Rate Mismatch

**Warning:** `Rate doesn't match (requested 16000Hz, get 48000Hz)`

**Solution:**
```bash
# ALSA automatically resamples, but can create .asoundrc:
pcm.rate_convert {
    type rate
    slave {
        pcm "hw:2,0"
        rate 16000
    }
}

pcm.!default {
    type plug
    slave.pcm "rate_convert"
}
```

**Or in code (automatic):**
```python
# PyAudio handles resampling automatically
# No action needed if using voice_chat_riva_aws.py
```

---

## Advanced Configuration

### USB Audio Settings

```bash
# Check USB audio info
cat /proc/asound/card2/stream0
# Shows supported formats, rates, channels

# Force specific USB configuration
# Create /etc/modprobe.d/alsa-base.conf:
options snd-usb-audio nrpacks=1
# nrpacks=1 = lower latency (default is 8)
```

### PulseAudio Configuration

```bash
# Edit PulseAudio config
nano ~/.config/pulse/daemon.conf

# Add for lower latency:
default-fragments = 2
default-fragment-size-msec = 5

# Restart PulseAudio
pulseaudio -k
pulseaudio --start
```

### JACK Audio (Professional)

```bash
# Install JACK (lower latency than ALSA/PulseAudio)
sudo apt install jackd2 qjackctl

# Start JACK
jackd -d alsa -r 48000 -p 128

# Connect Riva to JACK (requires JACK bridge)
```

---

## Audio Quality Settings

### Optimal Settings for Voice Chat

**For Riva ASR:**
- Sample Rate: 16kHz (required)
- Channels: 1 (mono)
- Format: 16-bit PCM (paInt16)
- Buffer: 1024 frames (~64ms latency)

**For Riva TTS:**
- Sample Rate: 16kHz (Riva output)
- Channels: 1 (mono)
- Format: 16-bit PCM

**For Music/High Quality:**
- Sample Rate: 44.1kHz or 48kHz
- Channels: 2 (stereo)
- Format: 24-bit or 32-bit float

---

## Additional Resources

- [ALSA Documentation](https://www.alsa-project.org/wiki/Main_Page)
- [PulseAudio Documentation](https://www.freedesktop.org/wiki/Software/PulseAudio/)
- [PyAudio Documentation](https://people.csail.mit.edu/hubert/pyaudio/docs/)
- [Jetson Audio Guide](https://forums.developer.nvidia.com/c/agx-autonomous-machines/jetson-embedded-systems/70)

---

**Next:** Run the full system: `python3 voice_chat_riva_aws.py --mode madagascar_quiz --llm llama70b --rag`
