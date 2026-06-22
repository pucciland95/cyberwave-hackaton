from cyberwave import Cyberwave
import json
import threading
from os.path import dirname, abspath, join
import pinocchio
import numpy as np

PLANNING_TARGET_LINK = "gripper_base"

cw = Cyberwave()
arm = cw.twin("agile-x-robotics/piper")
joint_names = arm.joints.list()

_latest_joints: dict = {}
_joints_event = threading.Event()


def _on_joint_update(payload):
    try:
        data = json.loads(payload) if isinstance(payload, str) else payload
        if "positions" in data:
            _latest_joints.update(data["positions"])
        elif "joint_name" in data and "joint_state" in data:
            pos = data["joint_state"].get("position")
            if pos is not None:
                _latest_joints[data["joint_name"]] = pos
        else:
            for key, val in data.items():
                if key in joint_names and isinstance(val, (int, float)):
                    _latest_joints[key] = val
        if _latest_joints:
            _joints_event.set()
    except Exception:
        pass


arm.subscribe_joints(_on_joint_update)


def get_robot_feedback():
    _joints_event.wait()
    values = [_latest_joints[j] for j in joint_names if j in _latest_joints]
    return np.array(values[:-2])  # drop gripper fingers


def get_end_effector_pose(joints):
    pinocchio_model_dir = join(dirname(dirname(str(abspath(__file__)))), "manipulation")
    urdf_filename = pinocchio_model_dir + "/models/piper_description.urdf"
    model = pinocchio.buildModelFromUrdf(urdf_filename)
    data = model.createData()
    pinocchio.forwardKinematics(model, data, np.array(joints, dtype=float))
    pinocchio.updateFramePlacements(model, data)
    frame_id = model.getFrameId(PLANNING_TARGET_LINK)
    return data.oMf[frame_id]


q = get_robot_feedback()
pose = get_end_effector_pose(q)

print("End-effector pose:")
print("  Translation (x, y, z):", pose.translation)
print("  Rotation matrix:\n", pose.rotation)
