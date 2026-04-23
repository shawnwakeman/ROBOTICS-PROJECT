# ROBOTICS-PROJECT

# 🤖 ROS 2 + Gazebo 6DOF Arm Simulation — Team README

A fully containerized robotics simulation running ROS 2 Jazzy + Gazebo Harmonic.
No local ROS install needed. Everything runs in Docker and streams to your browser.

---

## What Is This?

This repo contains a Docker-based ROS 2 workspace that simulates a **6-joint robotic arm mounted on a table** inside Gazebo. The GUI streams over a web port so it works identically on Mac (Intel or Apple Silicon), Windows, and Linux — no display configuration required.

**Stack:**
- ROS 2 Jazzy
- Gazebo Harmonic
- NoVNC (browser-based desktop streaming)
- gz_ros2_control (joint position controllers)

---

## Prerequisites



- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (make sure it's running)


---

## First-Time Setup

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd <your-repo-folder>

# 2. Build the Docker image (takes a few minutes the first time)
docker compose build

# 3. Start the container in the background
docker compose up -d
```

---

## Opening the Simulation in Your Browser

Once the container is running, open your browser and go to:

```
http://localhost:8080
```

You'll see a full Linux desktop streaming in your browser tab. That is is the robot's environment.

---

## Running the Arm Simulation

Inside the browser desktop, open a terminal and run:

```bash

cd ~/ros2_ws
colcon build
source install/setup.bash
ros2 launch my_robot_arm sim.launch.py
```

**What happens:**
1. Gazebo opens inside the browser tab
2. A wooden table appears with a blue 6DOF arm on top
3. The joint controllers load automatically in the background

---

## Sending Commands to the Arm

Open a **second terminal** inside the browser desktop and run this to see all active ROS topics:

```bash
ros2 topic list
```

To move the arm, publish a joint trajectory command to:

```
/arm_controller/joint_trajectory
```

Example command (moves all 6 joints to 0 radians):

```bash
ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{
  joint_names: [joint1, joint2, joint3, joint4, joint5, joint6],
  points: [{positions: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: {sec: 2}}]
}"
```

Change the `positions` values (in radians, range `-3.14` to `3.14`) to move individual joints.

---

## Project Structure

```
my_ros_workspace/
├── docker-compose.yml          # Container config
├── Dockerfile                  # ROS 2 image definition
└── src/
    └── my_robot_arm/
        ├── description/
        │   └── arm.urdf.xacro  # Robot model (links, joints, physics)
        ├── config/
        │   └── controllers.yaml # Joint controller config
        ├── launch/
        │   └── sim.launch.py   # Launches Gazebo + robot + controllers
        └── CMakeLists.txt
```

---

## Rebuilding After Code Changes

If you edit any files in `src/`, rebuild inside the browser terminal:

```bash
cd ~/ros2_ws
colcon build
source install/setup.bash
```

Then relaunch the simulation.

---

## Stopping Everything

```bash
docker compose down
```

---

cd ros2_control_demos
colcon build --symlink-install
source install/setup.bash
ros2 launch ros2_control_demo_example_7 view_r6bot.launch.py

cmd to rebuild docker container without cached files:


# 1. Stop and remove the broken container
docker compose down

# 2. Build from scratch (forces the ARM64 download and uses the right bash script)
docker compose build --no-cache

# 3. Start the container
docker compose up