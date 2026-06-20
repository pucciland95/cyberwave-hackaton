
from cyberwave import Cyberwave

cw = Cyberwave()

# Connect to Realsense D455
realsense_d435 = cw.twin(
    "intel/realsensed435",
    twin_id="e2855c58-e69b-460d-8b5d-54f97139b8cb",
    environment_id="d31e9fab-9a70-41d8-82de-a675cbae0c2e"
)


# Edit transform in the studio
realsense_d435.edit_position(x=1, y=0, z=0.5)
realsense_d435.edit_rotation(yaw=90)  # degrees

# Start streaming sensor data
realsense_d435.start_streaming()


'''
# Code for testing connection with python
import pyrealsense2 as rs
pipeline = rs.pipeline()
config = rs.config()
pipeline.start(config)
frames = pipeline.wait_for_frames()
print('Success! Got frames:', frames)
pipeline.stop()
'''
