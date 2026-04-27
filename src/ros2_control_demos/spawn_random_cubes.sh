#!/bin/bash
# spawn_random_cubes.sh — spawn N random cubes on the table
#
# Usage: bash spawn_random_cubes.sh [N] [size]
#   N:    number of cubes (default: 5)
#   size: cube side length in meters (default: 0.04)

N=${1:-5}
SIZE=${2:-0.04}
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

COLORS=("red" "green" "blue")

# Spawn area in table coordinates
X_MIN=0.3
X_MAX=1.7
Y_MIN=0.5
Y_MAX=1.3

echo "=== Spawning ${N} random cubes ==="

for i in $(seq 1 $N); do
  TABLE_X=$(awk "BEGIN { srand($(date +%s%N)); printf \"%.3f\", $X_MIN + ($X_MAX - $X_MIN) * rand() }")
  TABLE_Y=$(awk "BEGIN { srand($(date +%s%N) + $i); printf \"%.3f\", $Y_MIN + ($Y_MAX - $Y_MIN) * rand() }")

  ROT_DEG=$((RANDOM % 360))
  COLOR=${COLORS[$((RANDOM % 3))]}

  echo "Cube ${i}/${N}: table(${TABLE_X}, ${TABLE_Y}) rot=${ROT_DEG}° color=${COLOR}"
  bash "${SCRIPT_DIR}/spawn_cube.sh" "$TABLE_X" "$TABLE_Y" "$ROT_DEG" "$COLOR" "$SIZE"

  sleep 1
done

echo "=== All ${N} cubes spawned ==="