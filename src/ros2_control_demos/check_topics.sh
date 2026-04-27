#!/bin/bash
# check_topics.sh — verify all the pieces are working
# Run in a separate terminal while the full system is running

source ~/ros2_ws/src/ros2_control_demos/install/setup.bash

echo "=== 1. Active topics ==="
ros2 topic list | grep -E "camera|detected|joint"

echo ""
echo "=== 2. Camera image rate ==="
timeout 5 ros2 topic hz /overhead_camera/image 2>&1 | tail -1 || echo "No camera data"

echo ""
echo "=== 3. Joint states ==="
timeout 3 ros2 topic echo /joint_states --once 2>&1 | head -20 || echo "No joint states"

echo ""
echo "=== 4. Detected cubes (waiting 5s) ==="
timeout 5 ros2 topic echo /detected_cubes --once 2>&1 || echo "No detections yet"

echo ""
echo "=== 5. Active nodes ==="
ros2 node list 2>&1 | grep -E "perception|pick_and_place|controller|robot_state"

echo ""
echo "=== Done ==="