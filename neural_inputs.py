import math
from human import Human

# TODO change them after performance
MAX_ANG_VEL = 15.0
MAX_TORSO_VEL = 10.0
MAX_JOINT_ANGLE = math.pi


def clamp(val: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, val))


def torso_angle(human: Human) -> float:
    torso = human.engine.boxes[1]
    return torso.body.orientation


def torso_ang_vel(human: Human) -> float:
    torso = human.engine.boxes[1]
    return torso.body.ang_velocity


def torso_vel_x(human: Human) -> float:
    torso = human.engine.boxes[1]
    return torso.body.velocity.x


def torso_vel_y(human: Human) -> float:
    torso = human.engine.boxes[1]
    return torso.body.velocity.y


def joint_angle(human: Human, leg_index: int) -> float:
    torso = human.engine.boxes[1]
    leg = human.engine.boxes[leg_index]
    relative_angle = leg.body.orientation - torso.body.orientation
    while relative_angle > math.pi:
        relative_angle -= 2 * math.pi
    while relative_angle < -math.pi:
        relative_angle += 2 * math.pi
    return relative_angle


def joint_ang_vel(human: Human, leg_index: int) -> float:
    torso = human.engine.boxes[1]
    leg = human.engine.boxes[leg_index]
    return leg.body.ang_velocity - torso.body.ang_velocity


def foot_contact(human: Human, leg_index: int) -> bool:
    leg = human.engine.boxes[leg_index]
    ground = human.engine.ground

    foot_pos = leg.get_world_anchor("bottom")
    ground_top = ground.body.position.y - ground.height / 2

    threshold = 5.0
    return foot_pos.y <= (ground_top + threshold)


def motor_target_angles(human: Human) -> list:
    return [m.target_angle for m in human.motors]


def all_inputs(human: Human) -> dict:
    return {
        "torso_angle": torso_angle(human),
        "torso_ang_vel": torso_ang_vel(human),
        "torso_vel_x": torso_vel_x(human),
        "torso_vel_y": torso_vel_y(human),
        "left_joint_angle": joint_angle(human, 0),
        "left_joint_ang_vel": joint_ang_vel(human, 0),
        "right_joint_angle": joint_angle(human, 2),
        "right_joint_ang_vel": joint_ang_vel(human, 2),
        "left_foot_contact": foot_contact(human, 0),
        "right_foot_contact": foot_contact(human, 2),
        "motor_target_angles": motor_target_angles(human),
    }


def input_vec(human: Human) -> list:
    inputs = []
    inputs.append(torso_angle(human) / math.pi)
    # inputs.append(clamp(torso_ang_vel(human) / MAX_ANG_VEL))
    # inputs.append(clamp(torso_vel_x(human) / MAX_TORSO_VEL))
    # inputs.append(clamp(torso_vel_y(human) / MAX_TORSO_VEL))
    inputs.append(joint_angle(human, 0) / MAX_JOINT_ANGLE)
    inputs.append(clamp(joint_ang_vel(human, 0) / MAX_ANG_VEL))
    inputs.append(joint_angle(human, 2) / MAX_JOINT_ANGLE)
    inputs.append(clamp(joint_ang_vel(human, 2) / MAX_ANG_VEL))
    for angle in motor_target_angles(human):
        inputs.append(angle / math.pi)
    inputs.append(1.0 if foot_contact(human, 0) else 0.0)
    inputs.append(1.0 if foot_contact(human, 2) else 0.0)
    return inputs
