import rclpy

from rclpy.node import Node
from sensor_msgs.msg import PointCloud2

import sensor_msgs_py.point_cloud2 as pc2
import open3d as o3d

import numpy as np

class PointCloudToMesh(Node):
    def __init__(self):
        super().__init__('pointcloud_to_mesh')
        self.points = []
        self.max_frames = 10 #changed this from 80 to 10 to speed up the process, you can increase it if you want a denser mesh but it will take more time``
        self.frames = 0
        self.sub = self.create_subscription(
            PointCloud2,
            '/oak/rgbd/points',
            self.callback,
            10
        )

        self.get_logger().info('Listening to /oak/rgbd/points...')

    def callback(self, msg):
        self.frames += 1
        self.get_logger().info(f'Received cloud frame {self.frames}/{self.max_frames}')
        for p in pc2.read_points(msg, field_names=('x', 'y', 'z'), skip_nans=True):
            x, y, z = p
            if np.isfinite(x) and np.isfinite(y) and np.isfinite(z):
                self.points.append([x, y, z])

        if self.frames >= self.max_frames:
            self.save_mesh()
            rclpy.shutdown()

    def save_mesh(self):
        pts = np.array(self.points, dtype=np.float64)
        print(f'Total points: {len(pts)}')
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(pts)
        pcd = pcd.voxel_down_sample(voxel_size=0.08) #adjust voxel size for more/less detail - hopefully will reduce point cloud
        pcd, _ = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
        o3d.io.write_point_cloud('/ros2_ws/chairs_pointcloud.ply', pcd)

        print("saved point cloud")

        pcd.estimate_normals()
        pcd.orient_normals_consistent_tangent_plane(20)

        mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
            pcd,
            depth=7
        )

        mesh.remove_degenerate_triangles()
        mesh.remove_duplicated_triangles()
        mesh.remove_duplicated_vertices()
        mesh.remove_non_manifold_edges()
        o3d.io.write_triangle_mesh('/ros2_ws/chairs_open3d_mesh.ply', mesh)
        print('Saved:')
        print('/ros2_ws/chairs_pointcloud.ply')
        print('/ros2_ws/chairs_open3d_mesh.ply')

def main():
    rclpy.init()
    node = PointCloudToMesh()
    rclpy.spin(node)

if __name__ == '__main__':
    main()
