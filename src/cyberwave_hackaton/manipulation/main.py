from cyberwave import Cyberwave
import json
import threading
import time
from pyroboplan.ik.differential_ik import DifferentialIk, DifferentialIkOptions
import pinocchio
from os.path import dirname, abspath, join

import numpy as np
from pyroboplan.planning.cartesian_planner import (
    CartesianPlanner,
    CartesianPlannerOptions,
)
import math

PLANNING_TARGET_LINK = "gripper_base"


def get_pinocchio_moder():
    # This path refers to Pinocchio source code but you can define your own directory here.
    pinocchio_model_dir = join(dirname(dirname(str(abspath(__file__)))), "manipulation")

    # You should change here to set up your own URDF file or just pass it as an argument of this example.
    urdf_filename = pinocchio_model_dir + "/models/piper_description.urdf"

    # Load the urdf model
    pinocchio_model = pinocchio.buildModelFromUrdf(urdf_filename)

    return pinocchio_model


def create_ikin_solver():
    model = get_pinocchio_moder()

    ik = DifferentialIk(
        model,
        options=DifferentialIkOptions(max_retries=5, rng_seed=None),
    )

    return ik


def create_planner(ik_solver, tforms):

    model = get_pinocchio_moder()

    options = CartesianPlannerOptions(
        use_trapezoidal_scaling=True,
        max_linear_velocity=0.1,
        max_linear_acceleration=0.5,
        max_angular_velocity=1.0,
        max_angular_acceleration=1.0,
    )

    planner = CartesianPlanner(
        model, PLANNING_TARGET_LINK, tforms, ik_solver, options=options
    )

    return planner


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

    arm.joints.set(
        joints,
        degrees=True,
    )

    time.sleep(0.5)

    # while True:

    #     all_joints = arm.joints.get()
    #     current_deg = [all_joints[j] * 180.0 / math.pi for j in joint_names]
    #     if all(abs(curr - des) <= err_tol for curr, des in zip(current_deg, des)):
    #         print("Finished")
    #         break

    #     print(f"desired: {des}")
    #     print(f"current: {current_deg}")

    #     time.sleep(0.5)


def open_gripper(arm):
    arm.joints.set({"joint7": 3, "joint8": 3}, degrees=False)
    time.sleep(1)


def close_gripper(arm):
    arm.joints.set({"joint7": 0, "joint8": 0}, degrees=False)
    time.sleep(1)


def get_robot_feedback():
    _joints_event.wait()
    values = [_latest_joints[j] for j in _joint_names if j in _latest_joints]
    # drop the last two joints (gripper fingers, not used for FK)
    return np.array(values[:-2])


cw = Cyberwave()
arm = cw.twin("agile-x-robotics/piper")

_joint_names = arm.joints.list()
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
                if key in _joint_names and isinstance(val, (int, float)):
                    _latest_joints[key] = val
        if _latest_joints:
            _joints_event.set()
    except Exception:
        pass


arm.subscribe_joints(_on_joint_update)


ik_solver = create_ikin_solver()

dt = 0.05

q_start = get_robot_feedback()
tform_start = get_forward_kinemaics(q_start)

tform_end = get_forward_kinemaics(q_start)
tform_end.translation += np.array([0.0, 0.0, 0.1])  # e.g. 10 cm up in world Z

tforms = [tform_start, tform_end]

planner = create_planner(ik_solver, tforms)
success, t_vec, q_pos = planner.generate(q_start, dt)

for i in range(q_pos.shape[1]):
    waypoint_deg = np.degrees(q_pos[:, i]).tolist()
    move_to(arm, waypoint_deg)
