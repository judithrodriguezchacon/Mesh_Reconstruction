# RTABMap Mesh Reconstruction

This approach uses RTABMap for depth registration and Open3D for mesh generation to perform real-time 3D mesh reconstruction from an Oak-D stereo camera input. Mesh data is published live to the `/mesh` ROS 2 topic as well as saved locally.

**Pipeline:** Oak-D → RTABMap (depth registration + point cloud) → Open3D (meshing) → `/mesh` topic / file output

---

## Prerequisites

- Docker (with `sudo` privileges or appropriate group membership)
- Linux host OS (required for Oak-D USB device discovery)
- Oak-D camera

---

## Installation

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

> **Note:** `--privileged` is required to grant the container access to USB devices for Oak-D camera discovery. This flag should only be used in trusted environments.

**Subsequent sessions** — if the container already exists, start and attach to it with:

```bash
docker start mesh-dev
docker exec -it mesh-dev bash
```

---

## Usage

### 1. Build the ROS 2 workspace

Inside the container, build and source the workspace:

```bash
colcon build && source install/setup.bash
```

### 2. Launch the pipeline

Each component runs in its own terminal session. Open three terminals (via `docker exec -it mesh-dev bash`) and run the following:

| Terminal | Role | Command |
|----------|------|---------|
| 1 | Camera driver | `ros2 launch mesh_reconstruction camera.launch.py` |
| 2 | RTABMap registration | `ros2 launch mesh_reconstruction rtabmap.launch.py` |
| 3 | Mesh node | `ros2 run mesh_reconstruction mesh_node` |

Start the nodes in the order listed above to ensure proper topic availability at startup.

---

## Visualizing Results

### Live visualization

Open rviz2 and subscribe to the `/mesh` topic to view the mesh updating in real time as the camera moves through the environment.

```bash
rviz2
```

Add `/mesh` by topic.

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

## Dependencies

| Component | Role |
|-----------|------|
| [RTABMap](http://introlab.github.io/rtabmap/) | Real-time appearance-based mapping and depth registration |
| [Open3D](http://www.open3d.org/) | Point cloud processing and mesh generation |
| [DepthAI / depthai-ros](https://github.com/luxonis/depthai-ros) | Oak-D camera ROS 2 driver |
| ROS 2 | Middleware and topic communication |