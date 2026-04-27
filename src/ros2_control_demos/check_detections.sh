# #!/bin/bash
# # check_detections.sh — monitor cube detections
# # Run while the full system is running with cubes spawned

# source ~/ros2_ws/src/ros2_control_demos/install/setup.bash

# echo "=== Checking perception node is running ==="
# ros2 node list 2>&1 | grep perception || echo "WARNING: perception node not found!"

# echo ""
# echo "=== Detected cubes topic (listening 10s) ==="
# echo "(Press Ctrl+C to stop early)"
# echo ""
# timeout 10 ros2 topic echo /detected_cubes --field data 2>&1 || echo "No detections received"


#!/bin/bash
# run_perception.sh — run the perception node directly to see errors
source ~/ros2_ws/src/ros2_control_demos/install/setup.bash
 
echo "=== Checking executable exists ==="
EXEC=$(ros2 pkg prefix ros2_control_demo_example_7)/lib/ros2_control_demo_example_7/perception_node
ls -la "$EXEC" 2>&1 || echo "NOT FOUND!"
 
echo ""
echo "=== Running perception node ==="
ros2 run ros2_control_demo_example_7 perception_node
 
# !/bin/bash
# debug_tf.sh — check what TF frames exist
# source ~/ros2_ws/src/ros2_control_demos/install/setup.bash

# echo "=== All TF frames ==="
# ros2 run tf2_tools view_frames --help > /dev/null 2>&1
# ros2 run tf2_ros tf2_echo world camera_link 2>&1 | head -5 &
# sleep 3
# kill %1 2>/dev/null

# echo ""
# echo "=== Full frame list ==="
# ros2 topic echo /tf_static --once 2>&1 | grep "child_frame_id" || echo "No static TF"
# echo "---"
# ros2 topic echo /tf --once 2>&1 | grep "child_frame_id" || echo "No dynamic TF"