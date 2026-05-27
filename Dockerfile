#image we're using
FROM osrf/ros:jazzy-desktop-full

#avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

#install useful ROS + Python tools
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

#create ROS workspace
WORKDIR /ros2_ws

#copy workspace into container
COPY ros2_workspace/src ./src

#build workspace
SHELL ["/bin/bash", "-c"]

RUN source /opt/ros/jazzy/setup.bash && \
    colcon build

#source ROS automatically
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
RUN echo "source /ros2_ws/install/setup.bash" >> ~/.bashrc

CMD ["/bin/bash"]
