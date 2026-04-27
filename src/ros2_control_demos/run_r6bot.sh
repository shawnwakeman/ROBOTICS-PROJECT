#!/bin/bash
# run_r6bot.sh — build, then launch controller + trajectory in split tmux panes
# Usage: bash run_r6bot.sh

set -e

# ---------- Build ----------
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash

echo "=== Build complete ==="

# ---------- Launch in tmux ----------
SESSION="r6bot"

# Kill old session if it exists
tmux kill-session -t $SESSION 2>/dev/null || true

# Create session with the controller launch
tmux new-session -d -s $SESSION -n "controller" \
  "bash -c 'source ~/ros2_ws/install/setup.bash && ros2 launch ros2_control_demo_example_7 r6bot_controller.launch.py; exec bash'"

# Wait for controller + RViz to come up
sleep 10

# Split horizontally and run the trajectory
tmux split-window -h -t $SESSION \
  "bash -c 'source ~/ros2_ws/install/setup.bash && ros2 launch ros2_control_demo_example_7 send_trajectory.launch.py; exec bash'"

# Attach so you can see both panes
tmux attach -t $SESSION