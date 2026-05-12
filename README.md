# Robotics Project

github repo: https://github.com/shawnwakeman/ROBOTICS-PROJECT
## Running the Project

### 1. Build the Docker image

```bash
docker compose build
```

### 2. Start the container

```bash
docker compose up
```

### 3. Open the simulation UI

Navigate to [http://localhost:8080](http://localhost:8080) in your browser.

### 4. Launch the full simulation with the build script

```bash
cd ~/ros2_ws/src/ros2_control_demos
bash run_full.sh
```

## Stopping

```bash
docker compose down
```

## Force Rebuild (no cache)

```bash
docker compose down
docker compose build --no-cache
docker compose up
```
