#!/bin/bash

# Exit on any error
set -e

echo "Starting FreeFlies application..."

# 1. Cleanup to be "stateless" on startup, otherwise pulseaudio daemon can't start
echo "Setting up audio environment..."
rm -rf /var/run/pulse /var/lib/pulse /root/.config/pulse
echo "Ensuring required directories exist..."
mkdir -p ./.temp/audio ./.temp/user_data
chmod 755 ./.temp/audio ./.temp/user_data

# 2. Start D-Bus for PulseAudio
mkdir -p /var/run/dbus
dbus-uuidgen > /var/lib/dbus/machine-id
dbus-daemon --config-file=/usr/share/dbus-1/system.conf --print-address &

# 3. Start PulseAudio server so Firefox will have somewhere to send audio
pulseaudio --fail -D --exit-idle-time=-1
pacmd load-module module-virtual-sink sink_name=v1  # Load a virtual sink as `v1`
pacmd set-default-sink v1  # Set the `v1` as the default sink device
pacmd set-default-source v1.monitor  # Set the monitor of the v1 sink to be the default source
sleep 0.5

# 4. Run X11 virtual display (framebuffer)
Xvfb :99 -ac -screen 0 1920x1080x24 2>&1 &
export DISPLAY=:99

# xdotool mousemove 1 1 click 1  # Move mouse out of the way so it doesn't trigger the "pause" overlay on the video tile
sleep 0.5

# 5. Start the streamlit application
echo "Starting application..."
exec streamlit run app.py
