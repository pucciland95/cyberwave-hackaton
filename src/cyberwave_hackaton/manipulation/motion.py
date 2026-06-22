from cyberwave import Cyberwave
import time
import threading
import json
from os.path import dirname, abspath, join
import pinocchio
import numpy as np
import math

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


def get_pinocchio_moder():
    # This path refers to Pinocchio source code but you can define your own directory here.
    pinocchio_model_dir = join(dirname(dirname(str(abspath(__file__)))), "manipulation")

    # You should change here to set up your own URDF file or just pass it as an argument of this example.
    urdf_filename = pinocchio_model_dir + "/models/piper_description.urdf"

    # Load the urdf model
    pinocchio_model = pinocchio.buildModelFromUrdf(urdf_filename)

    return pinocchio_model

def get_robot_feedback():
    _joints_event.wait()
    values = [_latest_joints[j] for j in joint_names if j in _latest_joints]
    # drop the last two joints (gripper fingers, not used for FK)
    return np.array(values[:-2])


def get_forward_kinemaics(joints):

    # Compute starting pose via forward kinematics so the planner has a valid start→end segment.
    _model = get_pinocchio_moder()
    _data = _model.createData()
    pinocchio.forwardKinematics(_model, _data, np.array(joints, dtype=float))
    pinocchio.updateFramePlacements(_model, _data)
    _frame_id = _model.getFrameId(PLANNING_TARGET_LINK)
    tform_start = _data.oMf[_frame_id]

    return tform_start


def move_to(arm, des: list, err_tol=5.0):

    joint_names = arm.joints.list()

    joint_names.remove("joint7")
    joint_names.remove("joint8")

    joints = {j_name: j_pos for j_name, j_pos in zip(joint_names, des)}

    for j_name, j_pos in joints.items():
        arm.joints.set(j_name, j_pos, degrees=True)

    # while True:

    #     feedback = get_robot_feedback()
    #     current_deg = [float(j) * 180.0 / math.pi for j in feedback]

    #     if all(abs(curr - des) <= err_tol for curr, des in zip(current_deg, des)):
    #         print("Finished")
    #         print(f"desired: {des}")
    #         print(f"current: {current_deg}")
    #         break

    #     time.sleep(0.5)


def open_gripper(arm):
    arm.joints.set("joint7", 3, degrees=False)
    arm.joints.set("joint8", 3, degrees=False)
    time.sleep(1)


def close_gripper(arm):
    arm.joints.set("joint7", 0, degrees=False)
    arm.joints.set("joint8", 0, degrees=False)
    time.sleep(1)


pos1 = [50.0, 30.0, -75.0, 0.0, 0.0, 0.0]
pos2 = [150.0, 30.0, -75.0, 0.0, 0.0, 0.0]

move_to(arm, pos1)
move_to(arm, pos2)
