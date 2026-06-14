#!/usr/bin/env python3
"""
Open3D Point Cloud / Mesh Filtering Explorer
=============================================

Loads a single sensor_msgs/PointCloud2 message from a ROS2 (mcap) bag and
opens an interactive Open3D GUI where you can toggle and tune a pipeline of
Open3D point-cloud filters, then reconstruct and display a mesh from the
result. The point cloud and mesh are redrawn every time a parameter changes.

Usage:
    python3 open3d_filter_gui.py <bag_dir> [topic_name]

If topic_name is omitted, "/cloud_map" is used.

Requirements (in addition to a sourced ROS2 environment):
    pip install open3d --break-system-packages
"""

import sys
import copy
import numpy as np

import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering

import rosbag2_py
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2 as pc2


# ---------------------------------------------------------------------------
# Bag / PointCloud2 loading
# ---------------------------------------------------------------------------

def pointcloud2_to_o3d(msg):
    """Convert a sensor_msgs/PointCloud2 message to an Open3D PointCloud."""
    cloud_arr = pc2.read_points(msg, skip_nans=False).reshape(-1)
    field_names = cloud_arr.dtype.names

    xyz = np.stack(
        [cloud_arr['x'], cloud_arr['y'], cloud_arr['z']], axis=-1
    ).astype(np.float64)

    finite_mask = np.isfinite(xyz).all(axis=1)
    xyz = xyz[finite_mask]

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(xyz)

    if 'rgb' in field_names:
        rgb_raw = cloud_arr['rgb'][finite_mask]
        if rgb_raw.dtype == np.float32:
            rgb_int = rgb_raw.copy().view(np.uint32)
        else:
            rgb_int = rgb_raw.astype(np.uint32)
        r = ((rgb_int >> 16) & 0xFF).astype(np.float64) / 255.0
        g = ((rgb_int >> 8) & 0xFF).astype(np.float64) / 255.0
        b = (rgb_int & 0xFF).astype(np.float64) / 255.0
        pcd.colors = o3d.utility.Vector3dVector(np.stack([r, g, b], axis=-1))

    return pcd


def load_pointcloud_from_bag(bag_path, topic_name='/cloud_map'):
    storage_options = rosbag2_py.StorageOptions(uri=bag_path, storage_id='mcap')
    converter_options = rosbag2_py.ConverterOptions('cdr', 'cdr')

    reader = rosbag2_py.SequentialReader()
    reader.open(storage_options, converter_options)

    available = [t.name for t in reader.get_all_topics_and_types()]
    if topic_name not in available:
        raise RuntimeError(
            f"Topic '{topic_name}' not found in bag. Available topics: {available}")

    msg = None
    while reader.has_next():
        topic, data, _ts = reader.read_next()
        if topic == topic_name:
            msg = deserialize_message(data, PointCloud2)

    if msg is None:
        raise RuntimeError(f"No messages found on topic '{topic_name}'")

    return pointcloud2_to_o3d(msg)


# ---------------------------------------------------------------------------
# GUI application
# ---------------------------------------------------------------------------

