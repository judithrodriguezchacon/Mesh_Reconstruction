# Industrial Reconstruction

Build:

```bash

cd /ros2_ws

colcon build

source install/setup.bash

```

Launch reconstruction:

```bash

ros2 launch industrial_reconstruction industrial_oak.launch.py

```

Play a bag:

```bash

ros2 bag play bagName.mcap --clock --rate 0.5

```

Save the mesh:

```bash

ros2 service call /stop_reconstruction industrial_reconstruction_msgs/srv/StopReconstruction "{
archive_directory: '',
mesh_filepath: '/ros2_ws/meshes/output_mesh.ply',
normal_filters: [],
min_num_faces: 0
}"

```

---

### Useful Commands

See available topics:

```bash

ros2 topic list

```

See running nodes:

```bash

ros2 node list

```

See TF tree:

```bash

ros2 run tf2_tools view_frames

```

