''' 
Sixth script: test the fine-tuned model.
Captures a live frame from the RealSense camera when 'q' is pressed,
then runs inference on it and computes the object pose w.r.t. the camera.
Rotation around Z is estimated from the bounding box content using PCA.
'''
from ultralytics import YOLO
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib as mpl
import cv2
import numpy as np
import pyrealsense2 as rs
import os
import glob
from scipy.spatial.transform import Rotation

# Imports for latex plots
mpl.rcParams['text.usetex'] = True
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['text.latex.preamble'] = r'\usepackage{amsmath}'

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import fonts


def euler_to_homogeneous(x, y, z, roll, pitch, yaw, degrees=True):
    """
    Build a 4x4 homogeneous matrix from translation and Euler angles.
    Roll  = rotation around X
    Pitch = rotation around Y
    Yaw   = rotation around Z
    Order: R = Rx @ Ry @ Rz (XYZ convention)
    """
    if degrees:
        roll  = np.deg2rad(roll)
        pitch = np.deg2rad(pitch)
        yaw   = np.deg2rad(yaw)

    Rx = np.array([[1,           0,            0],
                   [0, np.cos(roll), -np.sin(roll)],
                   [0, np.sin(roll),  np.cos(roll)]])

    Ry = np.array([[ np.cos(pitch), 0, np.sin(pitch)],
                   [0,              1,             0],
                   [-np.sin(pitch), 0, np.cos(pitch)]])

    Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0],
                   [np.sin(yaw),  np.cos(yaw), 0],
                   [0,            0,            1]])

    R = Rx @ Ry @ Rz

    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3]  = [x, y, z]

    return T


def pixels_to_camera(u, v, z_c, fx, fy, cx, cy):
    """
    Convert pixel coordinates (u, v) to camera frame 3D coordinates
    using the pinhole model.
    """
    X_c = (u - cx) * z_c / fx
    Y_c = (v - cy) * z_c / fy
    Z_c = z_c
    return X_c, Y_c, Z_c


def estimate_theta_z_from_box(image, x1, y1, x2, y2):
    crop = image[int(y1):int(y2), int(x1):int(x2)]
    if crop.size == 0:
        return 0.0

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)

    points = np.column_stack(np.where(edges > 0)).astype(np.float32)
    # points are (row, col) = (v, u)
    if len(points) < 10:
        return 0.0

    mean, eigenvectors = cv2.PCACompute(points, mean=None)
    # eigenvectors[0] = (dv, du) — principal axis
    dv, du = eigenvectors[0]
    # angle from u axis (X_c), positive = clockwise (toward Y_c = down)
    angle = np.degrees(np.arctan2(dv, du))
    return angle


def compute_A_c_o(u, v, z_c, fx, fy, cx, cy, theta_z_deg=0.0):
    """
    Compute the homogeneous transform A_c_o:
    pose of the object w.r.t. the camera frame.
    Translation: from pixel center of bounding box via pinhole model.
    Rotation:    only around Z axis.
    """
    X_c, Y_c, Z_c = pixels_to_camera(u, v, z_c, fx, fy, cx, cy)
    A_c_o = euler_to_homogeneous(
        x=X_c, y=Y_c, z=Z_c,
        roll=0, pitch=0, yaw=theta_z_deg,
        degrees=True
    )
    return A_c_o, (X_c, Y_c, Z_c)


current_directory = os.path.dirname(os.path.abspath(__file__))

# Load model — picks the latest training run automatically
weights = sorted(glob.glob(str(Path(current_directory) / "Model" / "cube_hackaton" / "train*" / "weights" / "best.pt")))
if not weights:
    raise FileNotFoundError("No trained model found. Run fine_tuning.py first.")
model_path = weights[-1]
print(f"{fonts.green}Loading model: {model_path}{fonts.reset}")
model = YOLO(model_path)

save_directory = Path(current_directory) / "Images" / "Inference"
save_directory.mkdir(parents=True, exist_ok=True)

# Start RealSense stream and get intrinsics
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
profile = pipeline.start(config)

color_stream = profile.get_stream(rs.stream.color).as_video_stream_profile()
intrinsics = color_stream.get_intrinsics()
fx = intrinsics.fx
fy = intrinsics.fy
cx = intrinsics.ppx
cy = intrinsics.ppy
print(f"{fonts.blue_light}Camera intrinsics: fx={fx:.2f}, fy={fy:.2f}, cx={cx:.2f}, cy={cy:.2f}{fonts.reset}")

