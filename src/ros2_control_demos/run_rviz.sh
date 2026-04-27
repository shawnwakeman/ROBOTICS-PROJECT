
#!/bin/bash
# run_rviz.sh — launch RViz with pre-configured camera displays
# Run in a separate terminal while Gazebo is running
 
source ~/ros2_ws/src/ros2_control_demos/install/setup.bash
 
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="${SCRIPT_DIR}/r6bot_gazebo.rviz"
 
if [ ! -f "$CONFIG" ]; then
  echo "WARNING: Config file not found at ${CONFIG}, launching default RViz"
  rviz2
else
  rviz2 -d "$CONFIG"
fi
 
