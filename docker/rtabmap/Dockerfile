FROM osrf/ros:jazzy-desktop

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y \
    ros-jazzy-rtabmap-ros \
    ros-jazzy-foxglove-bridge \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-rosbag2-storage-mcap \
    ros-jazzy-tf2-tools \
    ros-jazzy-rviz2 \
    git \
    nano \
    && rm -rf /var/lib/apt/lists/*

RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc && \
    echo "export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp" >> /root/.bashrc

WORKDIR /ros2_ws
