from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_setup(context):
    name = LaunchConfiguration("name").perform(context)

    # Get sim time arg
    sim_time_str = LaunchConfiguration("use_sim_time").perform(context)
    use_sim_time_bool = sim_time_str.lower() == 'true'

    parameters = [
        {
            "frame_id": "oak_parent_frame",
            "subscribe_rgb": True,
            "subscribe_depth": True,
            "subscribe_odom_info": False,
            "approx_sync": True,
            "use_sim_time": use_sim_time_bool,
            'Mem/NotLinkedNodesKept': 'false',
            "Rtabmap/DetectionRate": "10.0",
            "Grid/CellSize": '0.001',
        }
    ]

    # Map topic names to match what Oak-D gives
    remappings = [
        ("rgb/image", name + "/rgb/image_raw"),
        ("rgb/camera_info", name + "/rgb/camera_info"),
        ("depth/image", name + "/stereo/image_raw"),
        ("odom", name + "/vio/odometry")
    ]

    return [
        # RTABMap SLAM node
        Node(
            package="rtabmap_slam",
            executable="rtabmap",
            name="rtabmap",
            parameters=parameters,
            remappings=remappings,
            arguments=["-d"], # Clears previous database memory on startup
        ),
        # RTABmap visualizer
        Node(
            package="rtabmap_viz",
            executable="rtabmap_viz",
            output="screen",
            parameters=parameters,
            remappings=remappings,
        ),
    ]

def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument("name", default_value="oak"),
        DeclareLaunchArgument("use_sim_time", default_value="false"),
    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )