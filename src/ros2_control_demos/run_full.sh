#!/bin/bash
# run_full.sh — launch full system (Gazebo + perception + pick_and_place), spawn cubes
# Usage: bash run_full.sh [num_cubes]

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

echo "=== Build complete ==="
echo "=== Launching full system (Gazebo + perception + pick_and_place) ==="

# ---------- Launch full system in background ----------
ros2 launch ros2_control_demo_example_7 r6bot_full.launch.py &
LAUNCH_PID=$!

# ---------- Wait for Gazebo + camera to be ready ----------
echo "=== Waiting 30s for everything to start ==="
sleep 30

# ---------- Spawn cubes ----------
echo "=== Spawning ${N_CUBES} cubes ==="
source ~/ros2_ws/src/ros2_control_demos/install/setup.bash
bash "${SCRIPT_DIR}/spawn_random_cubes.sh" "$N_CUBES"

echo ""
echo "============================================"
echo "  System is running!"
echo "  Open other terminals to inspect:"
echo ""
echo "  bash run_rviz.sh          — open RViz"
echo "  bash check_topics.sh      — monitor topics"
echo "============================================"
echo ""
echo "Press Ctrl+C to shut down"

wait $LAUNCH_PID