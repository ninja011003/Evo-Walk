import json
import os
from engine.templates.vector import Vector
from engine.templates.body import Body
from engine.templates.contraint import Contraint
from engine.templates.collision_handler import Collision_Handler

TEMPLATES_FILE = os.path.join(os.path.dirname(__file__), "templates.json")

BOB_RADIUS = 5
BOX_WIDTH = 15
BOX_HEIGHT = 80
GRAVITY = Vector(0, 980)
FORCE_MAGNITUDE = 5000


class Bob:
    _id_counter = 0

    def __init__(self, x, y, pinned=False):
        Bob._id_counter += 1
        self.id = Bob._id_counter
        self.radius = BOB_RADIUS
        mass = 0 if pinned else 1
        self.body = Body(
            mass=mass, position=Vector(x, y), shape="circle", radius=self.radius
        )
        self.pinned = pinned
        if self.pinned:
            self.body.inv_moi = 0
        self.name = f"Bob_{self.id}"

    def contains(self, x, y):
        dx = x - self.body.position.x
        dy = y - self.body.position.y
        return (dx * dx + dy * dy) <= (self.radius + 8) ** 2

    def apply_force(self, force):
        self.body.apply_force(force)

    def apply_torque(self, torque):
        self.body.apply_torque(torque)

    def apply_point_force(self, force, point):
        self.body.apply_point_force(force, point)

    def clear_forces(self):
        self.body.clear_forces()

    def clear_torque(self):
        self.body.clear_torque()

    def get_debug_info(self):
        return {
            "type": "Bob",
            "id": self.id,
            "name": self.name,
            "position.x": round(self.body.position.x, 2),
            "position.y": round(self.body.position.y, 2),
            "velocity.x": round(self.body.velocity.x, 2),
            "velocity.y": round(self.body.velocity.y, 2),
            "mass": self.body.mass,
            "pinned": self.pinned,
            "radius": self.radius,
            "force.x": round(self.body.total_force.x, 2),
            "force.y": round(self.body.total_force.y, 2),
            "orientation": round(self.body.orientation, 2),
            "ang_velocity": round(self.body.ang_velocity, 2),
            "moi": round(self.body.moi, 2),
            "torque": round(self.body.total_torque, 2),
            "add_torque": 0.0,
            "add_force.x": 0.0,
            "add_force.y": 0.0,
        }

    def set_property(self, key, value):
        if key == "position.x":
            self.body.position.x = float(value)
        elif key == "position.y":
            self.body.position.y = float(value)
        elif key == "velocity.x":
            self.body.velocity.x = float(value)
        elif key == "velocity.y":
            self.body.velocity.y = float(value)
        elif key == "mass":
            self.body.mass = float(value)
            self.body.inv_mass = 1 / self.body.mass if self.body.mass > 0 else 0
            self.pinned = self.body.mass == 0
            self.radius = BOB_RADIUS * (self.body.mass / 5)
            self.body.radius = self.radius
        elif key == "pinned":
            self.pinned = bool(value)
            self.body.mass = 0 if self.pinned else 1
            self.body.inv_mass = 1 / self.body.mass if self.body.mass > 0 else 0
            self.body.inv_moi = (
                0
                if self.pinned
                else (1 / self.body.moi if self.body.moi > 0 else 0)
            )
        elif key == "radius":
            self.radius = max(5, int(value))
            self.body.radius = self.radius
        elif key == "orientation":
            self.body.orientation = float(value)
        elif key == "ang_velocity":
            self.body.ang_velocity = float(value)
        elif key == "add_torque":
            self.body.apply_torque(float(value))
        elif key == "add_force.x":
            self.body.apply_force(Vector(float(value), 0))
        elif key == "add_force.y":
            self.body.apply_force(Vector(0, float(value)))


