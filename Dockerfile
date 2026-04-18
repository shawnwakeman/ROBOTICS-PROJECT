# Native Apple Silicon compatible image
FROM osrf/ros:jazzy-desktop

ENV DEBIAN_FRONTEND=noninteractive

# 1. Add the official Gazebo repository (FIXED SPACING HERE)
RUN apt-get update && apt-get install -y curl gnupg lsb-release wget && \
    curl -sSL https://packages.osrfoundation.org/gazebo.gpg -o /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null

# 2. Install Gazebo, ROS, and Virtual Desktop (NoVNC) tools
RUN apt-get update && apt-get install -y \
    gz-harmonic \
    ros-jazzy-ros-gz \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-ros-gz-sim \
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-gz-ros2-control \
    ros-jazzy-xacro \
    ros-jazzy-joint-state-publisher-gui \
    # Web Virtual Desktop Tools
    xvfb \
    x11vnc \
    novnc \
    websockify \
    openbox \
    terminator \
    mesa-utils \
    libgl1-mesa-dri \
    && rm -rf /var/lib/apt/lists/*

    # Clone the ros2_control demos repository which contains the 6DOF robot example
# Fix NoVNC index page
RUN ln -s /usr/share/novnc/vnc.html /usr/share/novnc/index.html || true

# 3. Create the Startup Script
RUN echo '#!/bin/bash\n\
# Start Virtual Screen\n\
Xvfb :0 -screen 0 1920x1080x24 &\n\
sleep 1\n\
# Start Window Manager (gives windows borders/close buttons)\n\
openbox-session &\n\
# Start VNC Server\n\
x11vnc -display :0 -nopw -forever -quiet &\n\
# Start Web Server\n\
websockify --web /usr/share/novnc 8080 localhost:5900 &\n\
# Open a terminal on the desktop automatically\n\
DISPLAY=:0 terminator &\n\
echo "========================================================="\n\
echo "🚀 DESKTOP READY!"\n\
echo "👉 Open your Mac browser and go to: http://localhost:8080"\n\
echo "========================================================="\n\
tail -f /dev/null' > /root/entrypoint.sh

RUN chmod +x /root/entrypoint.sh
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc

WORKDIR /root/ros2_ws
CMD ["/root/entrypoint.sh"]