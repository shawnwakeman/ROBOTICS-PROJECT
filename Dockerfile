# Native Apple Silicon compatible image
FROM osrf/ros:jazzy-desktop

ENV DEBIAN_FRONTEND=noninteractive

# 1. Add the official Gazebo repository
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
    xvfb \
    x11vnc \
    novnc \
    websockify \
    openbox \
    terminator \
    mesa-utils \
    libgl1-mesa-dri \
    x11-utils \
    net-tools \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Fix NoVNC index page
RUN ln -s /usr/share/novnc/vnc.html /usr/share/novnc/index.html || true

# 3. Copy your specific startup script
COPY entrypoint.sh /root/entrypoint.sh
RUN chmod +x /root/entrypoint.sh

WORKDIR /root/ros2_ws
CMD ["/root/entrypoint.sh"]