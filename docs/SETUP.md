# Complete Setup Guide for Jetson Xavier ChatBot Robot

This guide will take you from a fresh Jetson Xavier to a fully working voice-enabled AI chatbot.

## Table of Contents
1. [Initial Jetson Xavier Setup](#initial-jetson-xavier-setup)
2. [VNC Remote Desktop Setup](#vnc-remote-desktop-setup)
3. [Install System Dependencies](#install-system-dependencies)
4. [Docker and NVIDIA Container Runtime](#docker-and-nvidia-container-runtime)
5. [Python Environment Setup](#python-environment-setup)
6. [Clone Repository](#clone-repository)
7. [Install Python Dependencies](#install-python-dependencies)
8. [Audio Device Configuration](#audio-device-configuration)
9. [Next Steps](#next-steps)

---

## Initial Jetson Xavier Setup

### 1. Flash JetPack 5.x

**Requirements:**
- Host computer running Ubuntu 18.04/20.04
- USB-C cable
- Jetson Xavier in recovery mode

**Steps:**
```bash
# On host machine
# Download NVIDIA SDK Manager
# https://developer.nvidia.com/nvidia-sdk-manager

# Install SDK Manager
sudo dpkg -i sdkmanager_*_amd64.deb
sudo apt-get install -f

# Launch SDK Manager
sdkmanager

# Follow GUI to flash:
# - Select Jetson AGX Xavier
# - JetPack 5.x (L4T R35.6.3)
# - Install to target device
```

### 2. Initial Boot Configuration

```bash
# SSH into Jetson (default password: nvidia)
ssh nvidia@<jetson-ip>

# Update system
sudo apt update
sudo apt upgrade -y

# Verify JetPack version
sudo apt-cache show nvidia-jetpack

# Expected output: Version: 5.x.x

# Verify CUDA
nvcc --version
# Expected: CUDA 11.4

# Check GPU and system stats
sudo tegrastats --interval 1000 --logfile /dev/null
# Press Ctrl+C after a few seconds
# Expected: Shows RAM, CPU, GPU usage

# Or install jtop (better visualization)
sudo pip3 install -U jetson-stats
sudo jtop
# Expected: Interactive dashboard showing GPU, CPU, memory
```

### 3. Set Up Storage

```bash
# Check NVMe SSD
lsblk
# Look for nvme0n1 device

# Format NVMe (if new)
sudo mkfs.ext4 /dev/nvme0n1

# Create mount point
sudo mkdir -p /mnt/nvme

# Mount
sudo mount /dev/nvme0n1 /mnt/nvme

# Auto-mount on boot
echo '/dev/nvme0n1 /mnt/nvme ext4 defaults 0 2' | sudo tee -a /etc/fstab

# Create user directory
sudo mkdir -p /mnt/nvme/adrian
sudo chown -R $USER:$USER /mnt/nvme/adrian
cd /mnt/nvme/adrian
```

---

## VNC Remote Desktop Setup

### 1. Install VNC Server

```bash
# Update package list
sudo apt update

# Install desktop environment (if not already installed)
sudo apt install ubuntu-desktop -y

# Install VNC server
sudo apt install vino -y

# Enable VNC
gsettings set org.gnome.Vino prompt-enabled false
gsettings set org.gnome.Vino require-encryption false

# Set VNC password
gsettings set org.gnome.Vino authentication-methods "['vnc']"
gsettings set org.gnome.Vino vnc-password $(echo -n 'yourpassword' | base64)

# Start VNC on boot
sudo systemctl enable vino
sudo systemctl start vino
```

### 2. Configure Display Settings

```bash
# Export display
export DISPLAY=:0

# Or add to ~/.bashrc
echo 'export DISPLAY=:0' >> ~/.bashrc
source ~/.bashrc
```

### 3. Connect from Client

**On your desktop/laptop:**

```bash
# Install VNC viewer
# Download from: https://www.realvnc.com/en/connect/download/viewer/

# Or use built-in VNC client
vncviewer <jetson-ip>:5900
```

**Alternative: X11 Forwarding (lighter weight)**

```bash
# On Jetson
sudo apt install xauth -y

# From client
ssh -X nvidia@<jetson-ip>
# Now GUI apps will display on your machine
```

---

## Install System Dependencies

```bash
# Build tools
sudo apt install -y build-essential cmake git

# Audio libraries
sudo apt install -y \
    portaudio19-dev \
    python3-pyaudio \
    alsa-utils \
    libasound2-dev \
    pulseaudio \
    pulseaudio-utils

# Python development
sudo apt install -y python3-pip python3-dev python3-venv

# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -rf aws awscliv2.zip

# Verify AWS CLI
aws --version
# Expected: aws-cli/2.x.x
```

---

## Docker and NVIDIA Container Runtime

### 1. Install Docker (if not already installed)

```bash
# Remove old versions
sudo apt remove docker docker-engine docker.io containerd runc

# Install dependencies
sudo apt update
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker run hello-world
```

### 2. Configure NVIDIA Container Runtime

```bash
# Should already be installed with JetPack
# Verify
docker run --rm --gpus all nvidia/cuda:11.4.0-base-ubuntu20.04 nvidia-smi

# Expected: GPU information displayed
```

---

## Python Environment Setup

```bash
# Upgrade pip
python3 -m pip install --upgrade pip

# Install virtualenv (optional but recommended)
python3 -m pip install virtualenv

# Create virtual environment (optional)
cd /mnt/nvme/adrian
python3 -m venv chatbot-env
source chatbot-env/bin/activate

# Or use system Python
```

---

## Clone Repository

```bash
cd /mnt/nvme/adrian

# Clone the repository
git clone https://github.com/rezashojaghiass/ChatBotRobot.git
cd ChatBotRobot

# Verify files
ls -la
# Expected: README.md, requirements.txt, src/, docs/, scripts/
```

---

## Install Python Dependencies

```bash
cd /mnt/nvme/adrian/ChatBotRobot

# Install all dependencies
pip3 install -r requirements.txt

# This will install:
# - boto3 (AWS SDK)
# - nvidia-riva-client (Speech AI)
# - sentence-transformers (RAG)
# - pyaudio (Audio I/O)
# - numpy (Math)

# Verify installations
python3 -c "import boto3; print('boto3:', boto3.__version__)"
python3 -c "import riva.client; print('riva.client: OK')"
python3 -c "import sentence_transformers; print('sentence-transformers: OK')"
python3 -c "import pyaudio; print('pyaudio: OK')"

# Download sentence-transformers model (will auto-download on first use)
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

---

## Audio Device Configuration

### 1. List Audio Devices

```bash
cd src

# Check ALSA devices
arecord -l
# Look for your microphone (e.g., Wireless GO II RX)

aplay -l
# Look for your speaker

# Check with Python
python3 list_audio_devices.py
```

### 2. Test Microphone

```bash
# Record 5-second test
arecord -D hw:2,0 -f S16_LE -r 16000 -c 1 -d 5 test.wav

# Play back
aplay test.wav

# If you hear your recording, microphone works!
rm test.wav
```

### 3. Configure Default Device (Optional)

```bash
# Create ALSA config
cat > ~/.asoundrc << 'EOF'
pcm.!default {
    type hw
    card 2
    device 0
}

ctl.!default {
    type hw
    card 2
}
EOF

# Replace "card 2" with your device number from arecord -l
```

---

## Next Steps

Now that your Jetson Xavier is set up, proceed to:

1. **[RIVA_GUIDE.md](RIVA_GUIDE.md)** - Install NVIDIA Riva speech services
2. **[AWS_BEDROCK.md](AWS_BEDROCK.md)** - Configure AWS Bedrock for LLMs
3. **[AUDIO_SETUP.md](AUDIO_SETUP.md)** - Fine-tune audio settings
4. **[RAG_IMPLEMENTATION.md](RAG_IMPLEMENTATION.md)** - Set up RAG with subtitles

---

## Verification Checklist

Before proceeding, verify:

- [ ] JetPack 5.x installed (L4T R35.6.3)
- [ ] CUDA 11.4 working (`nvcc --version`)
- [ ] GPU accessible (`sudo tegrastats` or `sudo jtop`)
- [ ] NVMe SSD mounted at `/mnt/nvme`
- [ ] VNC server running (optional)
- [ ] Docker installed and GPU-enabled
- [ ] Python 3.8+ available
- [ ] Repository cloned
- [ ] All Python packages installed
- [ ] Microphone detected
- [ ] Speaker working
- [ ] Internet connection active

---

## Troubleshooting

### JetPack Issues

**Problem:** Wrong JetPack version
```bash
# Check version
cat /etc/nv_tegra_release
# Should show: R35 (release), REVISION: 6.3
```

**Solution:** Reflash with SDK Manager

### Storage Issues

**Problem:** NVMe not mounting
```bash
# Check partition
sudo fdisk -l /dev/nvme0n1

# Format if needed
sudo mkfs.ext4 /dev/nvme0n1

# Mount
sudo mount /dev/nvme0n1 /mnt/nvme
```

### VNC Issues

**Problem:** Can't connect to VNC
```bash
# Check if vino is running
ps aux | grep vino

# Restart
sudo systemctl restart vino

# Check firewall
sudo ufw status
sudo ufw allow 5900/tcp
```

### Docker Issues

**Problem:** Permission denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or use sudo
sudo docker run hello-world
```

### Audio Issues

**Problem:** No audio devices detected
```bash
# Check USB devices
lsusb

# Reload ALSA
sudo alsa force-reload

# Check PulseAudio
pulseaudio --check
pulseaudio -D
```

---

## Additional Resources

- [NVIDIA Jetson Documentation](https://developer.nvidia.com/embedded/jetson-agx-xavier-developer-kit)
- [JetPack Release Notes](https://developer.nvidia.com/embedded/jetpack)
- [Jetson Linux Developer Guide](https://docs.nvidia.com/jetson/archives/r35.6/DeveloperGuide/index.html)

---

**Next:** [RIVA_GUIDE.md](RIVA_GUIDE.md) - Install NVIDIA Riva
