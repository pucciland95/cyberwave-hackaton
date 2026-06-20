from cyberwave import Cyberwave
import time
import math

def move_to(arm, des: list, err_tol=5.0):

    joint_names = arm.joints.list()

    joint_names.remove("joint7")
    joint_names.remove("joint8")

    joints = {j_name: j_pos for j_name, j_pos in zip(joint_names, des)}

    arm.joints.set(
        joints,
        degrees=True,
    )

    time.sleep(5)

    # while True:

    #     all_joints = arm.joints.get_all()
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


cw = Cyberwave()
arm = cw.twin("agile-x-robotics/piper")


pos1 = [0.0, 30.0, -75.0, 0.0, 0.0, 0.0]
pos2 = [180.0, 30.0, -75.0, 0.0, 0.0, 0.0]

# move_to(arm, pos1)
# move_to(arm, pos2)

