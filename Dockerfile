# ROS2 Jazzy
FROM osrf/ros:jazzy-desktop-full

ENV DEBIAN_FRONTEND=noninteractive

# General installs
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    git \
    vim \
    usbutils \
    && rm -rf /var/lib/apt/lists/*

# RTABMap and Depth ai installs
RUN apt-get update && apt-get install -y \
    ros-jazzy-depthai-ros-v3 \
    ros-jazzy-rtabmap-ros \
    && rm -rf /var/lib/apt/lists/*

# Open3D install
RUN pip3 install --break-system-packages --ignore-installed open3d


# Create ros2_ws folder
WORKDIR /ros2_ws/src

# Source ROS2
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc

WORKDIR /ros2_ws

# Start in bash
CMD ["/bin/bash"]