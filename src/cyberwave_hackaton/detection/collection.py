import pyrealsense2 as rs
import numpy as np
import cv2
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "Images")
os.makedirs(SAVE_DIR, exist_ok=True)

pipeline = rs.pipeline()
config = rs.config()

config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

try:
    pipeline.start(config)

    print("Press 's' to save an image.")
    print("Press 'q' to quit.")

    while True:
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()

        if not color_frame:
            continue

        frame = np.asanyarray(color_frame.get_data())

        cv2.imshow("RealSense Stream", frame)

        key = cv2.waitKey(1) & 0xFF

        # Save image
        if key == ord("s"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = os.path.join(
                SAVE_DIR,
                f"frame_{timestamp}.jpg"
            )

            cv2.imwrite(filename, frame)
            print(f"Saved image to: {filename}")

        # Quit
        elif key == ord("q"):
            print("Exiting...")
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()