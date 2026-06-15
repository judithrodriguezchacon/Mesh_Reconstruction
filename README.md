# RTABMap Mesh Generation

Depth registration and point cloud generation via RTABMap from Oak-D inputs, meshed with Open3D and published live to `/mesh`.

**Pipeline:** Oak-D camera → RTABMap registration → Open3D meshing → rviz2 / file output

---

## Installation

### 1. Clone the repo

```bash
# rtabmap branch
git clone -b rtabmap https://github.com/judithrodriguezchacon/Mesh_Reconstruction.git
cd Mesh_Reconstruction
```

### 2. Build and run the Docker container

```bash
sudo docker build -t mesh-reconstruction .
sudo docker run -it --name mesh-dev \
  --privileged --network host \
  -v /dev:/dev \
  -v "$(pwd)/ros2_ws:/ros2_ws" \
  mesh-reconstruction
```

> **Note:** The Oak-D camera requires Linux for USB discovery. `--privileged` grants the container device access.

---

## Usage

### 1. Build the workspace

```bash
cd ros2_ws && colcon build
```

### 2. Launch nodes — each in its own terminal

| Terminal | Command |
|----------|---------|
| 1 — Camera | `ros2 launch mesh_reconstruction camera.launch.py` |
| 2 — RTABMap | `ros2 launch mesh_reconstruction rtabmap.launch.py` |
| 3 — Mesh node | `ros2 run mesh_reconstruction mesh_node` |

---

## Visualizing Results

**Live in rviz2** — Subscribe to the `/mesh` topic to watch the mesh build in real time as the camera moves.

**File output** — Mesh and point cloud files are saved to:
- `ros2_ws/src/mesh`
- `ros2_ws/src/point_cloud`