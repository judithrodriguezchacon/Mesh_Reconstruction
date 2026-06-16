# ROS 2 Jazzy environment
FROM osrf/ros:jazzy-desktop-full

# Avoid interactive prompts during installs - (no 'Do you want to continue? [Y/N]' messages)
ENV DEBIAN_FRONTEND=noninteractive

# Downloads and installs all required packages
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    git \
    vim \
    usbutils \
    ros2-testing-apt-source \
    ros-jazzy-depthai-ros-v3 \
    && rm -rf /var/lib/apt/lists/* 

# Open3D
RUN pip3 install --break-system-packages --ignore-installed open3d

RUN pip3 install --force-reinstall numpy==1.26.4

# Workspace
WORKDIR /ros2_ws

# Source ROS 2 automatically:)
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
RUN echo "if [ -f /ros2_ws/install/setup.bash ]; then source /ros2_ws/install/setup.bash; fi" >> ~/.bashrc

CMD ["/bin/bash"]
