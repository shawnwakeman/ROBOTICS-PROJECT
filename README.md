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