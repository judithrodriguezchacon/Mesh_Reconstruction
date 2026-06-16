from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import AnyLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from pathlib import Path


def generate_launch_description():
    depth_topic = LaunchConfiguration("depth_topic")
    color_topic = LaunchConfiguration("color_topic")
    camera_info_topic = LaunchConfiguration("camera_info_topic")
    rgbd_debug_bag = LaunchConfiguration("rgbd_debug_bag")

    tracking_frame = LaunchConfiguration("tracking_frame")
    relative_frame = LaunchConfiguration("relative_frame")

    mesh_filepath = LaunchConfiguration("mesh_filepath")
    archive_directory = LaunchConfiguration("archive_directory")

    voxel_length = LaunchConfiguration("voxel_length")
    sdf_trunc = LaunchConfiguration("sdf_trunc")
    depth_scale = LaunchConfiguration("depth_scale")
    depth_trunc = LaunchConfiguration("depth_trunc")
    slop = LaunchConfiguration("slop")
    cache_count = LaunchConfiguration("cache_count")
    live = LaunchConfiguration("live")

    record_rgbd_debug = LaunchConfiguration("record_rgbd_debug")

    reconstruction_launch = (
        Path(get_package_share_directory("industrial_reconstruction"))
        / "launch"
        / "reconstruction.launch.xml"
    )

    start_reconstruction_yaml = [
        "{",
        "tracking_frame: '", tracking_frame, "',",
        "relative_frame: '", relative_frame, "',",
        # increased translation and rotational distance thresholds can help with reconstruction in environments with less geometric texture
        "translation_distance: 0.01,",
        "rotational_distance: 0.02,",
        "live: ", live, ",",
        "tsdf_params: {",
        "voxel_length: ", voxel_length, ",",
        "sdf_trunc: ", sdf_trunc, ",",
        "min_box_values: {x: 0.0, y: 0.0, z: 0.0},",
        "max_box_values: {x: 0.0, y: 0.0, z: 0.0}",
        "},",
        "rgbd_params: {",
        "depth_scale: ", depth_scale, ",",
        "depth_trunc: ", depth_trunc, ",",
        "convert_rgb_to_intensity: false",
        "}",
        "}",
    ]

    return LaunchDescription([
        # Camera/bag topics
        DeclareLaunchArgument("depth_topic", default_value="/oak/stereo/image_raw"), 
        DeclareLaunchArgument("color_topic", default_value="/oak/rgb/image_raw"),
        DeclareLaunchArgument("camera_info_topic", default_value="/oak/rgb/camera_info"),

        # TF frames
        DeclareLaunchArgument("tracking_frame", default_value="oak_rgb_camera_optical_frame"),
        DeclareLaunchArgument("relative_frame", default_value="odom"),

        # Output paths
        DeclareLaunchArgument("mesh_filepath", default_value="/ros2_ws/meshes/oak_mesh.ply"),
        DeclareLaunchArgument("archive_directory", default_value="/ros2_ws/reconstruction_archive"),
        DeclareLaunchArgument("rgbd_debug_bag", default_value="/ros2_ws/debug_bags/oak_rgbd_debug"),


        # TSDF parameters -- library tuning may be needed for different environments and applications
        DeclareLaunchArgument("voxel_length", default_value="0.02"),
        DeclareLaunchArgument("sdf_trunc", default_value="0.06"),
        DeclareLaunchArgument("depth_scale", default_value="1000.0"),
        DeclareLaunchArgument("depth_trunc", default_value="1.2"),
        DeclareLaunchArgument("slop", default_value="0.6"),
        DeclareLaunchArgument("cache_count", default_value="30"),
        DeclareLaunchArgument("live", default_value="true"),

        # RGB-D debug recording
        DeclareLaunchArgument("record_rgbd_debug", default_value="false"),

        IncludeLaunchDescription(
            AnyLaunchDescriptionSource(str(reconstruction_launch)),
            launch_arguments={
                "depth_image_topic": depth_topic,
                "color_image_topic": color_topic,
                "camera_info_topic": camera_info_topic,
                "slop": slop,
                "cache_count": cache_count,
                "use_sim_time": "true",
            }.items(),
        ),

        # Optional RGB-D debug recording. Industrial Reconstruction uses RGB image, depth image, camera info, and TF.
        ExecuteProcess(
            condition=IfCondition(record_rgbd_debug),
            cmd=[
                "ros2", "bag", "record",
                "-o", rgbd_debug_bag,
                "/oak/stereo/image_raw",
                "/oak/rgb/image_raw",
                "/oak/rgb/camera_info",
                "/oak/stereo/camera_info",
                "/oak/vio/odometry",
                "/tf",
                "/tf_static",
                "/clock",
            ],
            output="screen",
        ),

        TimerAction(
            period=15.0, #increase delay if reconstruction fails to start before service call is made
            actions=[
                ExecuteProcess(
                    cmd=[
                        "ros2", "service", "call",
                        "/start_reconstruction",
                        "industrial_reconstruction_msgs/srv/StartReconstruction",
                        start_reconstruction_yaml,
                    ],
                    output="screen",
                )
            ],
        ),

        # Stop manually:
        # ros2 service call /stop_reconstruction industrial_reconstruction_msgs/srv/StopReconstruction "{
        #   archive_directory: '/ros2_ws/reconstruction_archive/test_run',
        #   mesh_filepath: '/ros2_ws/meshes/test_mesh.ply',
        #   normal_filters: [],
        #   min_num_faces: 1000
        # }"
    ])
