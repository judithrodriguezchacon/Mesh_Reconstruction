import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # 1. Locate the read-only, system-installed rtabmap_launch package share path
    official_rtabmap_dir = get_package_share_directory('rtabmap_launch')

    return LaunchDescription([
        IncludeLaunchDescription(
            # 2. Tell ROS to point directly to the official underlying launch file (Jazzy path layout)
            PythonLaunchDescriptionSource(
                os.path.join(official_rtabmap_dir, 'launch', 'rtabmap.launch.py')
            ),
            # 3. Inject all of your optimized custom parameters automatically
            launch_arguments={
                # Camera Topics (Listening directly to the raw 30 FPS bag streams)
                'rgb_topic': '/oak/rgb/image_raw',
                'depth_topic': '/oak/stereo/image_raw',
                'camera_info_topic': '/oak/rgb/camera_info',
                'imu_topic': '/oak/imu/data',
                'frame_id': 'oak_parent_frame',
                
                # REBUILT BALANCED SYNCHRONIZATION (Fixes the 5-second starvation drop)
                'approx_sync': 'true',
                'approx_sync_max_interval': '0.03', # Increased to better match 30fps frame interval (33ms)
                
                # NODE-SPECIFIC QUEUES (This isolates the lag while keeping data alive)
                'odom_topic_queue_size': '10',       # TIGHT: Keeps odometry tracking instant (kills the 1.2s lag)
                'rtabmap_topic_queue_size': '100',   # WIDE: Gives the 1Hz mapping engine room to sample frames
                'sync_queue_size': '100',            # Global fallback buffer
                'qos': '2',                          # Matches bag QoS profiles automatically

                # Performance & Environment Settings
                'wait_imu_to_init': 'true',
                'use_sim_time': 'true',
                'rtabmap_viz': 'false',

                # RTAB-MAP NODE OPTIMIZATIONS (Map Cleaning & Storage)
                'rtabmap_args': (
                    '--Vis/MaxFeatures 600 '        # Reduced features for better robustness to blur/shake
                    '--Vis/MinInliers 20 '          # Increased to require better quality loop closures
                    '--Rtabmap/DetectionRate 1.0 '  # Increased to 1.0Hz for more frequent map updates
                    '--Mem/IncrementalMemory true '
                    '--Kp/MaxFeatures 600 '         # Controls loop closure database size

                    # Point Cloud Cleanup (Voxel Grid & Noise Isolation filters)
                    '--Cloud/VoxelSize 0.025 '      # Smaller voxel (2.5cm) for finer detail
                    '--Cloud/OutlierRadius 0.4 '    # Increased radius to better capture motion-blurred points
                    '--Cloud/OutlierMinNeighbors 6 '# Increased min neighbors to keep only stable points
                    '--Cloud/NoiseFiltering true '  # Re-enable noise filtering to clean up point cloud
                    '--Cloud/VoxelFiltering true '  # Enable voxel filtering for additional cleanup
                ),
                
                # ODOMETRY NODE OPTIMIZATIONS (Tracking Recovery & Surface Handling)
                'odom_args': (
                    '--Odom/ResetCountdown 1 '
                    '--OdomF2M/MaxSize 1000 '       # Increased visual vocabulary for better tracking robustness
                    '--Odom/IMUWeight 0.1 '         # Incorporate IMU data for improved motion estimation
                    '--Vis/FeatureType 8 '          # Keeps ORB (Type 8) active for smooth car surfaces
                    '--Vis/CorGuessWinSize 20 '     # Tightened matching window search zone to maximize processing speed
                )
            }.items()
        )
    ])
