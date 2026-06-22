from pyroboplan.ik.differential_ik import DifferentialIk, DifferentialIkOptions
import pinocchio
from os.path import dirname, abspath, join

import numpy as np
from pyroboplan.planning.cartesian_planner import (
    CartesianPlanner,
    CartesianPlannerOptions,
)

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


def get_forward_kinemaics(joints):

    # Compute starting pose via forward kinematics so the planner has a valid start→end segment.
    _model = get_pinocchio_moder()
    _data = _model.createData()
    pinocchio.forwardKinematics(_model, _data, joints)
    pinocchio.updateFramePlacements(_model, _data)
    _frame_id = _model.getFrameId(PLANNING_TARGET_LINK)
    tform_start = _data.oMf[_frame_id]

    return tform_start


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


ik_solver = create_ikin_solver()

dt = 0.05
q_start = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
tform_start = get_forward_kinemaics(q_start)
q_end = np.array([0.1, 0.1, -0.1, 0.1, 0.1, 0.1])
tform_end = get_forward_kinemaics(q_end)


tforms = [tform_start, tform_end]

planner = create_planner(ik_solver, tforms)
success, t_vec, q_vec = planner.generate(q_start, dt)

print(len(q_vec))
print(q_vec)

# if success:
#     q_arr = np.array(q_vec)
#     if q_arr.ndim == 2 and q_arr.shape[0] != len(t_vec):
#         q_arr = q_arr.T
#     num_joints = q_arr.shape[1] if q_arr.ndim == 2 else 1
#     for i in range(num_joints):
#         plt.plot(t_vec, q_arr[:, i], label=f"joint{i + 1}")
#     plt.xlabel("Time (s)")
#     plt.ylabel("Joint position (rad)")
#     plt.title("Joint trajectories")
#     plt.legend()
#     plt.tight_layout()
#     plt.show()
