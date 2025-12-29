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
        self.target_length = self.rest_length
        self.max_force = 5000.0
        self.stiffness = 2000.0
        self.damping = 50.0
        self.activation = 0.0
        self.name = f"Actuator_{self.id}"

    def _is_box(self, obj):
        return hasattr(obj, 'get_local_anchors')

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
        self.activation = max(0.0, min(1.0, value))
        min_length = self.rest_length * 0.3
        self.target_length = self.rest_length - self.activation * (self.rest_length - min_length)

    def apply_forces(self):
        p1 = self._get_world_position(self.obj1, self.anchor1)
        p2 = self._get_world_position(self.obj2, self.anchor2)

        dx = p2.x - p1.x
        dy = p2.y - p1.y
        current_length = (dx * dx + dy * dy) ** 0.5

        if current_length < 0.001:
            return

        dir_x = dx / current_length
        dir_y = dy / current_length

        stretch = current_length - self.target_length

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

        force_magnitude = self.stiffness * stretch + self.damping * rel_vel_along

        force_magnitude = max(-self.max_force, min(self.max_force, force_magnitude))

        force_x = force_magnitude * dir_x
        force_y = force_magnitude * dir_y

        self.obj1.body.apply_point_force(Vector(force_x, force_y), p1)
        self.obj2.body.apply_point_force(Vector(-force_x, -force_y), p2)

    def contains(self, x, y):
        x1, y1 = self.get_endpoint1()
        x2, y2 = self.get_endpoint2()

        line_len = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if line_len == 0:
            return False

        t = max(0, min(1, ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / (line_len ** 2)))
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)

        dist = ((x - proj_x) ** 2 + (y - proj_y) ** 2) ** 0.5
        return dist <= 10

    def get_debug_info(self):
        current_len = self.cur_length()
        p1 = self.get_endpoint1()
        p2 = self.get_endpoint2()
        return {
            "type": "Actuator",
            "id": self.id,
            "name": self.name,
            "obj1": self.obj1.name,
            "obj2": self.obj2.name,
            "anchor1": self.anchor1 or "center",
            "anchor2": self.anchor2 or "center",
            "rest_length": round(self.rest_length, 2),
            "target_length": round(self.target_length, 2),
            "current_length": round(current_len, 2),
            "activation": round(self.activation, 2),
            "max_force": round(self.max_force, 2),
            "stiffness": round(self.stiffness, 2),
        }

    def set_property(self, key, value):
        if key == "target_length":
            self.target_length = max(1, float(value))
        elif key == "activation":
            self.set_activation(float(value))
        elif key == "max_force":
            self.max_force = max(0, float(value))
        elif key == "stiffness":
            self.stiffness = max(0, float(value))

