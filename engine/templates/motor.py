from engine.templates.vector import Vector
from engine.templates.body import Body
from engine.templates.joint import Joint
from engine.utils.helper import clamp, normalize_angle
import math

class Motor:
    def __init__(
        self,
        joint: Joint,
        body1: Body,
        body2: Body,
        min_angle: float = -math.pi,
        max_angle: float = math.pi,
    ):
        self.joint = joint
        self.b1 = body1
        self.b2 = body2

        self.rest_angle = normalize_angle(body2.orientation - body1.orientation)

        self.kp_motor = 800000.0
        self.kd_motor = 800.0
        self.max_torque = 50000000000 #allah wu akbar

        self.min_angle = min_angle
        self.max_angle = max_angle
        self.kp_limit = 1000000.0
        self.kd_limit = 1000.0

    
    def update(self, target_angle: float):
        target_angle = normalize_angle(target_angle)

        rel_angle = normalize_angle(
            (self.b2.orientation - self.b1.orientation) - self.rest_angle
        )
        rel_ang_vel = self.b2.ang_velocity - self.b1.ang_velocity

        motor_error = normalize_angle(target_angle - rel_angle)
        motor_torque = self.kp_motor * motor_error - self.kd_motor * rel_ang_vel

        limit_torque = 0.0

        if rel_angle < self.min_angle:
            limit_error = self.min_angle - rel_angle
            limit_torque = self.kp_limit * limit_error - self.kd_limit * rel_ang_vel

        elif rel_angle > self.max_angle:
            limit_error = self.max_angle - rel_angle
            limit_torque = self.kp_limit * limit_error - self.kd_limit * rel_ang_vel

        torque = motor_torque + limit_torque
        torque = clamp(torque, -self.max_torque, self.max_torque)

        self.b1.apply_torque(-torque)
        self.b2.apply_torque(torque)
