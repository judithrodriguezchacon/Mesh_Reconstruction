"""
Launches Oak-D camera with driver.launch.py file
Uses custom configurations found in ~/Mesh_Reconstruction/ros2_ws/src/camera_config.yaml
"""

import os
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    depthai_prefix = get_package_share_directory("depthai_ros_driver_v3")
    
    name = LaunchConfiguration("name")
    params_file = LaunchConfiguration("params_file")

    declared_arguments = [
        DeclareLaunchArgument("name", default_value="oak"),
        DeclareLaunchArgument(
            "params_file",
            default_value=os.path.join(
                str(Path.home()), 
                "Mesh_Reconstruction", 
                "ros2_ws", 
                "src", 
                "mesh_reconstruction", 
                "config", 
                "camera_config.yaml"),
        ),
    ]

    camera_driver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(depthai_prefix, "launch", "driver.launch.py")
        ),
        launch_arguments={"name": name, "params_file": params_file}.items(),
    )

    return LaunchDescription(declared_arguments + [camera_driver])