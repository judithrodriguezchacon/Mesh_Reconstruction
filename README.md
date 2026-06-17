# Industrial Reconstruction

This branch contains the setup used to test the Stratom Industrial Reconstruction library with an OAK-D Pro camera.

## First Time Setup

Clone the repository and pull the submodules, then cd into it:

```bash
git clone --recurse-submodules -b testIndustrial_reconstruction https://github.com/judithrodriguezchacon/Mesh_Reconstruction.git
```

If you already cloned the repo:

```bash
git submodule update --init --recursive
```

Build the Docker image:

```bash
sudo docker build -t mesh-reconstruction .
```

Start the container:

```bash
sudo docker run -it --name mesh-dev \
  --network=host \
  --privileged \
  -v /dev:/dev \
  -v $(pwd)/ros2_ws:/ros2_ws \
  mesh-reconstruction
```
Now follow daily use instructions starting at building the workspace.

## Daily Use

Start the container:

```bash
sudo docker start mesh-dev
```

Open a shell inside the container:

```bash
sudo docker exec -it mesh-dev bash
```

Build the workspace:

```bash
cd /ros2_ws

colcon build

source install/setup.bash
```

> Run `source install/setup.bash` in every new terminal.

---

## Running Live Reconstruction

Terminal 1:

```bash
source /ros2_ws/install/setup.bash

ros2 launch industrial_reconstruction_config industrial_oak.launch.py
```

Terminal 2:

```bash
source /ros2_ws/install/setup.bash

ros2 launch industrial_reconstruction_config camera.launch.py
```

---

## Running From a Bag

Terminal 1:

```bash
source /ros2_ws/install/setup.bash

ros2 launch industrial_reconstruction_config industrial_oak.launch.py
```

Terminal 2:

```bash
source /ros2_ws/install/setup.bash

ros2 bag play bagName.mcap --clock --rate 0.5
```

---

## Save the Mesh

Create the meshes folder if it does not exist:

```bash
mkdir -p /ros2_ws/meshes
```

Save the mesh:

```bash
ros2 service call /stop_reconstruction \
industrial_reconstruction_msgs/srv/StopReconstruction \
"{
archive_directory: '',
mesh_filepath: '/ros2_ws/meshes/output_mesh.ply',
normal_filters: [],
min_num_faces: 0
}"
```

The mesh will be saved to:

```text
/ros2_ws/meshes/output_mesh.ply
```
