#!/bin/bash

# Exit on any error
set -e

# Install basic command line tools, audio dependencies, pyautogui dependencies etc
echo "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y \
    curl \
    build-essential \
    unzip \
    wget \
    xvfb \
    git \
    gnupg \
    portaudio19-dev \
    pulseaudio \
    pulseaudio-utils \
    ffmpeg \
    libsndfile1 \
    scrot \
    python3-tk

# Install Google Chrome
echo "Installing Google Chrome..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/google-chrome.gpg
sudo sh -c 'echo "deb [arch=amd64 signed-by=/etc/apt/trusted.gpg.d/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list'
sudo apt update
sudo apt install -y google-chrome-stable

# Install Poetry
echo "Installing Poetry..."
export PATH="/home/ubuntu/.local/bin:$PATH"
export POETRY_VIRTUALENVS_IN_PROJECT=1
echo "export POETRY_VIRTUALENVS_IN_PROJECT=1" >> ~/.bashrc
echo "export PATH=\"~/.local/bin:\$PATH\"" >> ~/.bashrc
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$(pwd)/.venv/bin:$PATH"
echo "export PATH=\"$(pwd)/.venv/bin:\$PATH\"" >> ~/.bashrc

# Install cuDNN 8 (for whisperx)
echo "Installing cuDNN 8..."
wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
rm cuda-keyring_1.0-1_all.deb
sudo apt update
sudo apt install -y libcudnn8 libcudnn8-dev

# Clean up unused packages
echo "Cleaning up..."
sudo apt-get autoremove -y
sudo apt-get clean
sudo rm -rf /var/lib/apt/lists/*

echo "Installation complete! Run 'source ~/.bashrc' to reload your environment in the current session."

# Install Python dependencies using Poetry
echo "Installing Python dependencies with Poetry..."
poetry install --no-interaction --no-ansi

# Install Chrome and ChromeDriver via seleniumbase
echo "Installing ChromeDriver via seleniumbase..."
seleniumbase get chromedriver