class Box:
    _id_counter = 0

    ANCHOR_CENTER = "center"
    ANCHOR_LEFT = "left"
    ANCHOR_RIGHT = "right"
    ANCHOR_TOP = "top"
    ANCHOR_BOTTOM = "bottom"

    def __init__(self, x, y, width=BOX_WIDTH, height=BOX_HEIGHT, pinned=False):
        Box._id_counter += 1
        self.id = Box._id_counter
        self.width = width
        self.height = height
        mass = 0 if pinned else 2
        self.body = Body(
            mass=mass,
            position=Vector(x, y),
            shape="rectangle",
            width=self.width,
            height=self.height,
        )
        self.pinned = pinned
        if self.pinned:
            self.body.inv_moi = 0
        self.name = f"Box_{self.id}"

    def get_local_anchors(self):
        hw = self.width / 2
        hh = self.height / 2
        return {
            self.ANCHOR_CENTER: Vector(0, 0),
            self.ANCHOR_LEFT: Vector(-hw, 0),
            self.ANCHOR_RIGHT: Vector(hw, 0),
            self.ANCHOR_TOP: Vector(0, -hh),
            self.ANCHOR_BOTTOM: Vector(0, hh),
        }

    def get_world_anchor(self, anchor_name):
        import math
        local = self.get_local_anchors()[anchor_name]
        cos_a = math.cos(self.body.orientation)
        sin_a = math.sin(self.body.orientation)
        wx = self.body.position.x + local.x * cos_a - local.y * sin_a
        wy = self.body.position.y + local.x * sin_a + local.y * cos_a
        return Vector(wx, wy)

    def get_all_world_anchors(self):
        import math
        cos_a = math.cos(self.body.orientation)
        sin_a = math.sin(self.body.orientation)
        cx, cy = self.body.position.x, self.body.position.y
        result = {}
        for name, local in self.get_local_anchors().items():
            wx = cx + local.x * cos_a - local.y * sin_a
            wy = cy + local.x * sin_a + local.y * cos_a
            result[name] = (wx, wy)
        return result

    def get_nearest_anchor(self, x, y):
        anchors = self.get_all_world_anchors()
        min_dist = float('inf')
        nearest = self.ANCHOR_CENTER
        for name, (ax, ay) in anchors.items():
            dist = (x - ax) ** 2 + (y - ay) ** 2
            if dist < min_dist:
                min_dist = dist
                nearest = name
        return nearest

    def contains(self, x, y):
        import math

        cos_a = math.cos(-self.body.orientation)
        sin_a = math.sin(-self.body.orientation)
        dx = x - self.body.position.x
        dy = y - self.body.position.y
        local_x = dx * cos_a - dy * sin_a
        local_y = dx * sin_a + dy * cos_a
        return (
            abs(local_x) <= self.width / 2 + 5
            and abs(local_y) <= self.height / 2 + 5
        )

    def apply_force(self, force):
        self.body.apply_force(force)

    def apply_torque(self, torque):
        self.body.apply_torque(torque)

    def apply_point_force(self, force, point):
        self.body.apply_point_force(force, point)

    def clear_forces(self):
        self.body.clear_forces()

    def clear_torque(self):
        self.body.clear_torque()

    def get_debug_info(self):
        return {
            "type": "Box",
            "id": self.id,
            "name": self.name,
            "position.x": round(self.body.position.x, 2),
            "position.y": round(self.body.position.y, 2),
            "velocity.x": round(self.body.velocity.x, 2),
            "velocity.y": round(self.body.velocity.y, 2),
            "mass": self.body.mass,
            "pinned": self.pinned,
            "width": self.width,
            "height": self.height,
            "force.x": round(self.body.total_force.x, 2),
            "force.y": round(self.body.total_force.y, 2),
            "orientation": round(self.body.orientation, 2),
            "ang_velocity": round(self.body.ang_velocity, 2),
            "moi": round(self.body.moi, 2),
            "torque": round(self.body.total_torque, 2),
            "add_torque": 0.0,
            "add_force.x": 0.0,
            "add_force.y": 0.0,
        }

    def set_property(self, key, value):
        if key == "position.x":
            self.body.position.x = float(value)
        elif key == "position.y":
            self.body.position.y = float(value)
        elif key == "velocity.x":
            self.body.velocity.x = float(value)
        elif key == "velocity.y":
            self.body.velocity.y = float(value)
        elif key == "mass":
            self.body.mass = float(value)
            self.body.inv_mass = 1 / self.body.mass if self.body.mass > 0 else 0
            self.pinned = self.body.mass == 0
        elif key == "pinned":
            self.pinned = bool(value)
            self.body.mass = 0 if self.pinned else 2
            self.body.inv_mass = 1 / self.body.mass if self.body.mass > 0 else 0
            self.body.inv_moi = (
                0
                if self.pinned
                else (1 / self.body.moi if self.body.moi > 0 else 0)
            )
        elif key == "width":
            self.width = max(10, float(value))
            self.body.width = self.width
        elif key == "height":
            self.height = max(10, float(value))
            self.body.height = self.height
        elif key == "orientation":
            self.body.orientation = float(value)
        elif key == "ang_velocity":
            self.body.ang_velocity = float(value)
        elif key == "add_torque":
            self.body.apply_torque(float(value))
        elif key == "add_force.x":
            self.body.apply_force(Vector(float(value), 0))
        elif key == "add_force.y":
            self.body.apply_force(Vector(0, float(value)))


