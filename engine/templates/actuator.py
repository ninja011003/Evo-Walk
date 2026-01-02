import math
from engine.templates.vector import Vector


class Actuator:
    _id_counter = 0

    def __init__(self, obj1, obj2, anchor1=None, anchor2=None):
        Actuator._id_counter += 1
        self.id = Actuator._id_counter
        self.obj1 = obj1
        self.obj2 = obj2
        self.anchor1 = anchor1
        self.anchor2 = anchor2

        p1 = self._get_world_position(obj1, anchor1)
        p2 = self._get_world_position(obj2, anchor2)
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        self.rest_length = (dx * dx + dy * dy) ** 0.5
        self.max_force = 100000.0
        self.max_stiffness = 5000.0
        self.damping = 100.0
        self.activation = 0.0
        self.target_activation = 0.0
        self.activation_tau = 0.1
        self.name = f"Actuator_{self.id}"

    def _is_box(self, obj):
        return hasattr(obj, "get_local_anchors")

    def _get_local_anchor(self, obj, anchor):
        if self._is_box(obj) and anchor:
            return obj.get_local_anchors()[anchor]
        return Vector(0, 0)

    def _get_world_position(self, obj, anchor):
        if self._is_box(obj) and anchor:
            return obj.get_world_anchor(anchor)
        return Vector(obj.body.position.x, obj.body.position.y)

    def get_endpoint1(self):
        pos = self._get_world_position(self.obj1, self.anchor1)
        return (pos.x, pos.y)

    def get_endpoint2(self):
        pos = self._get_world_position(self.obj2, self.anchor2)
        return (pos.x, pos.y)

    def cur_length(self):
        p1 = self._get_world_position(self.obj1, self.anchor1)
        p2 = self._get_world_position(self.obj2, self.anchor2)
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        return (dx * dx + dy * dy) ** 0.5

    def set_activation(self, value):
        self.target_activation = max(0.0, min(1.0, value))

    def update_activation(self, dt):
        alpha = 1.0 - math.exp(-dt / self.activation_tau)
        self.activation += (self.target_activation - self.activation) * alpha

    def apply_forces(self, dt):
        self.update_activation(dt)

        p1 = self._get_world_position(self.obj1, self.anchor1)
        p2 = self._get_world_position(self.obj2, self.anchor2)

        dx = p2.x - p1.x
        dy = p2.y - p1.y
        current_length = (dx * dx + dy * dy) ** 0.5

        if current_length < 1.0:
            sep_force = 500.0
            if current_length > 0.001:
                dir_x = dx / current_length
                dir_y = dy / current_length
            else:
                dir_x = 0.0
                dir_y = 1.0
            self.obj1.body.apply_point_force(
                Vector(-sep_force * dir_x, -sep_force * dir_y), p1
            )
            self.obj2.body.apply_point_force(
                Vector(sep_force * dir_x, sep_force * dir_y), p2
            )
            return

        dir_x = dx / current_length
        dir_y = dy / current_length

        stretch = current_length - self.rest_length

        local1 = self._get_local_anchor(self.obj1, self.anchor1)
        local2 = self._get_local_anchor(self.obj2, self.anchor2)

        cos1 = math.cos(self.obj1.body.orientation)
        sin1 = math.sin(self.obj1.body.orientation)
        r1_x = local1.x * cos1 - local1.y * sin1
        r1_y = local1.x * sin1 + local1.y * cos1

        cos2 = math.cos(self.obj2.body.orientation)
        sin2 = math.sin(self.obj2.body.orientation)
        r2_x = local2.x * cos2 - local2.y * sin2
        r2_y = local2.x * sin2 + local2.y * cos2

        v1_x = self.obj1.body.velocity.x - self.obj1.body.ang_velocity * r1_y
        v1_y = self.obj1.body.velocity.y + self.obj1.body.ang_velocity * r1_x

        v2_x = self.obj2.body.velocity.x - self.obj2.body.ang_velocity * r2_y
        v2_y = self.obj2.body.velocity.y + self.obj2.body.ang_velocity * r2_x

        rel_vel_x = v2_x - v1_x
        rel_vel_y = v2_y - v1_y
        rel_vel_along = rel_vel_x * dir_x + rel_vel_y * dir_y

        effective_stiffness = self.activation * self.max_stiffness
        effective_max_force = self.activation * self.max_force

        force_magnitude = (
            effective_stiffness * stretch - self.damping * rel_vel_along
        )

        if force_magnitude < 0:
            force_magnitude = 0

        force_magnitude = min(force_magnitude, effective_max_force)

        force_x = force_magnitude * dir_x
        force_y = force_magnitude * dir_y

        inv_mass1 = self.obj1.body.inv_mass
        inv_mass2 = self.obj2.body.inv_mass
        total_inv_mass = inv_mass1 + inv_mass2

        if total_inv_mass > 0:
            w1 = inv_mass1 / total_inv_mass
            w2 = inv_mass2 / total_inv_mass
        else:
            w1 = 0.5
            w2 = 0.5

        self.obj1.body.apply_point_force(
            Vector(force_x * w1 * 2, force_y * w1 * 2), p1
        )
        self.obj2.body.apply_point_force(
            Vector(-force_x * w2 * 2, -force_y * w2 * 2), p2
        )

    def contains(self, x, y):
        x1, y1 = self.get_endpoint1()
        x2, y2 = self.get_endpoint2()

        line_len = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if line_len == 0:
            return False

        t = max(
            0,
            min(
                1, ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / (line_len**2)
            ),
        )
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)

        dist = ((x - proj_x) ** 2 + (y - proj_y) ** 2) ** 0.5
        return dist <= 10

    def get_debug_info(self):
        current_len = self.cur_length()
        return {
            "type": "Actuator",
            "id": self.id,
            "name": self.name,
            "obj1": self.obj1.name,
            "obj2": self.obj2.name,
            "anchor1": self.anchor1 or "center",
            "anchor2": self.anchor2 or "center",
            "rest_length": round(self.rest_length, 2),
            "current_length": round(current_len, 2),
            "activation": round(self.activation, 2),
            "target_act": round(self.target_activation, 2),
            "max_force": round(self.max_force, 2),
            "max_stiffness": round(self.max_stiffness, 2),
            "damping": round(self.damping, 2),
        }

    def set_property(self, key, value):
        if key == "rest_length":
            self.rest_length = max(1, float(value))
        elif key == "activation":
            self.set_activation(float(value))
        elif key == "target_act":
            self.set_activation(float(value))
        elif key == "max_force":
            self.max_force = max(0, float(value))
        elif key == "max_stiffness":
            self.max_stiffness = max(0, float(value))
        elif key == "damping":
            self.damping = max(0, float(value))
