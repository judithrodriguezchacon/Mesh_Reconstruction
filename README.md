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