import math

class PointConstraint:
    def __init__(self, box, anchor_name, bob):
        self.box = box
        self.anchor_name = anchor_name
        self.bob = bob
        self.local_anchor = box.get_local_anchors()[anchor_name]

    def get_world_anchor(self):
        cos_a = math.cos(self.box.body.orientation)
        sin_a = math.sin(self.box.body.orientation)
        wx = self.box.body.position.x + self.local_anchor.x * cos_a - self.local_anchor.y * sin_a
        wy = self.box.body.position.y + self.local_anchor.x * sin_a + self.local_anchor.y * cos_a
        return Vector(wx, wy)

    def solve(self):
        world_anchor = self.get_world_anchor()
        bob_pos = self.bob.body.position

        err_x = bob_pos.x - world_anchor.x
        err_y = bob_pos.y - world_anchor.y

        if abs(err_x) < 0.001 and abs(err_y) < 0.001:
            return

        w_bob = self.bob.body.inv_mass
        w_box = self.box.body.inv_mass

        r_x = world_anchor.x - self.box.body.position.x
        r_y = world_anchor.y - self.box.body.position.y

        r_cross_nx = -r_y
        r_cross_ny = r_x

        angular_mass_x = self.box.body.inv_moi * r_cross_nx * r_cross_nx
        angular_mass_y = self.box.body.inv_moi * r_cross_ny * r_cross_ny

        eff_mass_x = w_bob + w_box + angular_mass_x
        eff_mass_y = w_bob + w_box + angular_mass_y

        if eff_mass_x > 0:
            lambda_x = err_x / eff_mass_x
            self.bob.body.position.x -= w_bob * lambda_x
            self.box.body.position.x += w_box * lambda_x
            self.box.body.orientation += self.box.body.inv_moi * r_cross_nx * lambda_x

        if eff_mass_y > 0:
            lambda_y = err_y / eff_mass_y
            self.bob.body.position.y -= w_bob * lambda_y
            self.box.body.position.y += w_box * lambda_y
            self.box.body.orientation += self.box.body.inv_moi * r_cross_ny * lambda_y

        world_anchor = self.get_world_anchor()
        r_x = world_anchor.x - self.box.body.position.x
        r_y = world_anchor.y - self.box.body.position.y

        box_anchor_vel_x = self.box.body.velocity.x - self.box.body.ang_velocity * r_y
        box_anchor_vel_y = self.box.body.velocity.y + self.box.body.ang_velocity * r_x

        rel_vel_x = self.bob.body.velocity.x - box_anchor_vel_x
        rel_vel_y = self.bob.body.velocity.y - box_anchor_vel_y

        r_cross_nx = -r_y
        r_cross_ny = r_x

        angular_mass_x = self.box.body.inv_moi * r_cross_nx * r_cross_nx
        angular_mass_y = self.box.body.inv_moi * r_cross_ny * r_cross_ny

        eff_mass_x = w_bob + w_box + angular_mass_x
        eff_mass_y = w_bob + w_box + angular_mass_y

        if eff_mass_x > 0:
            impulse_x = rel_vel_x / eff_mass_x
            self.bob.body.velocity.x -= w_bob * impulse_x
            self.box.body.velocity.x += w_box * impulse_x
            self.box.body.ang_velocity += self.box.body.inv_moi * r_cross_nx * impulse_x

        if eff_mass_y > 0:
            impulse_y = rel_vel_y / eff_mass_y
            self.bob.body.velocity.y -= w_bob * impulse_y
            self.box.body.velocity.y += w_box * impulse_y
            self.box.body.ang_velocity += self.box.body.inv_moi * r_cross_ny * impulse_y


