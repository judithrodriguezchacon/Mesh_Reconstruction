import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    depthai_prefix = get_package_share_directory("depthai_ros_driver_v3")
    config_dir = os.path.join(
        get_package_share_directory("industrial_reconstruction_config"),
        "config"
    )

    name = LaunchConfiguration("name")
    params_file = LaunchConfiguration("params_file")

    return LaunchDescription([
        DeclareLaunchArgument("name", default_value="oak"),
        DeclareLaunchArgument(
            "params_file",
            default_value=os.path.join(config_dir, "camera_config.yaml"),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(depthai_prefix, "launch", "vio.launch.py")
            ),
            launch_arguments={
                "name": name,
                "params_file": params_file,
            }.items(),
        ),
    ])
