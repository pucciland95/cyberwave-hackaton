''' 
Sixth script: test the fine-tuned model.
Captures a live frame from the RealSense camera when 'q' is pressed,
then runs inference on it.
'''
from ultralytics import YOLO
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib as mpl
import cv2
import numpy as np
import pyrealsense2 as rs
import os

# Imports for latex plots
mpl.rcParams['text.usetex'] = True
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['text.latex.preamble'] = r'\usepackage{amsmath}'

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import fonts

current_directory = os.path.dirname(os.path.abspath(__file__))

# Load model — picks the latest training run automatically
import glob
weights = sorted(glob.glob(str(Path(current_directory) / "Model" / "cube_hackaton" / "train*" / "weights" / "best.pt")))
if not weights:
    raise FileNotFoundError("No trained model found. Run fine_tuning.py first.")
model_path = weights[-1]
print(f"{fonts.green}Loading model: {model_path}{fonts.reset}")
model = YOLO(model_path)

save_directory = Path(current_directory) / "Images" / "Inference"
save_directory.mkdir(parents=True, exist_ok=True)

# Start RealSense stream
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
pipeline.start(config)

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

        # Show live preview with instruction overlay
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

# Save the captured frame
capture_path = save_directory / "captured_frame.jpg"
cv2.imwrite(str(capture_path), captured_frame)

# Run inference
print(f"{fonts.green}Running inference...{fonts.reset}")
results = model.predict(str(capture_path), imgsz=640, conf=0.2, save=False)

# Display result
detected_image = cv2.cvtColor(results[0].plot(), cv2.COLOR_BGR2RGB)

# Save annotated result
save_path = save_directory / "inference_result.jpg"
plt.imsave(str(save_path), detected_image)
print(f"{fonts.green}Result saved to: {save_path}{fonts.reset}")

# Show result
plt.figure(figsize=(8, 6))
plt.imshow(detected_image)
plt.axis('off')
plt.title(rf"\textbf{{Detection}}", fontsize=16)
plt.show()