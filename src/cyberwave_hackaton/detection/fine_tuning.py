'''
Fine-tune YOLO on the cube_hackaton dataset.
Run: poetry run python src/cyberwave_hackaton/detection/finetune.py
'''
from ultralytics import YOLO
from pathlib import Path
import torch
import sys
import os

sys.path.append(".")

object_name = "cube_hackaton"
current_directory = os.path.dirname(os.path.abspath(__file__))
data_yaml = Path(current_directory) / "Dataset" / "data.yaml"
output_dir = Path(current_directory) / "Model" / object_name

if __name__ == '__main__':
    print(f'CUDA available: {torch.cuda.is_available()}')
    if torch.cuda.is_available():
        print(f'Device: {torch.cuda.get_device_name(0)}')
        device = 0
    else:
        print('No GPU found, using CPU.')
        device = 'cpu'

    model = YOLO("yolov8n.pt")

    results = model.train(
        data=str(data_yaml),
        epochs=100,
        imgsz=640,
        workers=4,
        batch=16,
        device=device,
        lr0=1e-4,
        project=str(output_dir)
    )

    print(f'Training complete. Model saved to {output_dir}')