'''
Point cloud visualization using RealSense D435.
Press 'q' to quit.
'''
import pyrealsense2 as rs
import numpy as np
import open3d as o3d

# Start RealSense stream (color + depth)
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
pipeline.start(config)

# Align depth to color frame
align = rs.align(rs.stream.color)

print("Warming up camera...")
for _ in range(30):
    pipeline.wait_for_frames()

print("Press 'q' in the Open3D window to quit.")

# Set up Open3D visualizer
vis = o3d.visualization.Visualizer()
vis.create_window("Point Cloud", width=1280, height=720)
pcd = o3d.geometry.PointCloud()
vis.add_geometry(pcd)
first_frame = True

try:
    while True:
        frames = pipeline.wait_for_frames()
        aligned = align.process(frames)

        depth_frame = aligned.get_depth_frame()
        color_frame = aligned.get_color_frame()
        if not depth_frame or not color_frame:
            continue

        # Convert to numpy
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        color_rgb = color_image[:, :, ::-1] / 255.0  # BGR -> RGB, normalize

        # Build point cloud using RealSense intrinsics
        depth_intrinsics = depth_frame.profile.as_video_stream_profile().intrinsics
        h, w = depth_image.shape
        fx, fy = depth_intrinsics.fx, depth_intrinsics.fy
        cx, cy = depth_intrinsics.ppx, depth_intrinsics.ppy

        u, v = np.meshgrid(np.arange(w), np.arange(h))
        z = depth_image * depth_frame.get_units()  # convert to meters
        x = (u - cx) * z / fx
        y = (v - cy) * z / fy

        mask = z > 0  # remove invalid points
        points = np.stack([x[mask], y[mask], z[mask]], axis=-1)
        colors = color_rgb.reshape(-1, 3)[mask.flatten()]

        pcd.points = o3d.utility.Vector3dVector(points)
        pcd.colors = o3d.utility.Vector3dVector(colors)

        if first_frame:
            vis.reset_view_point(True)
            first_frame = False

        vis.update_geometry(pcd)
        if not vis.poll_events():
            break
        vis.update_renderer()

finally:
    pipeline.stop()
    vis.destroy_window()