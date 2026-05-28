#ROS2 jazzy enviroment
FROM osrf/ros:jazzy-desktop-full

#avoid interactive prompts during installs
ENV DEBIAN_FRONTEND=noninteractive

#install useful ROS2 + Python development tools
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

#create the ROS2 workspace location inside the container
WORKDIR /ros2_ws

#source ROS2 automatically when opening the container
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc

#start in bash
CMD ["/bin/bash"]
