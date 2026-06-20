import json
import math
import threading
import time

from cyberwave import Cyberwave


cw = Cyberwave()
arm = cw.twin("agile-x-robotics/piper")

joint_names = arm.joints.list()

_latest_joints: dict = {}
_joints_event = threading.Event()


def _on_joint_update(payload):
    try:
        data = json.loads(payload) if isinstance(payload, str) else payload

        if "positions" in data:
            # aggregated bulk format: {"positions": {"joint1": 0.5, ...}, ...}
            _latest_joints.update(data["positions"])
        elif "joint_name" in data and "joint_state" in data:
            # single-joint format: {"joint_name": "j1", "joint_state": {"position": 0.5}}
            name = data["joint_name"]
            pos = data["joint_state"].get("position")
            if pos is not None:
                _latest_joints[name] = pos
        else:
            # flat bulk format: {"joint1": 0.5, "joint2": 0.3, "source_type": "tele", ...}
            for key, val in data.items():
                if key in joint_names and isinstance(val, (int, float)):
                    _latest_joints[key] = val

        if _latest_joints:
            _joints_event.set()
    except Exception as e:
        print(f"Error parsing joint update: {e}")


arm.subscribe_joints(_on_joint_update)

while True:
    if _joints_event.wait(timeout=5.0):
        current_deg = [_latest_joints.get(j, 0.0) * 180.0 / math.pi for j in joint_names]
        print(f"current: {current_deg}")
    else:
        print("Waiting for joint update...")
    time.sleep(0.5)
