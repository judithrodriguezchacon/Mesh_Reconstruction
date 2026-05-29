## change of plans gang
### first time do
```
git clone ...
docker build -t mesh-reconstruction .
docker run -it --name mesh-dev \
  --network=host \
  --privileged \
  -v /dev:/dev \
  -v $(pwd)/ros2_ws:/ros2_ws \
  mesh-reconstruction
```

### On Windows...
```
git clone https://github.com/judithrodriguezchacon/Mesh_Reconstruction.git
cd Mesh_Reconstruction
docker build -t mesh-reconstruction .
docker run -it --name mesh-dev -v $(pwd -W)/ros2_ws:/ros2_ws mesh-reconstruction
```

### next times 
```
docker start mesh-dev
docker exec -it mesh-dev bash
```
### notes
we all have to mount when running, that is not something in the dockerfile so that is the reason of  -v $(pwd)/ros2_ws:/ros2_ws \n
also:
this is not the only way to do it, we could either create a new container each time or have one container that remains alive, I chose the one container for its simplicity

### Linux 1st time startup Terminal 1
```
git clone https://github.com/judithrodriguezchacon/Mesh_Reconstruction.git
cd Mesh_Reconstruction
sudo docker build -t mesh-reconstruction .
sudo docker run -it --name mesh-dev --privileged --network host -v /dev:/dev -v "$(pwd)/ros2_ws:/ros2_ws" mesh-reconstruction
source /opt/ros/jazzy/setup.bash
ros2 launch depthai_ros_driver_v3 driver.launch.py
```

### Linux 1st time startup Terminal 2
```
sudo docker exec -it mesh-dev bash
source /opt/ros/jazzy/setup.bash

ros2 node list
ros2 topic list
```

### Returning Linux setup
```
sudo docker start -ai mesh-dev
sudo docker exec -it mesh-dev bash
source /opt/ros/jazzy/setup.bash
```
