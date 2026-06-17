# RTABMap Mesh Reconstruction

This approach uses RTABMap for depth registration and Open3D for mesh generation to perform real-time 3D mesh reconstruction from an Oak-D stereo camera input. Mesh data is published live to the `/mesh` ROS 2 topic as well as saved locally.

**Pipeline:** Oak-D → RTABMap (depth registration + point cloud) → Open3D (meshing) → `/mesh` topic / file output

---

## Prerequisites

- Linux host OS (required for Oak-D USB device discovery)
- Oak-D camera plugged in

---

## Installation

### 1. Clone the repository

```bash
git clone -b rtabmap https://github.com/judithrodriguezchacon/Mesh_Reconstruction.git
cd Mesh_Reconstruction
```

### 2. Build the Docker image

```bash
docker build -t mesh-reconstruction .
```

### 3. Start the container

```bash
docker run -it --name mesh-dev \
  --privileged \
  --network host \
  -v /dev:/dev \
  -v "$(pwd)/ros2_ws:/ros2_ws" \
  mesh-reconstruction
```

**Subsequent sessions** — if the container already exists, start and attach to it with:

```bash
docker start mesh-dev
docker exec -it mesh-dev bash
```

> **Note:** Installation command #2 and #3 may need to be run with `sudo` to ensure the container and camera both have the correct permissions to be discovered.

---

## Usage

### 1. Build the ROS 2 workspace

Inside the container, build and source the workspace:

```bash
colcon build && source install/setup.bash
```

### 2. Launch the pipeline

Each component runs in its own terminal. Open **three terminals** and attach each one to the container before running the commands below:

```bash
# Attach to the container (run in each terminal)
docker start mesh-dev
docker exec -it mesh-dev bash
colcon build && source install/setup.bash
```

Then start each node in order to ensure topics are available before dependent nodes start.

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
            ├── launch/
            │   ├── camera.launch.py
            │   └── rtabmap.launch.py
            └── mesh_reconstruction/
                └── mesh_node.py
```

---

## Dependencies

| Component | Role |
|-----------|------|
| [RTABMap](http://introlab.github.io/rtabmap/) | Real-time appearance-based mapping and depth registration |
| [Open3D](http://www.open3d.org/) | Point cloud processing and mesh generation |
| [DepthAI / depthai-ros](https://github.com/luxonis/depthai-ros) | Oak-D camera ROS 2 driver |
| ROS 2 | Middleware and topic communication |