''' 
Sixth script: test the fine-tuned model.

NOTE: when running the script, if you want to keep the LaTeX font in the plots,
install all the packages suggested by the pop-up panels that show up when running the script.
'''

from ultralytics import YOLO
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib as mpl
import cv2

# Imports for latex plots
mpl.rcParams['text.usetex'] = True
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['text.latex.preamble'] = r'\usepackage{amsmath}'

# Import the colors
import sys, fonts, os
current_directory = os.path.dirname(os.path.abspath(__file__))

model = YOLO(Path(current_directory)/"Model"/"cube_hackaton"/"train"/"weights"/"best.pt")
image_path = Path(current_directory)/"Images"/"frame_20260620_140826_884967.jpg"
save_directory = Path(current_directory)/"Images"/"Inference"
save_directory.mkdir(parents=True, exist_ok=True)

# Inference
results = model.predict(
    str(image_path), 
    imgsz = 640, 
    conf = 0.2, 
    save = False) 

# Result of the detection
detected_image = cv2.cvtColor(results[0].plot(), cv2.COLOR_BGR2RGB)

# Save the image
save_path = save_directory / f"{image_path.stem}_predictions.jpg"
plt.imsave(str(save_path), detected_image)

# Display the image
plt.figure(figsize=(8, 6))
plt.imshow(detected_image, cmap = 'viridis')
plt.axis('off')
plt.title(rf"\textbf{{Detection}}", fontsize=16)
plt.show()