# RTABMap Mesh Reconstruction

This approach uses RTABMap for depth registration and Open3D for mesh generation to perform real-time 3D mesh reconstruction from an Oak-D stereo camera input. Mesh data is published live to the `/mesh` ROS 2 topic as well as saved locally.

**Pipeline:** Oak-D → RTABMap (depth registration + point cloud) → Open3D (meshing) → `/mesh` topic / file output

---

## Prerequisites

- Linux host OS (required for Oak-D USB device discovery)
- Oak-D camera plugged in

---

## Installation

> **Note:** Some commands are run with `sudo` to ensure the camera is discoverable by the Docker container.

### 1. Clone the repository

```bash
git clone -b rtabmap https://github.com/judithrodriguezchacon/Mesh_Reconstruction.git
cd Mesh_Reconstruction
```

### 2. Build the Docker image

```bash
sudo docker build -t mesh-reconstruction .
```

### 3. Start the container

```bash
sudo docker run -it --name mesh-dev \
  --privileged \
  --network host \
  -v /dev:/dev \
  -v "$(pwd)/ros2_ws:/ros2_ws" \
  mesh-reconstruction
```

**Subsequent sessions** — if the container already exists, start and attach to it with:

```bash
sudo docker start mesh-dev
sudo docker exec -it mesh-dev bash
```

---

## Usage

### Launch the pipeline

Each component runs in its own terminal. Open **three terminals** and run the following in each to attach to the container:

```bash
sudo docker start mesh-dev && sudo docker exec -it mesh-dev bash
colcon build && source install/setup.bash
```

Then start each node **in order** to ensure topics are available before dependent nodes start:

**Terminal 1 — Camera driver**
```bash
ros2 launch mesh_reconstruction camera.launch.py
```

**Terminal 2 — RTABMap registration**
```bash
ros2 launch mesh_reconstruction rtabmap.launch.py
```

**Terminal 3 — Mesh node**
```bash
ros2 run mesh_reconstruction mesh_node
```

---

## Visualizing Results

### Live visualization

Open RViz2 and subscribe to the `/mesh` topic to view the mesh updating as the camera moves through the environment:

```bash
rviz2
```

Then add `/mesh` by topic in the RViz2 panel.

### File output

Mesh and point cloud files are written to the following directories within the workspace:

| Output | Path |
|--------|------|
| Mesh files | `ros2_ws/src/mesh/` |
| Point cloud files | `ros2_ws/src/point_cloud/` |

---

## Repository Structure

```
Mesh_Reconstruction/
├── Dockerfile
└── ros2_ws/
    └── src/
        └── mesh_reconstruction/
            ├── config/
            │   └── camera_config.yaml
            ├── launch/
            │   ├── camera.launch.py
            │   └── rtabmap.launch.py
            └── mesh_reconstruction/
                └── mesh_node.py
```

---

## Parameter Configuration

### Camera

The pipeline launches the camera using the configurations from the `driver.launch.py` launcher provided by the DepthAI ROS driver package. See the [DepthAI ROS launch file docs](https://docs.luxonis.com/software-v3/depthai/ros/driver/#DepthAI%20ROS%20Driver-Launch%20files) for full details.

Additional parameters are set in:

```
ros2_ws/src/mesh_reconstruction/config/camera_config.yaml
```

Notable parameters include `i_threshold_filter_min_range` and `i_threshold_filter_max_range`, which restrict the camera's depth range to isolate the object of interest and suppress background geometry. A full list of configurable camera parameters is available in the [DepthAI ROS parameter docs](https://docs.luxonis.com/software-v3/depthai/ros/parameters).

### RTABMap

RTABMap parameters are configured in:

```
ros2_ws/src/mesh_reconstruction/launch/rtabmap.launch.py
```

Additional parameters can be added to the `parameters` dictionary in that file. To discover all available parameters while RTABMap is running:

```bash
ros2 param dump /rtabmap
```

---

## Dependencies

| Component | Role |
|-----------|------|
| [RTABMap](http://introlab.github.io/rtabmap/) | Real-time appearance-based mapping and depth registration |
| [Open3D](http://www.open3d.org/) | Point cloud processing and mesh generation |
| [DepthAI / depthai-ros](https://github.com/luxonis/depthai-ros) | Oak-D camera ROS 2 driver |
| ROS 2 | Middleware and topic communication |