import math
from human import Human

# TODO change them after performance
MAX_ANG_VEL = 15.0
MAX_TORSO_VEL = 10.0
MAX_JOINT_ANGLE = math.pi
MAX_MUSCLE_VEL = 500.0


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


def muscle_len(human: Human, idx: int) -> float:
    actuator = human.actuators[idx]
    return actuator.cur_length() / actuator.rest_length


def muscle_vel(human: Human, idx: int) -> float:
    actuator = human.actuators[idx]
    p1 = actuator._get_world_position(actuator.obj1, actuator.anchor1)
    p2 = actuator._get_world_position(actuator.obj2, actuator.anchor2)

    dx = p2.x - p1.x
    dy = p2.y - p1.y
    length = (dx * dx + dy * dy) ** 0.5

    if length < 0.001:
        return 0.0

    dir_x = dx / length
    dir_y = dy / length

    local1 = actuator._get_local_anchor(actuator.obj1, actuator.anchor1)
    local2 = actuator._get_local_anchor(actuator.obj2, actuator.anchor2)

    cos1 = math.cos(actuator.obj1.body.orientation)
    sin1 = math.sin(actuator.obj1.body.orientation)
    r1_x = local1.x * cos1 - local1.y * sin1
    r1_y = local1.x * sin1 + local1.y * cos1

    cos2 = math.cos(actuator.obj2.body.orientation)
    sin2 = math.sin(actuator.obj2.body.orientation)
    r2_x = local2.x * cos2 - local2.y * sin2
    r2_y = local2.x * sin2 + local2.y * cos2

    v1_x = (
        actuator.obj1.body.velocity.x - actuator.obj1.body.ang_velocity * r1_y
    )
    v1_y = (
        actuator.obj1.body.velocity.y + actuator.obj1.body.ang_velocity * r1_x
    )

    v2_x = (
        actuator.obj2.body.velocity.x - actuator.obj2.body.ang_velocity * r2_y
    )
    v2_y = (
        actuator.obj2.body.velocity.y + actuator.obj2.body.ang_velocity * r2_x
    )

    rel_vel_x = v2_x - v1_x
    rel_vel_y = v2_y - v1_y

    return rel_vel_x * dir_x + rel_vel_y * dir_y


def all_muscle_lens(human: Human) -> list:
    return [muscle_len(human, i) for i in range(len(human.actuators))]


def all_muscle_vels(human: Human) -> list:
    return [muscle_vel(human, i) for i in range(len(human.actuators))]


def foot_contact(human: Human, leg_index: int) -> bool:
    leg = human.engine.boxes[leg_index]
    ground = human.engine.ground

    foot_pos = leg.get_world_anchor("bottom")
    ground_top = ground.body.position.y - ground.height / 2

    threshold = 5.0
    return foot_pos.y <= (ground_top + threshold)


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
        "muscle_lens": all_muscle_lens(human),
        "muscle_vels": all_muscle_vels(human),
        "left_foot_contact": foot_contact(human, 0),
        "right_foot_contact": foot_contact(human, 2),
    }


def input_vec(human: Human) -> list:
    inputs = []
    inputs.append(torso_angle(human) / math.pi)
    inputs.append(clamp(torso_ang_vel(human) / MAX_ANG_VEL))
    inputs.append(clamp(torso_vel_x(human) / MAX_TORSO_VEL))
    inputs.append(clamp(torso_vel_y(human) / MAX_TORSO_VEL))
    inputs.append(joint_angle(human, 0) / MAX_JOINT_ANGLE)
    inputs.append(clamp(joint_ang_vel(human, 0) / MAX_ANG_VEL))
    inputs.append(joint_angle(human, 2) / MAX_JOINT_ANGLE)
    inputs.append(clamp(joint_ang_vel(human, 2) / MAX_ANG_VEL))
    inputs.extend(
        [muscle_len(human, i) - 1.0 for i in range(len(human.actuators))]
    )
    inputs.extend([clamp(v / MAX_MUSCLE_VEL) for v in all_muscle_vels(human)])
    inputs.append(1.0 if foot_contact(human, 0) else 0.0)
    inputs.append(1.0 if foot_contact(human, 2) else 0.0)
    # print(len(inputs))
    return inputs
