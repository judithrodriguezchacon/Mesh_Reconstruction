import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
import sensor_msgs_py.point_cloud2 as pc2
import numpy as np
import open3d as o3d

class RTABMapMesher(Node):
    def __init__(self):
        super().__init__('rtabmap_mesher')

        # Subscribe to rtabmap cloud map output
        self.subscription = self.create_subscription(
            PointCloud2,
            '/rtabmap/cloud_map',
            self.listener_callback,
            10
        )

        self.latest_msg = None
        self.is_processing = False

        # Process clouds every 0.5 seconds
        self.timer = self.create_timer(0.5, self.process_latest_cloud)

    def listener_callback(self, msg):
        self.latest_msg = msg

    def process_latest_cloud(self):
        if self.is_processing or self.latest_msg is None:
            return

        latest_msg = self.latest_msg
        self.latest_msg = None

        self.is_processing = True

        # Generate a list of xyz points
        points = []
        for p in pc2.read_points(latest_msg, field_names=('x', 'y', 'z'), skip_nans=True):
            points.append([p[0], p[1], p[2]])

        self.get_logger().info(f'Processing LATEST cloud with {len(points)} points')

        if len(points) < 100:
            self.get_logger().warn('Not enough points to mesh yet')
            self.is_processing = False
            return

        # Generate a cloud and insert the np array of points
        cloud = o3d.geometry.PointCloud()
        cloud.points = o3d.utility.Vector3dVector(np.array(points, dtype=np.float64))
        
        # Save raw registered cloud first        
        o3d.io.write_point_cloud('/home/yamato_matsumura/Mesh_Reconstruction/ros2_ws/point_clouds/rtabmap_cloud.pcd', cloud)
        self.get_logger().info('Saved point cloud to /home/yamato_matsumura/Mesh_Reconstruction/ros2_ws/point_clouds/rtabmap_cloud.pcd')

        # Downsample cloud
        cloud = cloud.voxel_down_sample(voxel_size=0.03)

        # Remove noise from cloud
        cloud, _ = cloud.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)

        # Estimate normals
        cloud.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(
                radius=0.10,
                max_nn=30
            )
        )
        cloud.orient_normals_consistent_tangent_plane(30)


        self.get_logger().info('Creating mesh...')

        mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
            cloud,
            depth=8
        )

        densities = np.asarray(densities)
        threshold = np.quantile(densities, 0.02)
        mesh.remove_vertices_by_mask(densities < threshold)

        # Write final mesh
        o3d.io.write_triangle_mesh('/home/yamato_matsumura/Mesh_Reconstruction/ros2_ws/meshes/rtabmap_mesh.ply', mesh)
        self.get_logger().info('Saved mesh to /home/yamato_matsumura/Mesh_Reconstruction/ros2_ws/meshes/rtabmap_mesh.ply')

        self.is_processing = False

def main(args=None):
    rclpy.init(args=args)
    node = RTABMapMesher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()