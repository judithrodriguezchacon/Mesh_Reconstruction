#ros and python library
import rclpy
from rclpy.node import Node

#messages for the point cloud
from sensor_msgs.msg import PointCloud2
import sensor_msgs_py.point_cloud2 as pc2

#num py and meshing library
import numpy as np
import open3d as o3d

class RTABMapMesher(Node):
    #constructor
    def __init__(self):
        #call it rtabmap_mesher
        super().__init__('rtabmap_mesher')

        #subscribe to the rtabmap output that will give us the registered point cloud
        self.subscription = self.create_subscription(
            PointCloud2,
            '/rtabmap/cloud_map',
            self.cloud_callback,
            10
        )

        self.saved_once = False

    #what we will be doing with the rtab info
    def cloud_callback(self, msg):
        if self.saved_once:
            return

        points = []

        #generating a list of xyz points
        for p in pc2.read_points(
            msg,
            field_names=('x', 'y', 'z'),
            skip_nans=True
        ):
            points.append([p[0], p[1], p[2]])

        self.get_logger().info(f'Received cloud with {len(points)} points')


        if len(points) < 100:
            self.get_logger().warn('Not enough points to mesh yet')
            return

        #generate a cloud and insert the np array of points and (dont know what dtype is)
        cloud = o3d.geometry.PointCloud()
        cloud.points = o3d.utility.Vector3dVector(
            np.array(points, dtype=np.float64)
        )
        
        # Save raw registered cloud first
        # o3d.io.write_point_cloud('/ros2_ws/meshes/rtabmap_cloud.pcd', cloud)
        # self.get_logger().info('Saved point cloud to /ros2_ws/meshes/rtabmap_cloud.pcd')

        # Downsample
        cloud = cloud.voxel_down_sample(voxel_size=0.03)

        # Remove noise
        cloud, _ = cloud.remove_statistical_outlier(
            nb_neighbors=20,
            std_ratio=2.0
        )

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

        o3d.io.write_triangle_mesh('ros2_ws/meshes/rtabmap_mesh.ply', mesh)

        self.get_logger().info('Saved mesh to ros2_ws/meshes/rtabmap_mesh.ply')

        self.saved_once = True


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