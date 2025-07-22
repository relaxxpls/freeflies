FROM pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime
# FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_CACHE_DIR=/tmp/poetry_cache
ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=false
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install Bash Command Line Tools
RUN apt-get update
RUN apt-get -qy --no-install-recommends install \
    curl \
    build-essential \
    unzip \
    wget \
    xvfb \
    git

RUN apt-get install -y \
    xdg-utils \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libu2f-udev \
    libvulkan1 \
    libwayland-client0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxi6 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    libxrandr2

RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt --fix-broken install
RUN dpkg -i ./google-chrome-stable_current_amd64.deb
RUN rm ./google-chrome-stable_current_amd64.deb

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR /app

# Copy poetry configuration files
COPY pyproject.toml poetry.lock ./

# Configure poetry and install dependencies
RUN poetry install --without dev --no-interaction --no-ansi

# Install pulseaudio & dependencies
RUN apt-get update
RUN apt-get install -y \
    portaudio19-dev \
    pulseaudio \
    pulseaudio-utils \
    ffmpeg \
    alsa-utils \
    libsndfile1 \
    supervisor

RUN apt install libcudnn8 libcudnn8-dev -y

RUN adduser root pulse-access
# RUN useradd -ms /bin/bash streamer

# Install Chrome and ChromeDriver via seleniumbase
RUN seleniumbase get chromedriver

# Clean up unused packages
RUN apt-get autoremove -y
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x scripts/entrypoint.sh

# Expose port for Streamlit
EXPOSE 8501

# Use custom entrypoint
ENTRYPOINT ["scripts/entrypoint.sh"]