class FilterApp:
    def __init__(self, pcd, window_name="Open3D Cloud/Mesh Filter Explorer"):
        self.original_pcd = pcd
        self.filtered_pcd = pcd
        self.mesh = None
        self._first_run = True

        # ---- pipeline parameters & defaults -----------------------------
        self.params = {
            # downsampling
            'voxel_enabled': False, 'voxel_size': 0.02,
            'uniform_enabled': False, 'uniform_k': 2,
            # outlier removal
            'sor_enabled': False, 'sor_nb_neighbors': 20, 'sor_std_ratio': 2.0,
            'ror_enabled': False, 'ror_nb_points': 16, 'ror_radius': 0.05,
            # segmentation / clustering
            'plane_enabled': False, 'plane_dist': 0.02,
            'plane_ransac_n': 3, 'plane_iters': 1000,
            'dbscan_enabled': False, 'dbscan_eps': 0.1, 'dbscan_min_points': 10,
            # normals
            'normal_radius': 0.1, 'normal_max_nn': 30, 'orient_normals': True,
            # mesh reconstruction
            'mesh_method': 'Ball Pivoting',
            'alpha': 0.1,
            'bpa_radius': 0.02,
            'poisson_depth': 9, 'poisson_scale': 1.1,
            'poisson_trim': True, 'poisson_trim_quantile': 0.05,
            # mesh post-processing
            'simplify_enabled': False, 'simplify_target': 20000,
            'smooth_enabled': False, 'smooth_method': 'Taubin', 'smooth_iters': 5,
            # display
            'show_pcd': True, 'show_mesh': True, 'show_wireframe': False,
            'point_size': 3.0,
        }

        gui.Application.instance.initialize()
        self.window = gui.Application.instance.create_window(window_name, 1400, 950)
        self.em = self.window.theme.font_size

        self._scene = gui.SceneWidget()
        self._scene.scene = rendering.Open3DScene(self.window.renderer)
        self._scene.scene.set_background([0.05, 0.05, 0.08, 1.0])

        self._panel = gui.Vert(0.25 * self.em, gui.Margins(0.5 * self.em))
        self._build_panel()

        self.window.add_child(self._scene)
        self.window.add_child(self._panel)
        self.window.set_on_layout(self._on_layout)

        self._apply_pipeline()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _on_layout(self, layout_context):
        r = self.window.content_rect
        panel_width = 24 * self.em
        self._scene.frame = gui.Rect(r.x, r.y, r.width - panel_width, r.height)
        self._panel.frame = gui.Rect(r.get_right() - panel_width, r.y, panel_width, r.height)

    # ------------------------------------------------------------------
    # Widget helpers
    # ------------------------------------------------------------------
    def _add_checkbox(self, container, key, label):
        cb = gui.Checkbox(label)
        cb.checked = self.params[key]

        def on_checked(value):
            self.params[key] = value
            self._apply_pipeline()

        cb.set_on_checked(on_checked)
        container.add_child(cb)
        return cb

    @staticmethod
    def _slider_text(label, value, is_int, fmt):
        if is_int:
            return f"{label}: {int(value)}"
        return f"{label}: {fmt.format(value)}"

    def _add_slider(self, container, key, label, vmin, vmax, is_int=False, fmt="{:.4f}"):
        init = self.params[key]
        lbl = gui.Label(self._slider_text(label, init, is_int, fmt))
        slider = gui.Slider(gui.Slider.INT if is_int else gui.Slider.DOUBLE)
        slider.set_limits(vmin, vmax)
        if is_int:
            slider.int_value = int(init)
        else:
            slider.double_value = float(init)

        def on_changed(value):
            self.params[key] = int(value) if is_int else value
            lbl.text = self._slider_text(label, self.params[key], is_int, fmt)
            self._apply_pipeline()

        slider.set_on_value_changed(on_changed)

        v = gui.Vert(0.1 * self.em)
        v.add_child(lbl)
        v.add_child(slider)
        container.add_child(v)
        return slider

    def _add_combobox(self, container, key, label, options):
        v = gui.Vert(0.1 * self.em)
        v.add_child(gui.Label(label))
        combo = gui.Combobox()
        for opt in options:
            combo.add_item(opt)
        combo.selected_text = self.params[key]

        def on_changed(new_val, new_idx):
            self.params[key] = new_val
            self._apply_pipeline()

        combo.set_on_selection_changed(on_changed)
        v.add_child(combo)
        container.add_child(v)
        return combo

    # ------------------------------------------------------------------
    # Panel construction
    # ------------------------------------------------------------------
    def _build_panel(self):
        p = self._panel

        self.status_label = gui.Label("")
        p.add_child(self.status_label)

        # --- downsampling ---------------------------------------------
        sec = gui.CollapsableVert("Downsampling", 0.25 * self.em, gui.Margins(self.em, 0, 0, 0))
        self._add_checkbox(sec, 'voxel_enabled', "Voxel Down Sample")
        self._add_slider(sec, 'voxel_size', "voxel_size (m)", 0.005, 0.2)
        self._add_checkbox(sec, 'uniform_enabled', "Uniform Down Sample")
        self._add_slider(sec, 'uniform_k', "every_k_points", 1, 20, is_int=True)
        p.add_child(sec)

        # --- outlier removal ---------------------------------------------
        sec = gui.CollapsableVert("Outlier Removal", 0.25 * self.em, gui.Margins(self.em, 0, 0, 0))
        sec.set_is_open(False)
        self._add_checkbox(sec, 'sor_enabled', "Statistical Outlier Removal")
        self._add_slider(sec, 'sor_nb_neighbors', "nb_neighbors", 1, 100, is_int=True)
        self._add_slider(sec, 'sor_std_ratio', "std_ratio", 0.1, 5.0)
        self._add_checkbox(sec, 'ror_enabled', "Radius Outlier Removal")
        self._add_slider(sec, 'ror_nb_points', "nb_points", 1, 50, is_int=True)
        self._add_slider(sec, 'ror_radius', "radius (m)", 0.005, 1.0)
        p.add_child(sec)

        # --- segmentation / clustering -------------------------------------
        sec = gui.CollapsableVert("Segmentation / Clustering", 0.25 * self.em, gui.Margins(self.em, 0, 0, 0))
        sec.set_is_open(False)
        self._add_checkbox(sec, 'plane_enabled', "Remove Largest Plane (RANSAC)")
        self._add_slider(sec, 'plane_dist', "distance_threshold (m)", 0.001, 0.1)
        self._add_slider(sec, 'plane_ransac_n', "ransac_n", 3, 10, is_int=True)
        self._add_slider(sec, 'plane_iters', "num_iterations", 100, 2000, is_int=True)
        self._add_checkbox(sec, 'dbscan_enabled', "DBSCAN -> Keep Largest Cluster")
        self._add_slider(sec, 'dbscan_eps', "eps (m)", 0.01, 1.0)
        self._add_slider(sec, 'dbscan_min_points', "min_points", 1, 50, is_int=True)
        p.add_child(sec)

        # --- normals -------------------------------------------------------
        sec = gui.CollapsableVert("Normal Estimation", 0.25 * self.em, gui.Margins(self.em, 0, 0, 0))
        sec.set_is_open(False)
        self._add_slider(sec, 'normal_radius', "search radius (m)", 0.01, 0.5)
        self._add_slider(sec, 'normal_max_nn', "max_nn", 5, 100, is_int=True)
        self._add_checkbox(sec, 'orient_normals', "Orient (consistent tangent plane)")
        p.add_child(sec)

        # --- mesh reconstruction ---------------------------------------------
        sec = gui.CollapsableVert("Mesh Reconstruction", 0.25 * self.em, gui.Margins(self.em, 0, 0, 0))
        self._add_combobox(sec, 'mesh_method', "Method",
                            ['Alpha Shape', 'Ball Pivoting', 'Poisson'])
        self._add_slider(sec, 'alpha', "alpha", 0.005, 1.0)
        self._add_slider(sec, 'bpa_radius', "BPA base radius (m)", 0.005, 0.2)
        self._add_slider(sec, 'poisson_depth', "Poisson depth", 4, 12, is_int=True)
        self._add_slider(sec, 'poisson_scale', "Poisson scale", 1.0, 2.0)
        self._add_checkbox(sec, 'poisson_trim', "Poisson density trim")
        self._add_slider(sec, 'poisson_trim_quantile', "trim quantile", 0.0, 0.5)
        p.add_child(sec)

        # --- mesh post-processing ---------------------------------------------
        sec = gui.CollapsableVert("Mesh Post-processing", 0.25 * self.em, gui.Margins(self.em, 0, 0, 0))
        sec.set_is_open(False)
        self._add_checkbox(sec, 'simplify_enabled', "Simplify (Quadric Decimation)")
        self._add_slider(sec, 'simplify_target', "target triangle count", 100, 100000, is_int=True)
        self._add_checkbox(sec, 'smooth_enabled', "Smooth")
        self._add_combobox(sec, 'smooth_method', "Smoothing method",
                            ['Simple', 'Laplacian', 'Taubin'])
        self._add_slider(sec, 'smooth_iters', "iterations", 1, 50, is_int=True)
        p.add_child(sec)

        # --- display -------------------------------------------------------
        sec = gui.CollapsableVert("Display", 0.25 * self.em, gui.Margins(self.em, 0, 0, 0))
        self._add_checkbox(sec, 'show_pcd', "Show point cloud")
        self._add_checkbox(sec, 'show_mesh', "Show mesh")
        self._add_checkbox(sec, 'show_wireframe', "Show mesh wireframe")
        self._add_slider(sec, 'point_size', "point size", 1.0, 10.0)
        p.add_child(sec)

        # --- actions ---------------------------------------------------------
        actions = gui.Horiz(0.25 * self.em)
        reset_btn = gui.Button("Reset View")
        reset_btn.set_on_clicked(self._reset_camera)
        save_mesh_btn = gui.Button("Save Mesh (.ply)")
        save_mesh_btn.set_on_clicked(self._save_mesh)
        save_pcd_btn = gui.Button("Save Cloud (.ply)")
        save_pcd_btn.set_on_clicked(self._save_pcd)
        actions.add_child(reset_btn)
        actions.add_child(save_mesh_btn)
        actions.add_child(save_pcd_btn)
        p.add_child(actions)

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------
    def _apply_pipeline(self):
        try:
            pcd = copy.deepcopy(self.original_pcd)

            if self.params['voxel_enabled']:
                pcd = pcd.voxel_down_sample(voxel_size=self.params['voxel_size'])

            if self.params['uniform_enabled']:
                k = max(1, int(self.params['uniform_k']))
                pcd = pcd.uniform_down_sample(every_k_points=k)

            if self.params['sor_enabled'] and len(pcd.points) > 0:
                pcd, _ = pcd.remove_statistical_outlier(
                    nb_neighbors=int(self.params['sor_nb_neighbors']),
                    std_ratio=self.params['sor_std_ratio'])

            if self.params['ror_enabled'] and len(pcd.points) > 0:
                pcd, _ = pcd.remove_radius_outlier(
                    nb_points=int(self.params['ror_nb_points']),
                    radius=self.params['ror_radius'])

            if self.params['plane_enabled'] and len(pcd.points) >= self.params['plane_ransac_n']:
                _model, inliers = pcd.segment_plane(
                    distance_threshold=self.params['plane_dist'],
                    ransac_n=int(self.params['plane_ransac_n']),
                    num_iterations=int(self.params['plane_iters']))
                pcd = pcd.select_by_index(inliers, invert=True)

            if self.params['dbscan_enabled'] and len(pcd.points) > 0:
                labels = np.array(pcd.cluster_dbscan(
                    eps=self.params['dbscan_eps'],
                    min_points=int(self.params['dbscan_min_points'])))
                if labels.size > 0 and labels.max() >= 0:
                    counts = np.bincount(labels[labels >= 0])
                    largest = int(np.argmax(counts))
                    pcd = pcd.select_by_index(np.where(labels == largest)[0])

            if len(pcd.points) == 0:
                self.filtered_pcd = pcd
                self.mesh = None
                self._update_scene(pcd, None)
                self.status_label.text = "Filtered cloud is empty - relax filter settings."
                return

            # Normal estimation (needed by Ball Pivoting / Poisson, and shading)
            pcd.estimate_normals(
                search_param=o3d.geometry.KDTreeSearchParamHybrid(
                    radius=self.params['normal_radius'],
                    max_nn=int(self.params['normal_max_nn'])))
            if self.params['orient_normals']:
                pcd.orient_normals_consistent_tangent_plane(
                    int(self.params['normal_max_nn']))

            self.filtered_pcd = pcd

            mesh = self._reconstruct_mesh(pcd)
            mesh = self._postprocess_mesh(mesh)
            self.mesh = mesh

            self._update_scene(pcd, mesh)

            n_tri = len(mesh.triangles) if mesh is not None else 0
            self.status_label.text = f"Points: {len(pcd.points)}   Triangles: {n_tri}"

        except Exception as e:
            self.status_label.text = f"Error: {e}"

    def _reconstruct_mesh(self, pcd):
        method = self.params['mesh_method']

        if method == 'Alpha Shape':
            mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(
                pcd, self.params['alpha'])

        elif method == 'Ball Pivoting':
            r = self.params['bpa_radius']
            radii = o3d.utility.DoubleVector([r, r * 2, r * 4])
            mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
                pcd, radii)

        else:  # Poisson
            mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
                pcd, depth=int(self.params['poisson_depth']),
                scale=self.params['poisson_scale'])
            if self.params['poisson_trim'] and len(densities) > 0:
                densities = np.asarray(densities)
                thresh = np.quantile(densities, self.params['poisson_trim_quantile'])
                mesh.remove_vertices_by_mask(densities < thresh)

        mesh.compute_vertex_normals()
        return mesh

    def _postprocess_mesh(self, mesh):
        if mesh is None:
            return mesh

        if (self.params['simplify_enabled']
                and len(mesh.triangles) > self.params['simplify_target']):
            mesh = mesh.simplify_quadric_decimation(int(self.params['simplify_target']))

        if self.params['smooth_enabled'] and len(mesh.vertices) > 0:
            iters = int(self.params['smooth_iters'])
            if self.params['smooth_method'] == 'Simple':
                mesh = mesh.filter_smooth_simple(number_of_iterations=iters)
            elif self.params['smooth_method'] == 'Laplacian':
                mesh = mesh.filter_smooth_laplacian(number_of_iterations=iters)
            else:
                mesh = mesh.filter_smooth_taubin(number_of_iterations=iters)

        mesh.remove_degenerate_triangles()
        mesh.remove_duplicated_triangles()
        mesh.remove_duplicated_vertices()
        mesh.remove_non_manifold_edges()
        mesh.compute_vertex_normals()
        return mesh

    # ------------------------------------------------------------------
    # Scene / actions
    # ------------------------------------------------------------------
    def _update_scene(self, pcd, mesh):
        scene = self._scene.scene
        for name in ("pcd", "mesh", "wireframe"):
            if scene.has_geometry(name):
                scene.remove_geometry(name)

        if self.params['show_pcd'] and pcd is not None and len(pcd.points) > 0:
            mat = rendering.MaterialRecord()
            mat.shader = "defaultUnlit"
            mat.point_size = float(self.params['point_size'])
            scene.add_geometry("pcd", pcd, mat)

        if self.params['show_mesh'] and mesh is not None and len(mesh.triangles) > 0:
            mat = rendering.MaterialRecord()
            mat.shader = "defaultLit"
            mat.base_color = [0.75, 0.75, 0.85, 1.0]
            scene.add_geometry("mesh", mesh, mat)

            if self.params['show_wireframe']:
                wire = o3d.geometry.LineSet.create_from_triangle_mesh(mesh)
                wire.paint_uniform_color([0.1, 0.1, 0.1])
                mat_wire = rendering.MaterialRecord()
                mat_wire.shader = "unlitLine"
                mat_wire.line_width = 1.0
                scene.add_geometry("wireframe", wire, mat_wire)

        if self._first_run:
            bounds = self.original_pcd.get_axis_aligned_bounding_box()
            self._scene.setup_camera(60, bounds, bounds.get_center())
            self._first_run = False

    def _reset_camera(self):
        bounds = self.original_pcd.get_axis_aligned_bounding_box()
        self._scene.setup_camera(60, bounds, bounds.get_center())

    def _save_mesh(self):
        if self.mesh is not None and len(self.mesh.triangles) > 0:
            path = "filtered_mesh.ply"
            o3d.io.write_triangle_mesh(path, self.mesh)
            self.status_label.text = f"Saved mesh to {path}"
        else:
            self.status_label.text = "No mesh to save."

    def _save_pcd(self):
        if self.filtered_pcd is not None and len(self.filtered_pcd.points) > 0:
            path = "filtered_cloud.ply"
            o3d.io.write_point_cloud(path, self.filtered_pcd)
            self.status_label.text = f"Saved cloud to {path}"
        else:
            self.status_label.text = "No cloud to save."


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <bag_dir> [topic_name]")
        sys.exit(1)

    bag_path = sys.argv[1]
    topic_name = sys.argv[2] if len(sys.argv) > 2 else '/cloud_map'

    print(f"Loading '{topic_name}' from '{bag_path}' ...")
    pcd = load_pointcloud_from_bag(bag_path, topic_name)
    print(f"Loaded point cloud with {len(pcd.points)} points.")

    FilterApp(pcd)
    gui.Application.instance.run()


if __name__ == "__main__":
    main()