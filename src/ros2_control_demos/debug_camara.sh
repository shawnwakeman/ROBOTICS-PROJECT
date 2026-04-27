#!/bin/bash
# debug_camera.sh — check if camera data is flowing
source ~/ros2_ws/src/ros2_control_demos/install/setup.bash

echo "=== All camera topics ==="
ros2 topic list | grep -i camera

echo ""
echo "=== Checking topic rates (5 seconds each) ==="

echo "--- /overhead_camera/image ---"
timeout 5 ros2 topic hz /overhead_camera/image 2>&1 || echo "No messages!"

echo ""
echo "--- Gazebo camera topics (raw gz side) ---"
gz topic -l 2>&1 | grep -i camera || echo "No gz camera topics found"

echo ""
echo "=== Camera info ==="
timeout 5 ros2 topic echo /overhead_camera/camera_info --once 2>&1 || echo "No camera_info!"