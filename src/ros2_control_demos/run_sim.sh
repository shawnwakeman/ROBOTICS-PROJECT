#!/bin/bash
# run_r6bot.sh — build, launch Gazebo, spawn cubes
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
N_CUBES=${1:-5}

# ---------- Kill any leftover processes ----------
pkill -f gz 2>/dev/null || true
pkill -f ros2 2>/dev/null || true
sleep 2

# ---------- Build ----------
cd ~/ros2_ws/src/ros2_control_demos/
colcon build --symlink-install
source install/setup.bash

echo "=== Build complete, launching Gazebo ==="

# ---------- Launch Gazebo in background ----------
ros2 launch ros2_control_demo_example_7 r6bot_gazebo.launch.py &
GAZEBO_PID=$!

# ---------- Wait for Gazebo to settle ----------
echo "=== Waiting 20s for Gazebo to start ==="
sleep 20

# ---------- Spawn cubes ----------
echo "=== Spawning ${N_CUBES} cubes ==="
bash "${SCRIPT_DIR}/spawn_random_cubes.sh" "$N_CUBES"

echo "=== All done! Gazebo is running (PID ${GAZEBO_PID}) ==="
echo "=== Press Ctrl+C to shut down ==="

wait $GAZEBO_PID