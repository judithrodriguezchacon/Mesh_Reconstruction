## Setup

### 1. Clone the repository

```bash
git clone https://github.com/judithrodriguezchacon/Mesh_Reconstruction.git
cd Mesh_Reconstruction
```


### 2. Build the Docker image

```bash
docker build -t mesh-reconstruction .
```


### 3. Run the container

```bash
docker run -it mesh-reconstruction
```

---


### Build ROS2 Notes

Inside the container:

```bash
source /opt/ros/jazzy/setup.bash
```

To build the workspace:

```bash
cd /ros2_workspace
colcon build
source install/setup.bash
```