class Rod:
    _id_counter = 0

    def __init__(self, obj1, obj2, anchor1=None, anchor2=None):
        Rod._id_counter += 1
        self.id = Rod._id_counter
        self.bob1 = obj1
        self.bob2 = obj2
        self.anchor1 = anchor1
        self.anchor2 = anchor2

        self.constraint = None
        self.point_constraint1 = None
        self.point_constraint2 = None

        p1 = self._get_position(obj1, anchor1)
        p2 = self._get_position(obj2, anchor2)
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        self.length = (dx * dx + dy * dy) ** 0.5

        is_box1 = isinstance(obj1, Box)
        is_box2 = isinstance(obj2, Box)

        if is_box1 and anchor1 and not isinstance(obj2, Box):
            self.point_constraint1 = PointConstraint(obj1, anchor1, obj2)
        elif is_box2 and anchor2 and not isinstance(obj1, Box):
            self.point_constraint1 = PointConstraint(obj2, anchor2, obj1)
        else:
            self.constraint = Contraint(obj1.body, obj2.body, self.length)

        self.name = f"Rod_{self.id}"

    def _get_position(self, obj, anchor):
        if isinstance(obj, Box) and anchor:
            return obj.get_world_anchor(anchor)
        return obj.body.position

    def get_endpoint1(self):
        pos = self._get_position(self.bob1, self.anchor1)
        return (pos.x, pos.y)

    def get_endpoint2(self):
        pos = self._get_position(self.bob2, self.anchor2)
        return (pos.x, pos.y)

    def solve(self):
        if self.point_constraint1:
            self.point_constraint1.solve()
        if self.point_constraint2:
            self.point_constraint2.solve()
        if self.constraint:
            self.constraint.solve()

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
        return dist <= 8

    def cur_length(self):
        p1 = self._get_position(self.bob1, self.anchor1)
        p2 = self._get_position(self.bob2, self.anchor2)
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        return (dx * dx + dy * dy) ** 0.5

    def get_debug_info(self):
        current_len = self.cur_length()
        p1 = self.get_endpoint1()
        p2 = self.get_endpoint2()
        return {
            "type": "Rod",
            "id": self.id,
            "name": self.name,
            "bob1": self.bob1.name,
            "bob2": self.bob2.name,
            "anchor1": self.anchor1 or "center",
            "anchor2": self.anchor2 or "center",
            "rest_length": round(self.length, 2),
            "current_length": round(current_len, 2),
            "stretch": round(current_len - self.length, 2),
            "bob1.x": round(p1[0], 2),
            "bob1.y": round(p1[1], 2),
            "bob2.x": round(p2[0], 2),
            "bob2.y": round(p2[1], 2),
        }

    def set_property(self, key, value):
        if key == "rest_length":
            self.length = max(1, float(value))
            if self.constraint:
                self.constraint.l = self.length
        elif key == "bob1.x":
            self.bob1.body.position.x = float(value)
        elif key == "bob1.y":
            self.bob1.body.position.y = float(value)
        elif key == "bob2.x":
            self.bob2.body.position.x = float(value)
        elif key == "bob2.y":
            self.bob2.body.position.y = float(value)


class SimulationEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.bobs = []
        self.boxes = []
        self.rods = []
        self.running = False
        self.iterations = 8
        self.dragging_bob = None
        self.dragging_box = None
        self.collision_handler = Collision_Handler()
        self.ground = self.create_box(
            width / 2, height - 20, width, 40, pinned=True
        )

    def create_bob(self, x, y, pinned=False):
        bob = Bob(x, y, pinned)
        self.bobs.append(bob)
        self.collision_handler.add_body(bob.body)
        return bob

    def create_box(
        self, x, y, width=BOX_WIDTH, height=BOX_HEIGHT, pinned=False
    ):
        box = Box(x, y, width, height, pinned)
        self.boxes.append(box)
        self.collision_handler.add_body(box.body)
        return box

    def delete_box(self, box):
        self.rods = [r for r in self.rods if r.bob1 != box and r.bob2 != box]
        if box in self.boxes:
            self.boxes.remove(box)
            self.collision_handler.remove_body(box.body)

    def get_box_at(self, x, y):
        for box in reversed(self.boxes):
            if box.contains(x, y):
                return box
        return None

    def body_at(self, x, y):
        bob = self.get_bob_at(x, y)
        if bob:
            return bob
        box = self.get_box_at(x, y)
        if box:
            return box
        return None

    def force_at(self, x, y, fx, fy):
        body = self.body_at(x, y)
        if body:
            body.body.apply_point_force(Vector(fx, fy), Vector(x, y))
            return body
        return None

    def create_rod(self, bob1, bob2, anchor1=None, anchor2=None):
        rod = Rod(bob1, bob2, anchor1, anchor2)
        self.rods.append(rod)
        return rod

    def delete_bob(self, bob):
        self.rods = [r for r in self.rods if r.bob1 != bob and r.bob2 != bob]
        if bob in self.bobs:
            self.bobs.remove(bob)
            self.collision_handler.remove_body(bob.body)

    def get_bob_at(self, x, y):
        for bob in reversed(self.bobs):
            if bob.contains(x, y):
                return bob
        return None

    def get_rod_at(self, x, y):
        for rod in reversed(self.rods):
            if rod.contains(x, y):
                return rod
        return None

    def toggle_pin(self, obj):
        obj.pinned = not obj.pinned
        default_mass = 1 if isinstance(obj, Bob) else 2
        obj.body.mass = 0 if obj.pinned else default_mass
        obj.body.inv_mass = 1 / obj.body.mass if obj.body.mass > 0 else 0
        obj.body.inv_moi = (
            0 if obj.pinned else (1 / obj.body.moi if obj.body.moi > 0 else 0)
        )

    def set_dragging(self, obj):
        if isinstance(obj, Bob):
            self.dragging_bob = obj
        elif isinstance(obj, Box):
            self.dragging_box = obj

    def release(self):
        self.dragging_bob = None
        self.dragging_box = None

    def move(self, obj, x, y):
        obj.body.position.x = x
        obj.body.position.y = y
        if self.running:
            obj.body.velocity = Vector(0, 0)
            obj.body.ang_velocity = 0.0

    def clear_forces(self):
        for bob in self.bobs:
            bob.body.clear_forces()
            bob.body.clear_torque()

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def toggle(self):
        self.running = not self.running

    def clear(self):
        for bob in self.bobs:
            bob.body.clear_forces()
            bob.body.clear_torque()
        for box in self.boxes:
            box.body.clear_forces()
            box.body.clear_torque()
        self.bobs = []
        self.boxes = []
        self.rods = []
        self.running = False
        self.dragging_bob = None
        self.dragging_box = None
        self.collision_handler = Collision_Handler()
        Bob._id_counter = 0
        Box._id_counter = 0
        Rod._id_counter = 0
        self.ground = self.create_box(
            self.width / 2, self.height - 20, self.width, 40, pinned=True
        )

    def update(self, dt):
        if not self.running:
            return

        for bob in self.bobs:
            if bob != self.dragging_bob and not bob.pinned:
                bob.body.apply_point_force(
                    Vector(
                        GRAVITY.x * bob.body.mass, GRAVITY.y * bob.body.mass
                    ),
                    bob.body.position,
                )

        for box in self.boxes:
            if box != self.dragging_box and not box.pinned:
                box.body.apply_point_force(
                    Vector(
                        GRAVITY.x * box.body.mass, GRAVITY.y * box.body.mass
                    ),
                    box.body.position,
                )

        for bob in self.bobs:
            if bob != self.dragging_bob:
                bob.body.integrate(dt)

        for box in self.boxes:
            if box != self.dragging_box:
                box.body.integrate(dt)

        for _ in range(self.iterations):
            for rod in self.rods:
                rod.solve()

        self.collision_handler.update()

        # for bob in self.bobs:
        #     if bob.body.position.y > self.height - BOB_RADIUS:
        #         bob.body.position.y = self.height - BOB_RADIUS
        #         bob.body.velocity.y *= -0.5
        #     if bob.body.position.x < BOB_RADIUS:
        #         bob.body.position.x = BOB_RADIUS
        #         bob.body.velocity.x *= -0.5
        #     if bob.body.position.x > self.width - BOB_RADIUS:
        #         bob.body.position.x = self.width - BOB_RADIUS
        #         bob.body.velocity.x *= -0.5

        # for box in self.boxes:
        #     half_h = box.height / 2
        #     half_w = box.width / 2
        #     if box.body.position.y > self.height - half_h:
        #         box.body.position.y = self.height - half_h
        #         box.body.velocity.y *= -0.5
        #     if box.body.position.x < half_w:
        #         box.body.position.x = half_w
        #         box.body.velocity.x *= -0.5
        #     if box.body.position.x > self.width - half_w:
        #         box.body.position.x = self.width - half_w
        #         box.body.velocity.x *= -0.5

    def get_debug_info(self, fps, dt):
        return {
            "type": "Simulation",
            "name": "World",
            "is_running": self.running,
            "bob_count": len(self.bobs),
            "box_count": len(self.boxes),
            "rod_count": len(self.rods),
            "iterations": self.iterations,
            "gravity.x": GRAVITY.x,
            "gravity.y": GRAVITY.y,
            "fps": int(fps),
            "dt": round(dt * 1000, 2),
        }

    def set_property(self, key, value):
        global GRAVITY
        if key == "iterations":
            self.iterations = max(1, int(value))
        elif key == "gravity.x":
            GRAVITY = Vector(float(value), GRAVITY.y)
        elif key == "gravity.y":
            GRAVITY = Vector(GRAVITY.x, float(value))

    def serialize(self):
        bob_map = {}
        bobs_data = []
        for i, bob in enumerate(self.bobs):
            bob_map[bob] = i
            bobs_data.append({
                "x": bob.body.position.x,
                "y": bob.body.position.y,
                "pinned": bob.pinned,
                "radius": bob.radius,
                "mass": bob.body.mass,
            })

        box_map = {}
        boxes_data = []
        for i, box in enumerate(self.boxes):
            if box == self.ground:
                continue
            box_map[box] = i
            boxes_data.append({
                "x": box.body.position.x,
                "y": box.body.position.y,
                "width": box.width,
                "height": box.height,
                "pinned": box.pinned,
                "orientation": box.body.orientation,
            })

        rods_data = []
        for rod in self.rods:
            bob1_type = "bob" if rod.bob1 in bob_map else "box"
            bob2_type = "bob" if rod.bob2 in bob_map else "box"
            bob1_idx = bob_map.get(rod.bob1, box_map.get(rod.bob1, -1))
            bob2_idx = bob_map.get(rod.bob2, box_map.get(rod.bob2, -1))
            if bob1_idx >= 0 and bob2_idx >= 0:
                rods_data.append({
                    "bob1_type": bob1_type,
                    "bob1_idx": bob1_idx,
                    "bob2_type": bob2_type,
                    "bob2_idx": bob2_idx,
                    "anchor1": rod.anchor1,
                    "anchor2": rod.anchor2,
                    "length": rod.length,
                })

        return {
            "bobs": bobs_data,
            "boxes": boxes_data,
            "rods": rods_data,
        }

    def load_template(self, data, offset_x=0, offset_y=0):
        bob_map = {}
        box_map = {}

        for i, bob_data in enumerate(data.get("bobs", [])):
            bob = self.create_bob(
                bob_data["x"] + offset_x,
                bob_data["y"] + offset_y,
                pinned=bob_data.get("pinned", False)
            )
            if "radius" in bob_data:
                bob.radius = bob_data["radius"]
                bob.body.radius = bob_data["radius"]
            if "mass" in bob_data and bob_data["mass"] > 0:
                bob.body.mass = bob_data["mass"]
                bob.body.inv_mass = 1 / bob.body.mass
            bob_map[i] = bob

        for i, box_data in enumerate(data.get("boxes", [])):
            box = self.create_box(
                box_data["x"] + offset_x,
                box_data["y"] + offset_y,
                width=box_data.get("width", BOX_WIDTH),
                height=box_data.get("height", BOX_HEIGHT),
                pinned=box_data.get("pinned", False)
            )
            if "orientation" in box_data:
                box.body.orientation = box_data["orientation"]
            box_map[i] = box

        for rod_data in data.get("rods", []):
            bob1_type = rod_data.get("bob1_type", "bob")
            bob2_type = rod_data.get("bob2_type", "bob")
            bob1_idx = rod_data["bob1_idx"]
            bob2_idx = rod_data["bob2_idx"]

            bob1 = bob_map.get(bob1_idx) if bob1_type == "bob" else box_map.get(bob1_idx)
            bob2 = bob_map.get(bob2_idx) if bob2_type == "bob" else box_map.get(bob2_idx)

            if bob1 and bob2:
                anchor1 = rod_data.get("anchor1")
                anchor2 = rod_data.get("anchor2")
                rod = self.create_rod(bob1, bob2, anchor1, anchor2)
                if rod and "length" in rod_data:
                    rod.length = rod_data["length"]
                    if rod.constraint:
                        rod.constraint.l = rod_data["length"]


def load_templates():
    if os.path.exists(TEMPLATES_FILE):
        try:
            with open(TEMPLATES_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_template(name, data):
    templates = load_templates()
    templates[name] = data
    with open(TEMPLATES_FILE, "w") as f:
        json.dump(templates, f, indent=2)


def delete_template(name):
    templates = load_templates()
    if name in templates:
        del templates[name]
        with open(TEMPLATES_FILE, "w") as f:
            json.dump(templates, f, indent=2)
