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
    pointcloud_topic = LaunchConfiguration("pointcloud_topic")

    tracking_frame = LaunchConfiguration("tracking_frame")
    relative_frame = LaunchConfiguration("relative_frame")

    mesh_filepath = LaunchConfiguration("mesh_filepath")
    archive_directory = LaunchConfiguration("archive_directory")
    pointcloud_bag = LaunchConfiguration("pointcloud_bag")

    voxel_length = LaunchConfiguration("voxel_length")
    sdf_trunc = LaunchConfiguration("sdf_trunc")
    depth_scale = LaunchConfiguration("depth_scale")
    depth_trunc = LaunchConfiguration("depth_trunc")
    slop = LaunchConfiguration("slop")
    cache_count = LaunchConfiguration("cache_count")
    live = LaunchConfiguration("live")

    record_pointclouds = LaunchConfiguration("record_pointclouds")

    reconstruction_launch = (
        Path(get_package_share_directory("industrial_reconstruction"))
        / "launch"
        / "reconstruction.launch.xml"
    )

    start_reconstruction_yaml = [
        "{",
        "tracking_frame: '", tracking_frame, "',",
        "relative_frame: '", relative_frame, "',",
        "translation_distance: 0.0,",
        "rotational_distance: 0.0,",
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
        DeclareLaunchArgument("pointcloud_topic", default_value="/oak/points"),

        # TF frames
        DeclareLaunchArgument("tracking_frame", default_value="oak_rgb_camera_optical_frame"),
        DeclareLaunchArgument("relative_frame", default_value="odom"),

        # Output paths
        DeclareLaunchArgument("mesh_filepath", default_value="/ros2_ws/meshes/oak_mesh.ply"),
        DeclareLaunchArgument("archive_directory", default_value="/ros2_ws/reconstruction_archive"),
        DeclareLaunchArgument("pointcloud_bag", default_value="/ros2_ws/point_clouds/oak_pointcloud_debug"),

        # TSDF reconstruction tuning parameters
        DeclareLaunchArgument("voxel_length", default_value="0.02"),
        DeclareLaunchArgument("sdf_trunc", default_value="0.06"),
        DeclareLaunchArgument("depth_scale", default_value="1000.0"),
        DeclareLaunchArgument("depth_trunc", default_value="2.0"),
        DeclareLaunchArgument("slop", default_value="0.6"),
        DeclareLaunchArgument("cache_count", default_value="30"),
        DeclareLaunchArgument("live", default_value="true"),

        # Point cloud recording
        DeclareLaunchArgument("record_pointclouds", default_value="true"),

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

        # Record the raw point cloud topic while reconstructing. --debugging purposes, can be used to compare the reconstruction results with the raw point clouds.
        ExecuteProcess(
            condition=IfCondition(record_pointclouds),
            cmd=[
                "ros2", "bag", "record",
                "-o", pointcloud_bag,
                pointcloud_topic,
                "/tf",
                "/tf_static",
                "/clock",
            ],
            output="screen",
        ),

        TimerAction(
            period=3.0,
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
    ])