#!/bin/bash
# Don't use set -e — background process failures will kill the script

export DISPLAY=:0

echo "[1/5] Starting Xvfb..."
rm -f /tmp/.X0-lock /tmp/.X11-unix/X0
Xvfb :0 -screen 0 1920x1080x24 &

echo "[2/5] Waiting for Xvfb to be ready..."
TRIES=0
until xdpyinfo -display :0 >/dev/null 2>&1; do
    sleep 0.5
    TRIES=$((TRIES+1))
    if [ $TRIES -ge 60 ]; then
        echo "ERROR: Xvfb never became ready after 30s. Aborting."
        exit 1
    fi
done
echo "Xvfb is up."

echo "[3/5] Starting window manager..."
openbox-session &
sleep 1

echo "[4/5] Starting x11vnc..."
x11vnc \
    -display :0 \
    -nopw \
    -forever \
    -shared \
    -rfbport 5900 \
    -o /var/log/x11vnc.log \
    -bg

echo "Waiting for x11vnc on port 5900..."
TRIES=0
until nc -z 127.0.0.1 5900 2>/dev/null; do
    sleep 0.5
    TRIES=$((TRIES+1))
    if [ $TRIES -ge 60 ]; then
        echo "ERROR: x11vnc never opened port 5900. Log:"
        cat /var/log/x11vnc.log
        exit 1
    fi
done
echo "x11vnc is up on 5900."

echo "[5/5] Starting noVNC..."
websockify --web /usr/share/novnc 8080 127.0.0.1:5900 &

DISPLAY=:0 terminator &

echo "========================================================="
echo "DESKTOP READY → http://localhost:8080/vnc.html"
echo "========================================================="
tail -f /var/log/x11vnc.log