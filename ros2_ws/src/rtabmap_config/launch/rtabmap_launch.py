import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    official_rtabmap_dir = get_package_share_directory('rtabmap_launch')

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(official_rtabmap_dir, 'launch', 'rtabmap.launch.py')
            ),
            launch_arguments={
                # Camera Topics
                'rgb_topic': '/oak/rgb/image_raw',
                'depth_topic': '/oak/stereo/image_raw',
                'camera_info_topic': '/oak/rgb/camera_info',
                'frame_id': 'oak_rgb_camera_frame',

                # Bigger queues so fast bag playback doesn't overflow the sync buffer
                'topic_queue_size': '50',
                'sync_queue_size': '50',

                # Synchronization
                'approx_sync': 'true',
                'use_sim_time': 'true',

                # GUI
                'rtabmap_viz': 'false',
                'rviz': 'false',

                'rtabmap_args': '--delete_db_on_start --Rtabmap/DetectionRate 1',
            }.items()
        )
    ])