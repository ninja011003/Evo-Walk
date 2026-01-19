import math
from human import Human

MAX_ANG_VEL = 15.0
MAX_TORSO_VEL = 10.0
MAX_JOINT_ANGLE = math.pi

TORSO_IDX = 4
LEFT_THIGH_IDX = 0
LEFT_SHIN_IDX = 1
RIGHT_SHIN_IDX = 2
RIGHT_THIGH_IDX = 3


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


def foot_contact(human: Human, shin_idx: int) -> float:
    shin = human.engine.boxes[shin_idx]
    ground = human.engine.ground
    shin_pos = shin.get_world_anchor("bottom")
    ground_top = ground.body.position.y - ground.height / 2
    threshold = 5.0
    return 1.0 if shin_pos.y >= (ground_top - threshold) else 0.0


def input_vec(human: Human) -> list:
    inputs = []
    
    
    inputs.append(torso_angle(human) / math.pi)
    inputs.append(clamp(torso_ang_vel(human) / MAX_ANG_VEL))
    inputs.append(clamp(torso_vel_x(human) / MAX_TORSO_VEL))
    inputs.append(clamp(torso_vel_y(human) / MAX_TORSO_VEL))
    
    
    inputs.append(joint_angle_between(human, TORSO_IDX, LEFT_THIGH_IDX) / MAX_JOINT_ANGLE)
    inputs.append(clamp(joint_ang_vel_between(human, TORSO_IDX, LEFT_THIGH_IDX) / MAX_ANG_VEL))
    
    
    inputs.append(joint_angle_between(human, LEFT_THIGH_IDX, LEFT_SHIN_IDX) / MAX_JOINT_ANGLE)
    inputs.append(clamp(joint_ang_vel_between(human, LEFT_THIGH_IDX, LEFT_SHIN_IDX) / MAX_ANG_VEL))
    
    
    inputs.append(joint_angle_between(human, TORSO_IDX, RIGHT_THIGH_IDX) / MAX_JOINT_ANGLE)
    inputs.append(clamp(joint_ang_vel_between(human, TORSO_IDX, RIGHT_THIGH_IDX) / MAX_ANG_VEL))
    
    
    inputs.append(joint_angle_between(human, RIGHT_THIGH_IDX, RIGHT_SHIN_IDX) / MAX_JOINT_ANGLE)
    inputs.append(clamp(joint_ang_vel_between(human, RIGHT_THIGH_IDX, RIGHT_SHIN_IDX) / MAX_ANG_VEL))
    
    
    inputs.append(foot_contact(human, LEFT_SHIN_IDX))
    inputs.append(foot_contact(human, RIGHT_SHIN_IDX))
    
    return inputs
