#!/bin/bash
# setup_permissions.sh — run once after rebuilding the Docker container
# Makes all scripts and Python nodes executable

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXAMPLE7_DIR=~/ros2_ws/src/ros2_control_demos/example_7

echo "=== Setting permissions for shell scripts ==="
chmod +x "${SCRIPT_DIR}/run_r6bot.sh" 2>/dev/null && echo "  run_r6bot.sh"
chmod +x "${SCRIPT_DIR}/run_rviz.sh" 2>/dev/null && echo "  run_rviz.sh"
chmod +x "${SCRIPT_DIR}/spawn_cube.sh" 2>/dev/null && echo "  spawn_cube.sh"
chmod +x "${SCRIPT_DIR}/spawn_random_cubes.sh" 2>/dev/null && echo "  spawn_random_cubes.sh"
chmod +x "${SCRIPT_DIR}/debug_gazebo.sh" 2>/dev/null && echo "  debug_gazebo.sh"
chmod +x "${SCRIPT_DIR}/debug_xacro.sh" 2>/dev/null && echo "  debug_xacro.sh"
chmod +x "${SCRIPT_DIR}/debug_camera.sh" 2>/dev/null && echo "  debug_camera.sh"

echo ""
echo "=== Setting permissions for Python nodes ==="
# Try common locations for the example_7 package
for DIR in \
    ~/ros2_ws/src/ros2_control_demos/example_7 \
    ~/ros2_ws/src/ros2_control_demos/ros2_control_demo_example_7 \
    ~/ros2_ws/src/ros2_control_demo_example_7; do
  if [ -d "${DIR}/scripts" ]; then
    chmod +x "${DIR}/scripts/"*.py 2>/dev/null
    echo "  Set permissions in ${DIR}/scripts/"
    ls -la "${DIR}/scripts/"*.py 2>/dev/null
    break
  fi
done

echo ""
echo "=== Done ==="