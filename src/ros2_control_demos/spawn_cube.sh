#!/bin/bash
# spawn_cube.sh — spawn a cube on the table using table-corner coordinates
#
# Table origin (0,0) = back-left corner of the table
# X: 0 → 2.0  (left to right)
# Y: 0 → 1.6  (back to front)
#
# Usage: bash spawn_cube.sh X Y [rotation_deg] [color] [size]
#
# Examples:
#   bash spawn_cube.sh 1.0 0.8                     # center of table, red
#   bash spawn_cube.sh 0.5 1.0 45 blue             # blue cube rotated 45°
#   bash spawn_cube.sh 1.0 0.8 0 green 0.05        # green 5cm cube

source ~/ros2_ws/src/ros2_control_demos/install/setup.bash

TABLE_X=${1:?  "Usage: bash spawn_cube.sh X Y [rotation_deg] [color] [size]"}
TABLE_Y=${2:?  "Provide Y (0-1.6, back to front)"}
ROT_DEG=${3:-0}
COLOR=${4:-red}
SIZE=${5:-0.08}
MASS=0.05

# Convert table coords to world coords and degrees to radians using awk
read WORLD_X WORLD_Y WORLD_Z YAW <<< $(awk "BEGIN {
  printf \"%.6f %.6f %.6f %.6f\", -1.0 + $TABLE_X, -0.8 + $TABLE_Y, 0.75 + $SIZE / 2.0, $ROT_DEG * 3.14159265358979 / 180.0
}")

# Pick color values
case $COLOR in
  red)   R=0.8; G=0.1; B=0.1 ;;
  green) R=0.1; G=0.8; B=0.1 ;;
  blue)  R=0.1; G=0.1; B=0.8 ;;
  *)     R=0.8; G=0.8; B=0.1 ;;
esac

NAME="cube_${COLOR}_$(date +%s%N)"

SDF="<?xml version='1.0'?>
<sdf version='1.8'>
  <model name='${NAME}'>
    <link name='link'>
      <inertial>
        <mass>${MASS}</mass>
        <inertia>
          <ixx>0.00001</ixx><iyy>0.00001</iyy><izz>0.00001</izz>
          <ixy>0</ixy><ixz>0</ixz><iyz>0</iyz>
        </inertia>
      </inertial>
      <collision name='collision'>
        <geometry>
          <box><size>${SIZE} ${SIZE} ${SIZE}</size></box>
        </geometry>
        <surface>
          <friction>
            <ode><mu>1.0</mu><mu2>1.0</mu2></ode>
          </friction>
        </surface>
      </collision>
      <visual name='visual'>
        <geometry>
          <box><size>${SIZE} ${SIZE} ${SIZE}</size></box>
        </geometry>
        <material>
          <ambient>${R} ${G} ${B} 1</ambient>
          <diffuse>${R} ${G} ${B} 1</diffuse>
        </material>
      </visual>
    </link>
  </model>
</sdf>"

echo "Spawning ${COLOR} cube at table(${TABLE_X}, ${TABLE_Y}) rot=${ROT_DEG}° → world(${WORLD_X}, ${WORLD_Y}, ${WORLD_Z})"
ros2 run ros_gz_sim create \
  -string "$SDF" \
  -name "$NAME" \
  -x "$WORLD_X" \
  -y "$WORLD_Y" \
  -z "$WORLD_Z" \
  -Y "$YAW" \
  2>&1
echo "Done."