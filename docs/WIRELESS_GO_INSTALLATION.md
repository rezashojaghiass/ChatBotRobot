# RODE Wireless GO Installation Guide

## Overview
This guide covers installing and configuring the RODE Wireless GO microphone on your NVIDIA Jetson Xavier.

## Prerequisites
- RODE Wireless GO microphone
- USB adapter/connection to Jetson Xavier
- USB audio driver support

## Installation Steps

### 1. Verify USB Connection
First, confirm your RODE Wireless GO is connected via USB:

```bash
lsusb | grep -i rode
```

Expected output:
```
Bus 001 Device 004: ID 19f7:002a RODE Microphones
```

### 2. Load USB Audio Driver
Load the USB audio kernel module to enable audio device support:

```bash
sudo modprobe snd_usb_audio
```

### 3. Verify Audio Device Recognition
Check if the device is recognized by ALSA (Advanced Linux Sound Architecture):

```bash
cat /proc/asound/cards
```

Expected output should include:
```
0 [Audio          ]: USB-Audio - KT USB Audio
                    KTMicro KT USB Audio at usb-3610000.xhci-2.3, full speed
```

### 4. Make Installation Persistent
To ensure the USB audio driver loads automatically on system startup:

```bash
echo "snd_usb_audio" | sudo tee -a /etc/modules
```

This adds the module to the system's persistent module list.

## Verification

### Check Audio Input Devices
Run the audio device detection script:

```bash
cd /home/reza/ChatBotRobot
python3 src/list_audio_devices.py
```

### Check with ALSA
Use ALSA utilities to list capture devices:

```bash
arecord -l
```

### Check System Audio Cards
View all registered audio cards:

```bash
cat /proc/asound/cards
```

## Troubleshooting

### Device Not Appearing
If your RODE Wireless GO doesn't appear in the audio device list:

1. **Verify USB connection**: Use `lsusb` to confirm the device is connected
2. **Reload the driver**:
   ```bash
   sudo modprobe -r snd_usb_audio
   sudo modprobe snd_usb_audio
   ```
3. **Check device info**:
   ```bash
   ls -la /proc/asound/card0/
   ```

### Permission Issues
If you get permission errors, ensure you have sudo access or add your user to the audio group:

```bash
sudo usermod -a -G audio $USER
```

Then log out and back in for changes to take effect.

## Usage

Once installed, your RODE Wireless GO will be available as a USB audio device and can be used with:

- **Python applications** using PyAudio or similar libraries
- **ALSA tools** for direct audio capture
- **PulseAudio/JACK** for advanced audio routing
- **Voice chat applications** in your ChatBotRobot project

## Device Information

| Property | Value |
|----------|-------|
| Vendor ID | 19f7 |
| Product ID | 002a |
| Device Name | RODE Microphones |
| Protocol | USB 2.0 |
| Interface | Audio Class |

## Additional Resources

- [RODE Wireless GO Official Site](https://www.rode.com/en/microphones/wireless/wireless-go)
- [ALSA Project](https://www.alsa-project.org/)
- [Jetson Audio Configuration](https://docs.nvidia.com/jetson/l4t/index.html)

## Notes

- The RODE Wireless GO may appear as a generic USB audio device initially
- The device registers in ALSA as Card 0 after driver installation
- USB audio priority depends on device order - may change if other USB audio devices are connected
- For best audio quality, ensure your Xavier has stable power supply during audio capture

---

Last Updated: March 15, 2026
