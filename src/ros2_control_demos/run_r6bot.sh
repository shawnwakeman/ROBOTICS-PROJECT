#!/bin/bash
# run_r6bot.sh — kill old stuff, rebuild, launch Gazebo sim
set -e

# ---------- Kill any leftover processes ----------
pkill -f gz 2>/dev/null || true
pkill -f ros2 2>/dev/null || true
pkill -f rviz2 2>/dev/null || true
sleep 2

# ---------- Build ----------
cd ~/ros2_ws/src/ros2_control_demos/
colcon build --symlink-install
source install/setup.bash

echo "=== Build complete, launching Gazebo ==="

# ---------- Launch ----------
ros2 launch ros2_control_demo_example_7 r6bot_gazebo.launch.py