# Fixed depth: camera points at table, z = 45 cm = 0.45 m
Z_FIXED = 0.45

print(f"{fonts.green}Live preview started. Press 'q' to capture and run inference.{fonts.reset}")

captured_frame = None
try:
    while True:
        frames = pipeline.try_wait_for_frames(100)
        if not frames[0]:
            continue
        color_frame = frames[1].get_color_frame()
        if not color_frame:
            continue

        img = np.asanyarray(color_frame.get_data())
        preview = img.copy()
        cv2.putText(preview, "Press 'q' to capture for inference",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow("Live Preview", preview)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            captured_frame = img.copy()
            print(f"{fonts.green}Frame captured!{fonts.reset}")
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()

if captured_frame is None:
    print(f"{fonts.red}No frame captured.{fonts.reset}")
    sys.exit(1)

# Save captured frame
capture_path = save_directory / "captured_frame.jpg"
cv2.imwrite(str(capture_path), captured_frame)

# Run YOLO inference
print(f"{fonts.green}Running inference...{fonts.reset}")
results = model.predict(str(capture_path), imgsz=640, conf=0.6, save=False)
boxes = results[0].boxes

A_c_o = None
if len(boxes) == 0:
    print(f"{fonts.red}No object detected.{fonts.reset}")
else:
    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        u = (x1 + x2) / 2.0
        v = (y1 + y2) / 2.0
        conf = box.conf[0].item()

        print(f"\n{fonts.purple}Detection #{i+1} | conf={conf:.2f}{fonts.reset}")
        print(f"{fonts.green}  Bounding box center: u={u:.1f} px, v={v:.1f} px{fonts.reset}")

        # Estimate theta_z from bounding box content using PCA
        theta_z = estimate_theta_z_from_box(captured_frame, x1, y1, x2, y2)
        print(f"{fonts.green}  Estimated theta_z (PCA) = {theta_z:.2f} deg{fonts.reset}")

        A_c_o, (X_c, Y_c, Z_c) = compute_A_c_o(
            u=u, v=v,
            z_c=Z_FIXED,
            fx=fx, fy=fy, cx=cx, cy=cy,
            theta_z_deg=theta_z
        )

        print(f"{fonts.green}  Object position in camera frame:{fonts.reset}")
        print(f"    X_c = {X_c:.4f} m")
        print(f"    Y_c = {Y_c:.4f} m")
        print(f"    Z_c = {Z_c:.4f} m  (fixed)")
        print(f"{fonts.green}  A_c_o (homogeneous transform):{fonts.reset}")
        print(A_c_o)

        # Draw center and angle on image
        cv2.circle(captured_frame, (int(u), int(v)), 6, (0, 0, 255), -1)
        cv2.putText(captured_frame,
                    f"({X_c:.2f}, {Y_c:.2f}, {Z_c:.2f}) m | theta_z={theta_z:.1f} deg",
                    (int(x1), int(y1) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

# Display result
detected_image = cv2.cvtColor(results[0].plot(), cv2.COLOR_BGR2RGB)
save_path = save_directory / "inference_result.jpg"
plt.imsave(str(save_path), detected_image)
print(f"\n{fonts.green}Result saved to: {save_path}{fonts.reset}")

plt.figure(figsize=(8, 6))
plt.imshow(detected_image)
plt.axis('off')
plt.title(rf"\textbf{{Detection}}", fontsize=16)
plt.show()

# World transforms
A_w_b = euler_to_homogeneous(x=0.0, y=0.0, z=0.07, roll=0, pitch=0, yaw=60)
print(f"\n{fonts.green}A_w_b:{fonts.reset}")
print(A_w_b)

A_w_c = euler_to_homogeneous(x=-0.07, y=0.5, z=0.48, roll=180, pitch=0, yaw=60)
print(f"\n{fonts.green}A_w_c:{fonts.reset}")
print(A_w_c)

if A_c_o is not None:
    A_b_o = np.linalg.inv(A_w_b) @ A_w_c @ A_c_o
    print(f"\n{fonts.green}A_b_o:{fonts.reset}")
    print(A_b_o)

    R = A_b_o[:3, :3]
    angles = Rotation.from_matrix(R).as_euler('XYZ', degrees=True)
    print(f"Roll  (X): {angles[0]:.4f} deg")
    print(f"Pitch (Y): {angles[1]:.4f} deg")
    print(f"Yaw   (Z): {angles[2]:.4f} deg")
else:
    print(f"{fonts.red}Skipping A_b_o: no detection.{fonts.reset}")