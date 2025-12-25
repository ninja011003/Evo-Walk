from engine.templates.vector import Vector
from engine.utils.helper import sub, cross, compute_moi

from typing import Literal


class Body:
    def __init__(
        self,
        mass: float = 0.0,
        position: Vector = None,
        velocity: Vector = None,
        orientation: float = 0.0,
        shape: Literal["circle", "rectangle"] = "circle",
        radius: float = None,
        height: float = None,
        width: float = None,
    ):
        self.shape = shape
        self.radius = radius
        self.height = height
        self.width = width
        self.position = position if position else Vector(0, 0)
        self.velocity = velocity if velocity else Vector(0, 0)
        self.mass = mass
        self.inv_mass = 1 / mass if mass > 0 else 0
        self.total_force = Vector(0, 0)

        # for rotational [physics]
        self.orientation = orientation
        self.ang_velocity: float = 0.0
        self.moi = compute_moi(
            shape=self.shape,
            mass=self.mass,
            radius=self.radius,
            height=self.height,
            width=self.width,
        )
        self.inv_moi = 1 / self.moi if self.moi > 0 else 0
        self.total_torque: float = 0.0

    def apply_force(self, force: Vector):
        self.total_force.add(force)

    def apply_torque(self, torque: float):
        self.total_torque += torque

    def apply_point_force(self, force: Vector, point: Vector):
        self.total_force.add(force)
        r = sub(point, self.position)
        torque = cross(r, force)
        self.total_torque += torque

    def clear_forces(self):
        self.total_force = Vector(0, 0)

    def clear_torque(self):
        self.total_torque = 0

    def compute_dist(b1: "Body", b2: "Body"):
        v1, v2 = b1.position, b2.position
        return ((v2.x - v1.x) ** 2 + (v2.y - v1.y) ** 2) ** 0.5

    def integrate(self, dt):
        # semi euler's method
        a = Vector(
            self.total_force.x * self.inv_mass,
            self.total_force.y * self.inv_mass,
        )
        self.velocity.add(Vector(a.x * dt, a.y * dt))
        self.position.add(Vector(self.velocity.x * dt, self.velocity.y * dt))

        ang_a = self.total_torque * self.inv_moi
        self.ang_velocity = self.ang_velocity + ang_a * dt
        self.orientation += self.ang_velocity * dt
        self.total_torque = 0.0
        self.total_force = Vector(0, 0)
