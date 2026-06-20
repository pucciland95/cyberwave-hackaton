import time
from pyroboplan.ik.differential_ik import DifferentialIk, DifferentialIkOptions
import pinocchio
from os.path import dirname, abspath, join

import numpy as np
import matplotlib.pyplot as plt
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

    print(pinocchio_model_dir + "/piper_description.urdf")
    print(urdf_filename)

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


ik_solver = create_ikin_solver()


tforms = [
    pinocchio.SE3(np.eye(3), np.array([1.0, 1.0, 0.3])),
]

planner = create_planner(ik_solver, tforms)

dt = 0.05
q_start = [0, 0, 0, 0, 0, 0]
success, t_vec, q_vec = planner.generate(q_start, dt)


if success:
    q_arr = np.array(q_vec)
    num_joints = q_arr.shape[1] if q_arr.ndim == 2 else 1
    for i in range(num_joints):
        plt.plot(t_vec, q_arr[:, i], label=f"joint{i + 1}")
    plt.xlabel("Time (s)")
    plt.ylabel("Joint position (rad)")
    plt.title("Joint trajectories")
    plt.legend()
    plt.tight_layout()
    plt.show()
