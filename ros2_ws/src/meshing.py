import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
import sensor_msgs_py.point_cloud2 as pc2
import numpy as np
import open3d as o3d
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point
from std_msgs.msg import ColorRGBA

class RTABMapMesher(Node):
    def __init__(self):
        super().__init__('rtabmap_mesher')

        # Subscribe to rtabmap cloud map output
        self.subscription = self.create_subscription(
            PointCloud2,
            '/cloud_map',
            self.listener_callback,
            10
        )

        self.mesh_publisher = self.create_publisher(Marker, '/mesh', 10)

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
        colors = []
        for p in pc2.read_points(latest_msg, field_names=('x', 'y', 'z', 'rgb'), skip_nans=False):
            if np.isnan(p[0]) or np.isnan(p[1]) or np.isnan(p[2]):
                continue

            points.append([p[0], p[1], p[2]])

            # Reinterpret as 4 bytes directly
            packed = np.array([p[3]], dtype=np.float32).view(np.uint8)
            b = packed[0] / 255.0
            g = packed[1] / 255.0
            r = packed[2] / 255.0
            colors.append([r, g, b])

        self.get_logger().info(f'Processing latest cloud with {len(points)} points')

        if len(points) < 100:
            self.get_logger().warn('Not enough points to mesh yet')
            self.is_processing = False
            return

        # Generate a cloud and insert the np array of points
        cloud = o3d.geometry.PointCloud()
        cloud.points = o3d.utility.Vector3dVector(np.array(points, dtype=np.float64))
        cloud.colors = o3d.utility.Vector3dVector(np.array(colors, dtype=np.float64))

        cl, ind = cloud.remove_statistical_outlier(nb_neighbors=20, std_ratio=1.5)

        # Select only the inlier points
        cloud = cloud.select_by_index(ind)

        # Save raw registered cloud first
        cloud_loc = "../point_clouds/rtabmap_cloud.ply"        
        o3d.io.write_point_cloud(cloud_loc, cloud)
        self.get_logger().info(f"Saved point cloud to {cloud_loc}")

        # Estimate normals
        cloud.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
        )
        cloud.orient_normals_towards_camera_location(np.array([0., 0., 0.]))

        self.get_logger().info('Creating mesh...')
        mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
            cloud, depth=7
        )

        densities = np.asarray(densities)
        mesh.remove_vertices_by_mask(densities < np.quantile(densities, 0.10))
        mesh.remove_unreferenced_vertices()

        # Write final mesh
        mesh_loc = "../meshes/rtabmap_mesh.obj"
        o3d.io.write_triangle_mesh(mesh_loc, mesh)
        self.get_logger().info(f'Saved mesh to {mesh_loc}')

        # Publish the mesh
        self.publish_mesh(mesh, latest_msg.header.frame_id)

        self.is_processing = False

    def publish_mesh(self, o3d_mesh, frame_id):
            # Ensure vertex normals are computed so RViz shades it properly
            o3d_mesh.compute_vertex_normals()

            vertices = np.asarray(o3d_mesh.vertices)
            triangles = np.asarray(o3d_mesh.triangles)
            vertex_colors = np.asarray(o3d_mesh.vertex_colors)

            # Set up marker
            marker = Marker()
            marker.header.frame_id = frame_id
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = "rtabmap_mesh"
            marker.id = 0
            marker.type = Marker.TRIANGLE_LIST
            marker.action = Marker.ADD

            # Position and orientation relative to its frame_id frame
            marker.pose.position.x = 0.0
            marker.pose.position.y = 0.0
            marker.pose.position.z = 0.0
            marker.pose.orientation.x = 0.0
            marker.pose.orientation.y = 0.0
            marker.pose.orientation.z = 0.0
            marker.pose.orientation.w = 1.0

            # Scale must be 1.0 to keep original size
            marker.scale.x = 1.0
            marker.scale.y = 1.0
            marker.scale.z = 1.0

            # Base alpha configuration (individual vertex transparency fallback)
            marker.color.a = 1.0 

            # ROS TRIANGLE_LIST expects groups of 3 consecutive points to form a triangle face
            for triangle in triangles:
                for vertex_index in triangle:
                    # 1. Map Coordinates
                    vert = vertices[vertex_index]
                    p = Point()
                    p.x = float(vert[0])
                    p.y = float(vert[1])
                    p.z = float(vert[2])
                    marker.points.append(p)

                    col = vertex_colors[vertex_index]
                    c = ColorRGBA()
                    c.r = float(col[0])
                    c.g = float(col[1])
                    c.b = float(col[2])
                    c.a = 1.0  # Fully opaque
                    marker.colors.append(c)

            self.mesh_publisher.publish(marker)
            self.get_logger().info(f"Published mesh with {len(triangles)} triangles to ROS 2 topic.")

def main():
    rclpy.init()
    node = RTABMapMesher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()