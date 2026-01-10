import math
from human import Human

MAX_ANG_VEL = 15.0
MAX_TORSO_VEL = 10.0
MAX_JOINT_ANGLE = math.pi
MAX_CONTACT_FORCE = 1000.0
MAX_FOOT_OFFSET = 200.0

TORSO_IDX = 1
LEFT_THIGH_IDX = 6
RIGHT_THIGH_IDX = 7
LEFT_FOOT_IDX = 8
RIGHT_FOOT_IDX = 9
LEFT_UPPER_ARM_IDX = 4
LEFT_LOWER_ARM_IDX = 5
RIGHT_UPPER_ARM_IDX = 2
RIGHT_LOWER_ARM_IDX = 3


def clamp(val: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, val))


def normalize_angle(angle: float) -> float:
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle


def torso_angle(human: Human) -> float:
    torso = human.engine.boxes[TORSO_IDX]
    return torso.body.orientation


def torso_ang_vel(human: Human) -> float:
    torso = human.engine.boxes[TORSO_IDX]
    return torso.body.ang_velocity


def torso_vel_x(human: Human) -> float:
    torso = human.engine.boxes[TORSO_IDX]
    return torso.body.velocity.x


def torso_vel_y(human: Human) -> float:
    torso = human.engine.boxes[TORSO_IDX]
    return torso.body.velocity.y


def joint_angle_between(human: Human, body1_idx: int, body2_idx: int) -> float:
    body1 = human.engine.boxes[body1_idx]
    body2 = human.engine.boxes[body2_idx]
    relative_angle = body2.body.orientation - body1.body.orientation
    return normalize_angle(relative_angle)


def joint_ang_vel_between(human: Human, body1_idx: int, body2_idx: int) -> float:
    body1 = human.engine.boxes[body1_idx]
    body2 = human.engine.boxes[body2_idx]
    return body2.body.ang_velocity - body1.body.ang_velocity


def foot_contact(human: Human, foot_idx: int) -> float:
    foot = human.engine.boxes[foot_idx]
    ground = human.engine.ground
    foot_pos = foot.get_world_anchor("bottom")
    ground_top = ground.body.position.y - ground.height / 2
    threshold = 5.0
    return 1.0 if foot_pos.y >= (ground_top - threshold) else 0.0


def foot_contact_force(human: Human, foot_idx: int) -> float:
    foot = human.engine.boxes[foot_idx]
    ground = human.engine.ground
    foot_pos = foot.get_world_anchor("bottom")
    ground_top = ground.body.position.y - ground.height / 2
    penetration = foot_pos.y - ground_top
    if penetration > 0:
        force = min(penetration * 100.0, MAX_CONTACT_FORCE)
        return force
    return 0.0


def foot_relative_pos(human: Human, foot_idx: int) -> tuple:
    torso = human.engine.boxes[TORSO_IDX]
    foot = human.engine.boxes[foot_idx]
    foot_pos = foot.get_world_anchor("bottom")
    torso_pos = torso.body.position
    rel_x = foot_pos.x - torso_pos.x
    rel_y = foot_pos.y - torso_pos.y
    return (rel_x, rel_y)


def input_vec(human: Human) -> list:
    inputs = []
    
    inputs.append(torso_angle(human) / math.pi)
    inputs.append(clamp(torso_ang_vel(human) / MAX_ANG_VEL))
    inputs.append(clamp(torso_vel_x(human) / MAX_TORSO_VEL))
    inputs.append(clamp(torso_vel_y(human) / MAX_TORSO_VEL))
    
    inputs.append(joint_angle_between(human, TORSO_IDX, LEFT_THIGH_IDX) / MAX_JOINT_ANGLE)
    inputs.append(clamp(joint_ang_vel_between(human, TORSO_IDX, LEFT_THIGH_IDX) / MAX_ANG_VEL))
    
    inputs.append(joint_angle_between(human, LEFT_THIGH_IDX, LEFT_FOOT_IDX) / MAX_JOINT_ANGLE)
    inputs.append(clamp(joint_ang_vel_between(human, LEFT_THIGH_IDX, LEFT_FOOT_IDX) / MAX_ANG_VEL))
    
    inputs.append(joint_angle_between(human, TORSO_IDX, RIGHT_THIGH_IDX) / MAX_JOINT_ANGLE)
    inputs.append(clamp(joint_ang_vel_between(human, TORSO_IDX, RIGHT_THIGH_IDX) / MAX_ANG_VEL))
    
    inputs.append(joint_angle_between(human, RIGHT_THIGH_IDX, RIGHT_FOOT_IDX) / MAX_JOINT_ANGLE)
    inputs.append(clamp(joint_ang_vel_between(human, RIGHT_THIGH_IDX, RIGHT_FOOT_IDX) / MAX_ANG_VEL))
    
    inputs.append(joint_angle_between(human, TORSO_IDX, LEFT_UPPER_ARM_IDX) / MAX_JOINT_ANGLE)
    inputs.append(clamp(joint_ang_vel_between(human, TORSO_IDX, LEFT_UPPER_ARM_IDX) / MAX_ANG_VEL))
    
    inputs.append(joint_angle_between(human, TORSO_IDX, RIGHT_UPPER_ARM_IDX) / MAX_JOINT_ANGLE)
    inputs.append(clamp(joint_ang_vel_between(human, TORSO_IDX, RIGHT_UPPER_ARM_IDX) / MAX_ANG_VEL))
    
    inputs.append(foot_contact(human, LEFT_FOOT_IDX))
    inputs.append(clamp(foot_contact_force(human, LEFT_FOOT_IDX) / MAX_CONTACT_FORCE))
    inputs.append(foot_contact(human, RIGHT_FOOT_IDX))
    inputs.append(clamp(foot_contact_force(human, RIGHT_FOOT_IDX) / MAX_CONTACT_FORCE))
    
    left_rel = foot_relative_pos(human, LEFT_FOOT_IDX)
    inputs.append(clamp(left_rel[0] / MAX_FOOT_OFFSET))
    inputs.append(clamp(left_rel[1] / MAX_FOOT_OFFSET))
    right_rel = foot_relative_pos(human, RIGHT_FOOT_IDX)
    inputs.append(clamp(right_rel[0] / MAX_FOOT_OFFSET))
    inputs.append(clamp(right_rel[1] / MAX_FOOT_OFFSET))
    
    return inputs
